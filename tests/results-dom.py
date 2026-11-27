"""Real Chromium layout and DOM interaction test, offline harness with mocked API (no network navigation)."""
from pathlib import Path
import re, json, base64, io
from playwright.sync_api import sync_playwright
from PIL import Image
root=Path(__file__).resolve().parents[1]; public=root/'public'
html=re.sub(r'<script type="module"[^>]*></script>','',(public/'index.html').read_text())
source='\n'.join(re.sub(r'\bexport (?=(?:const|function)\b)','',(public/x).read_text()) for x in ['qr.js','presentation-theme.js'])+'\n'+re.sub(r'^import[^\n]+\n','',(public/'app.js').read_text(),flags=re.M)
source+='\nwindow.harness={set(s){state=s;phoneLastSync=Date.now();phoneSyncFailed=false;render()},get(){return state},setApi(f){api=f},render,phone,activityPhone,tick,selection(){return activityChoice},getDraft(){return activityDraft},deck(){return draft}};'
# about:blank navigation is not needed. Actual app renderer and event listeners run in a browser with a fake location and API.
boot='''({src,path})=>{const data=new Map();const store={getItem:k=>k==='jksAdmin'&&path!=='/join'?'test':data.get(k)||null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)};const loc=new URL('https://test.example'+path);const c={randomUUID:()=> 'participant-'+Math.random().toString(36).slice(2)+'-abcdef'};new Function('location','localStorage','sessionStorage','crypto','fetch','setInterval','setTimeout','WebSocket',src)(loc,store,store,c,()=>new Promise(()=>{}),()=>0,()=>0,function(){});}'''
img=Image.new('RGB',(24,24),(103,142,177));buf=io.BytesIO();img.save(buf,format='PNG');bg='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
slides=[dict(id=t,type=t,title={'join':'Join the session','rating':'Rate the presentation','competition':'Competition A','wordcloud':'One word','qa':'Questions','video':'Video','standard':'Welcome','poll':'Choose an option','countdown':'Countdown','results':'Results'}[t],mobileBg=bg,mobileColor='#111111',votePanel='#f4f3f2',ratingMax=10 if t=='rating' else 7,options='Yes\nNo',mobileQuestion='What do you think?') for t in ['standard','join','competition','rating','wordcloud','qa','video','poll','countdown','results']]
base=dict(title='Example presentation',slides=slides,rounds=[dict(id='1',name='Team A')],screens=[0,0],completed=[],ratingMax=7,revision=1,serverTime=0,timerEnd=0,pausedRemaining=0,open=False,voteEpoch=1,interaction=None)
def state(i,phase=None):
 import time
 s=dict(base,screens=[i,i],serverTime=int(time.time()*1000),revision=i+2)
 if i in [3,4,5,7,8]:s['interaction']=dict(slide=slides[i]['id'],token='token-'+str(i),open=True,end=s['serverTime']+42000)
 if i==2:s.update(competitionSlide='competition',active='1',open=phase=='voting',timerEnd=s['serverTime']+42000 if phase=='countdown' else 0)
 if phase=='finished':s['phoneEnded']=True
 if i==9:s['publishedBySlide']={'results':dict(title='Contest A',source='competition',max=7,items=[dict(name='Team A',average=6,count=4)])}
 return s

# Check true rendered bounding boxes in the actual TV, controller, and participant views.
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);errors=[]; checks=0
 def make(path,w,h):
  page=browser.new_page(viewport={'width':w,'height':h});page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(html);page.evaluate(boot,dict(src=source,path=path));return page
 def result_state(n,kind):
  import time
  ss=state(9 if kind=='published' else 2);ss.update(open=False,timerEnd=0,active=None,ledgerSlide='competition',competitionSlide='competition',serverTime=int(time.time()*1000),resultsRevealedAt=int(time.time()*1000),rounds=[dict(id=str(i),name='Team '+str(i)+' — additional name') for i in range(1,n+1)],completed=[str(i) for i in range(1,n+1)])
  ss['slides'][2]['title']='A long competition title with multiple words and a second line';ss['results']=[dict(**r,average=6 if i==0 else 4.5 if i<3 else 0,count=8 if i<3 else 0) for i,r in enumerate(ss['rounds'])];ss['showResults']=kind=='reveal';ss['publishedBySlide']={'results':dict(title=ss['slides'][2]['title'],source='competition',max=7,items=ss['results'],publishedAt=ss['serverTime'])} if kind=='published' else {}
  if kind=='group':ss['roundResult']=dict(slide='competition',round='1',name='Team A',max=10,count=8,average=6.5,distribution=[0,0,1,0,0,3,1,1,1,1])
  return ss
 def verify(page,selector,kind,n):
  global checks
  board=page.locator(selector).first;assert board.is_visible(),(selector,kind)
  metrics=board.evaluate("""e=>{let bounds=e.getBoundingClientRect(),outer=e.closest('.slide,.phone-screen').getBoundingClientRect();let inside=(a,b)=>a.left>=b.left-1&&a.right<=b.right+1&&a.top>=b.top-1&&a.bottom<=b.bottom+1;let rows=[...e.querySelectorAll('.fit-score-row,.fit-distribution-column')].filter(x=>x.getClientRects().length);return {fits:inside(bounds,outer),width:e.clientWidth,height:e.clientHeight,overflow:e.scrollWidth>e.clientWidth+1||e.scrollHeight>e.clientHeight+1,rows:rows.length,debug:rows.map(x=>[x.className,x.clientWidth,x.scrollWidth,x.clientHeight,x.scrollHeight,x.getBoundingClientRect().bottom,bounds.bottom]),rowsFit:rows.every(x=>inside(x.getBoundingClientRect(),bounds)&&x.scrollWidth<=x.clientWidth+1&&x.scrollHeight<=x.clientHeight+1),rootOverflow:document.documentElement.scrollWidth>innerWidth,footerFit:e.closest('.phone-screen')?e.closest('.phone-screen').scrollHeight<=e.closest('.phone-screen').clientHeight+1:true}}""")
  assert metrics['fits'] and not metrics['overflow'] and metrics['rowsFit'] and not metrics['rootOverflow'] and metrics['footerFit'],(selector,kind,n,metrics)
  assert metrics['rows']==(10 if kind=='group' else min(8,n)),metrics
  checks+=1
 for path,w,h,selector in [('/tv/2',1920,1080,'.fit-scoreboard'),('/tv/2',1280,720,'.fit-scoreboard'),('/join',320,568,'.fit-scoreboard'),('/join',390,844,'.fit-scoreboard'),('/join',650,998,'.fit-scoreboard'),('/control',1366,768,'.production-preview .fit-scoreboard'),('/control',1920,1080,'.production-preview .fit-scoreboard')]:
  page=make(path,w,h)
  for kind,n in [('reveal',8),('published',8),('group',8),('published',17)]:
   ss=result_state(n,kind);page.evaluate('s=>harness.set(s)',ss);verify(page,selector,kind,n)
   if path=='/control':verify(page,'.production-phone .fit-scoreboard',kind,n)
   if kind=='published' and n==17:
    page.evaluate("()=>{for(const e of document.querySelectorAll('[data-score-pages]'))e.dataset.scoreStart=Date.now()-8500;harness.tick()}");assert page.locator(selector).first.locator('[data-score-page-label]').inner_text()=='Seite 2 / 3';verify(page,selector,kind,n)
   if n==8 and path in ['/tv/2','/join'] and w in [1920,390]:page.screenshot(path=f'/tmp/jks310-{path.split("/")[1]}-{kind}.png')
  page.close()
 assert not errors,errors;browser.close();print(f'{checks} Chromium result layout checks passed across actual TV, participant and controller views; automatic paging verified.')

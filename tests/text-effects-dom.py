"""Real Chromium layout and DOM interaction test, offline harness with mocked API (no network navigation)."""
from pathlib import Path
import re, json, base64, io
from playwright.sync_api import sync_playwright
from PIL import Image
root=Path(__file__).resolve().parents[1]; public=root/'public'
html=re.sub(r'<script type="module"[^>]*></script>','',(public/'index.html').read_text())
source='\n'.join(re.sub(r'\bexport (?=(?:const|function)\b)','',(public/x).read_text()) for x in ['qr.js','presentation-theme.js'])+'\n'+re.sub(r'^import[^\n]+\n','',(public/'app.js').read_text(),flags=re.M)
source+='\nwindow.harness={set(s){state=s;phoneLastSync=Date.now();phoneSyncFailed=false;render()},get(){return state},setApi(f){api=f},render,phone,activityPhone,selection(){return activityChoice},getDraft(){return activityDraft},deck(){return draft}};'
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
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);errors=[]
 def newpage(path):
  page=browser.new_page(viewport={'width':1366,'height':768});page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(html);page.evaluate(boot,dict(src=source,path=path));page.evaluate('s=>harness.set(s)',state(0));return page
 editor=newpage('/admin');editor.locator('[data-action="section-typography"]').click();mode=editor.locator('[data-prop="textEffect"]');assert mode.input_value()=='none';assert not editor.locator('[data-number="textEffectBlur"]').is_visible();mode.select_option('shadow');editor.locator('[data-prop="textEffectColor"]').fill('#123456');editor.locator('[data-number="textEffectOpacity"]').fill('85');editor.locator('[data-number="textEffectBlur"]').fill('18');editor.locator('[data-number="textEffectY"]').fill('9');shadow=editor.locator('#preview .slide-copy h2').evaluate('e=>getComputedStyle(e).textShadow');assert 'rgba(18, 52, 86, 0.85)' in shadow,shadow;assert editor.evaluate('harness.deck().slides[0].textEffectBlur')==18
 mode.select_option('glow');assert not editor.locator('[data-number="textEffectY"]').is_visible();glow=editor.locator('#preview .slide-copy h2').evaluate('e=>getComputedStyle(e).textShadow');assert '0px 0px' in glow,glow
 editor.locator('[data-action="view-mobile"]').click();editor.locator('[data-prop="mobileTextEffect"]').select_option('shadow');assert editor.locator('#phone-preview .phone-content h2').evaluate('e=>getComputedStyle(e).textShadow')!='none';assert editor.evaluate('harness.deck().slides[0].textEffect')=='glow';editor.locator('[data-action="design"]').click();editor.locator('[data-theme-tab="tvTypography"]').click();editor.locator('[data-theme-key="textEffect"]').select_option('shadow');assert editor.locator('[data-theme-tv] .slide-copy h2').evaluate('e=>getComputedStyle(e).textShadow')!='none';editor.locator('[data-theme-save]').click();assert editor.evaluate('harness.deck().theme.textEffect')=='shadow'
 tv=newpage('/tv/1');st=state(0);st['slides'][0].update(textEffect='glow',textEffectColor='#ffffff',textEffectOpacity=90,textEffectBlur=18);tv.evaluate('s=>harness.set(s)',st);assert 'rgba(255, 255, 255, 0.9)' in tv.locator('.slide-copy h2').evaluate('e=>getComputedStyle(e).textShadow');assert tv.locator('.slide-copy p').evaluate('e=>getComputedStyle(e).textShadow')!='none';assert not errors,errors
 browser.close();print('Chromium text effects: editor control visibility, colour, numeric values, live preview, glow, independent phone setting, theme editor and TV computed styles passed (mocked API).')

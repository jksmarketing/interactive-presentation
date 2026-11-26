"""Browser interaction test; HTTP proxy via Playwright route to local Worker simulation."""
import os, subprocess, time, json, urllib.request, urllib.error
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
os.chdir(Path(__file__).resolve().parents[1])
server=subprocess.Popen(['node','tests/local-server.mjs'],stdout=subprocess.DEVNULL)
base='http://127.0.0.1:8765'; url='https://jks-test.example'; offline=False; votes=0

def request(path, body=None, admin=False):
    headers={'Content-Type':'application/json'}
    if admin: headers['Authorization']='Bearer test'
    with urllib.request.urlopen(urllib.request.Request(base+path,headers=headers,data=json.dumps(body).encode() if body is not None else None),timeout=5) as r: return json.load(r)
try:
    time.sleep(.5)
    st=request('/api/state',admin=True)
    slides=st['slides']; slides[2]['duration']=5; slides[0]['mobileTitle']='Mobile welcome'; slides[0]['mobileText']='Custom mobile content'
    request('/api/edit',{'title':st['title'],'slides':slides,'rounds':st['rounds'],'editVersion':st['editVersion']},True)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']); context=browser.new_context(viewport={'width':390,'height':844}); page=context.new_page(); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        def route(r):
            global votes
            path=r.request.url[len(url):]
            if offline and path.startswith('/api/'): r.abort(); return
            if path.startswith('/api/vote'): votes+=1
            if not path.startswith('/api/'):
                file=Path('public')/('index.html' if not path.split('?')[0].endswith('.js') else path.split('?')[0].lstrip('/')); r.fulfill(status=200,body=file.read_bytes(),content_type='text/javascript' if file.suffix=='.js' else 'text/html');return
            try:
                req=urllib.request.Request(base+path,headers={'Content-Type':'application/json'},data=r.request.post_data.encode() if r.request.post_data else None,method=r.request.method)
                with urllib.request.urlopen(req,timeout=5) as response: r.fulfill(status=response.status,body=response.read(),content_type='application/json')
            except urllib.error.HTTPError as e: r.fulfill(status=e.code,body=e.read(),content_type='application/json')
        page.route(url+'/**',route);page.goto(url+'/join',timeout=8000)
        expect(page.locator('[data-phone-phase=waiting]')).to_be_visible(timeout=8000);expect(page.locator('.connection-label')).to_have_text('Verbunden');expect(page.get_by_text('Mobile welcome')).to_be_visible();expect(page.get_by_text('Custom mobile content')).to_be_visible()
        request('/api/control',{'screens':[2,2]},True);st=request('/api/state',admin=True);request('/api/control',{'guided':'start','slide':slides[2]['id'],'round':'1','epoch':st['voteEpoch']},True)
        expect(page.locator('[data-phone-phase=countdown]')).to_be_visible(timeout=5000);expect(page.locator('[data-phone-phase=voting]')).to_be_visible(timeout=10000)
        expect(page.get_by_role('button',name='Stimme abgeben')).to_be_disabled();page.get_by_role('button',name='7 von 7 Punkten').click();expect(page.get_by_role('button',name='Stimme abgeben')).to_be_enabled();page.get_by_role('button',name='Stimme abgeben').click();expect(page.locator('[data-phone-phase=submitted]')).to_be_visible();assert votes==1
        page.reload();expect(page.locator('[data-phone-phase=submitted]')).to_be_visible();assert votes==1
        offline=True;expect(page.locator('.phone-connection')).to_have_attribute('data-status','reconnecting',timeout=10000);offline=False;expect(page.locator('.phone-connection')).to_have_attribute('data-status','online',timeout=10000)
        st=request('/api/state',admin=True);request('/api/control',{'guided':'close','slide':slides[2]['id'],'round':'1','epoch':st['voteEpoch']},True);expect(page.locator('[data-phone-phase=waiting]')).to_be_visible();expect(page.get_by_text('Gruppe 2')).to_be_visible()
        request('/api/control',{'screens':[3,3]},True);expect(page.get_by_role('heading',name='Hauptgang')).to_be_visible();assert not errors,errors
        browser.close();print('Participant browser checks passed: waiting, custom content, countdown, seven-point voting, receipt/reload, connection loss/recovery, next group and slide navigation.')
finally:
    server.terminate();server.wait()

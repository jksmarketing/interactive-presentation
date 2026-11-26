from playwright.sync_api import sync_playwright, expect
import subprocess,time,os
from pathlib import Path
os.chdir(Path(__file__).resolve().parents[1])
server=subprocess.Popen(['node','tests/local-server.mjs'],stdout=subprocess.DEVNULL)
try:
 time.sleep(.5)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None),args=['--no-sandbox']); context=browser.new_context(viewport={'width':1440,'height':900},accept_downloads=True); errors=[]
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  base='http://127.0.0.1:8765';page.goto(base+'/admin');page.locator('#pw').fill('test');page.get_by_role('button',name='Sign in').click();expect(page.locator('.slide-list')).to_be_visible(timeout=5000)
  page.locator('textarea[data-prop=title]').fill('Browser test');page.locator('textarea[data-prop=subtitle]').click();expect(page.locator('#save-status')).to_contain_text('All changes saved',timeout=6000)
  page.get_by_role('button',name='Undo',exact=True).click();expect(page.locator('textarea[data-prop=title]')).to_have_value('Willkommen');page.get_by_role('button',name='Redo',exact=True).click();expect(page.locator('textarea[data-prop=title]')).to_have_value('Browser test');page.get_by_role('button',name='Save',exact=True).click();expect(page.locator('#save-status')).to_contain_text('All changes saved',timeout=5000)
  page.reload();expect(page.locator('textarea[data-prop=title]')).to_have_value('Browser test',timeout=5000)
  page.locator('[data-action=section-typography]').click();target=page.locator('#preview .slide-copy');box=target.bounding_box();page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);page.mouse.down();page.mouse.move(box['x']+box['width']/2+45,box['y']+box['height']/2+30,steps=8);page.mouse.up();assert float(page.locator('[data-number=textX]').input_value())>50
  page.locator('[data-action=section-content]').click();page.locator('#preview .slide-copy h2').dblclick();expect(page.locator('#preview .slide-copy h2')).to_have_attribute('contenteditable','plaintext-only');page.keyboard.type('Direct edit');page.locator('.stage-footer').click();expect(page.locator('textarea[data-prop=title]')).to_have_value('Direct edit')
  page.locator('[data-action=gallery]').click();page.locator('dialog input[value=join]').check();page.locator('dialog button[value=add]').click();expect(page.locator('#preview .join-qr svg')).to_be_visible();page.get_by_role('button',name='Save',exact=True).click();expect(page.locator('#save-status')).to_contain_text('All changes saved',timeout=6000)
  page.screenshot(path='/tmp/jks-editor.png');page.goto(base+'/library');expect(page.locator('.deck-card')).to_have_count(1,timeout=5000);page.locator('.deck-menu summary').click();page.get_by_role('button',name='Duplicate',exact=True).click();page.locator('dialog input').fill('Copied deck');page.locator('dialog button[value=create]').click();expect(page.locator('[data-event=title]')).to_have_value('Copied deck',timeout=5000)
  page.goto(base+'/control');expect(page.locator('.timeline-list')).to_be_visible(timeout=5000);tv=context.new_page();tv.on('pageerror',lambda e:errors.append(str(e)));tv.goto(base+'/tv/1');guest=browser.new_context(viewport={'width':390,'height':844});phone=guest.new_page();phone.on('pageerror',lambda e:errors.append(str(e)));phone.goto(base+'/join');expect(phone.locator('.phone-screen')).to_be_visible(timeout=5000)
  page.locator('[data-action="live:3"]').click();expect(tv.locator('.slide-copy h2')).to_have_text('Weihnachtsgeschichten in 60 Sekunden',timeout=7000)
  page.get_by_role('button',name='Blackout').click();expect(tv.locator('.blackout')).to_be_visible(timeout=7000);page.get_by_role('button',name='Restore TVs').click();expect(tv.locator('.slide-copy')).to_be_visible(timeout=7000)
  page.screenshot(path='/tmp/jks-control.png');assert not errors,errors
  print('Browser checks passed: login, autosave, reload, undo/redo, drag, direct text edit, QR, duplication, timeline, TV, phone, blackout.')
  browser.close()
finally:
 server.terminate();server.wait()

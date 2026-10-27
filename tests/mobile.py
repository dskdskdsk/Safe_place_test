from pathlib import Path
from playwright.sync_api import sync_playwright
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(Path(__file__).resolve().parents[1])))
Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:') else r.abort())
 page.add_init_script('''(()=>{
 const v=new EventTarget();Object.assign(v,{width:390,height:844,offsetTop:0,offsetLeft:0,scale:1});
 Object.defineProperty(window,'visualViewport',{value:v});
 window.testViewport=(height,offsetTop=0,scale=1)=>{Object.assign(v,{height,offsetTop,scale});v.dispatchEvent(new Event('resize'));};
 })()''')
 page.goto(f'http://127.0.0.1:{server.server_port}/index.html');page.wait_for_timeout(500)
 assert not errors,errors
 page.evaluate("()=>{document.querySelector('[data-page=settings]').click();document.querySelector('[data-page=settings]').focus();openHabitSheet()}")
 page.wait_for_timeout(350)
 assert page.evaluate("document.activeElement.id")=='habit-name-input'
 assert page.evaluate("document.querySelector('.bnav').inert")
 page.evaluate('testViewport(360)');page.wait_for_timeout(400)
 assert page.evaluate("document.documentElement.classList.contains('keyboard-open')")
 geo=page.evaluate("()=>{const s=document.getElementById('habit-sheet').getBoundingClientRect(),i=document.getElementById('habit-name-input').getBoundingClientRect();return {top:s.top,bottom:s.bottom,inputTop:i.top,inputBottom:i.bottom}}")
 assert geo['top']>=0 and geo['bottom']<=361,geo
 assert geo['inputTop']>=0 and geo['inputBottom']<=360,geo
 assert page.evaluate("getComputedStyle(document.getElementById('habit-name-input')).fontSize")=='16px'
 # Reach last action by scrolling the sheet; background page stays still.
 page.locator('#habit-save-btn').scroll_into_view_if_needed()
 assert page.locator('#habit-save-btn').bounding_box()['y']+44<=361
 page.evaluate("()=>{window.dialogResult=null;showDialog({title:'Long test',text:'Synthetic line\\n'.repeat(100),actions:[{label:'Cancel',value:false},{label:'Confirm',primary:true,value:true}]}).then(x=>dialogResult=x)}")
 page.wait_for_timeout(250)
 assert page.evaluate("!!document.getElementById('habit-sheet').closest('[inert]')")
 foot=page.locator('#err-dlg .ob-foot').bounding_box()
 assert foot['y']>=0 and foot['y']+foot['height']<=361,foot
 assert page.evaluate("(()=>{let b=document.querySelector('#err-dlg .ob-body');return b.scrollHeight>b.clientHeight})()")
 # Keyboard loop stays in top modal.
 for _ in range(8):page.keyboard.press('Tab')
 assert page.evaluate("document.getElementById('err-dlg').contains(document.activeElement)")
 Path(__file__).with_name('artifacts').mkdir(exist_ok=True)
 page.screenshot(path=str(Path(__file__).with_name('artifacts')/'dialog-keyboard.png'))
 page.keyboard.press('Escape');page.wait_for_timeout(250)
 assert page.locator('#err-dlg').count()==0
 assert page.evaluate("document.getElementById('habit-sheet').classList.contains('open')")
 assert page.evaluate("document.querySelector('.bnav').inert")
 page.keyboard.press('Escape');page.wait_for_timeout(350)
 assert not page.evaluate("document.documentElement.classList.contains('modal-open')")
 assert not page.evaluate("document.querySelector('.bnav').inert")
 page.evaluate('testViewport(844)');page.wait_for_timeout(300)
 assert page.evaluate("document.activeElement.dataset.page")=='settings'
 # Closing a sheet immediately cannot resurrect its delayed input focus.
 page.evaluate('()=>{openHabitSheet();closeHabitSheet()}');page.wait_for_timeout(500)
 assert page.evaluate("document.activeElement.id")!='habit-name-input'
 page.evaluate('testViewport(844)');page.wait_for_timeout(300)
 assert not page.evaluate("document.documentElement.classList.contains('keyboard-open')")
 # A visible input should not be centred on focus.
 page.evaluate("()=>{let p=document.getElementById('page-settings');let i=document.getElementById('gemini-key-input');i.closest('.gem-body').style.maxHeight='2000px';i.scrollIntoView({block:'center'});window.beforeScroll=p.scrollTop;i.focus({preventScroll:true})}")
 page.wait_for_timeout(350)
 assert abs(page.evaluate("document.getElementById('page-settings').scrollTop-beforeScroll"))<2
 # Pinch-zoom should not update the layout geometry.
 old=page.evaluate("document.documentElement.style.getPropertyValue('--sp-view-height')")
 page.evaluate('testViewport(300,100,2)');page.wait_for_timeout(250)
 assert page.evaluate("document.documentElement.style.getPropertyValue('--sp-view-height')")==old
 page.evaluate('testViewport(360,40,1)');page.wait_for_timeout(300)
 page.evaluate('openEmotionSheet()');page.wait_for_timeout(350)
 g=page.locator('#emotion-sheet').bounding_box();assert g['y']>=40 and g['y']+g['height']<=401,g
 page.keyboard.press('Escape');page.wait_for_timeout(300)
 # Landscape / narrow layouts: action footer remains reachable without horizontal overflow.
 for width,height in [(844,390),(320,568)]:
  page.set_viewport_size({'width':width,'height':height})
  page.evaluate(f'testViewport({height})')
  page.evaluate("()=>{showDialog({title:'Long title '.repeat(8),text:'Long body line\\n'.repeat(80)})}")
  page.wait_for_timeout(300)
  bounds=page.locator('#err-dlg .ob-foot').bounding_box()
  assert bounds['y']+bounds['height']<=height+1,bounds
  assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
  page.keyboard.press('Escape');page.wait_for_timeout(200)
 page.set_viewport_size({'width':390,'height':844});page.evaluate('testViewport(360)')
 # PIN cannot be escaped. Verify overlay blocks background.
 page.evaluate("openPinOverlay('unlock')");page.wait_for_timeout(300)
 page.keyboard.press('Escape');page.wait_for_timeout(150)
 assert page.evaluate("document.getElementById('lock-screen').style.display")=='flex'
 assert page.evaluate("document.getElementById('app').inert")
 page.evaluate('closePinOverlay()');page.wait_for_timeout(200)
 assert not errors,errors
 browser.close()
 print('PASS: startup, simulated keyboard geometry, scrollable sheet, long dialog/footer, nested modals, Tab/Escape, focus restore, no stale focus, no unnecessary centering, pinch zoom, viewport offset, PIN isolation')

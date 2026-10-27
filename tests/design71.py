from pathlib import Path
import json
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'tests/artifacts/design71';OUT.mkdir(parents=True,exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
results=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(375,667),(390,844),(393,852),(402,874),(414,896),(430,932),(440,956),(844,390)]:
  for dark in [False,True]:
   ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True,device_scale_factor=1)
   ctx.route('**/*',lambda r:r.continue_() if r.request.url.startswith(url) else r.abort())
   p=ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(url);p.wait_for_function('_writeReady')
   p.evaluate('''dark=>{S.settings.dark=dark;applyTheme(dark);addSummaryEntry('Тестовий запис: спокійний день, довга думка та вдячність. '.repeat(5));day().media=[{name:'Довга українська назва книжки про повсякденне життя та маленькі радощі',cat:'watch',status:'active',rating:0}];renderSummaryEntries();renderMediaList();renderCal()}''',dark)
   for tab in ['today','notes','dash','settings']:
    p.locator('[data-page='+tab+']').click();p.wait_for_timeout(120)
    geo=p.evaluate('''()=>{let p=document.querySelector('.page.active');return {client:p.clientWidth,scroll:p.scrollWidth,body:document.body.scrollWidth,viewport:innerWidth}}''')
    assert geo['scroll']<=geo['client']+1,(width,dark,tab,geo)
    assert geo['body']<=geo['viewport']+1,(width,dark,tab,geo)
    if width in [375,430]:p.screenshot(path=str(OUT/f'{width}-{dark}-{tab}.png'))
   p.locator('[data-page=today]').click()
   assert p.locator('.summary-entry-actions').first.evaluate('(e)=>getComputedStyle(e).opacity')=='1'
   assert p.locator('.summary-entry-btn').first.bounding_box()['width']>=44
   assert p.evaluate("CSS.supports('font-size',getComputedStyle(document.documentElement).getPropertyValue('--sm'))")
   # A larger root font exercises reflow without changing saved preferences.
   p.evaluate("document.documentElement.style.fontSize='20px'")
   for tab in ['today','notes','settings']:
    p.locator('[data-page='+tab+']').click()
    assert p.evaluate("(()=>{let e=document.querySelector('.page.active');return e.scrollWidth<=e.clientWidth+1})()"),(width,dark,tab,'large text overflow')
   assert not errors,errors
   results.append({'width':width,'height':height,'dark':dark,'status':'PASS'})
   ctx.close()
 browser.close()
(OUT/'results.json').write_text(json.dumps(results,indent=2));print('PASS',len(results),'viewport/theme configurations, 4 tabs, large-root text reflow')

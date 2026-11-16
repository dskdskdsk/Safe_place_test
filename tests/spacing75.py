from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];out=root/'tests/artifacts/spacing75';out.mkdir(parents=True,exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
srv=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width in [320,375,390,400,430,440]:
  for dark in [False,True]:
   p=b.new_page(viewport={'width':width,'height':844},is_mobile=True,has_touch=True);errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
   p.goto(f'http://127.0.0.1:{srv.server_port}');p.wait_for_function('_writeReady');p.evaluate('(d)=>applyTheme(d)',dark)
   for size in [16,20]:
    p.evaluate('(s)=>document.documentElement.style.fontSize=s+"px"',size)
    for tab in ['today','notes','dash','settings']:
     p.locator('[data-page='+tab+']').click();p.wait_for_timeout(100)
     if size==16 and tab=='today':
      rows=p.locator('#rating-row .rating-value').evaluate_all('(es)=>new Set(es.map(e=>Math.round(e.getBoundingClientRect().top))).size')
      assert rows==(1 if width>=390 else 2),(width,rows)
     if size==16 and tab=='settings':
      for button in ['#lang-uk-btn','#lang-en-btn']:
       assert p.locator(button).evaluate('(e)=>getComputedStyle(e).whiteSpace')=='nowrap'
       assert p.locator(button).bounding_box()['height']<40
     assert p.evaluate('(()=>{let p=document.querySelector(".page.active");return p.scrollWidth<=p.clientWidth+1})()'),(width,dark,size,tab)
   p.evaluate('document.documentElement.style.fontSize="16px"');p.locator('[data-page=today]').click()
   print(width,dark,p.locator('[data-block=events]>.cb').evaluate('(e)=>getComputedStyle(e).paddingLeft'))
   if width in [375,400,430]:p.screenshot(path=str(out/f'75.0-{width}-{dark}.png'))
   assert not errors,errors;p.close()
 b.close()
srv.shutdown();print('PASS: 12 viewport/theme combinations, four tabs, normal and enlarged text')

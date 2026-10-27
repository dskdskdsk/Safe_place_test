from pathlib import Path
import subprocess,json
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from functools import partial
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tests/artifacts/type712';OUT.mkdir(parents=True,exist_ok=True)
base=subprocess.check_output(['git','show','v70.5:index.html'],cwd=ROOT,text=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));Thread(target=s.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{s.server_port}'
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);results=[]
 for width in [375,390,430]:
  for dark in [False,True]:
   styles=[]
   for baseline in [True,False]:
    c=b.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True,service_workers='block');p=c.new_page()
    c.route('**/*',lambda r:r.fulfill(status=200,content_type='text/html',body=base) if r.request.url.endswith('/baseline') else (r.continue_() if r.request.url.startswith(url) else r.abort()))
    p.goto(url+('/baseline' if baseline else '/'));p.wait_for_function('_writeReady');p.evaluate('d=>{applyTheme(d);addSummaryEntry("Тестовий запис українською. Ґ Є Ї І");renderSummaryEntries()}',dark)
    snapshot={}
    for tab in ['today','notes','dash','settings']:
     p.locator('[data-page='+tab+']').click();p.wait_for_timeout(250)
     snapshot[tab]=p.evaluate('''()=>Array.from(document.querySelectorAll('.page.active *,.bnav *')).map(e=>{let c=getComputedStyle(e);return [e.tagName,...['fontFamily','fontSize','fontWeight','lineHeight','letterSpacing','textTransform'].map(k=>c[k])]})''')
     if not baseline:assert p.evaluate('(()=>{let e=document.querySelector(".page.active");return e.scrollWidth<=e.clientWidth+1})()'),(width,tab)
    styles.append(snapshot)
    if not baseline:
     p.locator('[data-page=today]').click()
     for status in ['work','home','travel']:
      chip=p.locator('[data-status='+status+']');chip.click();p.wait_for_timeout(250)
      state=chip.evaluate('(e)=>{let s=getComputedStyle(e);return [s.borderColor,s.color,s.boxShadow,e.className]}');assert state[0]==state[1] and state[2]!='none',(status,state)
      chip.click();assert 'sel-' not in chip.get_attribute('class')
     chip=p.locator('[data-status=home]');chip.click();p.reload();p.wait_for_function('_writeReady');assert 'sel-home' in chip.get_attribute('class');p.evaluate('d=>applyTheme(d)',dark)
     rect=chip.bounding_box();p.mouse.move(rect['x']+20,rect['y']+15);p.mouse.down();assert chip.evaluate('(e)=>getComputedStyle(e).outlineStyle')=='solid';p.mouse.up()
     p.screenshot(path=str(OUT/f'{width}-{dark}.png'))
    c.close()
   (OUT/'before.json').write_text(json.dumps(styles[0]));(OUT/'after.json').write_text(json.dumps(styles[1]))
   assert styles[0]==styles[1],(width,dark,'Typography differs from 70.5')
   results.append([width,dark,'PASS'])
 b.close()
(OUT/'results.json').write_text(json.dumps(results));print('PASS: 6 viewport/theme pairs; typography equal to 70.5 on 4 tabs; status select/deselect/reload/press; no page overflow')

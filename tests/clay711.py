"""Contrast, light entry states and dark-theme equivalence to release 71.0."""
from pathlib import Path
import json, subprocess, re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'tests/artifacts/clay711';OUT.mkdir(parents=True,exist_ok=True)
BASELINE=subprocess.check_output(['git','show','v71.0:index.html'],cwd=ROOT,text=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
def ratio(a,b):
 def lum(s):
  v=[float(x)/255 for x in re.findall(r'[\d.]+',s)[:3]];v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v];return sum(x*y for x,y in zip(v,[.2126,.7152,.0722]))
 x,y=sorted([lum(a),lum(b)]);return (y+.05)/(x+.05)
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 snapshots=[];contrasts={}
 for baseline in [True,False]:
  ctx=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,service_workers='block')
  def route(r):
   if r.request.url==url+'/baseline.html':r.fulfill(status=200,content_type='text/html',body=BASELINE)
   elif r.request.url.startswith(url):r.continue_()
   else:r.abort()
  ctx.route('**/*',route);p=ctx.new_page();p.goto(url+('/baseline.html' if baseline else '/'));p.wait_for_function('_writeReady')
  p.evaluate("()=>{addSummaryEntry('Тихий ранок. Кілька думок і маленька вдячність.');renderSummaryEntries();applyTheme(true)}")
  snapshot={}
  for tab in ['today','notes','dash','settings']:
   p.locator('[data-page='+tab+']').click();p.wait_for_timeout(400)
   snapshot[tab]=p.evaluate("""()=>Array.from(document.querySelectorAll('.page.active,.page.active *,.bnav,.bnav *')).map(e=>{const c=getComputedStyle(e);return [e.tagName,e.className,...['color','backgroundColor','backgroundImage','borderTopColor','borderLeftColor','boxShadow','fontSize','fontWeight','lineHeight','padding','borderRadius'].map(k=>c[k])]})""")
  snapshots.append(snapshot)
  if not baseline:
   p.locator('[data-page=today]').click();p.evaluate('applyTheme(false)');p.wait_for_timeout(300)
   assert p.locator('meta[name=theme-color]').get_attribute('content')=='rgb(250 249 245)'
   for name,sel in [('entry','.summary-entry'),('primary','.summary-send-btn'),('selected','.preset-btn.active')]:
    colors=p.locator(sel).first.evaluate('(e)=>{let c=getComputedStyle(e);return [c.color,c.backgroundColor]}');contrasts[name]=round(ratio(*colors),2);assert contrasts[name]>=4.5,(name,colors,contrasts[name])
   p.locator('.summary-entry').first.scroll_into_view_if_needed();p.screenshot(path=str(OUT/'light-entry.png'))
   p.evaluate("()=>{const e=document.querySelector('.summary-entry');e.classList.add('summary-entry-excluded');const b=e.querySelector('.summary-entry-del');b.classList.add('summary-entry-del-armed');b.textContent='Видалити?'}")
   p.wait_for_timeout(300)
   assert p.locator('.summary-entry').first.evaluate('(e)=>getComputedStyle(e).opacity')=='1'
   colors=p.locator('.summary-entry-del-armed').evaluate('(e)=>{let c=getComputedStyle(e);return [c.color,c.backgroundColor]}');assert ratio(*colors)>=4.5
   p.screenshot(path=str(OUT/'light-excluded-delete.png'))
   p.evaluate("()=>{addVoiceSummaryEntry('synthetic-voice',12);renderSummaryEntries()}")
   p.locator('.summary-entry-voice').scroll_into_view_if_needed();p.screenshot(path=str(OUT/'light-voice.png'))
   colors=p.locator('.voice-msg-time').evaluate('(e)=>[getComputedStyle(e).color,getComputedStyle(e.closest(\'.voice-msg\')).backgroundColor]');contrasts['voice-time']=round(ratio(*colors),2);assert contrasts['voice-time']>=4.5
   p.evaluate('applyTheme(true)');assert p.locator('meta[name=theme-color]').get_attribute('content')=='rgb(23 22 20)'
  ctx.close()
 (OUT/'dark-before.json').write_text(json.dumps(snapshots[0],indent=2));(OUT/'dark-after.json').write_text(json.dumps(snapshots[1],indent=2))
 assert snapshots[0]==snapshots[1],'Dark computed style regression'
 browser.close()
(OUT/'results.json').write_text(json.dumps({'dark_styles':'unchanged vs v71.0','contrast':contrasts,'entry_states':'PASS'},indent=2));print('PASS dark computed styles across four tabs; light entry/delete/voice states; contrast:',contrasts)

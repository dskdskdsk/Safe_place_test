from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tests/artifacts/rating714';OUT.mkdir(parents=True,exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));Thread(target=s.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{s.server_port}'
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for w in [375,390,430]:
  for dark in [False,True]:
   c=b.new_context(viewport={'width':w,'height':844},is_mobile=True,has_touch=True,service_workers='block');c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(url) else r.abort());p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(url);p.wait_for_function('_writeReady');p.evaluate('d=>applyTheme(d)',dark)
   card=p.locator('[data-block=rating]');card.scroll_into_view_if_needed()
   buttons=p.locator('#rating-row button');assert buttons.count()==10
   y1=buttons.nth(0).bounding_box()['y'];y6=buttons.nth(5).bounding_box()['y'];assert (y6>y1)==(w<430)
   buttons.nth(2).click();assert p.locator('#rating-label').inner_text().startswith('3 —')
   card.screenshot(path=str(OUT/f'{w}-{dark}-one.png'))
   buttons.nth(7).click();assert p.locator('#rating-label').inner_text().startswith('8 —')
   label=p.locator('#rating-label').bounding_box();chips=p.locator('#rating-chips').bounding_box();assert chips['y']>=label['y']+label['height']
   assert card.bounding_box()['height']<380
   card.screenshot(path=str(OUT/f'{w}-{dark}-two.png'))
   # Existing two-tap chip editing still changes one entry, not its count.
   chip=p.locator('#rating-chips>div').first.locator('span').first;chip.click();assert p.locator('#rating-label').inner_text().startswith('3 —');chip.click();buttons.nth(4).click();assert p.evaluate('day().dayRatings.length')==2;assert p.evaluate('ratingVal(day().dayRatings[0])')==5
   p.locator('#rating-chips>div').first.locator('button').click();assert p.evaluate('day().dayRatings.length')==1
   p.reload();p.wait_for_function('_writeReady');assert p.evaluate('ratingVal(day().dayRatings[0])')==8
   p.evaluate('()=>{day().dayRatings=Array.from({length:10},(_,i)=>({v:i+1,t:"12:00"}));renderRating()}');buttons.nth(9).click();assert p.evaluate('day().dayRatings.length')==10
   card.screenshot(path=str(OUT/f'{w}-{dark}-ten.png'))
   assert not errors,errors
   assert card.evaluate('(e)=>e.scrollWidth<=e.clientWidth')
   c.close()
 b.close()
print('PASS 6 width/theme combinations; 5+5 and 10-column layouts; description; edit/delete/reload/10-entry limit; screenshots')

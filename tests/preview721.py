"""Attachment fallback vs working HTTP app, with a real save/reload."""
from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text()
exec(src[:src.index('with sync_playwright() as pw:')],globals())
OUT=Path(__file__).parent/'artifacts'/'preview721';OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for js in [False,True]:
  c=b.new_context(java_script_enabled=js,viewport={'width':390,'height':844});p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(URL)
  if js:
   p.wait_for_function('_writeReady');assert p.locator('#rating-row button').count()==10
   assert 'HTML-вкладення' not in p.locator('#rating-row').inner_text()
   assert p.locator('#today-date').inner_text()
   p.locator('#rating-row button').nth(6).click();p.reload();p.wait_for_function('_writeReady');assert p.evaluate('day().dayRatings[0].v')==7
  else:
   assert p.locator('#rating-row button').count()==0
   assert 'Safari' in p.locator('#rating-row').inner_text()
   assert not p.locator('#today-date').inner_text()
  p.locator('[data-block=rating]').screenshot(path=str(OUT/f'javascript-{js}.png'))
  assert not errors,errors
  results.append({'javascript':js,'status':'PASS','pageErrors':errors});c.close()
 b.close()
(OUT/'results.json').write_text(json.dumps(results,indent=2));print(results)

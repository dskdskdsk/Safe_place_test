"""75.2 notification hierarchy, queue and responsive presentation."""
from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text();exec(src[:src.index('with sync_playwright() as pw:')],globals())
OUT=Path(__file__).parent/'artifacts'/'notifications752';OUT.mkdir(parents=True,exist_ok=True)

def notification_rules(p,c):
 p.wait_for_function('_writeReady')
 # Plain notifications are queued, duplicate messages are suppressed and geometry is rectangular.
 ev(p,"()=>{showToast('First',1200);showToast('Second',1200);showToast('Second',1200)}")
 p.wait_for_selector('#app-toast.show');
 first=ev(p,"""()=>{const e=document.getElementById('app-toast'),s=getComputedStyle(e);return {text:e.textContent,radius:s.borderRadius,role:e.getAttribute('role'),live:e.getAttribute('aria-live'),count:document.querySelectorAll('#app-toast').length,queued:_toastQueue.length}}""")
 check(first['text']=='First' and first['radius']=='12px' and first['role']=='status' and first['live']=='polite' and first['count']==1 and first['queued']==1,first)
 p.wait_for_function("document.getElementById('app-toast').textContent==='Second'",timeout=3000)
 # Undo notification interrupts the ordinary queue, never overlaps it and resumes queued feedback.
 ev(p,"()=>{showToast('After undo',1200);window.undoHit=false;showUndoToast('Deleted',()=>{undoHit=true},{ms:1800,kind:'danger'})}")
 p.wait_for_selector('#undo-toast.show')
 check(ev(p,"!document.getElementById('app-toast').classList.contains('show')"),'plain toast overlaps undo toast')
 check(ev(p,"getComputedStyle(document.getElementById('undo-toast')).borderRadius==='12px'"),'undo toast is not rectangular')
 p.locator('#undo-btn').click();p.wait_for_function('undoHit===true');p.wait_for_function("document.getElementById('app-toast').classList.contains('show')")
 # Field mistakes stay beside the date inputs and do not generate a notification.
 p.locator('[data-page=settings]').click();ev(p,"()=>{if(S.expCollapsed)document.querySelector('#export-grp .exp-ch').click()}")
 p.locator('#export-period-btn').click();
 check(ev(p,"!document.getElementById('export-period-error').hidden&&document.querySelectorAll('#export-period-row .field-invalid').length===2"),'missing dates are not inline')
 check(ev(p,"_toastQueue.every(x=>!x.msg.includes('дати'))"),'date error entered toast queue')
 p.locator('#export-period-from').fill('2026-11-10');p.locator('#export-period-to').fill('2026-11-01');p.locator('#export-period-btn').click()
 check('раніше' in p.locator('#export-period-error').inner_text(),'date order is not inline')
 # A failed write is critical and opens a dialog rather than a transient notification.
 ev(p,"()=>{_saveFailAt=0;notifySaveFail(new DOMException('full','QuotaExceededError'))}");p.wait_for_selector('#err-dlg')
 check(ev(p,"document.getElementById('err-dlg').dataset.kind==='error'"),'storage failure is not a dialog');p.locator('#err-dlg .ob-next').click()
 # A clean import is brief feedback; a partial import remains a warning window.
 ev(p,"()=>showImportSummary(false,{addedDays:2,updatedDays:1,skippedDays:0},{photos:1,voices:0})")
 p.wait_for_function("document.getElementById('app-toast').textContent.includes('Імпорт завершено')",timeout=5000)
 ev(p,"()=>{showImportSummary(false,{addedDays:1,updatedDays:0,skippedDays:1},{})}");p.wait_for_selector('#err-dlg')
 check(ev(p,"document.getElementById('err-dlg').dataset.kind==='warning'"),'partial import is not a warning dialog')
 return 'Queued rectangular toast; exclusive undo; inline date errors; storage dialog; import result hierarchy'

def narrow_geometry(p,c):
 p.wait_for_function('_writeReady');ev(p,"()=>showToast('Довге повідомлення для перевірки вузького екрана та переносу тексту',5000)");p.wait_for_selector('#app-toast.show')
 g=p.locator('#app-toast').bounding_box();check(g['x']>=11 and g['x']+g['width']<=309,g)
 p.screenshot(path=str(OUT/'toast-320.png'));return '320px toast stays inside viewport'

with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 run('notification_rules',['75.2'],notification_rules)
 ctx=browser.new_context(viewport={'width':320,'height':568},is_mobile=True,has_touch=True);p=ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(URL);detail=narrow_geometry(p,ctx);results.append({'name':'narrow_geometry','tests':['75.2'],'status':'PASS','detail':detail,'pageErrors':errors});ctx.close()
 browser.close()
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(results[-1],flush=True)
raise SystemExit(any(r['status']=='FAIL' or r.get('pageErrors') for r in results))

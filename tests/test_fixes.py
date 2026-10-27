from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text()
exec(src[:src.index('with sync_playwright() as pw:')],globals())
# The shared runner uses __file__, so artifacts go to qa-70.5.
def drafts(p,c):
 p.wait_for_function('_writeReady');p.locator('#day-summary').fill('Draft day one 🧪');p.reload();p.wait_for_function('_writeReady');check(p.locator('#day-summary').input_value()=='Draft day one 🧪')
 ev(p,"()=>{window.firstDay=activeDay;activeDay='2026-01-02';renderToday()}");check(p.locator('#day-summary').input_value()=='');p.locator('#day-summary').fill('Draft day two');ev(p,'()=>{activeDay=firstDay;renderToday()}');check(p.locator('#day-summary').input_value()=='Draft day one 🧪')
 p.locator('#summary-send-btn').click();p.reload();p.wait_for_function('_writeReady');check(p.locator('#day-summary').input_value()=='');check(ev(p,"day().summary==='Draft day one 🧪'&&S.days['2026-01-02'].draftText==='Draft day two'"));return 'Per-day drafts restored, switching days safe, submit clears only matching draft'
def draft_quota(p,c):
 p.wait_for_function('_writeReady');p.locator('#day-summary').fill('keep draft');ev(p,"()=>{window.origSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===SK)throw new DOMException('quota','QuotaExceededError');return origSet.call(this,k,v)}}")
 p.locator('#summary-send-btn').click();check(p.locator('#day-summary').input_value()=='keep draft');check(ev(p,"day().draftText==='keep draft'&&day().summaryEntries.length===0"));ev(p,'()=>{Storage.prototype.setItem=origSet}');p.locator('#summary-send-btn').click();p.reload();p.wait_for_function('_writeReady');check(ev(p,"day().summary==='keep draft'&&day().draftText===''"));return 'Failed submit keeps draft and creates no duplicate; retry succeeds once'
def tabs(p,c):
 p.wait_for_function('_writeReady');p.locator('#day-summary').fill('A draft');q=c.new_page();q.goto(URL);q.wait_for_selector('#err-dlg');check(ev(q,'!_writeReady&&_writeBlocked'));check(ev(q,"document.getElementById('app').inert"))
 before=ev(p,'localStorage.getItem(SK)');check(ev(q,"()=>{day().gratitude=['B should not overwrite','',''];dirty=true;return persist()}")==False);check(ev(p,'localStorage.getItem(SK)')==before)
 p.close();q.reload();q.wait_for_function('_writeReady');check(q.locator('#day-summary').input_value()=='A draft');q.locator('#summary-send-btn').click();check(ev(q,"day().summary==='A draft'"));return 'Second tab cannot write; closing owner then reload transfers editing with draft intact'
def legacy_conflict(p,c):
 p.wait_for_function('_writeReady');p.locator('#day-summary').fill('local pending');
 # Emulate an old document that does not participate in Web Locks.
 ev(p,"()=>{window.latest={days:{'2026-01-01':{summary:'external saved'}}};localStorage.setItem(SK,JSON.stringify(latest));day().gratitude=['unsaved','',''];dirty=true;window.saved=persist()}")
 p.wait_for_selector('#err-dlg');check(ev(p,"!saved&&_writeBlocked&&JSON.parse(localStorage.getItem(SK)).days['2026-01-01'].summary==='external saved'"));
 with p.expect_download() as d:p.locator('#err-dlg .ob-skip').click()
 exported=json.loads(Path(d.value.path()).read_text());check(any(x.get('draftText')=='local pending' for x in exported['days'].values()));return 'Legacy external write detected before persist; newest disk preserved; local draft downloadable'
def interrupted(p,c):
 p.wait_for_function('_writeReady');ev(p,"""async()=>{addSummaryEntry('existing');window.originalKeys=JSON.stringify(await _mediaKeys());const original=importMediaTransaction;importMediaTransaction=async(...args)=>{await original(...args);window.staged=true;await new Promise(()=>{})};window.staged=false;safeImportJournal({days:{'2026-09-01':{photoIds:['x']}},photoData:{x:'data:image/png;base64,aGVsbG8='}})}""")
 p.wait_for_function('window.staged===true');before=ev(p,'originalKeys');check(ev(p,'localStorage.getItem(PENDING_IMPORT_KEY)!==null'));p.reload();p.wait_for_function('_writeReady');check(ev(p,'async()=>JSON.stringify(await _mediaKeys())')==before);check(ev(p,"day().summary.includes('existing')&&localStorage.getItem(PENDING_IMPORT_KEY)===null"));return 'Real staged media + marker survive interruption; startup removes only unreferenced staged files'
def committed_marker(p,c):
 p.wait_for_function('_writeReady');ev(p,"""async()=>{const remove=Storage.prototype.removeItem;Storage.prototype.removeItem=function(k){if(k===PENDING_IMPORT_KEY)throw new Error('injected marker removal failure');return remove.call(this,k)};await safeImportJournal({days:{'2026-09-01':{photoIds:['x']}},photoData:{x:'data:image/png;base64,aGVsbG8='}});Storage.prototype.removeItem=remove;}""")
 check(ev(p,'localStorage.getItem(PENDING_IMPORT_KEY)!==null'));p.reload();p.wait_for_function('_writeReady');check(ev(p,"async()=>!!(await _photoGet(S.days['2026-09-01'].photoIds))[0]"));check(ev(p,'localStorage.getItem(PENDING_IMPORT_KEY)===null'));return 'Crash window after journal commit preserves referenced media; marker cleared at startup'
def recovery_failure(p,c):
 p.wait_for_function('_writeReady');ev(p,"localStorage.setItem(PENDING_IMPORT_KEY,JSON.stringify({version:1,photos:['unsafe-id'],voices:[]}))");p.reload();p.wait_for_selector('#err-dlg');check(ev(p,'!_writeReady&&localStorage.getItem(PENDING_IMPORT_KEY)!==null'));return 'Invalid marker not used for deletion; writes blocked with retry dialog'
def unsupported(p,c):
 c.add_init_script("Object.defineProperty(navigator,'locks',{value:undefined})");p.reload();p.wait_for_selector('#err-dlg');check(ev(p,'!_writeReady'));check(ev(p,'persist()')==False);return 'Unsupported locking fails closed; no silent multi-tab overwrite'
def wipe_failure(p,c):
 p.wait_for_function('_writeReady');r=ev(p,"""async()=>{addSummaryEntry('keep');localStorage.setItem(GEMINI_KEY_SK,'test-key');const before=localStorage.getItem(SK),original=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===SK)throw new DOMException('quota','QuotaExceededError');return original.call(this,k,v)};let failed=false;try{await wipeAllData({undoable:false})}catch(e){failed=true}finally{Storage.prototype.setItem=original}return {failed,same:localStorage.getItem(SK)===before,key:localStorage.getItem(GEMINI_KEY_SK)==='test-key',memory:day().summary==='keep'}}""");check(all(r.values()),r);return 'Failed wipe leaves disk, in-memory entries and API key unchanged'

with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for name,ids,fn in [('drafts',['D1'],drafts),('draft_quota',['D1'],draft_quota),('single_writer',['D2'],tabs),('legacy_conflict',['D2'],legacy_conflict),('interrupted_import',['D3'],interrupted),('committed_marker',['D3'],committed_marker),('recovery_failure',['D3'],recovery_failure),('unsupported_locks',['D2'],unsupported),('wipe_failure',['wipe'],wipe_failure)]:run(name,ids,fn)
 browser.close()
(OUT/'fix-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))

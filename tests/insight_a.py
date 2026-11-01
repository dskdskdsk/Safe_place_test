"""Stage A acceptance: synthetic data, actual app/import/export and Chromium UI."""
from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text()
exec(src[:src.index('with sync_playwright() as pw:')],globals())
def check(value,msg='assertion failed'):
 if not value:raise AssertionError(str(msg)+' at '+str(traceback.extract_stack()[-2].lineno))
OUT=Path(__file__).parent/'artifacts'/'insight-a';OUT.mkdir(parents=True,exist_ok=True)
def profiles(p,c):
 p.wait_for_function('_writeReady')
 return ev(p,Path(__file__).with_name('insight_a_cases.js').read_text())
def provenance(p,c):
 p.wait_for_function('_writeReady')
 # A clock just before midnight, then midnight while TODAY intentionally remains stale.
 p.clock.set_fixed_time(__import__('datetime').datetime.fromisoformat('2026-03-10T23:59:59+00:00'))
 ev(p,"()=>{TODAY='2026-03-10';activeDay='2026-03-10';day().draftText='pending midnight draft';renderToday()}")
 p.locator('#rating-row button').nth(1).click()
 first=ev(p,'day().dayRatings[0]');check(first=={'v':2,'t':'23:59','ts':1773187199000,'recordedDay':'2026-03-10','retro':False},first)
 p.clock.set_fixed_time(__import__('datetime').datetime.fromisoformat('2026-03-11T00:00:01+00:00'))
 ev(p,"()=>{activeDay='2026-03-11';day().draftText='pending midnight draft';renderToday()}")
 p.locator('#rating-row button').nth(7).click();second=ev(p,'day().dayRatings[0]');check(second['recordedDay']=='2026-03-11' and second['t']=='00:00' and not second['retro']);check(ev(p,"TODAY==='2026-03-10'"),'TODAY stays stale while composing')
 ev(p,"()=>{activeDay='2026-03-10';renderToday()}")
 p.locator('#rating-row button').nth(8).click();retro=ev(p,'day().dayRatings[1]');check(retro['retro'] and retro['recordedDay']=='2026-03-11')
 # Select an edit target; the matrix below also exercises actual two-tap editing.
 ev(p,"()=>{ratingChipEditIdx=0;renderRating()}")
 check(p.locator('#rating-row .is-lit').count()==0,'neutral edit scale')
 p.locator('#rating-row button').nth(5).click();edited=ev(p,'day().dayRatings[0]');check(edited['v']==6 and edited['edited'] and edited['editedAt']>first['ts']);check(all(edited[k]==first[k] for k in ['t','ts','recordedDay','retro']))
 p.clock.set_fixed_time(__import__('datetime').datetime.fromisoformat('2026-03-11T00:00:02+00:00'))
 ev(p,"()=>{ratingChipEditIdx=0;renderRating()}");p.locator('#rating-row button').nth(3).click();again=ev(p,'day().dayRatings[0]');check(again['editedAt']>edited['editedAt'] and again['ts']==first['ts'],'editedAt updates')
 ev(p,"()=>{day().dayRatings=[3,{v:4,t:'00:00'}];ratingChipEditIdx=0;renderRating()}")
 p.locator('#rating-row button').nth(6).click();check(set(ev(p,'day().dayRatings[0]'))=={'v','edited','editedAt'})
 ev(p,"()=>{ratingChipEditIdx=1;renderRating()}");p.locator('#rating-row button').nth(5).click();r=ev(p,'day().dayRatings[1]');check(set(r)=={'v','t','edited','editedAt'},str(r))
 # Navigation must cancel edit, then deletion persists.
 ev(p,"()=>{ratingChipEditIdx=0;activeDay='2026-03-11';renderToday()}");p.locator('#rating-row button').nth(4).click();check(ev(p,'day().dayRatings.length')==2)
 p.locator('#rating-chips button').last.click();check(ev(p,'day().dayRatings.length')==1)
 before=ev(p,'JSON.stringify(day().dayRatings)');p.reload();p.wait_for_function('_writeReady');check(ev(p,"JSON.stringify(S.days['2026-03-11'].dayRatings)")==before)
 return 'single instant, midnight/stale TODAY, retro, edits preserve origin, legacy edits, neutral edit scale, navigation, deletion, reload'
def rollback(p,c):
 p.wait_for_function('_writeReady');ev(p,"()=>{day().dayRatings=[makeRecordedRating(4,activeDay,new Date())];syncDayRating(day());markNow();renderRating();window.beforeRatings=JSON.stringify(day().dayRatings);window.oldSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===SK)throw new DOMException('quota','QuotaExceededError');return oldSet.call(this,k,v)}}")
 p.locator('#rating-row button').nth(7).click();check(ev(p,'JSON.stringify(day().dayRatings)===beforeRatings'),'add rollback')
 ev(p,'()=>{ratingChipEditIdx=0;renderRating()}');p.locator('#rating-row button').nth(8).click();check(ev(p,'JSON.stringify(day().dayRatings)===beforeRatings'),'edit rollback');ev(p,'()=>{Storage.prototype.setItem=oldSet}')
 return 'real localStorage failure rolls back value and metadata on add/edit'
def archives(p,c):
 p.wait_for_function('_writeReady')
 r=ev(p,"""async()=>{
 const key='2026-02-01',r=makeRecordedRating(8,key,new Date());r.edited=true;r.editedAt=r.ts+100;
 S.days[key]={dayRatings:[r,5,{v:6,t:'08:00'}],dayRating:6};markNow();
 const full=await buildFullExportObj(),period=await buildPeriodExportObj(key,key);
 const expected=JSON.stringify(S.days[key].dayRatings);
 if(JSON.stringify(period.days[key].dayRatings)!==expected)throw Error('period fields');
 const json=JSON.parse(JSON.stringify(full));delete S.days[key];let res=await safeImportJournal(json);if(res.error)throw Error(res.error);
 if(JSON.stringify(S.days[key].dayRatings)!==expected)throw Error('JSON fields');
 const zipped=await buildCombinedZip(await buildFullExportObj(),'journal.json');const zip=await JSZip.loadAsync(zipped.zipBlob);
 const data=JSON.parse(await zip.file('journal.json').async('string'));delete S.days[key];res=await safeImportJournal(data,zip);if(res.error)throw Error(res.error);
 if(JSON.stringify(S.days[key].dayRatings)!==expected)throw Error('ZIP fields');
 res=await safeImportJournal({days:{'2020-01-01':{dayRating:7,summary:'old archive'}}});if(res.error)throw Error(res.error);
 return {expected,legacy:readInsightDay(S,'2020-01-01',todayKey()).ratings.mean};
 }""")
 check(r['legacy']==7);p.reload();p.wait_for_function('_writeReady');check(ev(p,"JSON.stringify(S.days['2026-02-01'].dayRatings)")==r['expected'])
 return 'full/period exports, JSON import, actual JSZip builder/parse/import/merge, old archive, reload preserve metadata'
def timezone(p,c):
 p.wait_for_function('_writeReady')
 r=ev(p,"""()=>{const instant=new Date('2026-01-01T00:30:00Z'),r=makeRecordedRating(5,'2025-12-31',instant);return {r,profile:readInsightDay({days:{'2025-12-31':{dayRatings:[r]}}},'2025-12-31','2026-01-01')};}""")
 check(r['r']['ts']==1767227400000);check(r['profile']['ratings']['entries'][0]['recordedDay']==r['r']['recordedDay'])
 return r
def ui_matrix(p,c):
 p.wait_for_function('_writeReady')
 for lang in ['uk','en']:
  for dark in [False,True]:
   ev(p,"({lang,dark})=>{S.settings.lang=lang;applyTheme(dark);activeDay=todayKey();const d=day();d.dayRatings=[];d.dayRating=0;ratingChipEditIdx=-1;ratingChipSelectedIdx=-1;applyI18n();renderToday()}",{'lang':lang,'dark':dark})
   buttons=p.locator('#rating-row button');check(p.locator('#rating-row .is-lit').count()==0,'initial neutral '+lang+str(dark))
   buttons.nth(2).click();buttons.nth(7).click()
   chip=p.locator('#rating-chips>div').first.locator('span').first;chip.click();chip.click();check(p.locator('#rating-row .is-lit').count()==0,'edit neutral '+lang+str(dark));buttons.nth(4).click();check(ev(p,'day().dayRatings[0].v===5&&day().dayRatings.length===2'),'edit value '+lang+str(dark))
   p.locator('[data-block=rating]').screenshot(path=str(OUT/f'{lang}-{dark}-rating.png'))
   ev(p,"()=>{document.getElementById('dash-content').innerHTML='<div id=qa-chart></div>';moodPeriod='week';moodWeekOffset=0;buildMoodChart(document.getElementById('qa-chart'))}")
   col=p.locator('.mc-col[data-k="'+ev(p,'todayKey()')+'"]')
   # Trigger pointer gesture on actual chart event listeners, including drag suppression.
   col.dispatch_event('pointerdown',{'clientX':0,'clientY':0});col.dispatch_event('pointermove',{'clientX':20,'clientY':20});col.dispatch_event('click');check(not ev(p,"document.getElementById('day-rating-popup').classList.contains('on')"),'popup gesture '+lang+str(dark))
   col.dispatch_event('pointerdown',{'clientX':0,'clientY':0});col.dispatch_event('click');check(ev(p,"document.getElementById('day-rating-popup').classList.contains('on')"),'popup gesture '+lang+str(dark))
   check(('Average' if lang=='en' else 'Середня') in p.locator('#drp-avg').inner_text(),'popup language '+lang+str(dark))
   ev(p,"document.dispatchEvent(new Event('scroll'))");check(not ev(p,"document.getElementById('day-rating-popup').classList.contains('on')"),'popup gesture '+lang+str(dark))
   p.locator('#rating-chips button').first.click();check(ev(p,'day().dayRatings.length===1'),'delete '+lang+str(dark))
 return 'UK/EN × light/dark: neutral scale, add, two-tap edit, delete, popup tap/drag/scroll; four screenshots'

with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for name,fn in [('profiles',profiles),('provenance_ui',provenance),('rollback',rollback),('archives',archives),('ui_matrix',ui_matrix)]:run(name,['A4'],fn)
 for zone in ['America/Los_Angeles','Pacific/Kiritimati','Europe/Kyiv']:
  ctx=browser.new_context(timezone_id=zone);p=ctx.new_page();p.goto(URL)
  try:
   detail=profiles(p,ctx);r=timezone(p,ctx);expected='2025-12-31' if zone=='America/Los_Angeles' else '2026-01-01';check(r['r']['recordedDay']==expected);check(r['r']['retro']==(expected!='2025-12-31'))
   # Stored local day remains authoritative when reading under a different zone.
   stored={'v':8,'t':'16:30','ts':1767227400000,'recordedDay':'2025-12-31','retro':False}
   got=ev(p,"r=>readInsightDay({days:{'2025-12-31':{dayRatings:[r]}}},'2025-12-31','2026-01-01').ratings.entries[0]",stored);check(got['recordedDay']=='2025-12-31' and got['provenance']=='recorded')
   results.append({'name':'timezone '+zone,'status':'PASS','detail':detail+'; local recording + stable recordedDay across timezone change'})
  except Exception as e:results.append({'name':'timezone '+zone,'status':'FAIL','detail':str(e)})
  ctx.close()
 browser.close()
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False,indent=2))
raise SystemExit(any(r['status']=='FAIL' or r.get('pageErrors') for r in results))

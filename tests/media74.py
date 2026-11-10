"""74.0: commands, history, rollback, persistence, mobile UI and localization."""
from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text();exec(src[:src.index('with sync_playwright() as pw:')],globals())
OUT=Path(__file__).parent/'artifacts'/'media74';OUT.mkdir(parents=True,exist_ok=True)
def seed(p):
 p.wait_for_function('_writeReady && typeof media74Latest === "function"')
 ev(p,"""()=>{S.days={};activeDay=todayKey();S.days['2026-01-01']={recs:['watch','read','play','listen','todo'].map(cat=>({id:cat,name:'Title '+cat,cat,done:false}))};S.settings.mediaDashOpen=true;S.dashCollapsed={recs:false};markNow();renderToday();renderDash();}""")
def lifecycle(p,c):
 seed(p)
 for cat in ['watch','read','play','listen','todo']:check(ev(p,"cat=>startRecommendation('2026-01-01',cat)",cat),'start '+cat)
 check(ev(p,"()=>{const d=S.days[todayKey()];return d.media.length===4&&new Set(d.media.map(m=>m.mediaId)).size===4&&d.media.every(m=>m.entryId&&m.status==='active')&&S.days['2026-01-01'].recs[4].doneDate===todayKey()}"),'all categories/date')
 check(not ev(p,"startRecommendation('2026-01-01','read')"),'idempotence')
 check(ev(p,"S.days[todayKey()].media.length===4"),'no duplicates')
 ev(p,"media74SetStatus(todayKey(),1,'pause')");check(ev(p,"media74Recs().find(r=>r.id==='read')._state==='pause'"),'pause propagates')
 ev(p,"media74SetStatus(todayKey(),1,'done')");check(ev(p,"media74Recs().find(r=>r.id==='read')._state==='done'"),'done propagates')
 ev(p,"media74SetStatus(todayKey(),1,'active')");check(ev(p,"media74Recs().find(r=>r.id==='read')._state==='active'"),'resume propagates')
 ev(p,"media74SetStatus(todayKey(),1,'del')");check(ev(p,"media74Recs().find(r=>r.id==='read')._state==='missing'"),'delete preserves rec')
 before=ev(p,"JSON.stringify(Object.fromEntries(Object.entries(S.days).map(([k,d])=>[k,{media:d.media,recs:d.recs}])))");p.reload();p.wait_for_function('_writeReady');check(ev(p,"JSON.stringify(Object.fromEntries(Object.entries(S.days).map(([k,d])=>[k,{media:d.media,recs:d.recs}])))")==before,'media/recommendations reload exact')
 return '5 categories; local today; repeated start; pause/done/resume; independent deletion; reload'
def readers(p,c):
 seed(p)
 r=ev(p,"""()=>{const s={days:{'2026-01-01':{media:[{name:'Book',cat:'read',mediaId:'a',status:'progress'},{name:'Same',cat:'watch',status:'planned'},{name:'Same',cat:'watch',status:'active'}]},'2026-02-01':{media:[{name:'Book renamed',cat:'read',mediaId:'a',status:'done'}]},'2099-01-01':{media:[{name:'Future',cat:'read',mediaId:'a',status:'active'}]}}};const before=JSON.stringify(s);const a=media74Latest(s,'2026-01-31'),b=media74Latest(s,'2026-02-28');return {a,b,same:before===JSON.stringify(s)};}""")
 check(r['same'] and len(r['a'])==3 and r['a'][0]['status']=='active',r)
 check(len(r['b'])==3 and r['b'][0]['name']=='Book renamed' and r['b'][0]['status']=='done',r)
 check(ev(p,"Object.keys(LANG.uk).filter(k=>k.startsWith('m74_')).every(k=>LANG.en[k]&&LANG.en[k]!==LANG.uk[k])"),'translations')
 return 'Readers immutable; legacy progress/planned; same-name legacy records distinct; latest identity; cutoff'
def rollback(p,c):
 seed(p)
 check(ev(p,"""async()=>{const before=JSON.stringify(S.days),stored=localStorage.getItem(SK),orig=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===SK)throw Error('test quota');return orig.call(this,k,v)};const ok=await startRecommendation('2026-01-01','listen');Storage.prototype.setItem=orig;return !ok&&before===JSON.stringify(S.days)&&stored===localStorage.getItem(SK)&&!dirty;}"""),'atomic rollback')
 check(ev(p,"startRecommendation('2026-01-01','listen')"),'retry')
 p.locator('#m74-notice button').last.click();check(ev(p,"!S.days[todayKey()]?.media?.length&&!S.days['2026-01-01'].recs[3].mediaId"),'undo')
 ev(p,"startRecommendation('2026-01-01','watch')");ev(p,"()=>{S.days[todayKey()].summary='later edit';markNow();}")
 p.locator('#m74-notice button').last.click();check(ev(p,"S.days[todayKey()].summary==='later edit'&&S.days[todayKey()].media.length===1"),'undo does not overwrite newer edits')
 return 'Quota rollback; retry; exact undo; guarded undo after edits'
def duplicate(p,c):
 seed(p)
 ev(p,"()=>{S.days['2026-02-01']={media:[{name:'  TITLE read ',cat:'read',status:'progress'}]};markNow();window.startPromise=startRecommendation('2026-01-01','read');}")
 p.wait_for_selector('dialog[open]');p.locator('dialog button').first.click();check(ev(p,'startPromise'),'choose existing')
 check(ev(p,"S.days['2026-02-01'].media[0].mediaId===S.days[todayKey()].media[0].mediaId"),'linked existing')
 check(ev(p,"S.days['2026-02-01'].media[0].status==='progress'"),'historic status preserved')
 ev(p,"()=>{activeDay='2026-01-15';mediaCat='read';renderCarryMedia();}");check(p.locator('#media-carry-wrap .m74-row').count()==0,'no future carry')
 ev(p,"()=>{activeDay='2026-02-02';renderCarryMedia();}")
 p.locator('[data-page=today]').click();ev(p,"()=>{document.querySelector('#media-card .media-body').style.maxHeight='none';}")
 p.locator('#media-carry-wrap [data-action=carry]').click()
 check(ev(p,"S.days['2026-02-02'].media[0].mediaId===S.days['2026-02-01'].media[0].mediaId&&S.days['2026-02-01'].media[0].status==='progress'"),'carry button identity and past snapshot')
 check(p.locator('#media-carry-wrap [data-action=carry]').count()==0,'already added carry disappears')
 return 'Explicit duplicate choice; legacy ID attachment; historic snapshot preserved; no future carry; actual carry button' 
def local_dates(p,c):
 from datetime import datetime
 from zoneinfo import ZoneInfo
 for zone in ['Pacific/Kiritimati','America/Los_Angeles','Europe/Kyiv']:
  z=browser.new_context(timezone_id=zone);q=z.new_page();q.goto(URL);seed(q)
  expected=datetime.now(ZoneInfo(zone)).strftime('%Y-%m-%d')
  ev(q,"()=>{activeDay='2026-01-01';renderToday();}")
  check(ev(q,"startRecommendation('2026-01-01','watch')"),'start in '+zone)
  check(ev(q,"key=>S.days[key]?.media?.length===1&&!S.days['2026-01-01'].media",expected),'local target from historical day '+zone)
  z.close()
 return '3 timezones, local target independent of historical active day'

def roundtrip74(p,c):
 seed(p)
 ev(p,"startRecommendation('2026-01-01','listen')")
 expected=ev(p,"JSON.stringify({recs:S.days['2026-01-01'].recs,media:S.days[todayKey()].media})")
 archive=ev(p,"async()=>{const x=await buildCombinedZip(await buildFullExportObj(),'journal.json');return Array.from(new Uint8Array(await x.zipBlob.arrayBuffer()))}")
 target=browser.new_context();q=target.new_page();q.goto(URL);q.wait_for_function('_writeReady')
 for attempt in range(2):
  q.locator('#import-file').set_input_files({'name':'journal.zip','mimeType':'application/zip','buffer':bytes(archive)});q.wait_for_selector('#err-dlg')
  check(ev(q,"JSON.stringify({recs:S.days['2026-01-01'].recs,media:S.days[todayKey()].media})")==expected,'ZIP preserves links, repeated import')
  q.locator('#err-dlg .ob-next').click()
 q.reload();q.wait_for_function('_writeReady');check(ev(q,"media74Recs().find(r=>r.id==='listen')._state==='active'"),'restored link resolves');target.close()
 result=ev(p,"()=>importJournalJson({days:{'2020-01-01':{media:[{name:'Old book',cat:'read',status:'progress'}],recs:[{id:'old',name:'Old rec',cat:'read',done:true}]}},settings:{}},'uk')")
 check('error' not in result,result)
 return 'Real ZIP export/import in clean context; repeat import; ID/link preservation; legacy archive'

def ui(p,c):
 seed(p)
 ev(p,"startRecommendation('2026-01-01','listen')")
 ev(p,"()=>{S.days[todayKey()].media[0].name='Довга назва твору '.repeat(12);S.days[todayKey()].media[0].note='Враження\\nДругий рядок';media74SetStatus(todayKey(),0,'done');}")
 p.locator('[data-page=dash]').click()
 for lang in ['uk','en']:
  for dark in [False,True]:
   ev(p,"({lang,dark})=>{S.settings.lang=lang;applyTheme(dark);applyI18n();renderDash();}",{'lang':lang,'dark':dark})
   for width in [320,390,430,1024]:
    p.set_viewport_size({'width':width,'height':844})
    for mode in ['now','history']:
     p.locator('[data-mode='+mode+']').click()
     check(ev(p,"document.body.scrollWidth<=innerWidth"),(width,mode,'overflow'))
   ev(p,"document.getElementById('m74-notice')?.remove()");p.set_viewport_size({'width':390,'height':844});p.locator('#media-dash-card').scroll_into_view_if_needed();p.screenshot(path=str(OUT/f'{lang}-{dark}.png'))
 p.locator('#media-dash-card [data-action=today]').click();check(ev(p,"S.days[todayKey()].media.length===2&&S.days[todayKey()].media[0].mediaId!==S.days[todayKey()].media[1].mediaId"),'start again distinct cycle')
 return 'UK/EN, themes, 4 widths, long names, current/history, repeat cycle'
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for name,fn in [('lifecycle',lifecycle),('readers',readers),('rollback',rollback),('duplicate',duplicate),('roundtrip',roundtrip74),('local_dates',local_dates),('ui',ui)]:run(name,['74.0'],fn)
 browser.close()
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
raise SystemExit(any(r['status']=='FAIL' or r.get('pageErrors') for r in results))

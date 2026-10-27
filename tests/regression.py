from pathlib import Path
import json,base64,io,wave,struct,math,time,traceback
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright
OUT=Path(__file__).parent/'artifacts';OUT.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(Path(__file__).resolve().parents[1])));Thread(target=server.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{server.server_port}/'
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
buf=io.BytesIO()
with wave.open(buf,'wb') as w:
 w.setparams((1,2,8000,0,'NONE','not compressed'));w.writeframes(b''.join(struct.pack('<h',int(1000*math.sin(2*math.pi*440*i/8000))) for i in range(4000)))
WAV=list(buf.getvalue());results=[]
def check(value,msg='assertion failed'):
 if not value:raise AssertionError(msg)
def run(name,ids,fn):
 ctx=browser.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 ctx.route('**/*',lambda r:r.continue_() if r.request.url.startswith(URL) else r.abort())
 p=ctx.new_page();p.set_default_timeout(5000);errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 try:
  p.goto(URL);p.wait_for_timeout(120)
  detail=fn(p,ctx)
  results.append({'name':name,'tests':ids,'status':'PASS','detail':detail,'pageErrors':errors})
 except Exception as e:
  results.append({'name':name,'tests':ids,'status':'FAIL','detail':str(e),'pageErrors':errors})
  try:p.screenshot(path=str(OUT/(name+'.png')))
  except:pass
 finally:ctx.close()
 print(results[-1],flush=True);(OUT/'regression-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
def ev(p,code,arg=None):return p.evaluate(code,arg)
def submitted(p,c):
 p.locator('#day-summary').fill('QA запис 🧪 українською');p.locator('#summary-send-btn').click();p.reload()
 check(ev(p,"day().summary.includes('QA запис 🧪 українською')"));return 'Submitted through UI, persisted across reload'
def edit(p,c):
 ev(p,"()=>{let e=addSummaryEntry('before');updateSummaryEntry(e.id,'after');window.dispatchEvent(new Event('pagehide'))}");p.reload();check(ev(p,"day().summary==='after'"));return 'Edit + synthetic pagehide + reload'
def structured(p,c):
 ev(p,"()=>{const d=day();d.gratitude=['дякую','',''];d.dayRatings=[3,8];S.habits=[{id:'qa',name:'QA habit',freq:7,hasGoal:true}];setHabitDone('qa',activeDay,true);S.ideaTree={roots:[{id:'root',text:'Ідея',children:[{id:'child',text:'Підпункт',children:[]}]}],_migrated:true};S.ideaStatus={root:'active'};markNow()}")
 p.reload();check(ev(p,"day().gratitude[0]==='дякую'&&day().dayRatings.length===2&&S.ideaTree.roots[0].children.length===1&&S.habits.length===1&&Object.keys(S.habitLog).length===1"));return 'Ratings, gratitude, habit/log and nested idea persist'
def preferences(p,c):
 p.locator('[data-page=settings]').click();p.locator('#lang-en-btn').click();p.wait_for_function("typeof getLang==='function' && getLang()==='en'");p.locator('[data-page=settings]').click();p.locator('#dark-tog').click();p.reload()
 check(ev(p,"getLang()==='en'&&S.settings.dark===true&&document.documentElement.dataset.theme==='dark'"));return 'Language/theme via UI persist'
def draft(p,c):
 p.locator('#day-summary').fill('UNSENT draft');p.wait_for_timeout(1200);p.reload();check(p.locator('#day-summary').input_value()=='UNSENT draft','Unsent draft is lost on reload');return 'Draft survives'
def photos(p,c):
 files=[{'name':f'p{i}.png','mimeType':'image/png','buffer':PNG} for i in range(6)]
 p.locator('#photo-in').set_input_files(files);p.wait_for_function('!_photoAdding');check(ev(p,'day().photoIds.length===4'))
 p.reload();check(ev(p,'day().photoIds.length===4'));check(ev(p,'async()=> (await _photoGet(day().photoIds)).every(Boolean)'))
 ev(p,'async()=>openPhoto((await _photoGet(day().photoIds))[0])');p.wait_for_timeout(100);check(ev(p,"document.getElementById('fpimg').naturalWidth===1"));return '6 selected → 4 saved and decodable after reload'
def photo_switch(p,c):
 ev(p,"()=>{window.startDay=activeDay;window.origCompress=compressPhoto;compressPhoto=async f=>{await new Promise(r=>setTimeout(r,300));return origCompress(f)}}")
 p.locator('#photo-in').set_input_files({'name':'x.png','mimeType':'image/png','buffer':PNG})
 ev(p,"()=>{activeDay='2026-01-01';renderToday()}");p.wait_for_function('!_photoAdding');check(ev(p,"S.days[startDay].photoIds.length===1&&!(S.days['2026-01-01'].photoIds||[]).length"));return 'Photo remains on original day'
def photo_bad(p,c):
 p.locator('#photo-in').set_input_files({'name':'bad.png','mimeType':'image/png','buffer':b'broken'});p.wait_for_function('!_photoAdding');check(ev(p,'!(day().photoIds||[]).length'))
 p.locator('#photo-in').set_input_files({'name':'ok.png','mimeType':'image/png','buffer':PNG});p.wait_for_function('!_photoAdding');check(ev(p,'day().photoIds.length===1'));return 'Decode error releases input; next photo works'
def voice(p,c):
 ev(p,"async bytes=>{await _voicePut('qa_voice',new Blob([new Uint8Array(bytes)],{type:'audio/wav'}));addVoiceSummaryEntry('qa_voice',.5)}",WAV);p.reload()
 out=ev(p,"async()=>{const blob=await _voiceGet('qa_voice');const a=new Audio(URL.createObjectURL(blob));await new Promise((resolve,reject)=>{a.onloadedmetadata=resolve;a.onerror=reject});await a.play();return {bytes:Array.from(new Uint8Array(await blob.arrayBuffer())),duration:a.duration}}")
 check(out['bytes']==WAV and out['duration']>.4);return 'Synthetic WAV persisted byte-for-byte, decoded and playback started; microphone not tested'
def roundtrip(p,c):
 archive=ev(p,"""async ({png,wav})=>{
 for(let i=1;i<=30;i++){const date='2026-09-'+String(i).padStart(2,'0');addSummaryEntry('День '+i+' 🧪',date);const id='p'+i;await _photoPut(id,'data:image/png;base64,'+png);S.days[date].photoIds=[id];}
 await _voicePut('qa_voice',new Blob([new Uint8Array(wav)],{type:'audio/wav'}));addVoiceSummaryEntry('qa_voice',.5,'2026-09-01');
 S.habits=[{id:'habit',name:'Habit',freq:7,hasGoal:true}];setHabitDone('habit','2026-09-01',true);
 S.ideaTree={roots:[{id:'root',text:'Ідея',date:'2026-09-01',children:[{id:'child',text:'Child',date:'2026-09-01',children:[]}]}],_migrated:true};markNow();
 const exported=await buildFullExportObj();const result=await buildCombinedZip(exported,'journal.json');return Array.from(new Uint8Array(await result.zipBlob.arrayBuffer()));
 }""",{'png':base64.b64encode(PNG).decode(),'wav':WAV})
 target=browser.new_context(accept_downloads=True);q=target.new_page();q.set_default_timeout(8000);q.goto(URL)
 q.locator('#import-file').set_input_files({'name':'journal.zip','mimeType':'application/zip','buffer':bytes(archive)});q.wait_for_selector('#err-dlg')
 check('30' in q.locator('#err-dlg-text').inner_text());q.locator('#err-dlg .ob-next').click();q.reload()
 got=ev(q,"""async()=>{
 const d=S.days['2026-09-01'];return {days:Object.keys(S.days).filter(k=>k.startsWith('2026-09')).length,text:d.summary,photo:(await _photoGet(d.photoIds))[0],voice:Array.from(new Uint8Array(await (await _voiceGet(d.summaryEntries.find(e=>e.type==='voice').audioId)).arrayBuffer())),tree:S.ideaTree,habits:S.habits,logs:S.habitLog};
 }""")
 check(got['days']==30 and 'День 1 🧪' in got['text']);check(got['photo']=='data:image/png;base64,'+base64.b64encode(PNG).decode());check(got['voice']==WAV);check(len(got['tree']['roots'][0]['children'])==1 and len(got['habits'])==1 and len(got['logs'])==1)
 q.locator('#import-file').set_input_files({'name':'journal.zip','mimeType':'application/zip','buffer':bytes(archive)});q.wait_for_selector('#err-dlg');check(ev(q,"S.days['2026-09-01'].summaryEntries.length===2&&S.ideaTree.roots.length===1"));target.close()
 return 'Real export builder → ZIP → clean context file input import; 30 days/photos + WAV/tree/habit; media bytes exact; repeated import no duplicate entries'
def oldformat(p,c):
 result=ev(p,"()=>importJournalJson({days:{'2020-01-01':{summary:'legacy text',dayRating:7,ideas:['old idea']}},settings:{dark:false}},'uk')")
 check('error' not in result,result);p.reload();check(ev(p,"S.days['2020-01-01'].summary.includes('legacy text')"));return 'Minimal old-format JSON accepted; not a real user archive'
def invalid(p,c):
 ev(p,"()=>{addSummaryEntry('keep');window.prior=localStorage.getItem(SK)}")
 for name,data in [('bad.json',b'{broken'),('other.json',b'{"unrelated":true}'),('bad.zip',b'not a zip')]:
  p.locator('#import-file').set_input_files({'name':name,'mimeType':'application/octet-stream','buffer':data});p.wait_for_selector('#err-dlg');check(ev(p,'localStorage.getItem(SK)===prior'));p.locator('#err-dlg .ob-next').click()
 return 'Malformed JSON, unrelated JSON and invalid ZIP leave saved state unchanged'
def separate_voice(p,c):
 r=ev(p,"""async bytes=>{
 const imp={days:{'2026-09-01':{summaryEntries:[{id:'ve',type:'voice',audioId:'v',text:''}]}}};await safeImportJournal(imp);
 const zip=new JSZip();zip.file('v.webm',new Uint8Array(bytes));zip.file('manifest.json',JSON.stringify({entries:[{dayKey:'2026-09-01',audioId:'v',entryId:'ve'}]}));
 const result=await restoreVoiceEntriesFromZip(await JSZip.loadAsync(await zip.generateAsync({type:'blob'})));
 const d=S.days['2026-09-01'];return {result,count:d.summaryEntries.length,bytes:Array.from(new Uint8Array(await (await _voiceGet(d.summaryEntries[0].audioId)).arrayBuffer()))};
 }""",WAV);check(r['count']==1 and r['bytes']==WAV,r);return 'JSON voice references restored by separate voice ZIP'
def quota(p,c):
 r=ev(p,"""()=>{addSummaryEntry('before');const prev=localStorage.getItem(SK),original=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===SK)throw new DOMException('quota','QuotaExceededError');return original.call(this,k,v)};day().gratitude=['pending','',''];dirty=true;const fail=persist(),pending=dirty;Storage.prototype.setItem=original;const same=localStorage.getItem(SK)===prev;const retry=persist();return {fail,pending,same,retry,dirty}}""");check(r=={'fail':False,'pending':True,'same':True,'retry':True,'dirty':False},r);return 'Injected QuotaExceededError: original saved blob intact; dirty retained; retry succeeds'
def corrupt(p,c):
 ev(p,"localStorage.setItem(SK,'{corrupt-original')");p.reload();p.wait_for_selector('#err-dlg');check(ev(p,"_storageBlocked&&localStorage.getItem(SK)==='{corrupt-original'&&!persist()"))
 p.keyboard.press('Escape');check(p.locator('#err-dlg').count()==1)
 with p.expect_download() as d:p.locator('#err-dlg .ob-skip').click()
 check(Path(d.value.path()).read_text()=='{corrupt-original');return 'Corrupt local JSON locked; exact raw download; Escape cannot dismiss recovery'
def import_rollback(p,c):
 r=ev(p,"""async png=>{addSummaryEntry('keep');const before=localStorage.getItem(SK),keys=JSON.stringify(await _mediaKeys()),original=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===SK)throw new DOMException('quota','QuotaExceededError');return original.call(this,k,v)};let failed=false;try{await safeImportJournal({days:{'2026-09-02':{photoIds:['new']}},photoData:{new:'data:image/png;base64,'+png}})}catch(e){failed=true}finally{Storage.prototype.setItem=original}return {failed,same:before===localStorage.getItem(SK),media:keys===JSON.stringify(await _mediaKeys())}}
 """,base64.b64encode(PNG).decode());check(all(r.values()),r);return 'Real staged IndexedDB photo removed after injected journal-commit failure'
def idb_abort(p,c):
 r=ev(p,"""async()=>{await _photoPut('existing','original');const db=await _openPDB();let failed=false;try{await importMediaTransaction(db,[{store:_PST,value:{id:'new',dataUrl:'new'}},{store:_PST,value:{id:'existing',dataUrl:'replacement'}}])}catch(e){failed=true}return {failed,photos:await _photoGet(['existing','new'])}}""");check(r=={'failed':True,'photos':['original',None]},r);return 'Duplicate add aborts actual IDB transaction; old media intact and new record rolled back'
def twotabs(p,c):
 q=c.new_page();q.goto(URL);ev(p,"()=>{day().gratitude=['pending tab A','',''];dirty=true}")
 ev(q,"addSummaryEntry('saved in tab B')");p.wait_for_timeout(100);ev(p,'persist()');p.reload()
 check(ev(p,"day().summary.includes('saved in tab B')"),'Tab A dirty state overwrites the saved entry from tab B');return 'No lost concurrent edit'
def ai(p,c):
 ev(p,"()=>{localStorage.setItem('gemini_api_key','synthetic');window.calls=[];window.fetch=async(u,o)=>{calls.push({u,o});return {ok:true,json:async()=>({candidates:[{content:{parts:[{text:'test response'}]}}]})}}}")
 for mode in ['cancel','close','backdrop']:
  ev(p,"()=>{window.result=null;callGemini('Synthetic <b>text</b>').then(v=>result=v).catch(e=>result=e.code)}");p.wait_for_selector('#err-dlg')
  if mode=='cancel':p.locator('#err-dlg .ob-skip').click()
  elif mode=='close':p.locator('#err-dlg .ob-x').click()
  else:p.locator('#err-dlg').click(position={'x':2,'y':2})
  p.wait_for_function("result==='aborted'");check(ev(p,'calls.length===0'))
 for lang in ['uk','en']:
  ev(p,"lang=>{S.settings.lang=lang;window.result=null;callGemini('Synthetic <b>text</b>').then(v=>result=v).catch(e=>result=e.code)}",lang)
  p.locator('#err-dlg summary').click();check(p.locator('#err-dlg pre').inner_text()=='Synthetic <b>text</b>');check(p.locator('#err-dlg pre b').count()==0)
  check('ai_consent_' not in p.locator('#err-dlg').inner_text());p.locator('#err-dlg .ob-next').click();p.wait_for_function("result==='test response'")
 check(ev(p,"calls.every(x=>!x.u.includes('key=')&&x.o.headers['x-goog-api-key']==='synthetic')"));return '3 cancel paths = zero fetches; uk/en preview and fake response, key in header'
def ai_offline(p,c):
 ev(p,"()=>{localStorage.setItem('gemini_api_key','synthetic');window.fetch=async()=>{throw new TypeError('Failed to fetch')};window.result=null;callGemini('test').catch(e=>{result=e.code;reportError(e,{ctx:'ai'})})}")
 p.locator('#err-dlg .ob-next').click();p.wait_for_function("result==='ai_network'");p.wait_for_selector('#err-dlg');check('ai_network' not in p.locator('#err-dlg-text').inner_text());return 'Network failure mapped to localized dialog'
def pin(p,c):
 ev(p,"()=>{setPinState({enabled:true,hash:pinHash('1234')});sessionStorage.removeItem('journal_pin_unlocked')}");p.reload();p.wait_for_selector('#lock-screen',state='visible');p.keyboard.press('Escape');check(ev(p,"document.getElementById('lock-screen').style.display==='flex'"))
 p.locator('#pin-input').fill('9999');p.locator('#pin-submit').click();check(ev(p,"document.getElementById('lock-screen').style.display==='flex'&&getPinAttempts()===1"))
 p.locator('#pin-input').fill('1234');p.locator('#pin-submit').click();p.wait_for_timeout(200);check(ev(p,"document.getElementById('lock-screen').style.display==='none'&&!document.getElementById('app').inert"));return 'Real PIN state/hash, wrong attempt, correct unlock and background isolation'
def select_controls(p,c):
 out=ev(p,"""()=>{const host=document.createElement('div');host.innerHTML='<button><span>Label</span></button><div role="button"><input value="Edit"></div><p>Journal text</p>';document.body.append(host);const get=q=>getComputedStyle(host.querySelector(q)).userSelect;const r={button:get('button'),label:get('span'),input:get('input'),text:get('p')};host.remove();return r}""");check(out['button']==out['label']=='none' and out['input']=='text' and out['text']!='none',out)
 p.locator('#day-summary').fill('copy and paste');p.locator('#day-summary').press('Control+a');p.locator('#day-summary').press('Backspace');p.locator('#day-summary').fill('edited');check(p.locator('#day-summary').input_value()=='edited');return 'Computed CSS and keyboard editing; native iOS long-press menu not exercised'
def pwa(p,c):
 ev(p,'async()=>{await navigator.serviceWorker.ready}');p.reload();p.wait_for_function('navigator.serviceWorker.controller!==null');ev(p,"addSummaryEntry('offline stored')");c.set_offline(True);p.reload();check(ev(p,"day().summary.includes('offline stored')"))
 ev(p,"addSummaryEntry('offline new')");p.reload();check(ev(p,"day().summary.includes('offline new')"));return 'Actual service worker reload offline and new entry persisted'
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
 cases=[('submitted',[1,2],submitted),('edit_flush',[3],edit),('structured_data',[4,6],structured),('preferences',[5],preferences),('unsent_draft',['draft'],draft),('photos_limit_reload',[7,8],photos),('photo_day_switch',[9],photo_switch),('photo_decode_failure',[11],photo_bad),('voice_storage_playback',[12],voice),('full_roundtrip',[13,14,15,16,17],roundtrip),('legacy_format',[18],oldformat),('invalid_files',[19],invalid),('separate_voice',[20],separate_voice),('quota_retry',['quota'],quota),('corrupt_recovery',['corrupt'],corrupt),('import_rollback',['rollback'],import_rollback),('idb_atomic_abort',['idb'],idb_abort),('ai_consent',[22,23,24,25,26,27],ai),('ai_network',[28],ai_offline),('pin_auth',[45,46],pin),('selection',[49,50,51,52,53],select_controls),('pwa_offline',[21],pwa)]
 for name,ids,fn in cases:
  import sys
  if len(sys.argv)==1 or name in sys.argv[1:]:run(name,ids,fn)
 browser.close()
print('FINISHED',len(results),'scenarios',sum(r['status']=='PASS' for r in results),'passed',flush=True)

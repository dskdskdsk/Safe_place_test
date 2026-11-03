"""73.0 read-only memories: real browser/storage/media and mobile UI checks."""
from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text();exec(src[:src.index('with sync_playwright() as pw:')],globals())
OUT=Path(__file__).parent/'artifacts'/'memories73';OUT.mkdir(parents=True,exist_ok=True)

def setup(p):
 p.wait_for_function('_writeReady && !!document.getElementById("memory-launch")')
 ev(p,"""()=>{activeDay='2026-10-31';S.days={
 '2026-10-31':{summary:'Current',draftText:'Keep my draft'},
 '2025-10-31':{summary:'A year ago <img src=x onerror=alert(1)>',dayRating:8},
 '2026-09-30':{summary:'Do not use a nearby day'}};renderToday();markNow();}""")

def readers(p,c):
 setup(p)
 r=ev(p,"""()=>{
 const freeze=x=>{if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;};
 const s=freeze({days:{'2026-09-15':{summary:'Legacy',dayRating:7},'2025-10-15':{summaryEntries:[{type:'voice',audioId:'v',time:'09:30'}]},'2026-09-16':{draftText:'not submitted'},'2026-09-17':{dayRatings:[]}},habitLog:{'h_2026-09-18':true},ideaTree:{roots:[{text:'Idea',date:'2026-09-19'}]}});
 const before=JSON.stringify(s),a=readMemoryDay(s,'2026-09-15'),b=readMemoryDay(s,'2026-09-15');a.gratitude.push('detached');a.profile.ratings.entries[0].v=1;
 return {dates:[getExactMemoryDate('2026-03-31','month'),getExactMemoryDate('2024-02-29','year'),getExactMemoryDate('2026-01-15','month'),getExactMemoryDate('2024-03-29','month'),getExactMemoryDate('2025-03-29','month')],targets:getMemoryTargets(s,'2026-10-15'),same:before===JSON.stringify(s),detached:b.profile.ratings.entries[0].v===7&&!b.gratitude.length,skips:!hasMemoryContent(s,'2026-09-16')&&!hasMemoryContent(s,'2026-09-17'),standalone:hasMemoryContent(s,'2026-09-18')&&hasMemoryContent(s,'2026-09-19'),absent:readMemoryDay(s,'2020-01-01').entries.length===0};
 }""")
 check(r['dates']==[None,None,'2025-12-15','2024-02-29',None],r)
 check([x['dateKey'] for x in r['targets']]==['2026-09-15','2025-10-15'],r)
 check(all(r[k] for k in ['same','detached','skips','standalone','absent']),r)
 check(ev(p,"()=>Object.keys(LANG.uk).filter(k=>k.startsWith('memory_')).every(k=>typeof LANG.en[k]==='string'&&LANG.en[k]&&LANG.en[k]!==LANG.uk[k])"),'all memory strings translated')
 for zone in ['Pacific/Kiritimati','America/Los_Angeles','Europe/Kyiv']:
  z=browser.new_context(timezone_id=zone);q=z.new_page();q.goto(URL)
  check(ev(q,"getExactMemoryDate('2026-01-15','month')")=='2025-12-15',zone);z.close()
 return 'Frozen detached readers; exact calendar boundaries/leap dates; sparse targets; draft-only ignored; habits/ideas; 3 timezones'

def readonly(p,c):
 setup(p)
 p.locator('#memory-launch').scroll_into_view_if_needed();p.locator('#memory-launch').focus()
 ev(p,"()=>{window.beforeMemory={s:JSON.stringify(S),storage:localStorage.getItem(SK),active:activeDay,scroll:scrollY};window.forbiddenCalls=[];for(const key of ['day','ensureSummaryEntries','save','persist','renderToday']){const original=window[key];window[key]=function(...args){forbiddenCalls.push(key);return original.apply(this,args);};}}")
 p.locator('#memory-launch').click();p.wait_for_selector('#memory-view.open')
 check('31 жовтня 2025' in p.locator('#memory-date').inner_text(),'skip Sep31 and show year')
 check(p.locator('#memory-view textarea,#memory-view input,#memory-view [contenteditable]').count()==0,'no editors')
 check(p.locator('#memory-body img').count()==0,'escaped HTML')
 check('A year ago <img' in p.locator('#memory-body').inner_text(),'literal text')
 check(p.locator('#memory-next').is_disabled(),'bounded end')
 check(ev(p,"document.getElementById('app').inert"),'background isolated')
 p.keyboard.press('Tab');check(ev(p,"document.getElementById('memory-view').contains(document.activeElement)"),'focus trap')
 p.keyboard.press('Escape');p.wait_for_selector('#memory-view.open',state='hidden');p.wait_for_timeout(100)
 check(ev(p,"JSON.stringify(S)===beforeMemory.s&&localStorage.getItem(SK)===beforeMemory.storage&&activeDay===beforeMemory.active&&Math.abs(scrollY-beforeMemory.scroll)<2"),'data and position unchanged')
 check(ev(p,'forbiddenCalls.length===0'),ev(p,'forbiddenCalls'))
 check(p.locator('#day-summary').input_value()=='Keep my draft','draft preserved')
 check(ev(p,"document.activeElement.id==='memory-launch'"),'return focus')
 return 'Real click / Escape; zero editor or persistence calls; S and localStorage byte-identical; date/draft/scroll/focus preserved; HTML escaped'

def guards(p,c):
 setup(p)
 r=ev(p,"""()=>{const r=[];_voiceStarting=true;r.push(!openMemorySession());_voiceStarting=false;_voicePreviewBlob=new Blob(['x']);r.push(!openMemorySession());_voicePreviewBlob=null;_voiceMediaRecorder={state:'recording'};r.push(!openMemorySession());_voiceMediaRecorder=null;
 const orig=Storage.prototype.setItem;dirty=true;Storage.prototype.setItem=function(k,v){if(k===SK)throw new DOMException('quota','QuotaExceededError');return orig.call(this,k,v)};r.push(!openMemorySession()&&dirty&&memorySession===null);Storage.prototype.setItem=orig;
 S.days[activeDay].draftText='Latest draft';r.push(openMemorySession()&&JSON.parse(localStorage.getItem(SK)).days[activeDay].draftText==='Latest draft');closeMemorySession();
 S.days={};S.habitLog={};S.ideaTree={roots:[]};r.push(!openMemorySession()&&memorySession===null);return r;}""")
 check(all(r),r)
 return 'Recording, microphone permission, unsent voice, failed storage save block entry; retry saves draft; no targets stays on current day'

def media(p,c):
 setup(p)
 ev(p,"""async({png,wav})=>{S.days['2026-09-15']={summaryEntries:[{type:'voice',audioId:'wav',time:'12:30'},{type:'voice',audioId:'missing'}],photoIds:['photo','missing-photo'],photos:['javascript:alert(1)'],dayRatings:[{v:9,t:'13:30'}],status:'work',statusNote:'A good day',emotions:[{id:'good'}],gratitude:['A friend'],events:['A walk'],ideas:['Small idea'],media:[{name:'My book',cat:'read',status:'done',rating:4,note:'Worth reading'}]};S.days['2025-10-15']={summary:'Year'};S.habits=[{id:'h',name:'Stretch'}];S.habitLog={'h_2026-09-15':true};await _voicePut('wav',new Blob([new Uint8Array(wav)],{type:'audio/wav'}));await _photoPut('photo','data:image/png;base64,'+png);markNow();window.mediaBefore=JSON.stringify(S);window.keysBefore=JSON.stringify(await _mediaKeys());openMemorySession('2026-10-15');}""",{'png':base64.b64encode(PNG).decode(),'wav':WAV})
 p.wait_for_selector('#memory-body audio');p.wait_for_selector('#memory-photos img')
 p.wait_for_function("document.querySelector('#memory-body audio').readyState>=1")
 check(ev(p,"async()=>{const a=document.querySelector('#memory-body audio');await a.play();return a.duration>.4&&!a.paused}"),'voice plays')
 body=p.locator('#memory-body').inner_text()
 check(all(x in body for x in ['My book','Worth reading','A friend','A walk','Small idea','Stretch','9/10','Аудіозапис недоступний','Фото недоступне']),body)
 p.locator('.memory-photo').click();check(p.locator('.memory-photo').get_attribute('aria-expanded')=='true','photo expands')
 ev(p,"()=>{window.savedAudio=document.querySelector('#memory-body audio');window.revoked=[];const orig=URL.revokeObjectURL;URL.revokeObjectURL=u=>{revoked.push(u);orig(u)};}")
 p.locator('#memory-next').click();check(ev(p,"savedAudio.paused&&revoked.length===1&&memoryUrls.length===0"),'media disposed on next')
 p.locator('#memory-back').click();p.wait_for_selector('#memory-body audio');p.locator('#memory-close').click()
 check(ev(p,"async()=>JSON.stringify(S)===mediaBefore&&JSON.stringify(await _mediaKeys())===keysBefore"),'no media or journal mutations')
 # A stale asynchronous read must never attach content to another day or a closed view.
 ev(p,"()=>{window.originalGet=_voiceGet;_voiceGet=()=>new Promise(r=>window.releaseVoice=r);openMemorySession('2026-10-15');stepMemory(1);releaseVoice(new Blob(['late']));}")
 p.wait_for_timeout(50);check(p.locator('#memory-body audio').count()==0,'stale audio ignored');ev(p,"()=>{closeMemorySession();_voiceGet=originalGet;}")
 ev(p,"()=>{window.originalPhotoGet=_photoGet;_photoGet=()=>new Promise(r=>window.releasePhoto=r);S.days['2026-09-15']={photoIds:['late-photo']};openMemorySession('2026-10-15');closeMemorySession();releasePhoto(['data:image/png;base64,invalid']);}")
 p.wait_for_timeout(50);check(p.locator('#memory-body img').count()==0,'closed photo read ignored');ev(p,"()=>{_photoGet=originalPhotoGet;}")
 ev(p,"async()=>{S.days['2026-09-15']={summaryEntries:[{type:'voice',audioId:'bad'}],photos:['data:image/png;base64,invalid']};await _voicePut('bad',new Blob(['corrupt'],{type:'audio/wav'}));openMemorySession('2026-10-15');}")
 p.wait_for_function("document.getElementById('memory-body').textContent.includes(t('memory_audio_unplayable'))&&document.getElementById('memory-body').textContent.includes(t('memory_missing_photo'))")
 ev(p,'closeMemorySession()')
 return 'Actual IndexedDB WAV/photo, playback and zoom; missing/corrupt media; all day sections; URL cleanup; late audio/photo ignored; source storage unchanged'

def ui(p,c):
 setup(p)
 ev(p,"""()=>{S.days['2026-09-15']={summary:('Осінній день біля моря.\\n'.repeat(30)),dayRatings:[8],emotions:[{id:'good'}],gratitude:['Прогулянка з друзями'],status:'home'};S.days['2025-10-15']={summary:'A year ago'};markNow();window.swipe=(sel,dx,dy=0,x=90)=>{const el=document.querySelector(sel),touch=(x,y)=>new Touch({identifier:1,target:el,clientX:x,clientY:y});el.dispatchEvent(new TouchEvent('touchstart',{bubbles:true,touches:[touch(x,300)]}));el.dispatchEvent(new TouchEvent('touchend',{bubbles:true,touches:[],changedTouches:[touch(x+dx,300+dy)]}));};}""")
 for lang in ['uk','en']:
  for dark in [False,True]:
   ev(p,"({lang,dark})=>{S.settings.lang=lang;applyI18n();applyTheme(dark);openMemorySession('2026-10-15');}",{'lang':lang,'dark':dark})
   for width in [320,390,430,1024]:
    p.set_viewport_size({'width':width,'height':844});check(ev(p,"document.getElementById('memory-view').scrollWidth<=innerWidth&&document.getElementById('memory-body').scrollWidth<=innerWidth"),'overflow')
   p.set_viewport_size({'width':390,'height':844});p.screenshot(path=str(OUT/f'memory-{lang}-{dark}.png'))
   check(p.locator('#memory-title').inner_text()==('Day in the past' if lang=='en' else 'Цей день у минулому'),'i18n')
   ev(p,"swipe('#memory-body p',80,200)");check(ev(p,'memorySession.index===0'),'vertical ignored')
   ev(p,"swipe('#memory-body p',80,0,5)");check(ev(p,'memorySession.index===0'),'edge ignored')
   ev(p,"swipe('#memory-close',80)");check(ev(p,'memorySession.index===0'),'button ignored')
   ev(p,"()=>{const r=document.createRange();r.selectNodeContents(document.querySelector('#memory-body p'));getSelection().addRange(r);swipe('#memory-body p',80);}");check(ev(p,'memorySession.index===0'),'selection ignored');ev(p,'getSelection().removeAllRanges()')
   ev(p,"swipe('#memory-body p',80)");check(ev(p,'memorySession.index===1'),'right next')
   ev(p,"swipe('#memory-body p',80)");check(ev(p,'memorySession.index===1'),'no looping')
   ev(p,"swipe('#memory-body p',-80,0,200)");check(ev(p,'memorySession.index===0'),'left previous')
   ev(p,"swipe('#memory-body p',-80,0,200)");check(ev(p,'memorySession===null'),'left return')
 # Native touch contract: launch surface and textarea exclusion.
 ev(p,"()=>{activeDay='2026-10-15';swipe('#day-summary',80);}");check(ev(p,'memorySession===null'),'textarea excluded')
 ev(p,"swipe('[data-block=summary] .clabel',80)");check(ev(p,'memorySession.index===0'),'launch swipe')
 ev(p,"()=>{const before=activeDay;TODAY='2000-01-01';window.rolloverProtected=!checkDayRollover()&&activeDay===before;closeMemorySession();TODAY=todayKey();}")
 check(ev(p,'rolloverProtected'),'midnight anchor protected')
 ev(p,"()=>{const el=document.querySelector('[data-block=summary]');const a=new Touch({identifier:1,target:el,clientX:90,clientY:300}),b=new Touch({identifier:2,target:el,clientX:100,clientY:300});el.dispatchEvent(new TouchEvent('touchstart',{touches:[a],bubbles:true}));el.dispatchEvent(new TouchEvent('touchmove',{touches:[a,b],bubbles:true}));el.dispatchEvent(new TouchEvent('touchend',{touches:[],changedTouches:[new Touch({identifier:1,target:el,clientX:190,clientY:300})],bubbles:true}));}")
 check(ev(p,'memorySession===null'),'multi-touch cancels')
 return 'UK/EN x themes x 4 widths; synthetic touch direction/edge/vertical/control/textarea checks; bounded sequence; midnight guard'

with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for name,fn in [('readers',readers),('readonly',readonly),('guards',guards),('media',media),('ui',ui)]:run(name,['73.0'],fn)
 browser.close()
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
raise SystemExit(any(r['status']=='FAIL' or r.get('pageErrors') for r in results))

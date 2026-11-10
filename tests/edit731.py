"""73.1 editing existing ideas, events, custom emotions, media and recommendations."""
from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text();exec(src[:src.index('with sync_playwright() as pw:')],globals())
OUT=Path(__file__).parent/'artifacts'/'edit731';OUT.mkdir(parents=True,exist_ok=True)

def setup(p):
 p.wait_for_function('_writeReady')
 ev(p,"""()=>{
  const idea=addRootIdea('Стара ідея',activeDay);
  day().events=[{text:'Стара подія',time:'12:34'}];
  day().media=[{name:'Старе медіа',cat:'watch',status:'active'}];
  day().recs=[{id:'rec1',name:'Стара рекомендація',cat:'watch',done:false,addedDate:activeDay}];
  S.customEmotions=[{label:'Натхнення 🚀',level:'pos',color:'#34a853'}];
  day().emotions=[{id:'c_Натхнення 🚀',isManual:true,comments:[{cid:'c1',text:'Коментар',time:'12:35'}]}];
  day().summaryEntries=[{id:'entry1',type:'text',text:'Запис',time:'12:35',emotions:[{id:'c_Натхнення 🚀',comment:'До запису'}]}];
  markNow();renderToday();
  window.editIdeaId=idea.id;
 }""")

def edit_inline(p,c):
 setup(p)
 cases=[
  ('#idea-list [data-edit]', '#idea-list .entry-inline-edit input','Нова ідея'),
  ('#event-list [data-edit]', '#event-list .entry-inline-edit input','Нова подія'),
  ('#media-list [data-media-edit]', '#media-list .entry-inline-edit input','Нове медіа'),
  ('#rec-today-list [data-rec-edit]', '#rec-today-list .entry-inline-edit input','Нова рекомендація'),
 ]
 for button,field,value in cases:
  p.locator(button).click();p.locator(field).fill(value);p.locator(field).press('Enter')
 values=ev(p,"""()=>({idea:findIdeaNode(editIdeaId).node.text,event:day().events[0],media:day().media[0].name,rec:day().recs[0].name})""")
 check(values=={'idea':'Нова ідея','event':{'text':'Нова подія','time':'12:34'},'media':'Нове медіа','rec':'Нова рекомендація'},values)
 p.reload();p.wait_for_function('_writeReady');p.wait_for_selector('#idea-list')
 check(ev(p,"""()=>dayIdeasForDisplay(activeDay)[0]==='Нова ідея'&&day().events[0].text==='Нова подія'&&day().media[0].name==='Нове медіа'&&day().recs[0].name==='Нова рекомендація'"""),'reload')
 return 'Pencil → inline editor; Enter saves; event time preserved; values persist after reload'

def cancel_and_rollback(p,c):
 setup(p)
 p.locator('#event-list [data-edit]').click();p.locator('#event-list .entry-inline-edit input').fill('Не зберігати');p.locator('#event-list .entry-inline-action:not(.save)').click()
 check(ev(p,"day().events[0].text==='Стара подія'"),'cancel')
 ev(p,"""()=>{window.originalSetItem=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===SK)throw new DOMException('quota','QuotaExceededError');return originalSetItem.call(this,k,v);};}""")
 p.locator('#media-list [data-media-edit]').click();p.locator('#media-list .entry-inline-edit input').fill('Невдале медіа');p.locator('#media-list .entry-inline-action.save').click()
 check(ev(p,"day().media[0].name==='Старе медіа'&&!dirty"),'rollback in memory')
 ev(p,"()=>{Storage.prototype.setItem=originalSetItem;}");p.reload();p.wait_for_function('_writeReady')
 check(ev(p,"day().media[0].name==='Старе медіа'"),'rollback in storage')
 return 'Cancel leaves value; injected storage failure rolls back UI and storage'

def emotion(p,c):
 setup(p)
 chip=p.locator('.echip[data-id="c_Натхнення 🚀"]')
 chip.dblclick();p.wait_for_selector('dialog.edit-text-dialog[open]');p.locator('dialog.edit-text-dialog input').fill('Творчий підйом ✨');p.locator('dialog.edit-text-dialog .save').click()
 result=ev(p,"""()=>({custom:S.customEmotions[0],day:day().emotions[0],link:day().summaryEntries[0].emotions[0],comment:day().emotions[0].comments[0]})""")
 check(result['custom']['label']=='Творчий підйом ✨' and result['day']['id']=='c_Творчий підйом ✨' and result['link']['id']=='c_Творчий підйом ✨',result)
 check(result['comment']['text']=='Коментар' and result['link']['comment']=='До запису',result)
 # A single tap still toggles selection after the double-tap recognizer delay.
 p.locator('.echip[data-id="c_Творчий підйом ✨"]').click();p.wait_for_timeout(350)
 check(ev(p,"day().emotions.find(e=>e.id==='c_Творчий підйом ✨').isManual===false"),'single tap toggles manual selection while linked comments remain')
 ev(p,"()=>{S.customEmotions.push({label:'Зайнята назва',level:'neu'});renderEmotions();}")
 p.locator('.echip[data-id="c_Зайнята назва"]').dblclick();p.locator('dialog.edit-text-dialog input').fill('Творчий підйом ✨');p.locator('dialog.edit-text-dialog .save').click()
 check(p.locator('dialog.edit-text-dialog[open]').count()==1,'duplicate keeps editor open')
 p.locator('dialog.edit-text-dialog button:not(.save)').click()
 p.reload();p.wait_for_function('_writeReady');check(ev(p,"S.customEmotions[0].label==='Творчий підйом ✨'"),'rename persists')
 return 'Double tap renames custom emotion globally; comments and entry links preserved; duplicate blocked; single tap still toggles'

def responsive(p,c):
 setup(p)
 for lang in ['uk','en']:
  for dark in [False,True]:
   ev(p,"({lang,dark})=>{S.settings.lang=lang;applyTheme(dark);applyI18n();renderToday();}",{'lang':lang,'dark':dark})
   for width in [320,390,430,1024]:
    p.set_viewport_size({'width':width,'height':844})
    check(ev(p,"document.body.scrollWidth<=innerWidth"),(lang,dark,width,'overflow'))
    p.locator('#idea-list [data-edit]').click();check(ev(p,"document.querySelector('#idea-list .entry-inline-edit').getBoundingClientRect().right<=innerWidth"),'editor width');p.locator('#idea-list .entry-inline-action:not(.save)').click()
   p.set_viewport_size({'width':390,'height':844});p.locator('#idea-list').scroll_into_view_if_needed();p.screenshot(path=str(OUT/f'{lang}-{dark}.png'))
 check(ev(p,"Object.keys(LANG.uk).filter(k=>k.startsWith('edit_')).every(k=>LANG.en[k]&&LANG.en[k]!==LANG.uk[k])"),'translations')
 return 'UK/EN, themes, 320/390/430/1024 px; compact editors stay within viewport'

def visual_polish(p,c):
 setup(p)
 heights=[]
 for button,field in [
  ('#idea-list [data-edit]','#idea-list .entry-inline-edit input'),
  ('#event-list [data-edit]','#event-list .entry-inline-edit input'),
  ('#media-list [data-media-edit]','#media-list .entry-inline-edit input'),
  ('#rec-today-list [data-rec-edit]','#rec-today-list .entry-inline-edit input'),
 ]:
  p.locator(button).click();heights.append(round(p.locator(field).evaluate('e=>e.getBoundingClientRect().height'),1));p.locator('.entry-inline-action:not(.save)').click()
 check(max(heights)-min(heights)<=1,heights)
 ev(p,"()=>applyTheme(true)");p.locator('#event-list [data-edit]').click();p.locator('[data-block="events"]').scroll_into_view_if_needed();p.locator('[data-block="events"]').screenshot(path=str(OUT/'polish-editor-dark.png'));p.locator('#event-list .entry-inline-action:not(.save)').click()
 voice=ev(p,"""()=>{S.settings.showVoice=true;applyVoiceVisibility();const f=document.querySelector('#day-summary').getBoundingClientRect(),c=document.querySelector('.compose-btn-col').getBoundingClientRect();S.settings.showVoice=false;applyVoiceVisibility();const off=document.querySelector('#day-summary').getBoundingClientRect();return {field:f.height,buttons:c.height,off:off.height}}""")
 check(abs(voice['field']-voice['buttons'])<=1 and voice['off']<voice['field'],voice)
 ev(p,"()=>{S.settings.showVoice=true;applyVoiceVisibility();}");p.locator('[data-block="summary"]').scroll_into_view_if_needed();p.locator('[data-block="summary"]').screenshot(path=str(OUT/'polish-summary-dark.png'))
 p.locator('.summary-entry').first.click();delete=p.locator('[data-se-del]').first;delete.click();check(delete.inner_text()=='✕' and delete.evaluate("e=>e.classList.contains('summary-entry-del-armed')"),'delete confirm stays icon-only')
 ev(p,"()=>{S.settings.showVoice=true;day().status='travel';markNow();renderCal();}")
 sticker=p.locator('.cal-status-icon').first;check(sticker.evaluate("e=>getComputedStyle(e).fontSize")=='13px','calendar sticker size')
 return 'All inline fields share one-row height; voice-on composer aligns; delete stays icon-only; calendar sticker is 13px'

with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for name,fn in [('edit_inline',edit_inline),('cancel_rollback',cancel_and_rollback),('emotion',emotion),('responsive',responsive),('visual_polish',visual_polish)]:run(name,['73.1'],fn)
 browser.close()
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
raise SystemExit(any(r['status']=='FAIL' or r.get('pageErrors') for r in results))

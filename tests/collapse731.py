"""37.2 existing collapsible modules and persisted layout/preferences."""
from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text();exec(src[:src.index('with sync_playwright() as pw:')],globals())
OUT=Path(__file__).parent/'artifacts'/'collapse372';OUT.mkdir(parents=True,exist_ok=True)

def go(p,page):
 p.locator(f'.ni[data-page="{page}"]').click();p.wait_for_timeout(120)

def defaults(p,c):
 today=ev(p,"""()=>({
  fixed:['events','summary','ideas','rating','photos'].every(k=>!document.querySelector(`[data-block="${k}"] .today-coll-btn`))&&!document.querySelector('.today-collapse-body')&&!document.querySelector('.today-module-collapsed'),
  existing:S.emoCollapsed===true&&S.mediaCollapsed===true&&S.gratCollapsed===true&&S.habitsCollapsed===true&&S.settings.recCollapsed===true,
  existingDom:document.querySelector('#emo-card').classList.contains('emo-collapsed')&&document.querySelector('#media-card').classList.contains('media-collapsed')&&document.querySelector('#grat-card').classList.contains('grat-collapsed')&&document.querySelector('#habits-card').classList.contains('habits-collapsed')&&document.querySelector('#rec-card').classList.contains('rec-collapsed')
 })""")
 check(all(today.values()),today);p.locator('#page-today').screenshot(path=str(OUT/'today-default.png'))
 go(p,'dash');dash=ev(p,"""()=>({flags:['mood','habits','insights','ibank','timeline','recs'].every(k=>S.dashCollapsed[k]===true),cards:[...document.querySelectorAll('#dash-content>.card')].every(x=>x.classList.contains('mood-collapsed')),media:S.settings.mediaDashOpen===undefined||S.settings.mediaDashOpen===false})""");check(all(dash.values()),dash);p.locator('#page-dash').screenshot(path=str(OUT/'dash-default.png'))
 go(p,'settings');settings=ev(p,"""()=>({flags:[S.shCollapsed,S.expCollapsed,S.impCollapsed,S.gemCollapsed].every(v=>v===true),bodies:['.sh-body','.exp-body','.imp-body','.gem-body'].every(q=>document.querySelector(q).style.maxHeight==='0px')})""");check(all(settings.values()),settings);p.locator('#page-settings').screenshot(path=str(OUT/'settings-default.png'))
 return 'Only pre-existing collapsible Today, Dashboard and Settings modules start closed; fixed Today cards stay open'

def persistence(p,c):
 # Open one existing module on each screen and leave neighbouring modules closed.
 p.locator('#emo-card .emo-ch').click()
 go(p,'dash');p.locator('#dash-content>.card .mood-ch').first.click();p.locator('#ibank-dash-card .mood-ch').click()
 go(p,'settings');p.locator('#export-grp .exp-ch').click();p.locator('#dark-tog').click();p.locator('#lang-en-btn').click()
 p.wait_for_function("typeof _writeReady!=='undefined'&&_writeReady&&typeof getLang==='function'&&getLang()==='en'&&S.settings.dark===true")
 check(ev(p,"getLang()==='en'&&document.documentElement.dataset.theme==='dark'"),'language/theme after reload')
 today=ev(p,"""()=>({fixed:!document.querySelector('.today-coll-btn,.today-collapse-body,.today-module-collapsed'),emotion:S.emoCollapsed===false&&!document.querySelector('#emo-card').classList.contains('emo-collapsed'),media:S.mediaCollapsed===true&&document.querySelector('#media-card').classList.contains('media-collapsed')})""");check(all(today.values()),today)
 go(p,'dash');dash=ev(p,"""()=>({mood:S.dashCollapsed.mood===false&&!document.querySelector('#dash-content>.card').classList.contains('mood-collapsed'),ideas:S.dashCollapsed.ibank===false&&!document.querySelector('#ibank-dash-card').classList.contains('mood-collapsed'),habits:S.dashCollapsed.habits===true})""");check(all(dash.values()),dash)
 go(p,'settings');settings=ev(p,"""()=>({export:S.expCollapsed===false&&document.querySelector('.exp-body').style.maxHeight!=='0px',imports:S.impCollapsed===true&&document.querySelector('.imp-body').style.maxHeight==='0px'})""");check(all(settings.values()),settings)
 p.reload();p.wait_for_function("typeof _writeReady!=='undefined'&&_writeReady&&typeof getLang==='function'&&getLang()==='en'");check(ev(p,"S.emoCollapsed===false&&S.mediaCollapsed===true&&S.dashCollapsed.mood===false&&S.dashCollapsed.ibank===false&&S.expCollapsed===false&&S.settings.dark===true"),'second reload')
 return 'Existing opened modules, closed neighbours, English and dark theme survive two reloads'

with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for name,fn in [('defaults',defaults),('persistence',persistence)]:run(name,['37.2'],fn)
 browser.close()
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
raise SystemExit(any(r['status']=='FAIL' or r.get('pageErrors') for r in results))

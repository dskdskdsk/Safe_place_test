from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text();exec(src[:src.index('with sync_playwright() as pw:')],globals())
OUT=Path(__file__).parent/'artifacts'/'insight-d';OUT.mkdir(parents=True,exist_ok=True)
def ui(p,c):
 p.wait_for_function('_writeReady')
 for lang in ['uk','en']:
  for dark in [False,True]:
   ev(p,"""({lang,dark})=>{S.settings.lang=lang;applyI18n();applyTheme(dark);S.days={};S.habitLog={};S.habits=[{id:'h',name:'<img src=x onerror=alert(1)>'}];for(let i=0;i<84;i++){const k=insightShiftDays(todayKey(),-i);S.days[k]={dayRatings:[i%2?8:5],status:'work',emotions:[{id:'good'}]};if(i%2)S.habitLog['h_'+k]=true;}renderDash()}""",{'lang':lang,'dark':dark})
   p.locator('[data-page=dash]').click()
   for period in ['week','month','year','all']:
    p.locator('.mood-tab[data-period='+period+']').click()
    cards=p.locator('article.mood-insight');check(1<=cards.count()<=3,'card limit');check(cards.locator('img').count()==0,'escape');check(p.locator('.mood-insight-track').count()==0,'no duplicate carousel')
    check(not p.locator('#mood-period-facts').is_visible(),'raw details hidden')
    for w in [375,430,320]:
     p.set_viewport_size({'width':w,'height':844});check(ev(p,'document.documentElement.scrollWidth<=innerWidth'),'overflow')
    for d in cards.locator('details').all():d.locator('summary').click()
    p.screenshot(path=str(OUT/f'{lang}-{dark}-{period}.png'))
   ev(p,"()=>{S.days={};S.habitLog={};renderDash()}");check(p.locator('article.mood-insight').count()<=3,'empty')
 return 'UK/EN, both themes, four periods, three widths, escaping, details, empty state'
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);run('cards_ui',['D'],ui);browser.close()
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
raise SystemExit(any(r['status']=='FAIL' or r.get('pageErrors') for r in results))

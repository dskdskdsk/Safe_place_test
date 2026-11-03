from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text();exec(src[:src.index('with sync_playwright() as pw:')],globals())
OUT=Path(__file__).parent/'artifacts'/'insight-d';OUT.mkdir(parents=True,exist_ok=True)
def ui(p,c):
 p.wait_for_function('_writeReady')
 ev(p,"""()=>{const s={days:{},habitLog:{}};for(let i=1;i<=30;i++){const n=String(i).padStart(2,'0');s.days['2026-09-'+n]={dayRatings:[i%2?2:8]};s.days['2026-10-'+n]={dayRatings:[6]};}let m=readInsightOverview(s,'month','2026-10-01','2026-11-02'),e={candidates:[]};if(!selectMoodCards(m,e).some(c=>c.type==='swings'&&c.current===0))throw Error('missing swings');m.comparison.current.ratings.adjacentPairCount=4;if(selectMoodCards(m,e).some(c=>c.type==='swings'))throw Error('sparse pairs');}""")
 coverage=ev(p,"""()=>{const make=(n,prev=5)=>{const s={days:{},habitLog:{}};for(let i=1;i<=n;i++)s.days['2026-10-'+String(i).padStart(2,'0')]={dayRatings:[7]};for(let i=1;i<=prev;i++)s.days['2026-09-'+String(i).padStart(2,'0')]={dayRatings:[5]};const m=readInsightOverview(s,'month','2026-10-01','2026-11-02');return renderMoodCards(m,s,'uk')};return {full:make(29),below:make(15),half:make(16),comparable:make(29,15)}}""")
 check('Даних достатньо для підсумку' in coverage['full'] and 'На основі 29 оцінених днів' in coverage['full'],'29/31 is sufficient')
 check('Поки даних мало' in coverage['below'] and 'менше половини' in coverage['below'],'15/31 is preliminary')
 check('Поки даних мало' not in coverage['half'] and 'Даних достатньо' in coverage['half'],'16/31 meets half')
 check('Середня оцінка зросла' in coverage['comparable'] and 'На основі 29 днів цього періоду та 15 попереднього' in coverage['comparable'],'both periods meet comparison coverage')
 for lang in ['uk','en']:
  for dark in [False,True]:
   ev(p,"""({lang,dark})=>{S.settings.lang=lang;applyI18n();applyTheme(dark);S.days={};S.habitLog={};S.habits=[{id:'h',name:'<img src=x onerror=alert(1)>'}];for(let i=0;i<84;i++){const k=insightShiftDays(todayKey(),-i);S.days[k]={dayRatings:[i%2?8:5],status:'work',emotions:[{id:'good'}]};if(i%2)S.habitLog['h_'+k]=true;}renderDash()}""",{'lang':lang,'dark':dark})
   p.locator('[data-page=dash]').click()
   for period in ['week','month','year','all']:
    p.locator('.mood-tab[data-period='+period+']').click()
    story=p.locator('.mood-story');cards=story.locator('article.mood-insight-slide');check(story.count()==1 and 1<=cards.count()<=4,'one compact window, card limit');check(cards.locator('img').count()==0,'escape')
    check(story.locator('.mood-insight-track').count()==1,'single insight track');check('A / B' not in story.inner_text() and 'nA' not in story.inner_text(),'no raw formulas')
    if cards.count()>1:
     story.locator('.mood-insight-dot').last.click();p.wait_for_timeout(800);metrics=story.locator('.mood-insight-track').evaluate('e=>({client:e.clientWidth,scroll:e.scrollWidth,left:e.scrollLeft})');check(metrics['scroll']>metrics['client'] and metrics['left']>0,'dot navigation '+str(metrics))
     story.locator('.mood-insight-dot').first.click()
    check(not p.locator('#mood-period-facts').is_visible(),'raw details hidden')
    for w in [375,430,320]:
     p.set_viewport_size({'width':w,'height':844});check(ev(p,'document.documentElement.scrollWidth<=innerWidth'),'overflow')
    p.screenshot(path=str(OUT/f'{lang}-{dark}-{period}.png'))
    if lang=='uk' and not dark and period=='month':
     for i in range(cards.count()):cards.nth(i).screenshot(path=str(OUT/f'uk-month-card-{i+1}.png'))
   ev(p,"()=>{S.days={};S.habitLog={};renderDash()}");check(p.locator('.mood-story article').count()==1,'empty')
 return 'UK/EN, both themes, four periods, three widths, one compact carousel, escaping, hidden evidence, empty state'
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);run('cards_ui',['D'],ui);browser.close()
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
raise SystemExit(any(r['status']=='FAIL' or r.get('pageErrors') for r in results))

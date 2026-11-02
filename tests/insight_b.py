"""Stage B: synthetic browser acceptance and independent Python calendar oracle."""
from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text();exec(src[:src.index('with sync_playwright() as pw:')],globals())
OUT=Path(__file__).parent/'artifacts'/'insight-b';OUT.mkdir(parents=True,exist_ok=True)
def pure(p,c):
 p.wait_for_function('_writeReady');return ev(p,Path(__file__).with_name('insight_b_cases.js').read_text())
def open_facts(p):
 proof=p.locator('.insight-proof')
 if proof.get_attribute('open') is None:proof.locator(':scope > summary').click()
 f=p.locator('#mood-period-facts')
 if f.get_attribute('open') is None:f.locator(':scope > summary').click()
 return f
def ui(p,c):
 p.wait_for_function('_writeReady')
 for lang in ['uk','en']:
  for dark in [False,True]:
   ev(p,"""({lang,dark})=>{S.settings.lang=lang;applyI18n();applyTheme(dark);S.days={};S.habitLog={};S.customEmotions=[{label:'<img src=x onerror=alert(1)> '+ 'довга емоція '.repeat(8),level:'pos'}];
   const now=todayKey(),from=insightWeekStart(now),d=day(from);d.dayRatings=[2];d.emotions=[{id:'good'},{id:'bad'},{id:'c_'+S.customEmotions[0].label}];S.days[insightShiftDays(from,-7)]={dayRatings:[8]};moodPeriod='week';moodWeekOffset=0;renderDash();}""",{'lang':lang,'dark':dark})
   p.locator('[data-page=dash]').click();f=p.locator('#mood-period-facts');check(not f.get_attribute('open'));f=open_facts(p);p.wait_for_timeout(100)
   check(f.locator('summary').inner_text().startswith('Period in numbers' if lang=='en' else 'Числа за період'));check(f.locator('img').count()==0,'escaped emotion');check('-6' in f.inner_text(),'difference')
   check(ev(p,'document.documentElement.scrollWidth<=innerWidth'),'root overflow');check(f.evaluate('(e)=>e.scrollWidth<=e.clientWidth'),'facts overflow')
   check(f.evaluate("e=>{const b=e.closest('.mood-body');return b.scrollHeight<=parseFloat(b.style.maxHeight)+1}"),'clipped details')
   p.screenshot(path=str(OUT/f'{lang}-{dark}-top.png'))
   heading='Comparison with the previous period' if lang=='en' else 'Порівняння з попереднім періодом';f.get_by_role('heading',name=heading,exact=True).scroll_into_view_if_needed();p.screenshot(path=str(OUT/f'{lang}-{dark}-comparison.png'))
   for period in ['month','year','all']:
    p.locator('.mood-tab[data-period='+period+']').click();f=open_facts(p);check(f.count()==1)
   check(heading not in f.inner_text(),'all-time no comparison')
   p.locator('.mood-tab[data-period=month]').click();p.locator('#mood-prev').click();f=open_facts(p)
   check(ev(p,"insightMonthStart(todayKey(),-1).split('-').reverse().join('.')") in f.inner_text(),'historical dates')
 return 'UK/EN × light/dark, navigation/expand, escaping, dates, no overflow/clipping'
def edits(p,c):
 p.wait_for_function('_writeReady');ev(p,'()=>{activeDay=todayKey();renderToday()}');p.locator('#rating-row button').nth(1).click();p.locator('[data-page=dash]').click();check('2' in p.locator('.mood-story').inner_text())
 p.locator('[data-page=today]').click();chip=p.locator('#rating-chips>div').first.locator('span').first;chip.click();chip.click();p.locator('#rating-row button').nth(7).click();p.locator('[data-page=dash]').click();check('8' in p.locator('.mood-story').inner_text())
 p.locator('[data-page=today]').click();p.locator('#rating-chips button').first.click();p.locator('[data-page=dash]').click();f=open_facts(p);check('Ще немає оцінок' in f.inner_text());p.reload();p.wait_for_function('_writeReady');check(ev(p,'readInsightOverview(S,"week",todayKey(),todayKey()).summary.ratings.mean') is None)
 return 'Add/edit/delete refresh facts; null empty state survives reload'
def oracle(p,c):
 from datetime import date,timedelta
 from calendar import monthrange
 def dates(start,end):
  while start<=end:
   yield start;start+=timedelta(days=1)
 def score(d):return None if d.toordinal()%3==0 else d.toordinal()%10+1
 cases=[];snapshot={'days':{}}
 for y in range(2023,2027):
  for month in range(1,13):
   for day in [1,15,monthrange(y,month)[1]]:cases.append(('month',date(y,month,day)))
  for month,day in [(1,1),(2,28),(3,1),(6,15),(12,31)]:cases.append(('year',date(y,month,day)))
 for d in [date(2026,1,1),date(2026,3,8),date(2026,3,9),date(2026,10,25),date(2026,11,1),date(2026,12,31)]:cases.append(('week',d))
 for d in dates(date(2021,1,1),date(2026,12,31)):
  v=score(d);snapshot['days'][d.isoformat()]={'dayRatings':[v]} if v else {'emotions':[{'id':'ok'}]}
 expected=[]
 for kind,end in cases:
  start=end-timedelta(days=end.weekday()) if kind=='week' else date(end.year,end.month,1) if kind=='month' else date(end.year,1,1)
  pairs=[]
  for d in dates(start,end):
   try:prev=d-timedelta(days=7) if kind=='week' else date(d.year-(d.month==1),d.month-1 if d.month>1 else 12,d.day) if kind=='month' else d.replace(year=d.year-1)
   except ValueError:continue
   pairs.append({'current':d.isoformat(),'previous':prev.isoformat()})
  def stats(ds):
   vs=[score(d) for d in ds if score(d) is not None];return {'n':len(vs),'mean':sum(vs)/len(vs) if vs else None}
  baselineEnd=start-timedelta(days=start.weekday()+1);baselineFrom=baselineEnd-timedelta(days=55)
  expected.append({'period':kind,'asOf':end.isoformat(),'pairs':pairs,'current':stats([date.fromisoformat(x['current']) for x in pairs]),'previous':stats([date.fromisoformat(x['previous']) for x in pairs]),'selected':stats(list(dates(start,end))),'baselineFrom':baselineFrom.isoformat(),'baselineTo':baselineEnd.isoformat()})
 count=ev(p,"""({snapshot,cases})=>{for(const e of cases){const m=readInsightOverview(snapshot,e.period,e.asOf,e.asOf),c=m.comparison;
 if(JSON.stringify(c.pairs)!==JSON.stringify(e.pairs))throw Error('pairs '+e.asOf);
 for(const [key,profile] of [['selected',m.summary],['current',c.current],['previous',c.previous]])if(profile.ratings.count!==e[key].n||Math.abs(profile.ratings.mean-e[key].mean)>1e-10)throw Error(key+' '+e.asOf);
 if(m.baseline.range.from!==e.baselineFrom||m.baseline.range.to!==e.baselineTo)throw Error('baseline '+e.asOf);
 }return cases.length;}""",{'snapshot':snapshot,'cases':expected})
 return str(count)+' independent Python datetime/mean scenarios match'
def responsive(p,c):
 p.wait_for_function('_writeReady');p.locator('[data-page=dash]').click();f=open_facts(p)
 for width in [768,430,375,320]:
  p.set_viewport_size({'width':width,'height':844});ev(p,"document.documentElement.style.fontSize='24px'");p.wait_for_timeout(100)
  check(ev(p,'document.documentElement.scrollWidth<=innerWidth'),'root overflow');check(f.evaluate('(e)=>e.scrollWidth<=e.clientWidth'),'facts overflow');check(f.evaluate("e=>{const b=e.closest('.mood-body');return b.scrollHeight<=parseFloat(b.style.maxHeight)+1}"),'details clipped')
 return '320/375/430/768 px and enlarged root font: no overflow/clipping'
def large(p,c):
 r=ev(p,"""()=>{const snapshot={days:{},habitLog:{}};for(let i=0;i<2920;i++){const k=insightShiftDays('2019-01-01',i);snapshot.days[k]={dayRatings:[i%10+1]};for(let h=0;h<5;h++)snapshot.habitLog['h'+h+'_'+k]=1;}const t=performance.now(),m=readInsightOverview(snapshot,'year','2026-01-01','2026-11-01');return {elapsedMs:performance.now()-t,days:m.summary.calendarDayCount,mean:m.summary.ratings.mean,marks:Object.keys(snapshot.habitLog).length}}""")
 check(r['days']==305 and abs(r['mean']-5.508196721311475)<1e-10);return r
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for name,fn in [('pure',pure),('dashboard_ui',ui),('edits_refresh',edits),('calendar_oracle',oracle),('responsive',responsive),('large_history',large)]:run(name,['B'],fn)
 for zone in ['America/Los_Angeles','Pacific/Kiritimati','Europe/Kyiv']:
  c=browser.new_context(timezone_id=zone);p=c.new_page();p.goto(URL)
  try:detail=pure(p,c);results.append({'name':zone,'status':'PASS','detail':detail})
  except Exception as e:results.append({'name':zone,'status':'FAIL','detail':str(e)})
  c.close()
 browser.close()
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False,indent=2))
raise SystemExit(any(r['status']=='FAIL' or r.get('pageErrors') for r in results))

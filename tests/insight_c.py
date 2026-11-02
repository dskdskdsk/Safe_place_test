"""Stage C evidence engine acceptance; runs real inline application code."""
from pathlib import Path
import json
src=Path(__file__).with_name('regression.py').read_text();exec(src[:src.index('with sync_playwright() as pw:')],globals())
OUT=Path(__file__).parent/'artifacts'/'insight-c';OUT.mkdir(parents=True,exist_ok=True)
def pure(p,c):
 p.wait_for_function('_writeReady');return ev(p,Path(__file__).with_name('insight_c_cases.js').read_text())
def oracle(p,c):
 from datetime import date,timedelta
 from random import Random
 from statistics import mean
 from collections import defaultdict
 rng=Random(723);checked=0;repeated=0
 def stats(ds):
  vals=[d['v'] for d in ds if d['v'] is not None]
  return len(vals),mean(vals) if vals else None
 def compare(a,b):
  na,ma=stats(a);nb,mb=stats(b)
  return (ma-mb,na*nb/(na+nb)) if na and nb else (None,0)
 def close(x,y):return x is None and y is None or x is not None and y is not None and abs(x-y)<1e-10
 for case in range(24):
  start=date(2024,2,1)+timedelta(days=case*29);end=start+timedelta(days=83)
  ds=[];snapshot={'days':{},'habitLog':{},'settings':{'customStatuses':[{'id':'x'},{'id':'y'}]}}
  for i in range(84):
   day=start+timedelta(days=i);key=day.isoformat();v=rng.randint(1,10) if rng.random()<.7 else None;status=rng.choice(['x','y',None]);marks=[h for h in range(12) if rng.random()<.4]
   snapshot['days'][key]={'dayRatings':[] if v is None else [v],'status':status,'summary':'observed'}
   for h in marks:snapshot['habitLog'][f'h{h}_{key}']=True
   ds.append({'key':key,'v':v,'status':status,'marks':marks,'week':(day-timedelta(days=day.weekday())).isoformat(),'dayType':'mon-fri' if day.weekday()<5 else 'sat-sun'})
  model=ev(p,'({s,end})=>readInsightCandidates(s,"month",end,end)',{'s':snapshot,'end':end.isoformat()})
  for cand in model['candidates']:
   if cand['type']!='habit':continue
   h=int(cand['id'][1:]);first=next(d['key'] for d in ds if h in d['marks']);a=[d for d in ds if d['key']>=first and h in d['marks']];b=[d for d in ds if d['key']>=first and h not in d['marks']]
   delta,_=compare(a,b);na,_=stats(a);nb,_=stats(b)
   check(cand['A']['count']==na and cand['B']['count']==nb and close(cand['delta'],delta),'oracle groups')
   check(cand['A']['denominator']==len(a) and cand['B']['denominator']==len(b),'oracle coverage')
   weeks=[]
   for w in sorted(set(d['week'] for d in a+b)):
    dt,weight=compare([d for d in a if d['week']==w],[d for d in b if d['week']==w])
    if weight:weeks.append((dt,weight))
   local=sum(d*w for d,w in weeks)/sum(w for _,w in weeks) if weeks else None
   check(close(local,cand['localDelta']),'oracle weighted local')
   sign=1 if delta and delta>0 else -1 if delta and delta<0 else 0
   support=sum(sign*d>=.3-1e-12 for d,w in weeks) if sign else 0;opposite=sum(sign*d<=-.3+1e-12 for d,w in weeks) if sign else 0;K=len(weeks)
   eligible=bool(na>=10 and nb>=10 and K>=6 and local is not None and delta*local>0 and abs(delta)>=.7-1e-12 and abs(local)>=.7-1e-12 and 3*support>=2*K and 5*opposite<=K)
   check(cand['repeatability']['eligible']==eligible and cand['repeatability']['support']==support and cand['repeatability']['opposite']==opposite,'oracle thresholds')
   repeated+=eligible
   for ct in cand['context']['checks']:
    def key(d):
     if ct['kind']=='dayType':return d['dayType']
     if d['status'] is None:return None
     return d['status'] if ct['kind']=='status' else (d['status'],d['dayType'])
    strata=[]
    for k in set(key(d) for d in a+b)-{None}:
     aa=[d for d in a if key(d)==k];bb=[d for d in b if key(d)==k];n1,_=stats(aa);n2,_=stats(bb)
     if n1>=2 and n2>=2:strata.append((*compare(aa,bb),n1,n2))
    adj=sum(d*w for d,w,_,_ in strata)/sum(w for _,w,_,_ in strata) if strata else None
    check(ct['subgroupCount']==len(strata) and close(ct['adjustedDelta'],adj),'oracle joint/separate strata')
    check(ct['coverage']['A']['ratedIncluded']==sum(n for _,_,n,_ in strata) and ct['coverage']['B']['ratedIncluded']==sum(n for _,_,_,n in strata),'oracle context coverage')
   checked+=1
 return {'randomizedContrasts':checked,'repeatedCandidates':repeated,'seed':723,'note':'Synthetic random null data; not a false-positive guarantee'}
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 run('evidence_engine',['C'],pure)
 run('independent_python_oracle',['C'],oracle)
 for zone in ['America/Los_Angeles','Pacific/Kiritimati','Europe/Kyiv']:
  ctx=browser.new_context(timezone_id=zone);p=ctx.new_page();p.goto(URL)
  try:results.append({'name':zone,'status':'PASS','detail':pure(p,ctx)})
  except Exception as e:results.append({'name':zone,'status':'FAIL','detail':str(e)})
  ctx.close()
 browser.close()
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False,indent=2))
raise SystemExit(any(r['status']=='FAIL' or r.get('pageErrors') for r in results))

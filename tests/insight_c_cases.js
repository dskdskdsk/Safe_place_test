()=>{
 const check=(v,m)=>{if(!v)throw Error(m)},near=(a,b)=>Math.abs(a-b)<1e-10;
 let assertions=0;const ok=(v,m)=>{check(v,m);assertions++};
 const snap=()=>({days:{},habitLog:{},settings:{customStatuses:[{id:'x'},{id:'y'}]}});
 const add=(s,k,v,marked,status='x',emotion='good')=>{s.days[k]={dayRatings:v===null?[]:[v],status,emotions:emotion?[{id:emotion}]:[]};if(marked)s.habitLog['h_'+k]=true};
 const get=(s,period='month',anchor='2026-03-01',asOf='2026-03-29')=>readInsightCandidates(s,period,anchor,asOf);
 const habit=s=>get(s).candidates.find(c=>c.type==='habit'&&c.id==='h');
 const freeze=o=>{if(o&&typeof o==='object'){Object.values(o).forEach(freeze);Object.freeze(o)}return o};
 const stable=snap();for(let i=0;i<84;i++)add(stable,insightShiftDays('2026-01-05',i),i%7<3?8:6,i%7<3);
 freeze(stable);const before=JSON.stringify(stable),saved={day,save,persist,now:Date.now,random:Math.random};
 let result;
 try{day=save=persist=()=>{throw Error('forbidden mutation')};Date.now=Math.random=()=>{throw Error('implicit input')};result=get(stable);ok(JSON.stringify(result)===JSON.stringify(get(stable)),'deterministic');}finally{({day,save,persist}=saved);Date.now=saved.now;Math.random=saved.random;}
 ok(before===JSON.stringify(stable),'no mutation');const c=result.candidates.find(c=>c.type==='habit');
 ok(c.level===3&&c.repeatability.support===12&&near(c.delta,2)&&near(c.localDelta,2),'positive repeated');
 ok(c.context.checks.some(x=>x.kind==='joint'),'joint context reported');
 c.A.observedDays.push('mutated');ok(before===JSON.stringify(stable),'detached output');
 const neg=JSON.parse(before);for(const d of Object.values(neg.days))d.dayRatings=[10-d.dayRatings[0]];
 ok(habit(neg).level===3&&habit(neg).delta<0,'negative repeated');
 for(let freq=1;freq<=7;freq++){
  const s=snap();for(let i=0;i<84;i++)add(s,insightShiftDays('2026-01-05',i),i%7<freq?8:6,i%7<freq);
  const h=habit(s);ok(freq===7?h.delta===null&&h.level===1&&h.B.count===0:h.level===3,'frequency '+freq);
 }
 const rep=(d,l,ds,n=10)=>insightRepeatability(d,l,n,n,ds.map(delta=>({delta})));
 ok(rep(1,1,[1.2,1.2,1.2,1.2,1.2,.2,.2]).eligible,'5 support + 2 neutral');
 ok(rep(.7,.7,[.3,.3,.3,.3,0,0]).eligible,'exact 2/3 and .3');
 ok(!rep(.7,.7,[.3,.3,.3,0,0,0]).eligible,'below 2/3');
 ok(rep(.7,.7,[1,1,1,1,1,1,1,0,-.3,-.3]).eligible,'exact 20 percent');
 ok(!rep(.7,.7,[1,1,1,1,1,1,1,-.3,-.3,-.3]).eligible,'above 20 percent');
 ok(!rep(.699,.7,[1,1,1,1,1,1]).eligible&&!rep(.7,.699,[1,1,1,1,1,1]).eligible,'magnitude boundaries');
 ok(!rep(1,-1,[1,1,1,1,1,1]).eligible&&!rep(1,1,[1,1,1,1,1,1],9).eligible,'direction and count gates');
 ok(rep(-.7,-.7,[-.3,-.3,-.3,-.3,0,0]).eligible,'negative boundary');
 const sparse=snap();for(let i=0;i<20;i++)add(sparse,insightShiftDays('2026-01-05',i),i%2?null:8,i<10);
 let h=habit(sparse);ok(h.level===2&&h.A.count===5&&h.B.count===5&&h.A.coverage===.5,'5 per group');
 delete sparse.days['2026-01-05'];h=habit(sparse);ok(h.level===1&&h.A.count===4,'4 per group');
 const groups=snap();groups.habitLog.h_2026_01_01=false;
 groups.days['2026-01-05']={dayRatings:[1]};add(groups,'2026-01-06',8,true);
 groups.days['2026-01-07']={draftText:'draft'};groups.days['2026-01-08']={};groups.days['2026-01-09']={gratitude:['thanks']};groups.habitLog.other_2026_01_10=false;groups.habitLog['other_2026-01-10']=true;
 h=habit(groups);ok(h.firstAvailableMark==='2026-01-06'&&h.B.denominator===2&&h.B.count===0,'first mark, drafts, other marks, gratitude');
 add(groups,'2026-01-11',5,false,'missing',null);add(groups,'2026-01-12',4,false,'y','bad');
 const cs=get(groups).candidates;ok(cs.find(x=>x.type==='status'&&x.id==='x').B.count===1,'unknown status excluded');ok(cs.find(x=>x.type==='emotion'&&x.id==='good').B.count===1,'missing emotion excluded');
 const trend=snap();for(let w=0;w<12;w++)for(let j=0;j<7;j++)add(trend,insightShiftDays('2026-01-05',7*w+j),2+w*.5,j<(w<6?1:6));
 h=habit(trend);ok(h.delta>.7&&near(h.localDelta,0)&&h.level===2,'time trend without within-week link');
 const profile=(v,status,k)=>({dateKey:k,ratings:{mean:v},status:{id:status,known:status!==null}});
 const A=[],B=[];for(let i=0;i<10;i++){A.push(profile(i<8?8:2,i<8?'x':'y',insightShiftDays('2026-01-05',i)));B.push(profile(i<2?9:3,i<2?'x':'y',insightShiftDays('2026-02-02',i)));}
 const ctxt=insightContextCheck(A,B,'status',3.6);ok(ctxt.state==='contradiction'&&near(ctxt.adjustedDelta,-1)&&ctxt.subgroupCount===2,'Simpson status reversal');
 const partial=insightContextCheck([...A,...Array.from({length:30},()=>profile(5,null,'2026-03-01'))],B,'status',1);
 ok(partial.coverage.A.ratedFraction===.25&&partial.subgroupCount===2,'partial below 50 percent retained');
 ok(insightContextCheck(A.map(d=>({...d,status:{id:null,known:false}})),B,'status',1).state==='unavailable','unperformed is not success');
 const early=get(stable,'week','2026-02-04','2026-12-31');ok(early.range.to==='2026-02-08'&&early.range.from==='2025-11-17','historical 84 day window');
 const future=get(stable,'month','2027-01-01');ok(future.candidates.length===0&&future.range===null,'future');
 const year=get(stable,'year','2026-01-01');ok(year.range.from==='2026-01-01'&&year.range.to==='2026-03-29','year');
 ok(get(stable,'all').candidates.length===0,'all policy explicit');
 const historic=JSON.parse(before);add(historic,'2026-12-31',1,true);ok(JSON.stringify(get(historic))===JSON.stringify(get(stable)),'future observations ignored');
 const changed=JSON.parse(before);changed.days['2026-01-05'].dayRatings=[1];ok(habit(changed).delta!==habit(stable).delta,'edit refresh');delete changed.habitLog['h_2026-01-05'];ok(habit(changed).firstAvailableMark==='2026-01-06','delete first mark');
 ok(get(stable,'month','2026-03-01','2026-03-25').candidates[0].weeks.at(-1).partial,'partial edge week');
 const simpson=snap();for(let w=0;w<12;w++)for(let j=0;j<7;j++){
  const marked=j<4,status=j<3||j===4?'x':'y',v=marked?(status==='x'?8:2):(status==='x'?9:3);
  add(simpson,insightShiftDays('2026-01-05',7*w+j),v,marked,status);
 }
 const sh=habit(simpson);ok(sh.level===3&&sh.context.contradiction&&!sh.generalInterpretationAllowed&&sh.interpretation==='context-dependent','repeated Simpson candidate blocked, numbers retained');
 const ca=[],cb=[];for(let i=0;i<10;i++){
  ca.push(profile(i<8?8:2,'x',i<8?'2026-01-10':'2026-01-05'));
  cb.push(profile(i<2?9:3,'x',i<2?'2026-01-11':'2026-01-06'));
 }
 ok(insightContextCheck(ca,cb,'dayType',3.6).state==='contradiction','calendar day type reversal');
 const onlyA=[profile(8,'x','2026-01-05'),profile(8,'x','2026-01-06'),profile(8,'y','2026-01-10'),profile(8,'y','2026-01-11')];
 const onlyB=[profile(6,'y','2026-01-05'),profile(6,'y','2026-01-06'),profile(6,'x','2026-01-10'),profile(6,'x','2026-01-11')];
 ok(insightContextCheck(onlyA,onlyB,'status',2).state==='consistent'&&insightContextCheck(onlyA,onlyB,'dayType',2).state==='consistent'&&insightContextCheck(onlyA,onlyB,'joint',2).state==='unavailable','separate checks do not prove joint context');
 return {assertions};
}

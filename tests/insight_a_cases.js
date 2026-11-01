() => {
  const assert=(x,m)=>{if(!x)throw Error(m);};
  const equal=(a,b,m)=>assert(JSON.stringify(a)===JSON.stringify(b),m);
  const freeze=x=>{if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;};
  const asOf='2026-03-10';
  const s={days:{
    '2026-03-01':{dayRatings:[2],summary:'duplicated',summaryEntries:[{id:'real',text:'entry',time:'00:00',createdAt:1234,emotions:[{id:'good'},{id:'c_custom'}, {id:'bad'}],emotionId:'ok'}],emotions:[{id:'good'},{id:'c_string'},{id:'c_invalid'},{id:'missing'}],emotion:'great',emotionId:'c_custom',status:'work'},
    '2026-03-02':{dayRatings:Array(9).fill({v:8,t:'12:00'}),draftText:'draft'},
    '2026-03-03':{dayRatings:[null,0,11,'8',{}, {v:NaN}],dayRating:6,summary:'legacy'},
    '2026-03-04':{summary:'cleared',_summaryCleared:true,draftText:'draft',_voicePreviewBlob:{audioId:'preview'}},
    '2026-03-05':{summaryEntries:[{type:'voice',audioId:'voice',emotions:[{id:'c_negative'},{id:'c_neutral'}]},{text:'sent'},{text:''},{type:'voice'}],summary:'not another entry',status:'deleted'},
    '2026-03-06':{summaryEntries:[{text:''}],summary:'legacy fallback'},
    '2026-03-07':{dayRatings:[{v:7,ts:'bad',t:'99:00',recordedDay:'2026-02-30',retro:'no'}],status:'own'},
    '2026-03-08':{dayRatings:[{v:9,ts:1700000000000,t:'12:00',recordedDay:'2026-03-08',retro:false}]},
    '2026-03-09':{},'2026-03-11':{dayRatings:[10]}},
    habitLog:{'a_b_2026-03-09':1,'off_2026-03-10':0},customEmotions:[{label:'custom',level:'pos'},'string',{label:'invalid',level:'foo'},{label:'negative',level:'neg'},{label:'neutral',level:'neu'}],settings:{customStatuses:[{id:'own'}]}};
  const before=JSON.stringify(s);freeze(s);
  const originals=[day,ensureSummaryEntries,save,persist,Date.now,Math.random,Storage.prototype.setItem];
  const forbidden=()=>{throw Error('Reader side effect');};
  let a,b;
  try{
    day=ensureSummaryEntries=save=persist=Date.now=Math.random=Storage.prototype.setItem=forbidden;
    a=readInsightPeriod(s,'2026-03-01','2026-03-31',asOf);b=readInsightPeriod(s,'2026-03-01','2026-03-31',asOf);
  }finally{[day,ensureSummaryEntries,save,persist,Date.now,Math.random,Storage.prototype.setItem]=originals;}
  equal(a,b,'determinism');assert(JSON.stringify(s)===before,'input unchanged');
  equal(readInsightPeriod(s,'2026-03-01','2026-03-02',asOf).ratings.mean,5,'equal day weights');
  const d=a.days[0];equal(d.ratings.range,null,'one rating range');equal(d.ratings.meanAbsoluteDeviation,null,'one rating MAD');
  equal(readInsightPeriod(s,'2026-03-01','2026-03-02',asOf).ratings.medianAbsoluteDeviation,3,'period MAD');
  equal(d.entries.count,1,'summary not duplicated');equal(d.entries.sources[0].provenance,'unknown','midnight not declared migrated');
  equal(d.emotions.uniqueIds,['bad','c_custom','c_invalid','c_string','good','great','missing','ok'],'union IDs');
  equal(d.emotions.unknownIds,['c_invalid','c_string','missing'],'unknown not neutral');assert(d.emotions.knownLevels.some(e=>e.id==='c_custom'&&e.level==='pos'),'custom pos');
  assert(a.days[4].emotions.knownLevels.some(e=>e.level==='neg')&&a.days[4].emotions.knownLevels.some(e=>e.level==='neu'),'custom neg/neu');
  equal(a.days[2].ratings.mean,6,'legacy fallback');equal(a.days[2].quality.diagnostics.filter(x=>x.code==='invalid-rating').length,6,'invalid ratings diagnostics');
  equal(a.days[3].entries.count,0,'draft/preview/cleared excluded');assert(!a.days[3].flags.hasSubmittedData,'draft not observed');
  equal(a.days[4].entries.count,2,'voice+text');equal(a.days[5].entries.count,1,'invalid entries fallback summary');
  assert(a.days[4].status.id==='deleted'&&!a.days[4].status.known,'unknown status preserved');assert(a.days[6].status.known,'custom status');
  equal(a.days[6].ratings.mean,7,'invalid metadata preserves value');equal(a.days[6].ratings.entries[0].provenance,'unknown','invalid time unknown');
  equal(a.days[7].ratings.entries[0].provenance,'recorded','valid origin');
  equal(a.days[8].habits.markedIds,['a_b'],'habit key exact');assert(a.days[8].flags.hasSubmittedData,'habit only observed');
  equal(a.calendarDayCount,10,'elapsed denominator');equal(a.coverage.ratings,{count:5,denominator:10,fraction:.5},'coverage');
  equal(a.ratings.adjacentPairs.map(p=>[p.from,p.to]),[['2026-03-01','2026-03-02'],['2026-03-02','2026-03-03'],['2026-03-07','2026-03-08']],'no jumping gaps');
  equal(a.emotions.frequencies.find(e=>e.id==='good').count,1,'emotion frequency per day');equal(a.availableHistoryStart,'2026-03-01','available start');
  a.days[0].emotions.uniqueIds.push('mutation');a.days[0].ratings.entries[0].v=10;a.days[0].entries.sources[0].id='changed';equal(JSON.stringify(s),before,'detached output');
  const empty=readInsightPeriod({},'2026-03-11','2026-03-12',asOf);equal(empty.calendarDayCount,0,'future empty');equal(empty.ratings.mean,null,'empty null');equal(empty.coverage.ratings.fraction,null,'no denominator');
  const zeros=readInsightPeriod({},'2026-03-01','2026-03-10',asOf);equal(zeros.counts.unobserved,10,'empty dates counted');equal(zeros.ratings.meanAdjacentAbsoluteDifference,null,'no pairs');
  for(const [from,to,n] of [['2024-02-28','2024-03-01',3],['2026-03-07','2026-03-10',4],['2026-10-24','2026-10-27',4],['2025-12-31','2026-01-01',2]])equal(readInsightPeriod({},from,to,'2026-12-31').calendarDayCount,n,'calendar '+from);
  for(const v of [null,'2026-02-30','2026-2-03']){let failed=false;try{readInsightDay({},v,asOf);}catch(e){failed=true;}assert(failed,'invalid calendar input');}
  const dispersion=readInsightDay({days:{[asOf]:{dayRatings:[2,{v:8}]}}},asOf,asOf);equal([dispersion.ratings.mean,dispersion.ratings.range,dispersion.ratings.meanAbsoluteDeviation],[5,6,3],'day dispersion');
  const only=readInsightPeriod({habitLog:{h_2026_2026:0,'h_2026-03-01':1},days:{}},'2026-03-01','2026-03-02',asOf);equal(only.availableHistoryStart,'2026-03-01','habit history');
  return 'frozen input, no side effects, deterministic detached profiles, ratings, coverage, entries, emotions, habits, dates';
}

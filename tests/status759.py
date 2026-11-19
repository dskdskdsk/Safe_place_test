"""Archive preserves history, restoration is targeted and persistence is atomic."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root)))
Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=b.new_page(viewport={'width':390,'height':844})
    page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('_writeReady')
    page.evaluate('''()=>{
      S.settings.customStatuses=Array.from({length:7},(_,i)=>({id:'s'+i,label:'Status '+i,icon:'🎓',color:'#123456'}));
      day(TODAY).status='s0';day(addDaysKey(TODAY,-1)).status='s0';persist();renderToday();
    }''')
    page.locator('.cs-x[data-id="s0"]').click()
    assert page.evaluate("customStatusCount()") == 6
    assert page.evaluate("day(TODAY).status") == 's0'
    assert page.evaluate("getStatusDefinition(day(addDaysKey(TODAY,-1)).status).label") == 'Status 0'
    assert page.locator('#status-archive').is_visible()
    page.evaluate("renameCustomStatus('s1','Renamed');S.settings.customStatuses.push({id:'new',label:'New',icon:'📌',color:'#123456'});persist()")
    assert page.evaluate("restoreCustomStatus('s0')") is False
    assert page.evaluate("S.settings.customStatuses.find(s=>s.id==='s0').archived") is True
    page.evaluate("archiveCustomStatus('s2')")
    assert page.evaluate("restoreCustomStatus('s0')") is True
    assert page.evaluate("getStatusDefinition('s1').label") == 'Renamed'
    assert page.evaluate("getStatusDefinition('new').label") == 'New'
    page.evaluate('''()=>{
      const original=persist,before=JSON.stringify(S);persist=()=>false;
      if(archiveCustomStatus('s0')||JSON.stringify(S)!==before)throw Error('archive rollback');
      persist=original;archiveCustomStatus('s0');
      const archived=JSON.stringify(S);persist=()=>false;
      if(restoreCustomStatus('s0')||JSON.stringify(S)!==archived)throw Error('restore rollback');
      persist=original;
      const backup=JSON.parse(JSON.stringify(S));S.days={};S.settings.customStatuses=[];persist();
      if(importJournalJson(backup,'en').error)throw Error('import');
      if(!S.settings.customStatuses.find(s=>s.id==='s0').archived||day(TODAY).status!=='s0')throw Error('archive roundtrip');
      renderToday();
    }''')
    page.locator('#status-archive summary').click()
    page.locator('#status-archive button').first.click()
    assert page.evaluate("S.settings.customStatuses.find(s=>s.id==='s0').archived") is False
    b.close()
server.shutdown()
print('PASS archive history, active limit, targeted restoration, rollback, import and archive UI')

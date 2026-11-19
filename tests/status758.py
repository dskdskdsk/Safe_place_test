"""Status import integrity and immediate selection regression."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
Thread(target=server.serve_forever, daemon=True).start()
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page()
    page.goto(f'http://127.0.0.1:{server.server_port}')
    page.wait_for_function('_writeReady')
    result = page.evaluate('''() => {
      const definition={id:'cs_test',label:'Imported',icon:'🎓',color:'#123456'};
      const k=addDaysKey(TODAY,-1),local=addDaysKey(TODAY,-2);
      const backup={days:{[k]:{status:definition.id}},settings:{customStatuses:[definition]}};
      const imp=()=>importJournalJson(JSON.parse(JSON.stringify(backup)),'en');
      if(imp().error||getStatusDefinition(day(k).status).label!=='Imported')throw Error('clean import');
      S.settings.customStatuses[0].label='Local';day(local).status='cs_test';persist();
      if(imp().error)throw Error('conflict import');
      const mapped=day(k).status;
      if(mapped==='cs_test'||day(local).status!=='cs_test'||getStatusDefinition(mapped).label!=='Imported')throw Error('mapping');
      const count=S.settings.customStatuses.length;imp();
      if(count!==S.settings.customStatuses.length||day(k).status!==mapped)throw Error('repeat import');
      const before=JSON.stringify(S),original=persist;persist=()=>false;
      const failed=imp();persist=original;
      if(!failed.error||JSON.stringify(S)!==before)throw Error('rollback');
      for(const statuses of [{},[definition,definition],[{...definition,id:'home'}],[{...definition,color:'invalid'}]]){
        let rejected=false;try{validateJournal({days:{},settings:{customStatuses:statuses}})}catch(e){rejected=true}
        if(!rejected)throw Error('invalid accepted');
      }
      const legacy=Array.from({length:9},(_,i)=>({id:'legacy'+i,label:'Same'}));
      if(validateJournal({days:{},settings:{customStatuses:legacy}}).settings.customStatuses.length!==9)throw Error('legacy trimmed');
      activeDay=TODAY;day().status='home';renderToday();return definition.id;
    }''')
    chip = page.locator(f'.cs-chip[data-status="{result}"]')
    chip.click()
    assert page.evaluate('day().status') == result
    page.evaluate('activeDay=addDaysKey(TODAY,-3);renderToday()')
    page.wait_for_timeout(500)
    assert page.evaluate('day().status') == ''
    page.evaluate("activeDay=TODAY;day().status='home';renderToday()")
    chip.dblclick(delay=80)
    page.locator('dialog.edit-text-dialog').wait_for(state='visible')
    assert page.evaluate('day().status') == 'home'
    browser.close()
server.shutdown()
print('PASS: clean/conflicting/repeated imports, rollback, validation, legacy preservation, immediate tap and double tap')

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
    page=b.new_page(viewport={'width':375,'height':812})
    page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('_writeReady')
    page.evaluate('''()=>{
      day().status='travel';day().statusNote='Vienna';toggleDayStatus('home');
      if(readStatusNote(day())!=='')throw Error('leaked details');
      toggleDayStatus('travel');if(readStatusNote(day())!=='Vienna')throw Error('lost details');
      S.settings.customStatuses=[{id:'custom',label:'Unique training',icon:'🎓',color:'#123456'}];S.days={};
      for(const offset of [-5,-3])day(addDaysKey(TODAY,offset)).status='custom';
      const box=document.createElement('div');box.innerHTML=buildTimeline(null);
      if(box.querySelectorAll('.tl-days').length!==2)throw Error('gap merged');
      if(!box.querySelector('.tl-stat').textContent.includes('Unique training'))throw Error('filter label');
      day(addDaysKey(TODAY,-4)).status='custom';box.innerHTML=buildTimeline(null);
      if(box.querySelectorAll('.tl-days').length!==1)throw Error('adjacent not merged');
      searchQuery='unique training';renderNotesList();
      if(document.querySelectorAll('.nday-compact').length!==3)throw Error('status search');
      if(!document.querySelector('.nday-compact-date').textContent.includes('Unique training'))throw Error('list label');
      openDrawer(addDaysKey(TODAY,-3));
      if(!document.querySelector('.drawer-date').textContent.includes('Unique training'))throw Error('drawer label');
    }''')
    b.close()
server.shutdown()
print('PASS details ownership, timeline gaps/adjacency, filters, search and drawer labels')

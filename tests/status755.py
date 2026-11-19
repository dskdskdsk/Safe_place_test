"""75.5 custom-status propagation and unified dark accent."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tests' / 'artifacts' / 'status755'
OUT.mkdir(parents=True, exist_ok=True)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}'

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(url)
    page.wait_for_function('_writeReady')

    target = page.evaluate('''() => {
        const k=addDaysKey(TODAY,-1);
        activeDay=k;
        S.days[k]={emotions:[],dayRating:8,dayRatings:[{value:8,time:'20:00'}],ideas:[],events:[],photos:[],photoIds:[],gratitude:['','',''],summary:'Тест статусу',summaryEntries:[{id:'s1',type:'text',text:'Тест статусу',time:'20:00'}],status:'home',statusNote:''};
        renderToday();renderCal();return k;
    }''')

    # Create a custom status through the real form and select a non-default sticker.
    page.locator('#cs-add-btn').click()
    page.locator('#cs-name').fill('Навчання')
    page.locator('.cs-icon-btn[data-icon="🎓"]').click()
    page.screenshot(path=str(OUT / 'sticker-picker.png'), full_page=True)
    page.locator('#cs-save').click()
    custom = page.locator('#status-chips .cs-chip').last
    custom.click()
    page.wait_for_timeout(400)

    status_id = page.evaluate('(k) => S.days[k].status', target)
    assert status_id.startswith('cs_')
    assert page.evaluate('(id) => getStatusDefinition(id).icon', status_id) == '🎓'
    assert page.evaluate('(k) => JSON.parse(localStorage.getItem(SK)).days[k].status', target) == status_id

    # The already-rendered calendar must update immediately, not retain the old home sticker.
    sticker = page.locator(f'.cal-day[data-k="{target}"] .cal-status-icon')
    assert sticker.text_content() == '🎓'

    # Calendar drawer and compact Notes list use the same custom definition.
    page.evaluate('(k) => openDrawer(k)', target)
    assert '🎓' in page.locator('#day-drawer .drawer-date').text_content()
    page.locator('#drawer-overlay').click()
    page.locator('[data-page="notes"]').click()
    page.screenshot(path=str(OUT / 'calendar-custom-status.png'), full_page=True)
    page.locator('.notes-sw-btn[data-nview="list"]').click()
    assert '🎓' in page.locator(f'.nday-compact[data-k="{target}"] .nday-compact-date').text_content()

    # Dashboard timeline and legacy status statistics include custom statuses.
    page.locator('[data-page="dash"]').click()
    assert 'Навчання' in page.locator('#timeline-inner').text_content()
    status_insight = page.evaluate('''([id,target]) => {
        const k=addDaysKey(target,-1);
        S.days[k]={emotions:[],dayRating:9,dayRatings:[{value:9}],ideas:[],events:[],photos:[],photoIds:[],gratitude:['','',''],summary:'Ще день',summaryEntries:[],status:id,statusNote:''};
        const box=document.createElement('div');renderInsStatus(box);return box.textContent;
    }''', [status_id, target])
    assert 'Навчання' in status_insight

    # Memories and legacy definitions without an icon retain a safe pin fallback.
    assert page.evaluate('(k) => readMemoryDay(S,k).statusDef.icon', target) == '🎓'
    assert page.evaluate('''() => {S.settings.customStatuses.push({id:'legacy_status',label:'Старий',color:'#4A9EFF'});return getStatusDefinition('legacy_status').icon;}''') == '📌'

    # The intentional current-day rule remains: stickers appear only after a day ends.
    page.evaluate('''id => {day(TODAY).status=id;calYear=+TODAY.slice(0,4);calMonth=+TODAY.slice(5,7)-1;renderCal();}''', status_id)
    assert page.locator(f'.cal-day[data-k="{page.evaluate("TODAY")}"] .cal-status-icon').count() == 0

    # Dark theme now has one teal action token everywhere that previously used --fill.
    page.evaluate('applyTheme(true)')
    page.wait_for_timeout(400)
    tokens = page.evaluate('''() => {const s=getComputedStyle(document.documentElement);return{pri:s.getPropertyValue('--pri').trim(),fill:s.getPropertyValue('--fill').trim(),hover:s.getPropertyValue('--fill-hover').trim(),prih:s.getPropertyValue('--prih').trim()};}''')
    assert tokens['pri'] == tokens['fill'] == '#4f98a3', tokens
    assert tokens['hover'] == tokens['prih'] == '#227f8b', tokens
    for selector in ('.preset-btn.active', '#event-add', '.notes-sw-btn.active'):
        color = page.locator(selector).first.evaluate('(e) => getComputedStyle(e).backgroundColor')
        assert color == 'rgb(79, 152, 163)', (selector, color)

    assert not errors, errors
    page.close()
    browser.close()

server.shutdown()
source = (ROOT / 'index.html').read_text()
assert 'rgb(39 100 107)' not in source and 'rgb(30 83 89)' not in source
print('PASS: custom status across calendar, Notes, dashboard, insights, memories and dark theme')

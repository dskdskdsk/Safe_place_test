"""75.3 control depth, placeholder hierarchy and responsive containment."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}'

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    for width in (375, 390, 430):
        for dark in (False, True):
            page = browser.new_page(viewport={'width': width, 'height': 844}, is_mobile=True, has_touch=True)
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            page.wait_for_function('_writeReady')
            page.evaluate('''dark => {
                applyTheme(dark);
                const media = document.querySelector('#media-card .media-body');
                const rec = document.querySelector('#rec-card .rec-body');
                document.querySelector('#media-card').classList.remove('media-collapsed');
                document.querySelector('#rec-card').classList.remove('rec-collapsed');
                media.style.maxHeight = '2000px';
                rec.style.maxHeight = '2000px';
            }''', dark)

            for selector in ('.status-chip', '.media-tab', '.rec-cat-btn'):
                assert page.locator(selector).first.bounding_box()['height'] >= 40, (width, dark, selector)

            assert page.locator('#status-chips').evaluate('(e) => getComputedStyle(e).paddingLeft') == '16px'
            assert page.locator('#media-card>.media-body>.cb').evaluate('(e) => getComputedStyle(e).paddingLeft') == '16px'
            assert page.locator('#rec-card>.rec-body>.cb').evaluate('(e) => getComputedStyle(e).paddingLeft') == '16px'

            for selector in ('.media-tab.active', '.rec-cat-btn.active'):
                color = page.locator(selector).evaluate('(e) => getComputedStyle(e).color')
                assert color == 'rgb(255, 255, 255)', (width, dark, selector, color)

            if dark:
                placeholder = page.locator('#media-in').evaluate("e => getComputedStyle(e, '::placeholder').color")
                value_color = page.locator('#media-in').evaluate('e => getComputedStyle(e).color')
                assert placeholder == 'rgb(130, 126, 120)', placeholder
                assert placeholder != value_color

            assert page.evaluate("document.querySelector('#page-today').scrollWidth <= document.querySelector('#page-today').clientWidth + 1")
            assert not errors, errors
            page.close()
    browser.close()

server.shutdown()
print('PASS: 75.3 controls across 3 iPhone widths and both themes')

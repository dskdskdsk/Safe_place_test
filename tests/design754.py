"""75.4 dark-theme accent consistency and control height."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tests' / 'artifacts' / 'design754'
OUT.mkdir(parents=True, exist_ok=True)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}'

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    for width in (375, 390, 430):
        page = browser.new_page(viewport={'width': width, 'height': 844}, is_mobile=True, has_touch=True)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        page.wait_for_function('_writeReady')
        page.evaluate('''() => {
            applyTheme(true);
            document.querySelector('.toggle').classList.add('on');
        }''')
        page.wait_for_timeout(400)

        accent = 'rgb(79, 152, 163)'
        white = 'rgb(255, 255, 255)'
        active_controls = (
            '.preset-btn.active', '.notes-sw-btn.active', '.media-tab.active',
            '.rec-cat-btn.active', '#event-add', '#idea-add', '#media-add-btn',
            '#rec-add-btn', '#habit-add-btn', '.toggle.on'
        )
        for selector in active_controls:
            background = page.locator(selector).first.evaluate('(e) => getComputedStyle(e).backgroundColor')
            assert background == accent, (width, selector, background)

        for selector in active_controls[:-1]:
            color = page.locator(selector).first.evaluate('(e) => getComputedStyle(e).color')
            assert color == white, (width, selector, color)

        for selector in ('.preset-btn', '.status-chip', '#cs-add-btn'):
            height = page.locator(selector).first.evaluate('(e) => parseFloat(getComputedStyle(e).minHeight)')
            assert height >= 42, (width, selector, height)
        assert page.locator('.notes-sw-btn').first.evaluate('(e) => parseFloat(getComputedStyle(e).minHeight)') >= 40

        # Semantic status colors remain distinct from the general action accent.
        page.locator('.status-chip[data-status="travel"]').evaluate('(e) => e.classList.add("sel-travel")')
        travel = page.locator('.status-chip[data-status="travel"]').evaluate('(e) => getComputedStyle(e).color')
        assert travel != accent

        assert page.evaluate("document.querySelector('#page-today').scrollWidth <= document.querySelector('#page-today').clientWidth + 1")
        if width == 430:
            page.screenshot(path=str(OUT / 'dark-today.png'), full_page=True)
            page.locator('[data-page="notes"]').click()
            page.screenshot(path=str(OUT / 'dark-notes.png'), full_page=True)
            page.locator('[data-page="settings"]').click()
            page.screenshot(path=str(OUT / 'dark-settings.png'), full_page=True)
        assert not errors, errors
        page.close()
    browser.close()

server.shutdown()
print('PASS: 75.4 dark accent and heights across 3 iPhone widths')

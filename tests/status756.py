"""75.6 responsive custom-status sticker layout."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "artifacts" / "status756"
OUT.mkdir(parents=True, exist_ok=True)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}"

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    for width, expected_rows in ((375, 2), (390, 1), (430, 1)):
        page = browser.new_page(viewport={"width": width, "height": 844}, is_mobile=True, has_touch=True)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url)
        page.wait_for_function("_writeReady")
        page.locator("#cs-add-btn").click()

        buttons = page.locator("#cs-icon-picker .cs-icon-btn")
        assert buttons.count() == 8
        assert page.locator("#cs-icon-custom").count() == 0
        tops = buttons.evaluate_all("els => [...new Set(els.map(el => Math.round(el.getBoundingClientRect().top)))]")
        assert len(tops) == expected_rows, (width, tops)
        assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")

        # Selection remains functional after removing the free-form emoji input.
        page.locator('.cs-icon-btn[data-icon="🎓"]').click()
        assert page.locator('.cs-icon-btn[data-icon="🎓"]').evaluate("el => el.classList.contains('picked')")
        assert page.evaluate("selectedCustomStatusSticker()") == "🎓"

        # Previously persisted arbitrary stickers remain readable.
        assert page.evaluate("""() => {
          S.settings.customStatuses ||= [];
          S.settings.customStatuses.push({id:'saved_custom_icon',label:'Saved',icon:'🪐',color:'#4A9EFF'});
          return getStatusDefinition('saved_custom_icon').icon;
        }""") == "🪐"

        page.screenshot(path=str(OUT / f"stickers-{width}.png"), full_page=True)
        assert not errors, (width, errors)
        page.close()
    browser.close()

server.shutdown()
source = (ROOT / "index.html").read_text()
assert "id=\"cs-icon-custom\"" not in source
assert "journal-pwa-v75.6" in (ROOT / "sw.js").read_text()
print("PASS: sticker presets use 4+4 on mini and one row from 390px")

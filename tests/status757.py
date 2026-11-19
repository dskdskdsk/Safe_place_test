"""75.7 custom-status limit, cleanup, identity and rename checks."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "artifacts" / "status757"
OUT.mkdir(parents=True, exist_ok=True)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}"

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url)
    page.wait_for_function("_writeReady")

    # Seven visually identical statuses are valid but receive distinct identities.
    for _ in range(7):
        page.locator("#cs-add-btn").click()
        page.locator("#cs-name").fill("test")
        page.locator("#cs-save").click()
        assert page.locator("#cs-form").evaluate("el => getComputedStyle(el).display") == "none"
        assert page.locator("#cs-name").input_value() == ""

    statuses = page.evaluate("S.settings.customStatuses")
    ids = [status["id"] for status in statuses]
    assert len(statuses) == 7
    assert len(set(ids)) == 7
    assert all(status_id.startswith("cs_") for status_id in ids)
    assert page.locator("#cs-add-btn").get_attribute("aria-disabled") == "true"

    # The eighth status is blocked at both UI and state level.
    page.locator("#cs-add-btn").click()
    page.wait_for_timeout(100)
    assert page.evaluate("S.settings.customStatuses.length") == 7
    assert page.locator("#cs-form").evaluate("el => getComputedStyle(el).display") == "none"

    # Custom statuses no longer expose the unrelated clarification input.
    first_id = ids[0]
    page.evaluate("id => {day().status=id;renderStatus();}", first_id)
    assert not page.locator("#status-note-wrap").evaluate("el => el.classList.contains('show')")

    # Double tap renames only the targeted ID; linked days keep the same identity.
    first_chip = page.locator(f'.cs-chip[data-status="{first_id}"]')
    first_chip.click()
    page.wait_for_timeout(100)
    first_chip.click()
    dialog = page.locator("dialog.edit-text-dialog")
    dialog.wait_for(state="visible")
    dialog.locator("input").fill("Навчання")
    dialog.locator("button.save").click()
    page.wait_for_timeout(100)
    assert page.evaluate("id => S.settings.customStatuses.find(s => s.id === id).label", first_id) == "Навчання"
    assert page.evaluate("day().status") == first_id
    assert page.evaluate("S.settings.customStatuses.filter(s => s.label === 'test').length") == 6
    assert page.locator(f'.cs-chip[data-status="{first_id}"]').text_content().find("Навчання") >= 0

    # Persisted state retains all IDs and the linked day reference.
    saved = page.evaluate("JSON.parse(localStorage.getItem(SK))")
    assert saved["days"][page.evaluate("TODAY")]["status"] == first_id
    assert len({status["id"] for status in saved["settings"]["customStatuses"]}) == 7

    page.screenshot(path=str(OUT / "seven-statuses-renamed.png"), full_page=True)
    assert not errors, errors
    page.close()
    browser.close()

server.shutdown()
source = (ROOT / "index.html").read_text()
assert "const CUSTOM_STATUS_LIMIT=7" in source
assert "const APP_VERSION='75.7'" in source
assert "journal-pwa-v75.7" in (ROOT / "sw.js").read_text()
print("PASS: seven-status cap, UUID identity, clean form and double-tap rename")

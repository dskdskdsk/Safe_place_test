# Browser checks

Requires Python, Node, Playwright Python (`pip install playwright`) and Chromium at `/usr/bin/chromium` (adjust executable_path for your environment).

From the repository root:

```sh
python tests/test_fixes.py
python tests/regression.py
python tests/mobile.py
```

Each suite serves this repository on a temporary loopback port and uses clean browser contexts with synthetic data. No live Gemini calls or user diary data. Fault injection is limited to the test context. These checks do not replace native iPhone keyboard, microphone, long-press and Files testing.

Results/screenshots go to `tests/artifacts/`. `regression.py` accepts case names to rerun individual cases. The old two-tab overwrite test is replaced by single-writer and legacy-conflict tests in `test_fixes.py`.

71.0 design checks: `python tests/design71.py` — both themes, eight viewport sizes, long synthetic content, root font reflow, overflow and touch action geometry. Screenshots and results: `tests/artifacts/design71/`. This is Chromium emulation, not physical iPhone testing.

71.1 theme checks: `python tests/clay711.py` — compares dark computed styles against git tag `v71.0`, checks final light entry/delete/voice states and text contrast. Requires repository history and the tag. Results: `tests/artifacts/clay711/`.

71.2: `python tests/type712.py` compares typography to `v70.5` and verifies status selection and press feedback in both themes. Requires the v70.5 git tag.

71.3: `python tests/controls713.py` supersedes the 71.2 outline expectation with opacity feedback and verifies calendar navigation/chrome while comparing typography to `v70.5`.

71.4: `python tests/rating714.py` checks responsive rating layout, persistent explanations, edit/delete/reload/limit and generates narrow-screen screenshots.

72.1 Stage A: `python tests/insight_a.py` — frozen deterministic readers, calendar profiles, metadata, midnight/timezones, JSON/ZIP and UI regression. Exits nonzero on failure. Results: `tests/artifacts/insight-a/`.

72.2 Stage B: `python tests/insight_b.py` — descriptive facts, calendar comparisons, baseline thresholds, 170 independent Python calendar/mean scenarios, timezones, UI/reload, responsive details and large history. Results/screenshots: `tests/artifacts/insight-b/`; exits nonzero on FAIL/pageErrors.
# Stage C

Run `python tests/insight_c.py` for deterministic evidence, threshold and context checks,
an independent seeded Python oracle, and three time zones. Results: artifacts/insight-c/results.json.

73.0 memories: `python tests/memories73.py` — frozen detached readers, exact calendar dates,
read-only storage invariants, actual IndexedDB audio/photos, draft/save/recording guards,
late/corrupt media, focus/Escape, UK/EN, themes and mobile layout. Synthetic touch events
check gesture filtering; physical Safari/PWA gestures still require the iPhone checklist
in QA-73.0.md. Results/screenshots: `tests/artifacts/memories73/`.

73.1 editing: `python tests/edit731.py` — inline edit/save/cancel for ideas, events, media
and recommendations; custom-emotion double tap and global reference rename; injected
storage failure rollback, reload persistence, matching one-row editors, voice composer
alignment, delete confirmation and calendar sticker sizing; UK/EN, both themes and 320–1024 px layouts.
Results/screenshots: `tests/artifacts/edit731/`.

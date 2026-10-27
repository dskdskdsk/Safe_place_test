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

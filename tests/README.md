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

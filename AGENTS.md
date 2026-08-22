# lingvisticka_analyza — Skinner Pipeline

Czech biblical text analysis tool (Quentin Skinner speech-act framework). Single Streamlit app (`app.py`) backed by a Python NLP pipeline (`stanza` Czech model) plus a pre-computed SQLite corpus (`output/bible_analysis.db`).

## Cursor Cloud specific instructions

Standard setup/usage lives in `README.md` and `setup.sh`. Notes below are the non-obvious things that matter when developing here.

### Services

Single service: the Streamlit web app.

- The Cloud Agent environment `start` command launches it automatically on http://localhost:8501 (binds `0.0.0.0:8501`, waits until `/_stcore/health` is OK, then returns). It is a no-op if the app is already healthy.
- If you need to start it by hand: `python3 -m streamlit run app.py --server.headless true --server.port 8501 --server.address 0.0.0.0`.
- Tabs: **Analyzovat text** (Tab 1) runs the live Stanza NLP pipeline on pasted/uploaded Czech text; **Biblický korpus** (Tab 2) reads the pre-computed `output/bible_analysis.db`; **Výsledky** shows the last Tab-1 run.

### Non-obvious caveats

- pip installs to the user site; the `streamlit` CLI lands in `~/.local/bin`, which is not on `PATH` by default. Use `~/.local/bin/streamlit ...` or add that dir to `PATH` for the session.
- torch/stanza compatibility: `requirements.txt` pins `stanza<1.8.0` and `torch<2.6`. Do not upgrade torch to 2.6+: that defaults `torch.load(weights_only=True)` and Stanza 1.7 Czech checkpoints fail with `UnpicklingError` (breaks Tab 1).
- Tab 1 requires the Stanza Czech model (`stanza.download("cs")`, ~228 MB into `~/stanza_resources`). It is downloaded during environment setup; the first pipeline call after a fresh start still takes a few seconds to load the model into memory.
- Do NOT run `python generate_demo_db.py` on the committed corpus unless you pass `--force`. Tab 2 ships a live full-BKR Stanza run packed as `output/bible_analysis.db.gz` (~38k sentences). `a_paths.ensure_bible_db()` unpacks it to `output/bible_analysis.db` (gitignored). Without `--force` the demo script exits instead of replacing live rows. If the unpacked DB is clobbered, delete `output/bible_analysis.db` and unpack again, or restore `output/bible_analysis.db.gz` from git.
- Regenerating `output/*.csv` via `generate_demo_db.py` produces large git diffs with *synthetic* values; do not commit those unless intentional. Refreshing CSVs from the live pipeline (`l_taxonomy_analytics.py` etc.) is OK when you mean to update Tab 2.

### Lint / test / build

- No linter is configured in the repo.
- Tests are plain `unittest` and do not require Stanza: `python -m unittest test_architecture test_religious_categorization test_ui_labels`.
- There is no build step (pure Python + Streamlit).

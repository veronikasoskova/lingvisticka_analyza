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
- torch/stanza compatibility: `requirements.txt` pins `stanza<1.8.0` but does not pin `torch`. A fresh `pip install -r requirements.txt` pulls a torch that defaults `torch.load(weights_only=True)`, which makes Stanza model loading crash with an `UnpicklingError` (breaks Tab 1). The update script pins `torch<2.6` after the requirements install to keep the Stanza Czech model loadable. If you re-install/upgrade torch, keep it `<2.6`.
- Tab 1 requires the Stanza Czech model (`stanza.download("cs")`, ~228 MB into `~/stanza_resources`). It is downloaded during environment setup; the first pipeline call after a fresh start still takes a few seconds to load the model into memory.
- Do NOT run `python generate_demo_db.py` on the committed DB. The committed `output/bible_analysis.db` stores the linguistic boolean columns (`has_coordination`, `dative_present`, `indirect_object_present`) as SQLite INTEGER, which Tab 2's `groupby(...).mean()` charts need. `generate_demo_db.py` (and the live pipeline via `n_db`) writes those values as TEXT (`"0"/"1"` or `"True"/"False"`); with `pandas>=2` such string columns make Tab 2 crash with `TypeError: ... does not support operation 'mean'`. The committed DB already works, so leave it as-is (the README/`setup.sh` step that regenerates it is unnecessary here and will break Tab 2). If `output/bible_analysis.db` ever gets clobbered, restore it with `git checkout -- output/bible_analysis.db`.
- Regenerating `output/*` (via `generate_demo_db.py`) produces large git diffs with *synthetic* values; do not commit those unless intentional.

### Lint / test / build

- No linter is configured in the repo.
- Tests are plain `unittest` and do not require Stanza: `python -m unittest test_architecture test_religious_categorization test_ui_labels`.
- There is no build step (pure Python + Streamlit).

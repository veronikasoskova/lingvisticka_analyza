# lingvisticka_analyza

**Skinner Pipeline** — Czech biblical text analysis tool.  
Analyses illocutionary force, speaker intention, and rhetorical strategy
using Quentin Skinner's speech-act framework.

---

## Quick start (clean environment)

```bash
# 1. Clone
git clone https://github.com/veronikasoskova/lingvisticka_analyza.git
cd lingvisticka_analyza

# 2. Bootstrap (installs deps; unpacks the live Bible DB)
bash setup.sh

# 3. Launch
streamlit run app.py
```

The app opens at **http://localhost:8501**.

---

## What `setup.sh` does

| Step | What happens |
|------|-------------|
| 1 | `pip install -r requirements.txt` — all runtime dependencies |
| 2 | `stanza.download("cs")` — Stanza Czech NLP model for Tab 1 |
| 3 | Unpacks `output/bible_analysis.db.gz` (full BKR Stanza run) so the **Biblický korpus** tab shows live results. Does **not** run `generate_demo_db.py` over that file. |
| 4 | Instructions to re-run the full Stanza pipeline if you want to refresh the corpus |

---

## Tabs

| Tab | Description | Prerequisites |
|-----|-------------|---------------|
| **📝 Analyzovat text** | Upload or paste Czech text; runs full NLP pipeline | Stanza Czech model (step 2) |
| **📚 Biblický korpus** | Pre-computed analysis of the full BKR Bible (Stanza, 66 books) | `output/bible_analysis.db` (unpacked in step 3) |
| **📊 Výsledky** | Results of the most recent text analysis | Requires running Tab 1 first |

---

## Regenerating the Bible corpus with real NLP

Tab 2 ships with a **live** Stanza analysis of all 66 BKR books
(`run_id` of the packed DB; ~38k sentences).  It is stored as
`output/bible_analysis.db.gz` and unpacked to `output/bible_analysis.db`
on first use.

Do **not** run `python generate_demo_db.py` on that file — the script now
exits unless you pass `--force`.  Without the guard it would replace real
labels with synthetic ones.

To refresh the live corpus:

```bash
# Requires Stanza Czech model (see step 2 of setup.sh)
PIPELINE_FILES_LIMIT=66 python k_apply_all_to_bible.py
python l_taxonomy_analytics.py
python o_verbal_relations_analytics.py
```

---

## Repository layout

```
app.py                    Streamlit application
k_apply_all_to_bible.py   Full Stanza-based Bible pipeline (batch)
generate_demo_db.py       Demo DB generator (no Stanza required)
setup.sh                  One-command bootstrap script
requirements.txt          Python dependencies
bible_BKR_*.txt           Bible text files (BKR edition, 66 books)
output/                   Generated artifacts. Tab 2 on a fresh clone unpacks
                          output/bible_analysis.db.gz (live full-BKR run) and
                          reads the tracked analytics CSVs.
  bible_analysis.db.gz    Packed SQLite (live Stanza corpus; unpacked at runtime)
  bible_analysis.db       Unpacked SQLite (gitignored; written by the pipeline)
  q_skinner_analytics/    Analytics CSVs — intentions / strategies
  style_authorship/       Style clustering
  opposition_networks/    Opposition pair analysis
  ...
a_paths.py                Canonical paths, DB location, bible_BKR_*.txt discovery
k_pipeline_core.py        Shared 4-stage pipeline (Bible batch + upload)
n_db.py                   Single SQLite read/write path
```

Demo data from `generate_demo_db.py` (optional, only if no packed live DB is
present) uses the same classifier vocabularies as the production pipeline.

The production path is Quentin Skinner illocutionary analysis
(`j_q_skinner_taxonomy` via `k_pipeline_core.process_unit`).  B.F. Skinner
verbal-behavior rules (`h_classifiers`) are kept for training-data generation
only (`k_apply_all_to_bible.make_training_data_from_bible`).

---

## Dependencies

See `requirements.txt`. Key packages:

- `streamlit` — web UI
- `stanza` — Czech NLP (tokenisation, lemmatisation, dependency parsing)
- `pandas`, `plotly` — data processing and charts
- `scikit-learn` — clustering and style analysis
- `reportlab`, `kaleido` — PDF export (charts as images)
- `wordcloud`, `pdfplumber` — word cloud and PDF upload support
- `python-louvain` — word-network community detection

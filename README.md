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

# 2. Bootstrap (installs deps + generates demo Bible DB)
bash setup.sh

# 3. Launch
streamlit run app.py --server.maxUploadSize 2048 --server.maxMessageSize 2048
```

The app opens at **http://localhost:8501**.

In **GitHub Codespaces**, browser upload can still fail with **HTTP 413 before the
request reaches Streamlit**, because the forwarded-port proxy applies its own
request-size limit. For large PDFs, copy the file into the Codespaces workspace
first and use the app's **workspace/server path** field instead of the browser
upload widget.

---

## What `setup.sh` does

| Step | What happens |
|------|-------------|
| 1 | `pip install -r requirements.txt` — all runtime dependencies |
| 2 | `stanza.download("cs")` — Stanza Czech NLP model for Tab 1 |
| 3 | `python generate_demo_db.py` — builds `output/bible_analysis.db` + analytics CSVs so that the **Biblický korpus** tab renders immediately |
| 4 | Instructions to run the full Stanza-based pipeline for real NLP results |

---

## Tabs

| Tab | Description | Prerequisites |
|-----|-------------|---------------|
| **📝 Analyzovat text** | Upload or paste Czech text; runs full NLP pipeline | Stanza Czech model (step 2) |
| **📚 Biblický korpus** | Pre-computed analysis of the full BKR Bible | `output/bible_analysis.db` (step 3) |
| **📊 Výsledky** | Results of the most recent text analysis | Requires running Tab 1 first |

---

## Regenerating the Bible corpus with real NLP

The demo database created by `generate_demo_db.py` contains the actual
Bible verses with **synthetic classification values** — sufficient to
verify the UI but not for real research.

To replace it with genuine Stanza-based analysis:

```bash
# Requires Stanza Czech model (see step 2 of setup.sh)
python k_apply_all_to_bible.py          # full Bible pipeline → output/bible_analysis.db
python l_taxonomy_analytics.py          # analytics CSVs
python o_verbal_relations_analytics.py  # verbal relations CSVs
```

By default `k_apply_all_to_bible.py` processes up to 10 books
(`PIPELINE_FILES_LIMIT=10`). To process all 66:

```bash
PIPELINE_FILES_LIMIT=66 python k_apply_all_to_bible.py
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
output/                   Generated artifacts (gitignored)
  bible_analysis.db       SQLite database (Bible corpus)
  q_skinner_analytics/    Analytics CSVs — intentions / strategies
  style_authorship/       Style clustering
  opposition_networks/    Opposition pair analysis
  ...
```

---

## Dependencies

See `requirements.txt`. Key packages:

- `streamlit` — web UI
- `stanza` — Czech NLP (tokenisation, lemmatisation, dependency parsing)
- `pandas`, `plotly` — data processing and charts
- `scikit-learn` — clustering and style analysis
- `reportlab` — PDF export
- `wordcloud`, `pdfplumber` — word cloud and PDF upload support

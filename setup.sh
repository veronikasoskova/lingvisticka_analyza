#!/usr/bin/env bash
# setup.sh — Bootstrap the Skinner Pipeline in a clean environment
# Usage: bash setup.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Skinner Pipeline Setup ==="
echo ""

# 1. Install Python dependencies
echo "[1/4] Installing Python dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt"

# 2. Download Stanza Czech model (required for text analysis in Tab 1)
echo ""
echo "[2/4] Downloading Stanza Czech NLP model (needed for Tab 1 — text analysis)..."
python3 - <<'EOF'
import stanza
try:
    stanza.download("cs")
    print("  Stanza Czech model ready.")
except Exception as e:
    print(f"  WARNING: Stanza download failed: {e}")
    print("  Tab 1 (text analysis) will not work without the model.")
    print("  Re-run: python3 -c \"import stanza; stanza.download('cs')\"")
EOF

# 3. Bible corpus for Tab 2 — unpack the tracked live DB; do NOT regenerate demo
#    over it (generate_demo_db.py would replace real Stanza rows with synthetic
#    labels and store boolean flags as TEXT, which breaks Tab 2 charts).
echo ""
echo "[3/4] Preparing Bible corpus database (Tab 2 — Biblický korpus)..."
cd "$SCRIPT_DIR"
if [[ -f "$SCRIPT_DIR/output/bible_analysis.db.gz" ]]; then
  echo "      Unpacking output/bible_analysis.db.gz (full BKR Stanza run)."
  python3 -c "from a_paths import ensure_bible_db; ensure_bible_db()"
else
  echo "      No packed live DB found; generating demo data."
  python3 generate_demo_db.py
fi

# 4. (Optional) Full pipeline re-run
echo ""
echo "[4/4] Optional: re-run the full Stanza-based pipeline to refresh NLP results."
echo "      Requires the Stanza Czech model from step 2."
echo ""
echo "      PIPELINE_FILES_LIMIT=66 python3 k_apply_all_to_bible.py"
echo "      python3 l_taxonomy_analytics.py"

echo ""
echo "=== Setup complete. Start the app with: ==="
echo "    streamlit run $SCRIPT_DIR/app.py"

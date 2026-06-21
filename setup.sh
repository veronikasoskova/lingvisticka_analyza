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

# 3. Generate the Bible corpus database and analytics CSVs
echo ""
echo "[3/4] Generating Bible corpus database (Tab 2 — Biblický korpus)..."
echo "      This runs generate_demo_db.py to populate output/bible_analysis.db"
echo "      and output/ analytics folders."
cd "$SCRIPT_DIR"
python3 generate_demo_db.py

# 4. (Optional) Full pipeline run
echo ""
echo "[4/4] Optional: re-run the full Stanza-based pipeline for real NLP results."
echo "      This replaces the demo data with actual linguistic analysis."
echo "      Requires the Stanza Czech model from step 2."
echo ""
echo "      python3 k_apply_all_to_bible.py        # full Bible pipeline"
echo "      python3 l_taxonomy_analytics.py        # regenerate analytics CSVs"

echo ""
echo "=== Setup complete. Start the app with: ==="
echo "    streamlit run $SCRIPT_DIR/app.py"

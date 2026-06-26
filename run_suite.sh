#!/usr/bin/env bash
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$HARNESS_DIR/.venv"
DATASET="$HARNESS_DIR/datasets/qa_kaggle.json"
MODEL="${HARNESS_MODEL:-phi3}"
LIMIT="${HARNESS_LIMIT:-5}"
DASHBOARD="${HARNESS_DASHBOARD:-dashboard.html}"
SKIP_TESTS="${HARNESS_SKIP_TESTS:-}"

cd "$HARNESS_DIR"

echo "============================================"
echo "  AI Evaluation Harness — Full Suite"
echo "============================================"
echo "  Dataset:  $DATASET"
echo "  Model:    $MODEL"
echo "  Limit:    $LIMIT"
echo "  Dashboard: $DASHBOARD"
echo "============================================"
echo ""

# ---- Activate virtual environment ----
if [ -d "$VENV_DIR" ]; then
    echo "[1/5] Activating virtual environment..."
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
else
    echo "[1/5] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    pip install -r requirements.txt
fi
echo "  Python: $(python --version)"
echo ""

# ---- Run tests ----
if [ -z "$SKIP_TESTS" ]; then
    echo "[2/5] Running test suite..."
    python -m pytest tests/ -v --tb=short
    echo ""
else
    echo "[2/5] Skipping tests (HARNESS_SKIP_TESTS is set)"
    echo ""
fi

# ---- Run evaluation ----
echo "[3/5] Running evaluation ($MODEL, limit=$LIMIT)..."
python -m harness.cli eval \
    --dataset "$DATASET" \
    --model "$MODEL" \
    --limit "$LIMIT"
echo ""

# ---- Monitor status ----
echo "[4/5] Checking evaluation status..."
python -m harness.cli monitor status
echo ""

# ---- Generate dashboard ----
echo "[5/5] Generating dashboard..."
python -m harness.cli monitor dashboard --output "$DASHBOARD"
echo ""

echo "============================================"
echo "  Suite complete!"
echo "  Dashboard: $DASHBOARD"
echo "  Open it with: start $DASHBOARD"
echo "============================================"

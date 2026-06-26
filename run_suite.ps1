param(
    [string]$Model = "phi3",
    [int]$Limit = 5,
    [string]$Dashboard = "dashboard.html",
    [switch]$SkipTests
)

$HarnessDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dataset = "$HarnessDir\datasets\qa_kaggle.json"
$VenvDir = "$HarnessDir\.venv"

Write-Host "============================================"
Write-Host "  AI Evaluation Harness — Full Suite"
Write-Host "============================================"
Write-Host "  Dataset:   $Dataset"
Write-Host "  Model:     $Model"
Write-Host "  Limit:     $Limit"
Write-Host "  Dashboard: $Dashboard"
Write-Host "============================================"
Write-Host ""

# ---- Activate virtual environment ----
if (Test-Path "$VenvDir\Scripts\Activate.ps1") {
    Write-Host "[1/5] Activating virtual environment..."
    . "$VenvDir\Scripts\Activate.ps1"
} else {
    Write-Host "[1/5] Virtual environment not found at $VenvDir"
    Write-Host "  Run: python -m venv .venv && pip install -r requirements.txt"
    exit 1
}
Write-Host "  Python: $(python --version)"
Write-Host ""

# ---- Run tests ----
if (-not $SkipTests) {
    Write-Host "[2/5] Running test suite..."
    python -m pytest tests\ -v --tb=short
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Tests failed! Aborting." -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "[2/5] Skipping tests (-SkipTests)"
    Write-Host ""
}

# ---- Run evaluation ----
Write-Host "[3/5] Running evaluation ($Model, limit=$Limit)..."
python -m harness.cli eval `
    --dataset $Dataset `
    --model $Model `
    --limit $Limit
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Evaluation failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# ---- Monitor status ----
Write-Host "[4/5] Checking evaluation status..."
python -m harness.cli monitor status
Write-Host ""

# ---- Generate dashboard ----
Write-Host "[5/5] Generating dashboard..."
python -m harness.cli monitor dashboard --output $Dashboard
Write-Host ""

Write-Host "============================================"
Write-Host "  Suite complete!"
Write-Host "  Dashboard: $Dashboard"
Write-Host "  Open: start $Dashboard"
Write-Host "============================================"

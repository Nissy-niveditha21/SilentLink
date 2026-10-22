# SilentLink — one-command alphabet training pipeline
# Usage: powershell -ExecutionPolicy Bypass -File scripts\train_alphabet.ps1
#
# Runs (1) landmark extraction, (2) alphabet MLP training, (3) evaluation.
# Uses the project venv at veenv\Scripts\python.exe if it exists, otherwise
# falls back to plain `python` on PATH. Prints colored banners and pauses
# at the end so the user can read the output before the window closes.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

$venvPy = Join-Path $root 'veenv\Scripts\python.exe'
if (Test-Path $venvPy) {
    $py = $venvPy
} else {
    $py = 'python'
}

$dataDir   = Join-Path $root 'data'
$modelsDir = Join-Path $root 'models'
New-Item -ItemType Directory -Force -Path $dataDir   | Out-Null
New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null

$alphabetImages = Join-Path $root 'data\asl_alphabet_train'
$landmarksNpz   = Join-Path $root 'data\asl_landmarks.npz'
$alphabetModel  = Join-Path $root 'models\alphabet_mlp.json'

function Banner($msg, $fg = 'Cyan') {
    $bar = '=' * 72
    Write-Host ""
    Write-Host $bar -ForegroundColor $fg
    Write-Host "  $msg" -ForegroundColor $fg
    Write-Host $bar -ForegroundColor $fg
    Write-Host ""
}

function PauseOnError($stage, $exitCode) {
    if ($exitCode -ne 0) {
        Write-Host ""
        Write-Host "!!! Stage '$stage' FAILED (exit=$exitCode). Scroll up for error details." -ForegroundColor Red
        Write-Host "Press any key to exit..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
        exit $exitCode
    }
}

Banner "SilentLink Alphabet Pipeline  |  python = $py" DarkGreen

# ---------------------------------------------------------------
# Stage 1: extract MediaPipe landmarks from raw alphabet images
# ---------------------------------------------------------------
Banner "STAGE 1/3  —  Extract landmarks  (data/asl_alphabet_train -> data/asl_landmarks.npz)" Cyan
if (-not (Test-Path $alphabetImages)) {
    Write-Host "Missing image dataset folder: $alphabetImages" -ForegroundColor Red
    Write-Host "See dataset/README.md for the expected layout and where to download a public ASL dataset." -ForegroundColor Yellow
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}
& $py (Join-Path $root 'training\extract_landmarks.py') `
    --data $alphabetImages `
    --out  $landmarksNpz `
    --samples 400 `
    --seed 42
PauseOnError 'extract_landmarks' $LASTEXITCODE

# ---------------------------------------------------------------
# Stage 2: train the alphabet MLP
# ---------------------------------------------------------------
Banner "STAGE 2/3  —  Train alphabet MLP  (data/asl_landmarks.npz -> models/alphabet_mlp.json)" Cyan
& $py (Join-Path $root 'training\train_alphabet.py') `
    --data $landmarksNpz `
    --out  $alphabetModel `
    --hidden 64,32 `
    --val 0.15 `
    --seed 42
PauseOnError 'train_alphabet' $LASTEXITCODE

# ---------------------------------------------------------------
# Stage 3: evaluate on the held-out split and write model card
# ---------------------------------------------------------------
Banner "STAGE 3/3  —  Evaluate alphabet MLP (writes metrics into the model card JSON)" Cyan
& $py (Join-Path $root 'training\evaluate_alphabet.py') `
    --model $alphabetModel `
    --data  $landmarksNpz `
    --val 0.15 `
    --seed 42
PauseOnError 'evaluate_alphabet' $LASTEXITCODE

Banner "ALL STAGES COMPLETE  —  Model saved to models\alphabet_mlp.json" DarkGreen
Write-Host "Press any key to close..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
exit 0

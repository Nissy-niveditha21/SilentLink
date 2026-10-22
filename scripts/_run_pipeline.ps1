# SilentLink — one-shot background task: extract landmarks, then train + evaluate.
# Written by the build script; run with:  powershell -ExecutionPolicy Bypass -File scripts\_run_pipeline.ps1
$ErrorActionPreference = 'Stop'
$root = $PWD.Path
$log  = Join-Path $root 'data\pipeline_log.txt'
Remove-Item $log -ErrorAction SilentlyContinue

function Log($m){ "$(Get-Date -Format 'HH:mm:ss')  $m" | Out-File $log -Append -Encoding utf8 }

# Stage 1: landmark extraction (long, ~4-5 min for 150/class x 29)
Log "STAGE1 extract: python training\extract_landmarks.py --data data\asl_alphabet_train --out data\asl_landmarks.npz --samples 150"
& (Join-Path $root 'veenv\Scripts\python.exe') (Join-Path $root 'training\extract_landmarks.py') `
    --data (Join-Path $root 'data\asl_alphabet_train') `
    --out  (Join-Path $root 'data\asl_landmarks.npz') `swx
    --samples 150 2>&1 | ForEach-Object { Log $_; Write-Host $_ }
Log "STAGE1 done (exit=$LASTEXITCODE)"

# Stage 2: train alphabet MLP
Log "STAGE2 train"
& (Join-Path $root 'veenv\Scripts\python.exe') (Join-Path $root 'training\train_alphabet.py') `
    --data (Join-Path $root 'data\asl_landmarks.npz') `
    --out  (Join-Path $root 'models\alphabet_mlp.json') 2>&1 | ForEach-Object { Log $_; Write-Host $_ }
Log "STAGE2 done (exit=$LASTEXITCODE)"

# Stage 3: evaluate on held-out split (writes metrics into the model card)
Log "STAGE3 evaluate"
& (Join-Path $root 'veenv\Scripts\python.exe') (Join-Path $root 'training\evaluate_alphabet.py') `
    --model (Join-Path $root 'models\alphabet_mlp.json') `
    --data  (Join-Path $root 'data\asl_landmarks.npz') 2>&1 | ForEach-Object { Log $_; Write-Host $_ }
Log "STAGE3 done (exit=$LASTEXITCODE)"
Log "ALL STAGES COMPLETE"

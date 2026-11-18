# Run from repo root: .\scripts\verify_paper.ps1
$ErrorActionPreference = "Stop"
$py = Join-Path $PSScriptRoot "..\backend\.venv\Scripts\python.exe"
& $py (Join-Path $PSScriptRoot "..\paper\scripts\personal_verify_paper.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py (Join-Path $PSScriptRoot "..\paper\scripts\audit_paper_claims.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Paper verification OK"

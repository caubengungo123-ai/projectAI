$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.\.venv\Scripts\python.exe')) {
    Write-Host 'Chua co moi truong Python. Lam theo HUONG_DAN.md truoc.'
    exit 1
}
$env:EW_ENABLE_RESEARCH_UPLOAD = '1'
& '.\.venv\Scripts\python.exe' -m streamlit run web_deploy/app.py --server.address 127.0.0.1

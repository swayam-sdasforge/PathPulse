# run.ps1
# Sets the Exasol environment variables and starts the Streamlit application

$env:EXA_DSN="127.0.0.1:8563"
$env:EXA_USER="sys"
$env:EXA_PASSWORD="oyXyriJ0ryAKkzBxQFHxurI9"

Write-Host "Environment variables set. Starting PathPulse..." -ForegroundColor Green
python -m streamlit run app.py

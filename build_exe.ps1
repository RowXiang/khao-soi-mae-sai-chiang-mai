$ErrorActionPreference = "Stop"
$python = "C:\Users\15657\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $python -m pip install pyinstaller
& $python -m PyInstaller --noconfirm --clean --onefile --windowed --name LocalOutreachStudio outreach_app.py
Write-Host "Built dist\LocalOutreachStudio.exe"

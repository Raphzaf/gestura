# Build Gestura.exe (and the installer if Inno Setup is installed).
# Run from the repository root in an activated virtual environment:
#   .\scripts\build_windows.ps1
$ErrorActionPreference = "Stop"
pip install pyinstaller==6.22.3
pyinstaller --noconfirm gestura.spec
Write-Host "Built dist\Gestura\Gestura.exe"
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (Test-Path $iscc) {
    & $iscc installer\gestura.iss
    Write-Host "Installer written to installer\Output\"
} else {
    Write-Host "Inno Setup not found; skipping installer (https://jrsoftware.org/isdl.php)"
}

param(
    [string]$Python = "python",
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    Write-Host "Installing build dependencies..."
    & $Python -m pip install --upgrade pyinstaller pillow

    Write-Host "Generating icon..."
    & $Python scripts\make_icon.py

    $mode = @()
    if ($OneFile) { $mode += "--onefile" }

    Write-Host "Building executable..."
    & $Python -m PyInstaller @mode `
        --noconfirm `
        --clean `
        --windowed `
        --name RyzenTempLimit `
        --icon ryzen_temp_limit\assets\icon.ico `
        --collect-data zenmaster `
        --collect-submodules zenmaster `
        --collect-data certifi `
        --collect-submodules pystray `
        --hidden-import pystray._win32 `
        --hidden-import six `
        --add-data "ryzen_temp_limit\assets;ryzen_temp_limit\assets" `
        run.py

    $target = if ($OneFile) { Join-Path $root "dist" } else { Join-Path $root "dist\RyzenTempLimit" }
    Copy-Item -LiteralPath (Join-Path $root "LICENSE") -Destination $target -Force
    Copy-Item -LiteralPath (Join-Path $root "THIRD_PARTY_NOTICES.md") -Destination $target -Force
    if (Test-Path (Join-Path $root "licenses")) {
        Copy-Item -Recurse -Force (Join-Path $root "licenses") $target
    }

    if ($OneFile) {
        Write-Host "Done: dist\RyzenTempLimit.exe (single file, slower start)"
    }
    else {
        Write-Host "Done: dist\RyzenTempLimit\RyzenTempLimit.exe (folder, fast start)"
    }
}
finally {
    Pop-Location
}

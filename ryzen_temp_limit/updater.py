from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import certifi

from . import __version__

API_LATEST = "https://api.github.com/repos/socrabs151/ryzen-temp-limit/releases/latest"
PAGE_URL = "https://github.com/socrabs151/ryzen-temp-limit/releases/latest"
ONEDIR_ASSET = "RyzenTempLimit-win64.zip"
ONEFILE_ASSET = "RyzenTempLimit-onefile.exe"
SUMS_ASSET = "sha256sums.txt"
USER_AGENT = f"RyzenTempLimit/{__version__}"


class UpdateError(RuntimeError):
    pass


class NoReleases(UpdateError):
    pass


@dataclass
class Release:
    version: str
    tag: str
    page_url: str
    notes: str = ""
    assets: dict[str, str] = field(default_factory=dict)


def parse_version(text: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", str(text))
    return tuple(int(number) for number in numbers[:4]) if numbers else (0,)


def is_newer(latest: str, current: str) -> bool:
    left = parse_version(latest)
    right = parse_version(current)
    size = max(len(left), len(right))
    left = left + (0,) * (size - len(left))
    right = right + (0,) * (size - len(right))
    return left > right


def _request(url: str, timeout: int = 15) -> urllib.request.Request:
    return urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    )


def ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def update_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    return Path(base) / "RyzenTempLimit" / "update"


def fetch_latest(timeout: int = 15) -> Release:
    try:
        with urllib.request.urlopen(
            _request(API_LATEST, timeout), timeout=timeout, context=ssl_context()
        ) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise NoReleases("No releases have been published yet") from exc
        raise UpdateError(f"Could not reach GitHub: {exc}") from exc
    except Exception as exc:
        raise UpdateError(f"Could not reach GitHub: {exc}") from exc
    tag = str(data.get("tag_name") or "").strip()
    version = tag.lstrip("vV")
    if not version:
        raise UpdateError("The latest release has no version tag")
    assets = {
        str(asset.get("name")): str(asset.get("browser_download_url"))
        for asset in data.get("assets", [])
        if asset.get("name") and asset.get("browser_download_url")
    }
    return Release(
        version=version,
        tag=tag,
        page_url=str(data.get("html_url") or PAGE_URL),
        notes=str(data.get("body") or ""),
        assets=assets,
    )


def frozen_mode() -> str | None:
    if not getattr(sys, "frozen", False):
        return None
    exe = Path(sys.executable).resolve()
    if (exe.parent / "_internal").is_dir():
        return "onedir"
    return "onefile"


def pick_asset(release: Release, mode: str) -> str:
    name = ONEDIR_ASSET if mode == "onedir" else ONEFILE_ASSET
    url = release.assets.get(name)
    if not url:
        raise UpdateError(f"Release {release.version} does not provide {name}")
    return url


def parse_sums(text: str) -> dict[str, str]:
    sums: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) == 2:
            sums[parts[1].lstrip("*")] = parts[0].lower()
    return sums


def download(
    url: str,
    destination: Path,
    expected_sha: str | None = None,
    progress=None,
    timeout: int = 60,
) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(
            _request(url, timeout), timeout=timeout, context=ssl_context()
        ) as response:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            with destination.open("wb") as stream:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    stream.write(chunk)
                    done += len(chunk)
                    if progress and total:
                        progress(min(1.0, done / total))
    except Exception as exc:
        raise UpdateError(f"Download failed: {exc}") from exc

    if expected_sha:
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        if digest.lower() != expected_sha.lower():
            destination.unlink(missing_ok=True)
            raise UpdateError("The downloaded file failed checksum verification")
    return destination


def _ps_quote(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


UPDATER_SCRIPT = """$ErrorActionPreference = 'Stop'
$log = {log_path}
function Write-Log([string]$message) { "$(Get-Date -Format s) $message" | Out-File -LiteralPath $log -Append -Encoding UTF8 }
try {
    Write-Log "waiting for process {pid}"
    $deadline = (Get-Date).AddSeconds(90)
    while ((Get-Process -Id {pid} -ErrorAction SilentlyContinue) -and ((Get-Date) -lt $deadline)) {
        Start-Sleep -Milliseconds 200
    }
    Start-Sleep -Milliseconds 800
    if ({single_file}) {
        Copy-Item -LiteralPath {new_exe} -Destination {exe_path} -Force
        Write-Log "replaced executable"
    } else {
        robocopy {source} {target} /E /NFL /NDL /NJH /NJS /R:3 /W:1 | Out-Null
        Write-Log "robocopy exit $LASTEXITCODE"
    }
    Start-Process -FilePath {exe_path}
    Write-Log "restarted"
} catch {
    Write-Log "FAILED: $($_.Exception.Message)"
}
"""


def _launch_updater(
    pid: int,
    mode: str,
    source: Path | None,
    target: Path,
    exe: Path,
    new_exe: Path | None,
    workdir: Path,
) -> Path:
    script = UPDATER_SCRIPT.format(
        pid=int(pid),
        log_path=_ps_quote(str(workdir / "update.log")),
        single_file="$true" if mode == "onefile" else "$false",
        new_exe=_ps_quote(str(new_exe)) if new_exe else _ps_quote(""),
        source=_ps_quote(str(source)) if source else _ps_quote(""),
        target=_ps_quote(str(target)),
        exe_path=_ps_quote(str(exe)),
    )
    script_path = workdir / "apply-update.ps1"
    script_path.write_text(script, encoding="utf-8")

    flags = 0
    if os.name == "nt":
        flags = 0x08000000 | 0x00000008
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-File",
            str(script_path),
        ],
        creationflags=flags,
        close_fds=True,
    )
    return script_path


def install(release: Release, progress=None) -> None:
    mode = frozen_mode()
    if mode is None:
        raise UpdateError(
            "Automatic updates are only available for packaged builds. "
            "Run from a Git checkout and pull the repository instead."
        )

    asset_url = pick_asset(release, mode)
    asset_name = ONEDIR_ASSET if mode == "onedir" else ONEFILE_ASSET
    sums_url = release.assets.get(SUMS_ASSET)
    if not sums_url:
        raise UpdateError("The release does not include checksums")

    workdir = update_root() / release.version
    shutil.rmtree(workdir, ignore_errors=True)
    workdir.mkdir(parents=True, exist_ok=True)
    sums_path = download(sums_url, workdir / SUMS_ASSET)
    expected = parse_sums(sums_path.read_text(encoding="utf-8", errors="replace")).get(asset_name)
    if not expected:
        raise UpdateError(f"No checksum published for {asset_name}")

    asset_path = download(asset_url, workdir / asset_name, expected_sha=expected, progress=progress)

    exe = Path(sys.executable).resolve()
    target = exe.parent

    if mode == "onedir":
        stage = workdir / "stage"
        stage.mkdir()
        with zipfile.ZipFile(asset_path) as archive:
            root = stage.resolve()
            for member in archive.infolist():
                destination = (stage / member.filename).resolve()
                if root not in destination.parents and destination != root:
                    raise UpdateError("The update archive contains an unsafe path")
            archive.extractall(stage)
        if not (stage / "RyzenTempLimit.exe").is_file():
            raise UpdateError("The update archive is missing RyzenTempLimit.exe")
        _launch_updater(os.getpid(), mode, stage, target, exe, None, workdir)
    else:
        _launch_updater(os.getpid(), mode, None, target, exe, asset_path, workdir)


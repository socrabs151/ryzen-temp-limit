from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

from . import TASK_NAME
from .settings import Settings

TASK_XML = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{description}</Description>
    <URI>\\{task}</URI>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT20S</Delay>
      <Repetition>
        <Interval>PT{interval}M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </BootTrigger>
    <CalendarTrigger>
      <StartBoundary>{start}</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
      <Repetition>
        <Interval>PT{interval}M</Interval>
        <Duration>P1D</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </CalendarTrigger>
    <EventTrigger>
      <Enabled>true</Enabled>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="System"&gt;&lt;Select Path="System"&gt;*[System[Provider[@Name='Microsoft-Windows-Kernel-Power'] and EventID=107]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
      <Delay>PT15S</Delay>
    </EventTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings><StopOnIdleEnd>false</StopOnIdleEnd><RestartOnIdle>false</RestartOnIdle></IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT2M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{command}</Command>
      <Arguments>{arguments}</Arguments>
      <WorkingDirectory>{workdir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""


def _flags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _runner() -> tuple[str, str, str]:
    if getattr(sys, "frozen", False):
        return sys.executable, "--apply-only", os.path.dirname(sys.executable)
    package_dir = Path(__file__).resolve().parent
    project_root = package_dir.parent
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        candidate = exe[:-len("python.exe")] + "pythonw.exe"
        if os.path.exists(candidate):
            exe = candidate
    return exe, "-m ryzen_temp_limit --apply-only", str(project_root)


def task_exists() -> bool:
    if os.name != "nt":
        return False
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME],
        capture_output=True,
        creationflags=_flags(),
    )
    return result.returncode == 0


def task_interval() -> int | None:
    if os.name != "nt":
        return None
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME, "/XML"],
        capture_output=True,
        creationflags=_flags(),
    )
    if result.returncode != 0:
        return None
    text = ""
    for encoding in ("utf-8", "cp866", "cp1251", "utf-16"):
        try:
            candidate = result.stdout.decode(encoding)
        except UnicodeDecodeError:
            continue
        if "<Task" in candidate:
            text = candidate
            break
    match = re.search(r"<Interval>PT(\d+)M</Interval>", text)
    return int(match.group(1)) if match else None


def install(settings: Settings) -> None:
    if os.name != "nt":
        raise OSError("Scheduled tasks are only supported on Windows")
    command, arguments, workdir = _runner()
    start = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")
    xml = TASK_XML.format(
        description=escape(f"Keep AMD CPU temperature at {settings.temp} °C (Ryzen Temp Limit)"),
        task=TASK_NAME,
        interval=max(1, int(settings.interval_min)),
        start=start,
        command=escape(command),
        arguments=escape(arguments),
        workdir=escape(workdir),
    )
    handle, path = tempfile.mkstemp(suffix=".xml", prefix="ryzen-temp-limit-")
    try:
        with os.fdopen(handle, "w", encoding="utf-16") as stream:
            stream.write(xml)
        result = subprocess.run(
            ["schtasks", "/Create", "/XML", path, "/TN", TASK_NAME, "/F"],
            capture_output=True,
            creationflags=_flags(),
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).decode(errors="ignore").strip()
            raise OSError(detail or "schtasks failed")
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def remove() -> None:
    if os.name != "nt":
        return
    subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True,
        creationflags=_flags(),
    )


def run_now() -> None:
    if os.name != "nt":
        return
    subprocess.run(
        ["schtasks", "/Run", "/TN", TASK_NAME],
        capture_output=True,
        creationflags=_flags(),
    )

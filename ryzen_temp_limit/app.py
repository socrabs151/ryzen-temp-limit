from __future__ import annotations

import argparse
import ctypes
import importlib.metadata
import os
import platform
import queue
import sys
import threading
import time
import tkinter as tk
import webbrowser
from dataclasses import replace
from datetime import datetime
from tkinter import messagebox, ttk

from . import APP_NAME, MAX_TEMP, MIN_TEMP, __version__, about, autostart, core, updater
from . import settings as settings_mod
from .elevation import is_admin, message_box, relaunch_as_admin
from .settings import Settings
from .single_instance import SingleInstance

PAWNIO_URL = "https://github.com/namazso/PawnIO.Setup/releases/latest"
INTERVALS = [1, 5, 10, 15, 30]
ERROR_COLOR = "#c42b1c"
TEXT_COLOR = "#1a1a1a"
HINT_COLOR = "#666666"
RESTORE_TEMP = 95

BODY = ("Segoe UI", 9)
SMALL = ("Segoe UI", 8)
TITLE = ("Segoe UI Semibold", 12)
BIG = ("Segoe UI Semibold", 26)
MONO = ("Consolas", 9)


def _asset(name: str):
    from pathlib import Path

    base = getattr(sys, "_MEIPASS", None)
    if base:
        path = Path(base) / "ryzen_temp_limit" / "assets" / name
    else:
        path = Path(__file__).resolve().parent / "assets" / name
    return path if path.exists() else None


def _enable_dpi_awareness() -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _run_apply_only() -> int:
    current = settings_mod.load()
    try:
        core.start_pawnio_service()
        message = core.apply_temp(current.temp)
        limit = core.read_limit()
        detail = f" (SMU reports {limit:.0f} °C)" if limit is not None else ""
        core.log.info("apply-only: %s%s", message, detail)
        return 0
    except Exception as exc:
        core.log.error("apply-only failed: %s", exc)
        return 1


class App(tk.Tk):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.live = core.Live()
        self._live_errors = 0
        self._syncing = False
        self.skipped_version = settings.skipped_version
        self.update_release: updater.Release | None = None
        self._checking = False
        self._updating = False
        self._events: queue.Queue = queue.Queue()

        self.title(APP_NAME)
        self.minsize(600, 640)
        icon = _asset("icon.ico")
        if icon:
            try:
                self.iconbitmap(str(icon))
            except tk.TclError:
                pass

        self.temp_var = tk.IntVar(value=settings.temp)
        self.scale_var = tk.DoubleVar(value=float(settings.temp))
        self.autostart_var = tk.BooleanVar(value=settings.autostart)
        self.interval_var = tk.StringVar(value=f"{settings.interval_min} min")
        self.model_var = tk.StringVar(value="Detecting processor…")
        self.driver_var = tk.StringVar(value="Checking PawnIO…")
        self.status_var = tk.StringVar(value="Starting…")
        self.current_var = tk.StringVar(value="—")
        self.limit_var = tk.StringVar(value="—")
        self.load_var = tk.StringVar(value="—")
        self.power_var = tk.StringVar(value="—")
        self.gfx_var = tk.StringVar(value="—")
        self.latest_var = tk.StringVar(value="Latest: —")

        self._setup_style()
        self._build()
        self._update_pause_state()
        self._fit_to_content()
        self.temp_var.trace_add("write", self._on_temp_changed)
        self.bind("<Return>", lambda _event: self._apply())
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(60, self._startup)
        self.after(100, self._drain_events)
        self.after(400, self._poll)
        self.after(2500, self._task_status_loop)
        self.after(1500, lambda: self._check_updates(manual=False))

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=TITLE)
        style.configure("Hint.TLabel", font=SMALL, foreground=HINT_COLOR)
        style.configure("Big.TLabel", font=BIG)

    def _fit_to_content(self) -> None:
        self.update_idletasks()
        width = max(660, self.winfo_reqwidth() + 24)
        height = max(640, self.winfo_reqheight() + 24)
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(width, screen_w - 80)
        height = min(height, screen_h - 120)
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2 - 24)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(min(600, width), min(560, height))

    def _build(self) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        head = ttk.Frame(outer)
        head.pack(fill="x")
        ttk.Label(head, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(head, textvariable=self.model_var, style="Hint.TLabel").pack(anchor="w", pady=(1, 0))

        self._build_temperature(outer)
        self._build_status(outer)
        self._build_background(outer)
        self._build_activity(outer)
        self._build_footer(outer)
        self._build_bottom_bar(outer)

    def _build_temperature(self, parent: tk.Misc) -> None:
        group = ttk.LabelFrame(parent, text="Temperature limit", padding=10)
        group.pack(fill="x", pady=(10, 0))

        top = ttk.Frame(group)
        top.pack(fill="x")
        ttk.Label(top, text="Current temperature:").pack(side="left")
        self.current_label = ttk.Label(top, textvariable=self.current_var, style="Big.TLabel")
        self.current_label.pack(side="left", padx=(8, 4))
        ttk.Label(top, text="°C").pack(side="left", pady=(10, 0))

        self.scale = ttk.Scale(
            group, from_=MIN_TEMP, to=MAX_TEMP, orient="horizontal",
            variable=self.scale_var, command=self._on_scale,
        )
        self.scale.pack(fill="x", pady=(8, 8))

        row = ttk.Frame(group)
        row.pack(fill="x")
        ttk.Label(row, text="Limit:").pack(side="left")
        self.spin = ttk.Spinbox(
            row, from_=MIN_TEMP, to=MAX_TEMP, increment=1,
            textvariable=self.temp_var, width=5, justify="center",
        )
        self.spin.pack(side="left", padx=(6, 4))
        ttk.Label(row, text="°C").pack(side="left")
        self.apply_button = ttk.Button(row, text="Apply", command=self._apply)
        self.apply_button.pack(side="left", padx=(14, 0))
        ttk.Button(row, text=f"Restore {RESTORE_TEMP} °C", command=self._restore).pack(
            side="left", padx=(8, 0)
        )

        ttk.Label(
            group, text="A lower limit reduces heat, but also sustained performance.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(8, 0))

    def _build_status(self, parent: tk.Misc) -> None:
        group = ttk.LabelFrame(parent, text="Status", padding=10)
        group.pack(fill="x", pady=(10, 0))
        group.columnconfigure(1, weight=1)
        group.columnconfigure(3, weight=1)

        cells = [
            ("CPU load:", self.load_var),
            ("Package power:", self.power_var),
            ("iGPU clock:", self.gfx_var),
        ]
        ttk.Label(group, text="Limit in SMU:").grid(row=0, column=0, sticky="w", pady=1)
        ttk.Label(group, textvariable=self.limit_var).grid(row=0, column=1, sticky="w", padx=(6, 20), pady=1)
        for index, (label, variable) in enumerate(cells):
            row, column = divmod(index + 1, 2)
            column *= 2
            ttk.Label(group, text=label).grid(row=row, column=column, sticky="w", pady=1)
            ttk.Label(group, textvariable=variable).grid(
                row=row, column=column + 1, sticky="w", padx=(6, 20), pady=1
            )

    def _build_background(self, parent: tk.Misc) -> None:
        group = ttk.LabelFrame(parent, text="Background", padding=10)
        group.pack(fill="x", pady=(10, 0))

        ttk.Checkbutton(
            group, text="Keep the limit applied automatically",
            variable=self.autostart_var, command=self._on_autostart,
        ).pack(anchor="w")

        row = ttk.Frame(group)
        row.pack(fill="x", pady=(7, 0))
        ttk.Label(row, text="Re-apply every:").pack(side="left")
        self.interval_box = ttk.Combobox(
            row, values=[f"{value} min" for value in INTERVALS],
            textvariable=self.interval_var, state="readonly", width=8,
        )
        self.interval_box.pack(side="left", padx=(6, 0))
        self.interval_box.bind("<<ComboboxSelected>>", lambda _event: self._on_interval())
        ttk.Button(row, text="Run now", command=self._run_now).pack(side="left", padx=(10, 0))
        self.pause_button = ttk.Button(row, text="Pause", command=self._pause)
        self.pause_button.pack(side="left", padx=(8, 0))

        status_row = ttk.Frame(group)
        status_row.pack(fill="x", pady=(6, 0))
        self.task_var = tk.StringVar(value="Task: checking…")
        ttk.Label(status_row, textvariable=self.task_var, style="Hint.TLabel").pack(side="left")
        self.repair_button = ttk.Button(status_row, text="Repair task", command=self._repair_task)
        self.repair_button.pack(side="right")

        ttk.Label(
            group,
            text=(
                "Firmware resets the limit after reboot or sleep, so the task re-applies it "
                "at startup, on resume and periodically."
            ),
            style="Hint.TLabel", wraplength=590, justify="left",
        ).pack(anchor="w", pady=(8, 0))

    def _build_activity(self, parent: tk.Misc) -> None:
        group = ttk.LabelFrame(parent, text="Activity", padding=(10, 8))
        group.pack(fill="both", expand=True, pady=(10, 0))
        group.columnconfigure(0, weight=1)
        group.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            group, height=6, wrap="word", font=MONO, state="disabled",
            relief="solid", borderwidth=1, highlightthickness=0,
            padx=6, pady=4, background="#ffffff", foreground="#333333",
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(group, orient="vertical", command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.tag_configure("ok", foreground=TEXT_COLOR)
        self.log_text.tag_configure("err", foreground=ERROR_COLOR)
        self.log_text.tag_configure("muted", foreground=HINT_COLOR)

    def _build_footer(self, parent: tk.Misc) -> None:
        footer = ttk.Frame(parent)
        footer.pack(fill="x", pady=(8, 0))

        self.driver_label = ttk.Label(footer, textvariable=self.driver_var, style="Hint.TLabel")
        self.driver_label.pack(side="left")
        self.pawnio_button = ttk.Button(footer, text="Install PawnIO…", command=lambda: webbrowser.open(PAWNIO_URL))
        ttk.Button(footer, text="Open log", command=self._open_log).pack(side="left", padx=(10, 0))

        self.status_label = ttk.Label(footer, textvariable=self.status_var, style="Hint.TLabel")
        self.status_label.pack(side="right")

    def _build_bottom_bar(self, parent: tk.Misc) -> None:
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(8, 0))
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(6, 0))

        ttk.Label(bar, text=f"Version {__version__}", style="Hint.TLabel").pack(side="left")
        self.update_button = ttk.Button(bar, text="Check for updates", command=self._on_update_button)
        self.update_button.pack(side="left", padx=(10, 0))
        ttk.Label(bar, textvariable=self.latest_var, style="Hint.TLabel").pack(side="left", padx=(10, 0))
        ttk.Label(bar, text="GPL-3.0", style="Hint.TLabel").pack(side="right")
        ttk.Button(bar, text="About", command=lambda: about.show_about(self, self)).pack(
            side="right", padx=(0, 10)
        )

    def _startup(self) -> None:
        if autostart.task_exists():
            self.autostart_var.set(True)
            interval = autostart.task_interval()
            if interval in INTERVALS:
                self.interval_var.set(f"{interval} min")
        else:
            self.autostart_var.set(False)
        self._update_pause_state()

        try:
            info = core.cpu()
        except Exception as exc:
            self._log(f"Processor detection failed: {exc}", "err")
            self.model_var.set("Unsupported or unknown processor")
            self._set_driver(None)
            self._status("Cannot read processor info", error=True)
            return

        self.model_var.set(f"{info.name} · {info.family}")

        version = core.pawnio_version()
        self._set_driver(version)
        if version is None:
            self._log("PawnIO is not installed. Use the Install PawnIO button below.", "err")
            self._status("PawnIO driver is missing", error=True)
            return
        if not info.supported:
            self._log(f"{info.family} is not supported by zenmaster", "err")
            self._status("Unsupported processor family", error=True)
            return

        self._apply(initial=True)

    def _set_driver(self, version: str | None) -> None:
        if version:
            self.driver_var.set(f"PawnIO {version}")
            self.pawnio_button.pack_forget()
        else:
            self.driver_var.set("PawnIO not installed")
            self.pawnio_button.pack(side="left", padx=(8, 0), before=self.driver_label)

    def _on_scale(self, value: str) -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            self.temp_var.set(round(float(value)))
        finally:
            self._syncing = False

    def _on_temp_changed(self, *_args) -> None:
        if self._syncing:
            return
        try:
            value = int(self.temp_var.get())
        except (tk.TclError, ValueError):
            return
        self._syncing = True
        try:
            self.scale_var.set(float(value))
        finally:
            self._syncing = False

    def _target(self) -> int:
        try:
            value = int(self.temp_var.get())
        except (tk.TclError, ValueError):
            return self.settings.temp
        return max(MIN_TEMP, min(MAX_TEMP, value))

    def _poll(self) -> None:
        try:
            self.live = core.read_live()
            self._live_errors = 0
            self._render_live()
        except Exception as exc:
            self._live_errors += 1
            if self._live_errors == 1:
                self._log(f"Telemetry unavailable: {exc}", "err")
                self._status("Waiting for hardware access", error=True)
        finally:
            self.after(2000, self._poll)

    def _render_live(self) -> None:
        live = self.live
        if live.tctl is None:
            self.current_var.set("—")
            self.current_label.configure(foreground=TEXT_COLOR)
        else:
            self.current_var.set(f"{live.tctl:.1f}")
            hot = live.tctl >= self._target() - 2
            self.current_label.configure(foreground=ERROR_COLOR if hot else TEXT_COLOR)

        self.limit_var.set("—" if live.limit is None else f"{live.limit:.0f} °C")
        self.load_var.set("—" if live.load is None else f"{live.load:.0f} %")
        self.power_var.set("—" if live.socket_power is None else f"{live.socket_power:.0f} W")
        self.gfx_var.set("—" if live.gfx_clk is None else f"{live.gfx_clk:.0f} MHz")

    def _apply(self, initial: bool = False) -> None:
        try:
            value = int(self.temp_var.get())
        except (tk.TclError, ValueError):
            self._status(f"Enter a number between {MIN_TEMP} and {MAX_TEMP}", error=True)
            return
        temp = max(MIN_TEMP, min(MAX_TEMP, value))
        self.temp_var.set(temp)
        self.settings = self._collect()
        settings_mod.save(self.settings)
        try:
            message = core.apply_temp(temp)
            limit = core.read_limit()
            suffix = f" (SMU reports {limit:.0f} °C)" if limit is not None else ""
            core.log.info("applied %s%s", message, suffix)
            self._log(f"{message}{suffix}", "ok")
            self._status(f"Applied at {time.strftime('%H:%M:%S')}")
            if self.autostart_var.get():
                self._install_task(silent=True)
        except Exception as exc:
            core.log.error("apply failed: %s", exc)
            self._log(f"Apply failed: {exc}", "err")
            self._status(str(exc), error=True)
        self._render_live()

    def _on_autostart(self) -> None:
        if self.autostart_var.get():
            self._install_task()
        else:
            autostart.remove()
            core.log.info("background task removed")
            self._log("Background task removed", "muted")
            self._status("Background task removed")
        self._update_pause_state()
        self._save()
        self._refresh_task_status()

    def _on_interval(self) -> None:
        if self.autostart_var.get():
            self._install_task(silent=True)
        self._save()

    def _install_task(self, silent: bool = False) -> None:
        current = self._collect()
        try:
            autostart.install(current)
            core.log.info("task installed: temp=%s interval=%s", current.temp, current.interval_min)
            self._log(f"Background task installed (every {current.interval_min} min)", "ok")
            self._status("Background task active")
        except Exception as exc:
            core.log.error("task install failed: %s", exc)
            self._log(f"Background task failed: {exc}", "err")
            self._status(f"Background task failed: {exc}", error=True)
            if not silent:
                self.autostart_var.set(False)
        self._update_pause_state()
        self._save()
        self._refresh_task_status()

    def _run_now(self) -> None:
        if not autostart.task_exists():
            self._log("No background task yet — enable “Keep the limit applied” first", "muted")
            return
        autostart.run_now()
        self._log("Background task started manually", "muted")

    def _restore(self) -> None:
        self.temp_var.set(RESTORE_TEMP)
        self._apply()

    def _pause(self) -> None:
        if not self.autostart_var.get():
            return
        self.autostart_var.set(False)
        autostart.remove()
        core.log.info("automatic re-apply paused")
        self._log("Automatic re-apply paused; the firmware resets the limit on reboot", "muted")
        self._status("Automatic re-apply paused")
        self._save()
        self._update_pause_state()
        self._refresh_task_status()

    def _update_pause_state(self) -> None:
        self.pause_button.configure(state="normal" if self.autostart_var.get() else "disabled")

    def _task_status_loop(self) -> None:
        self._refresh_task_status()
        self.after(300_000, self._task_status_loop)

    def _refresh_task_status(self) -> None:
        threading.Thread(target=self._task_status_worker, daemon=True).start()

    def _task_status_worker(self) -> None:
        try:
            info = autostart.task_info()
        except Exception:
            info = autostart.TaskInfo(False)
        self._post(self._on_task_status, info)

    def _on_task_status(self, info: autostart.TaskInfo) -> None:
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        if not info.installed:
            self.task_var.set("Task: not installed")
            self.repair_button.configure(state="disabled")
            return
        parts = [f"Task: {(info.state or 'ready').lower()}"]
        if info.last_run:
            parts.append(f"last {self._short_time(info.last_run)}")
        if info.last_result is not None:
            parts.append(f"result {info.last_result}")
        if info.next_run:
            parts.append(f"next {self._short_time(info.next_run)}")
        self.task_var.set(" · ".join(parts))
        self.repair_button.configure(state="normal" if self.autostart_var.get() else "disabled")

    @staticmethod
    def _short_time(value: str) -> str:
        try:
            moment = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return value
        if moment.date() == datetime.now().date():
            return moment.strftime("%H:%M:%S")
        return moment.strftime("%d.%m %H:%M")

    def _repair_task(self) -> None:
        self._install_task()

    def _interval(self) -> int:
        try:
            value = int(str(self.interval_var.get()).split()[0])
        except (ValueError, IndexError):
            value = self.settings.interval_min
        return max(1, min(120, value))

    def _collect(self) -> Settings:
        return Settings(
            temp=self._target(),
            interval_min=self._interval(),
            autostart=bool(self.autostart_var.get()),
            skipped_version=self.skipped_version,
        ).normalized()

    def _save(self) -> None:
        self.settings = self._collect()
        try:
            settings_mod.save(self.settings)
        except OSError as exc:
            self._log(f"Could not save settings: {exc}", "err")

    def _open_log(self) -> None:
        try:
            os.startfile(core.log_path())  # type: ignore[attr-defined]
        except Exception:
            pass

    def _zenmaster_version(self) -> str:
        try:
            return importlib.metadata.version("zenmaster")
        except importlib.metadata.PackageNotFoundError:
            return "not installed"

    def _diagnostics_text(self) -> str:
        lines = [
            f"{APP_NAME} {__version__}",
            f"CPU: {self.model_var.get()}",
            f"PawnIO: {self.driver_var.get()}",
            f"zenmaster: {self._zenmaster_version()}",
            f"Python: {platform.python_version()}",
            f"Tk: {self.tk.call('info', 'patchlevel')}",
            f"settings: {self._collect()}",
            f"task: {autostart.task_info()}",
            f"task interval: {autostart.task_interval()}",
            "",
            "log:",
        ]
        try:
            tail = core.log_path()
            with open(tail, encoding="utf-8", errors="replace") as stream:
                lines.extend(stream.readlines()[-40:])
        except OSError as exc:
            lines.append(f"could not read the log: {exc}")
        return "\n".join(line.rstrip("\n") for line in lines)

    def _copy_diagnostics(self) -> bool:
        try:
            self.clipboard_clear()
            self.clipboard_append(self._diagnostics_text())
            self._status("Diagnostics copied to the clipboard")
            self._log("Diagnostics copied to the clipboard", "muted")
            return True
        except tk.TclError as exc:
            self._log(f"Could not copy diagnostics: {exc}", "err")
            return False

    def _status(self, text: str, error: bool = False) -> None:
        self.status_var.set(text)
        self.status_label.configure(foreground=ERROR_COLOR if error else HINT_COLOR)

    def _log(self, text: str, level: str = "info") -> None:
        tag = {"ok": "ok", "err": "err", "muted": "muted"}.get(level, "muted")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{time.strftime('%H:%M:%S')}  {text}\n", tag)
        lines = int(self.log_text.index("end-1c").split(".")[0])
        if lines > 250:
            self.log_text.delete("1.0", "60.0")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _post(self, callback, *args) -> None:
        self._events.put((callback, args))

    def _drain_events(self) -> None:
        try:
            while True:
                callback, args = self._events.get_nowait()
                try:
                    callback(*args)
                except Exception:
                    core.log.exception("update callback failed")
        except queue.Empty:
            pass
        try:
            self.after(100, self._drain_events)
        except tk.TclError:
            pass

    def _check_updates(self, manual: bool = False) -> None:
        if self._updating or self._checking:
            if manual:
                self._status("Already checking for updates")
            return
        self._checking = True
        if manual:
            self._status("Checking for updates…")
        threading.Thread(target=self._check_worker, args=(manual,), daemon=True).start()

    def _check_worker(self, manual: bool) -> None:
        try:
            release = updater.fetch_latest()
        except updater.NoReleases:
            self._post(self._on_no_releases, manual)
            return
        except Exception as exc:
            core.log.info("update check failed: %s", exc)
            self._post(self._on_check_failed, str(exc), manual)
            return
        self._post(self._on_check_done, release, manual)

    def _on_no_releases(self, manual: bool) -> None:
        self._checking = False
        self.latest_var.set("Latest: —")
        if manual:
            messagebox.showinfo(APP_NAME, "No releases have been published yet.")

    def _on_check_done(self, release: updater.Release, manual: bool) -> None:
        self._checking = False
        self.latest_var.set(f"Latest: {release.version}")
        if updater.is_newer(release.version, __version__):
            self.update_release = release
            self.update_button.configure(text=f"Update to {release.version}")
            if manual or release.version != self.skipped_version:
                self._prompt_update(release, manual=manual)
        elif manual:
            messagebox.showinfo(APP_NAME, f"You are running the latest version ({__version__}).")

    def _on_check_failed(self, message: str, manual: bool) -> None:
        self._checking = False
        self.latest_var.set("Latest: —")
        self._log(f"Update check failed: {message}", "muted")
        if manual:
            messagebox.showerror(APP_NAME, f"Could not check for updates:\n{message}")

    def _on_update_button(self) -> None:
        release = self.update_release
        if release and updater.is_newer(release.version, __version__):
            self._prompt_update(release, manual=True)
        else:
            self._check_updates(manual=True)

    def _prompt_update(self, release: updater.Release, manual: bool) -> None:
        if updater.frozen_mode() is None:
            question = (
                f"Version {release.version} is available (you have {__version__}).\n\n"
                "This is a source checkout, so open the release page instead?"
            )
            if messagebox.askyesno(APP_NAME, question):
                webbrowser.open(release.page_url)
            return

        question = (
            f"Version {release.version} is available (you have {__version__}).\n\n"
            "Download and install it now? The application will restart."
        )
        if messagebox.askyesno(APP_NAME, question):
            self._start_update(release)
        elif not manual:
            self._remember_skipped(release.version)

    def _remember_skipped(self, version: str) -> None:
        self.skipped_version = version
        self.settings = replace(self._collect(), skipped_version=version)
        try:
            settings_mod.save(self.settings)
        except OSError:
            pass

    def _start_update(self, release: updater.Release) -> None:
        if self._updating:
            return
        self._updating = True
        self.update_button.configure(state="disabled")
        self._status("Downloading update…")
        self._log(f"Downloading update {release.version}…", "muted")
        threading.Thread(target=self._update_worker, args=(release,), daemon=True).start()

    def _update_worker(self, release: updater.Release) -> None:
        try:
            updater.install(release, progress=lambda fraction: self._post(self._on_progress, fraction))
        except Exception as exc:
            core.log.error("update failed: %s", exc)
            self._post(self._on_update_failed, str(exc))
            return
        self._post(self._on_update_ready)

    def _on_progress(self, fraction: float) -> None:
        self._status(f"Downloading update… {fraction * 100:.0f}%")

    def _on_update_ready(self) -> None:
        self._status("Restarting to finish the update…")
        self._log("Update downloaded. Restarting…", "ok")
        self.after(500, self.destroy)

    def _on_update_failed(self, message: str) -> None:
        self._updating = False
        self.update_button.configure(state="normal")
        self._log(f"Update failed: {message}", "err")
        self._status("Update failed", error=True)
        messagebox.showerror(APP_NAME, f"Update failed:\n{message}")

    def _on_close(self) -> None:
        self._save()
        self.destroy()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ryzen-temp-limit", description=APP_NAME)
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument("--apply-only", action="store_true", help="apply the saved limit and exit")
    parser.add_argument("--elevated", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0
    if os.name != "nt":
        message_box(APP_NAME, "This application requires Windows.", error=True)
        return 1
    if args.apply_only:
        return _run_apply_only()

    _enable_dpi_awareness()

    if not is_admin():
        if args.elevated:
            message_box(APP_NAME, "Administrator rights are required.", error=True)
            return 1
        if relaunch_as_admin(["--elevated"]):
            return 0
        message_box(APP_NAME, "Administrator rights are required to change CPU limits.", error=True)
        return 1

    guard = SingleInstance()
    if guard.already_running:
        message_box(APP_NAME, "Ryzen Temp Limit is already running.")
        return 0

    current = settings_mod.load()
    app = App(current)
    app.mainloop()
    guard.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

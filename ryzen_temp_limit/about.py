from __future__ import annotations

import importlib.metadata
import platform
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

from . import APP_NAME, __version__, core

REPO_URL = "https://github.com/socrabs151/ryzen-temp-limit"
RELEASES_URL = "https://github.com/socrabs151/ryzen-temp-limit/releases/latest"
LICENSE_URL = "https://github.com/socrabs151/ryzen-temp-limit/blob/main/LICENSE"
PAWNIO_URL = "https://github.com/namazso/PawnIO.Setup/releases/latest"


def _version(name: str, fallback: str = "not installed") -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return fallback


def _link(parent: tk.Misc, text: str, url: str, row: int, column: int) -> None:
    label = ttk.Label(
        parent, text=text, foreground="#0067c0", cursor="hand2",
        font=("Segoe UI", 9, "underline"),
    )
    label.grid(row=row, column=column, sticky="w", padx=(0, 14), pady=1)
    label.bind("<Button-1>", lambda _event: webbrowser.open(url))


def show_about(parent: tk.Tk, app) -> None:
    window = tk.Toplevel(parent)
    window.title(f"About {APP_NAME}")
    window.transient(parent)
    window.resizable(False, False)
    window.grab_set()
    window.bind("<Escape>", lambda _event: window.destroy())

    frame = ttk.Frame(window, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=APP_NAME, style="Title.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(frame, text=f"Version {__version__}").grid(row=1, column=0, sticky="w", pady=(0, 2))
    ttk.Label(frame, text=app.model_var.get(), style="Hint.TLabel").grid(row=2, column=0, sticky="w")

    ttk.Separator(frame).grid(row=3, column=0, sticky="ew", pady=(12, 10))

    rows = [
        ("PawnIO driver", core.pawnio_version() or "not installed"),
        ("zenmaster", _version("zenmaster")),
        ("Python", platform.python_version()),
        ("Tk", str(parent.tk.call("info", "patchlevel"))),
        ("License", "GNU GPL v3.0"),
    ]
    for index, (label, value) in enumerate(rows, start=4):
        ttk.Label(frame, text=f"{label}:").grid(row=index, column=0, sticky="w", padx=(0, 16))
        ttk.Label(frame, text=value).grid(row=index, column=1, sticky="w")

    skipped_row = ttk.Frame(frame)
    skipped_row.grid(row=9, column=0, columnspan=2, sticky="w", pady=(8, 0))
    ttk.Label(skipped_row, text="Skipped update:").pack(side="left")
    skipped_var = tk.StringVar(value=app.skipped_version or "none")
    ttk.Label(skipped_row, textvariable=skipped_var).pack(side="left", padx=(8, 0))

    def clear_skipped() -> None:
        app._clear_skipped_version()
        skipped_var.set("none")

    ttk.Button(skipped_row, text="Clear", command=clear_skipped).pack(side="left", padx=(8, 0))

    ttk.Separator(frame).grid(row=11, column=0, columnspan=2, sticky="ew", pady=(12, 8))

    links = ttk.Frame(frame)
    links.grid(row=12, column=0, columnspan=2, sticky="w")
    _link(links, "GitHub", REPO_URL, 0, 0)
    _link(links, "Releases", RELEASES_URL, 0, 1)
    _link(links, "PawnIO", PAWNIO_URL, 0, 2)
    _link(links, "License", LICENSE_URL, 0, 3)

    ttk.Label(
        frame,
        text="Bundles zenmaster (GPL-3.0). PawnIO is a separate signed driver.",
        style="Hint.TLabel",
        wraplength=420,
        justify="left",
    ).grid(row=13, column=0, columnspan=2, sticky="w", pady=(10, 0))

    buttons = ttk.Frame(frame)
    buttons.grid(row=14, column=0, columnspan=2, sticky="ew", pady=(16, 0))
    ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")
    ttk.Button(
        buttons,
        text="Copy diagnostics",
        command=lambda: _copy(app),
    ).pack(side="right", padx=(0, 8))
    ttk.Button(buttons, text="Open data folder", command=app._open_data_folder).pack(side="left")
    ttk.Button(
        buttons,
        text="Reset settings",
        command=lambda: _reset(window, app),
    ).pack(side="left", padx=(8, 0))

    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    window.geometry(f"+{max(0, x)}+{max(0, y)}")


def _reset(window, app) -> None:
    if messagebox.askyesno(
        "Reset settings",
        "Reset temperature, interval, skipped update and the captured limit?",
        parent=window,
    ):
        app._reset_settings()


def _copy(app) -> None:
    if app._copy_diagnostics():
        messagebox.showinfo(APP_NAME, "Diagnostics copied to the clipboard.", parent=app)



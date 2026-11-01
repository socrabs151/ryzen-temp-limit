from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import ttk

from . import __version__, updater


def show(parent: tk.Tk, app, release: updater.Release) -> None:
    window = tk.Toplevel(parent)
    window.title("Update available")
    window.transient(parent)
    window.resizable(True, True)
    window.grab_set()
    window.bind("<Escape>", lambda _event: window.destroy())

    frame = ttk.Frame(window, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=f"Ryzen Temp Limit {release.version}", style="Title.TLabel").grid(
        row=0, column=0, sticky="w"
    )
    ttk.Label(frame, text=f"You have {__version__}.").grid(row=1, column=0, sticky="w", pady=(2, 10))
    ttk.Label(frame, text="What's new:").grid(row=2, column=0, sticky="w")

    notes = tk.Text(
        frame, height=10, width=64, wrap="word", font=("Consolas", 9),
        relief="solid", borderwidth=1, background="#ffffff", foreground="#222222",
        padx=6, pady=4,
    )
    notes.insert("1.0", release.notes.strip() or "No release notes were published.")
    notes.configure(state="disabled")
    notes.grid(row=3, column=0, sticky="nsew", pady=(4, 12))
    frame.rowconfigure(3, weight=1)

    buttons = ttk.Frame(frame)
    buttons.grid(row=4, column=0, sticky="ew")

    def accept() -> None:
        window.destroy()
        if updater.frozen_mode() is not None:
            app._start_update(release)
        else:
            webbrowser.open(release.page_url)

    def skip() -> None:
        window.destroy()
        app._remember_skipped(release.version)

    if updater.frozen_mode() is not None:
        ttk.Button(buttons, text=f"Install {release.version}", command=accept).pack(side="right")
    else:
        ttk.Button(buttons, text="Open release page", command=accept).pack(side="right")
    ttk.Button(buttons, text="Later", command=window.destroy).pack(side="right", padx=(0, 8))
    ttk.Button(buttons, text="Skip this version", command=skip).pack(side="left")

    window.update_idletasks()
    width = max(560, window.winfo_width())
    height = window.winfo_height()
    x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    window.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")


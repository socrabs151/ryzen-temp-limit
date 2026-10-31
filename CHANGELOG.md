# Changelog

## 0.3.4

- Executable metadata (product, version, company, copyright) for both builds.
- Update dialog with release notes, a download progress bar and a
  "skip this version" action; skipped versions can be cleared in About.
- A second launch now brings the existing window to the front.
- Reset settings, a confirmation for limits below 60 °C, an "Open data folder"
  action and keyboard shortcuts (Enter applies, Ctrl+Q quits).
- CI: mypy type checking, release notes generated from the changelog, SBOM,
  build provenance attestations and pip caching.

## 0.3.3

- Fixed the self-updater failing with a `KeyError` while rendering the
  PowerShell helper (literal braces were treated as format fields).
- Fixed the updater process not starting: `DETACHED_PROCESS` was removed and
  only `CREATE_NO_WINDOW` is used.
- Verified the updater end-to-end (wait, robocopy, restart).

## 0.3.2

- Notification-area icon with quick actions (show, apply, restore, pause,
  check for updates, exit).
- "Close window to tray" option.
- pystray and Pillow are now runtime dependencies; license texts are shipped
  in `licenses/`.

## 0.3.1

- Temperature history graph for the last 60 seconds.
- Restore now applies the SMU limit captured before the app first managed it,
  with a visible 95 °C fallback when no original value was recorded.

## 0.3.0

- Settings moved to `%LOCALAPPDATA%\RyzenTempLimit` and migrated from the old
  `%ProgramData%` location automatically.
- Single-instance guard for the GUI.
- About dialog with PawnIO/zenmaster/Python/Tk versions, license links and
  copy-diagnostics.
- Restore 95 °C action.
- Pause action that removes the background task until it is enabled again.
- Scheduled task status (last run, result, next run) and a repair button.
- CI now runs `ruff` and the expanded unit tests.

## 0.2.1

- The background task runs as the current user (`InteractiveToken`, highest
  privileges) instead of `SYSTEM`.
- Update files are staged in `%LOCALAPPDATA%` instead of `%TEMP%` to avoid
  persistence heuristics.

## 0.2.0

- Self-update through GitHub Releases with SHA-256 verification and restart.
- Bottom bar with installed/latest versions and an update button.
- Automatic update check on start; source checkouts open the release page.
- Standard Windows (ttk) interface.
- First published release pipeline (onedir zip, onefile exe, checksums).

## 0.1.0

- Initial release: temperature ceiling, live status, background task,
  PawnIO/zenmaster backend, gauge icon.

# Changelog

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

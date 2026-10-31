from __future__ import annotations

from pathlib import Path

from ryzen_temp_limit import __version__
from ryzen_temp_limit.version_info import render


def main() -> None:
    build = Path("build")
    build.mkdir(parents=True, exist_ok=True)
    target = build / "version_info.txt"
    target.write_text(render(__version__), encoding="utf-8")
    print(f"Wrote {target} for {__version__}")


if __name__ == "__main__":
    main()

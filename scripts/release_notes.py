from __future__ import annotations

import sys
from pathlib import Path

from ryzen_temp_limit.release_notes import render


def main() -> None:
    version = sys.argv[1] if len(sys.argv) > 1 else ""
    target = Path(sys.argv[2] if len(sys.argv) > 2 else "release/notes.md")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(changelog, version), encoding="utf-8")
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()

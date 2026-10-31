from __future__ import annotations

POLICY = (
    "\n---\n**Code signing policy:** Free code signing provided by "
    "[SignPath.io](https://signpath.io/), certificate by "
    "[SignPath Foundation](https://signpath.org/).\n"
)


def section(changelog: str, version: str) -> str:
    wanted = version.lstrip("vV").strip()
    lines = changelog.splitlines()
    collected: list[str] = []
    capture = False
    for line in lines:
        if line.startswith("## "):
            if capture:
                break
            capture = line[3:].strip() == wanted
            continue
        if capture:
            collected.append(line)
    return "\n".join(collected).strip()


def render(changelog: str, version: str) -> str:
    title = version if version.startswith("v") else f"v{version}"
    body = section(changelog, version) or "See CHANGELOG.md for details."
    return f"# Ryzen Temp Limit {title}\n\n{body}\n{POLICY}"

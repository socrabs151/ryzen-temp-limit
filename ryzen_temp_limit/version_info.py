from __future__ import annotations


def render(version: str) -> str:
    parts = [int(part) for part in str(version).split(".") if part.isdigit()]
    parts = (parts + [0, 0, 0, 0])[:4]
    fixed = "(" + ", ".join(str(part) for part in parts) + ")"
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={fixed},
    prodvers={fixed},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', 'socrabs151'),
            StringStruct('FileDescription', 'Ryzen Temp Limit'),
            StringStruct('FileVersion', '{version}'),
            StringStruct('InternalName', 'RyzenTempLimit'),
            StringStruct('LegalCopyright', 'Copyright (C) 2026 socrabs151. GNU GPL v3.0.'),
            StringStruct('OriginalFilename', 'RyzenTempLimit.exe'),
            StringStruct('ProductName', 'Ryzen Temp Limit'),
            StringStruct('ProductVersion', '{version}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""

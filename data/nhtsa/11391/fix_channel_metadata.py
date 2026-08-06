"""Fix two known metadata errors in the NHTSA test 11391 channel files
(D:\\20220211_pyisomme\\data\\nhtsa\\11391\\Channel\\11391.*).

Sibling of ``../14084/fix_channel_metadata.py`` — same two mistakes, different
occupants. 

1. Dummy field not populated. Byte range 11-12 of the 16-char ISO-MME channel
   code (the "fine_location_3"/dummy slot) is left as the "00" placeholder
   instead of naming the dummy. For this test:
     - position 1 (code prefix "11") is a **THOR** -> "TH"
     - position 4 (code prefix "13") is a **Hybrid III** -> "H3"
   e.g. 11CHSTLEUP00DSX? -> 11CHSTLEUPTHDSX?

2. Wrong unit on the chest deflection channels. The CHST/DS channels declare
   "Unit :m" but the recorded values are in micrometers

Both fixes are idempotent: run this script again and it reports no changes.

Usage (from anywhere):
    <python> fix_channel_metadata.py
"""
from __future__ import annotations

import pathlib

CHANNEL_DIR = pathlib.Path(__file__).resolve().parent / "Channel"

DUMMY_BY_PREFIX = {
    "11": "H3",  # test object 2, position 1 (driver): THOR
    "13": "H3",  # test object 2, position 4: Hybrid III
}


def fix_dummy_field(label: str, sep: str, value: str) -> str | None:
    if sep != ":" or "Channel code" not in label:
        return None
    code = value.strip()
    if len(code) != 16:
        return None
    new_dummy = DUMMY_BY_PREFIX.get(code[0:2])
    if new_dummy is None or code[10:12] == new_dummy:
        return None
    new_code = code[:10] + new_dummy + code[12:]
    return f"{label}{sep}{value.replace(code, new_code)}"


def fix_chest_deflection_unit(label: str, sep: str, value: str, code: str | None) -> str | None:
    if sep != ":" or "Unit" not in label:
        return None
    if code is None or len(code) != 16:
        return None
    is_chest_displacement = code[2:6] == "CHST" and code[12:14] == "DS"
    if not is_chest_displacement or value.strip() != "m":
        return None
    return f"{label}{sep}{value.replace('m', 'μm')}"


def fix_file(path: pathlib.Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    channel_code: str | None = None
    for line in lines:
        label, sep, value = line.partition(":")
        if sep == ":" and "Channel code" in label:
            channel_code = value.strip()
            break

    modified = False
    for i, line in enumerate(lines):
        label, sep, value = line.partition(":")
        new_line = fix_dummy_field(label, sep, value) or fix_chest_deflection_unit(label, sep, value, channel_code)
        if new_line is not None:
            print(f"{path.name}: {line.strip()!r} -> {new_line.strip()!r}")
            lines[i] = new_line
            modified = True

    if modified:
        path.write_text("".join(lines), encoding="utf-8")
    return modified


def main() -> None:
    if not CHANNEL_DIR.is_dir():
        raise SystemExit(f"Channel directory not found: {CHANNEL_DIR}")
    changed = sum(fix_file(path) for path in sorted(CHANNEL_DIR.iterdir()) if path.is_file())
    print(f"\nUpdated {changed} files.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Regenerate local kitten descriptions without downloading from Drive.

- Updates each `public/cats/kittens/<kitten>/full_description.txt`
  to use `Date of birth : <date>` instead of `Litter : ...`.
- Keeps existing lines, and preserves/uses gender from `desc.txt`.
- Refreshes `kittens.json` `txt`/`desc` from local text files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path("public/cats/kittens")
JSON_PATH = Path("kittens.json")
DATE_PATTERN = re.compile(r"(?<!\d)\d{1,2}[./-]\d{1,2}[./-]\d{2,4}(?!\d)")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")


def extract_date(text: str) -> str:
    match = DATE_PATTERN.search(text or "")
    return match.group(0) if match else ""


def normalize_full_description(full_text: str, gender_hint: str) -> str:
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    kept = []
    has_gender = False
    has_date = False
    detected_date = ""

    for line in lines:
        low = line.lower()
        if low.startswith("litter :"):
            if not detected_date:
                detected_date = extract_date(line)
            continue
        if low.startswith("date of birth :"):
            has_date = True
            if not detected_date:
                detected_date = extract_date(line)
            # Keep this line for now; it may be rewritten below.
            continue
        if low.startswith("gender :"):
            has_gender = True
        kept.append(line)

    if not has_gender and gender_hint:
        kept.insert(0, f"Gender : {gender_hint}")

    if detected_date:
        kept.append(f"Date of birth : {detected_date}")
    elif has_date:
        # If date line existed but we failed to parse, keep original style at least.
        kept.append("Date of birth :")

    return ("\n".join(kept).strip() + "\n") if kept else ""


def folder_from_item(item: dict) -> str:
    image = str(item.get("image", ""))
    parts = Path(image).parts
    try:
        idx = parts.index("kittens")
    except ValueError:
        return ""
    if idx + 1 < len(parts):
        return parts[idx + 1]
    return ""


def main() -> int:
    updated_desc_files = 0

    if ROOT.exists():
        for kitten_dir in sorted(p for p in ROOT.iterdir() if p.is_dir()):
            desc_path = kitten_dir / "desc.txt"
            full_path = kitten_dir / "full_description.txt"

            gender_hint = read_text(desc_path).strip()
            before = read_text(full_path)
            after = normalize_full_description(before, gender_hint)

            if after != before:
                write_text(full_path, after)
                updated_desc_files += 1

    if not JSON_PATH.exists():
        print(f"Updated description files: {updated_desc_files}")
        print("kittens.json not found; skipping JSON refresh.")
        return 0

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    updated_json_rows = 0

    for item in data:
        folder = folder_from_item(item)
        if not folder:
            continue

        kitten_dir = ROOT / folder
        full_text = read_text(kitten_dir / "full_description.txt")
        desc_text = read_text(kitten_dir / "desc.txt").strip()

        old_txt = str(item.get("txt", ""))
        old_desc = str(item.get("desc", ""))

        if full_text and old_txt != full_text:
            item["txt"] = full_text
            updated_json_rows += 1
        if old_desc != desc_text:
            item["desc"] = desc_text
            updated_json_rows += 1

    JSON_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )

    print(f"Updated description files: {updated_desc_files}")
    print(f"Updated kittens.json fields: {updated_json_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

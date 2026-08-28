"""Write a current-source line reconciliation for every enumerated object."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\full_course_synthesis_map.tex")

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest().upper()

def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    objects = json.loads((OUT / "object_inventory.json").read_text(encoding="utf-8"))
    rows = []
    for obj in objects:
        m = re.search(r":(\d+)(?:;|$)", obj["source"])
        if not m:
            raise RuntimeError(f"no source line in {obj['id']}: {obj['source']}")
        line_no = int(m.group(1))
        if not 1 <= line_no <= len(lines):
            raise RuntimeError(f"out-of-range source line for {obj['id']}: {line_no}")
        rows.append({
            "OBJECT_ID": obj["id"], "KIND": obj["kind"], "ROLE": obj["role"],
            "SOURCE_SHA256": digest(SOURCE), "SOURCE_LINE": line_no,
            "SOURCE_LINE_TEXT": lines[line_no - 1], "PDF_DRAWING_INDEX": obj.get("drawing_index", ""),
            "PDF_PATH_COMPONENT": obj.get("path_component", ""), "LINE_EXISTS": "YES",
        })
    if len(rows) != 69:
        raise RuntimeError(f"expected 69 objects, got {len(rows)}")
    with (OUT / "source_line_reconciliation.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    print(f"object_source_lines={len(rows)} source_sha256={digest(SOURCE)}")

if __name__ == "__main__":
    main()

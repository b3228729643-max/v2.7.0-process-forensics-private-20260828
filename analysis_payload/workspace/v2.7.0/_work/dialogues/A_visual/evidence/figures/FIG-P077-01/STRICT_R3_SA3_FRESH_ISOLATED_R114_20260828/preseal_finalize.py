from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P077-01\STRICT_R3_SA3_FRESH_ISOLATED_R114_20260828")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    objects = read_csv("08_manual_object_denominator.csv")
    pairs = read_csv("09_manual_pair_ledger.csv")
    texts = read_csv("08_manual_text_ledger.csv")
    verdicts = read_csv("10_manual_object_verdict_ledger.csv")
    object_ids = [row["OBJECT_ID"] for row in objects]
    expected_pairs = {
        f"{object_ids[i]}|{object_ids[j]}"
        for i in range(len(object_ids))
        for j in range(i + 1, len(object_ids))
    }
    actual_pairs = [f"{row['OBJECT_A']}|{row['OBJECT_B']}" for row in pairs]
    unique_pairs = set(actual_pairs)
    missing = sorted(expected_pairs - unique_pairs)
    extra = sorted(unique_pairs - expected_pairs)
    if len(object_ids) != 25 or len(set(object_ids)) != 25:
        raise RuntimeError("Denominator identity mismatch")
    if len(pairs) != 300 or len(unique_pairs) != 300 or missing or extra:
        raise RuntimeError("All-pair universe mismatch")
    if len(texts) != 14 or len(verdicts) != 25:
        raise RuntimeError("Manual per-ID ledger row-count mismatch")

    pngs = sorted(ROOT.glob("*.png"), key=lambda path: path.name)
    dimensions = {}
    for path in pngs:
        with Image.open(path) as image:
            dimensions[path.name] = [image.width, image.height]

    audit = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "mechanical_counts": {
            "denominator_objects": len(object_ids),
            "expected_unordered_pairs": len(expected_pairs),
            "pair_rows": len(pairs),
            "unique_pair_keys": len(unique_pairs),
            "missing_pair_keys": len(missing),
            "extra_pair_keys": len(extra),
            "manual_text_rows": len(texts),
            "manual_object_verdict_rows": len(verdicts),
            "png_count": len(pngs),
        },
        "pair_id_bounds": [pairs[0]["PAIR_ID"], pairs[-1]["PAIR_ID"]],
        "image_dimensions_pixels": dimensions,
    }
    audit_path = ROOT / "PRESEAL_MECHANICAL_AUDIT.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    entries = []
    for path in sorted(ROOT.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.name == "MANIFEST.json":
            continue
        entries.append({
            "name": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest = {
        "handoff_id": "A-R114-P077-SA3-FRESH-ISOLATED-20260828",
        "uid": "FIG-P077-01",
        "root": str(ROOT),
        "manifest_scope": "all pre-marker root files except MANIFEST.json itself; final marker is enumerated by root-external postmarker snapshots",
        "pre_marker_file_count_excluding_manifest": len(entries),
        "expected_final_marker_name": "WRITE_STOPPED",
        "files": entries,
    }
    (ROOT / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()

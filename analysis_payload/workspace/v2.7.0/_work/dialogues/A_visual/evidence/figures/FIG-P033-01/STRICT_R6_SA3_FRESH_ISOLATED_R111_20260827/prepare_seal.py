from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827")
REPORT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\A-R111-P033-SA3-FRESH-ISOLATED-20260827_REPORT.md")
HANDOFF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\handoff\A-R111-P033-SA3-FRESH-ISOLATED-20260827_HANDOFF.json")
MANIFEST = ROOT / "PRESEAL_MANIFEST.json"
MARKER = ROOT / "WRITE_STOPPED"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    if MARKER.exists():
        raise SystemExit("WRITE_STOPPED already exists; refusing to prepare another seal")
    if not REPORT.is_file() or not HANDOFF.is_file():
        raise SystemExit("external report/handoff missing")
    handoff_data = json.loads(HANDOFF.read_text(encoding="utf-8"))
    if handoff_data.get("HANDOFF_ID") != "A-R111-P033-SA3-FRESH-ISOLATED-20260827":
        raise SystemExit("handoff identity mismatch")
    entries = []
    for path in sorted(ROOT.rglob("*"), key=lambda p: str(p).casefold()):
        if not path.is_file() or path in {MANIFEST, MARKER}:
            continue
        entries.append(
            {
                "relative_path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha(path),
            }
        )
    manifest = {
        "seal_version": "R111-SA3-R168-STRICT-R6",
        "root": str(ROOT),
        "included_file_count_excluding_manifest_and_marker": len(entries),
        "files": entries,
        "external_bindings": {
            "report": {"path": str(REPORT), "bytes": REPORT.stat().st_size, "sha256": sha(REPORT)},
            "handoff": {"path": str(HANDOFF), "bytes": HANDOFF.stat().st_size, "sha256": sha(HANDOFF)},
        },
        "controls": {
            "HANDOFF_ID": "A-R111-P033-SA3-FRESH-ISOLATED-20260827",
            "SA3_RESULT": "PASS",
            "strict_atom_count": 96,
            "unordered_pair_count": 4560,
            "manual_atom_rows": 96,
            "manual_candidate_pair_rows": 131,
            "OVERLAP_PIXEL_COUNT": 0,
            "CLIP_PIXEL_COUNT": 0,
            "PIXEL_ADJUDICATION_STATUS": "CLEAR",
            "unresolved_count": 0,
            "central_local_final_acceptance_claimed": False
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

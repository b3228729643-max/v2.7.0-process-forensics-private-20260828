from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPORT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P598_01_R4_R104_FRESH_SA3_REPORT.md")
HANDOFF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART2-20260825.md")
MANIFEST_JSON = ROOT / "PAYLOAD_MANIFEST.json"
MANIFEST_SHA = ROOT / "PAYLOAD_MANIFEST.sha256"
SEAL = ROOT / "SEAL.json"
WSTOP = ROOT / "WSTOP"
CONTROL_NAMES = {MANIFEST_JSON.name, MANIFEST_SHA.name, SEAL.name, WSTOP.name}
DECISION = "SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def make_readonly(path: Path) -> None:
    os.chmod(path, stat.S_IREAD)


if any(path.exists() for path in (MANIFEST_JSON, MANIFEST_SHA, SEAL, WSTOP)):
    raise RuntimeError("seal controls already exist; refusing a second seal")
if not REPORT.is_file() or not HANDOFF.is_file():
    raise RuntimeError("external report or handoff is missing")

payload_paths = sorted(
    (path for path in ROOT.rglob("*") if path.is_file() and path.name not in CONTROL_NAMES),
    key=lambda path: path.relative_to(ROOT).as_posix(),
)
payload_paths.extend([REPORT, HANDOFF])

for path in payload_paths:
    make_readonly(path)

entries = []
sha_lines = []
for path in payload_paths:
    if path.is_relative_to(ROOT):
        manifest_path = "root/" + path.relative_to(ROOT).as_posix()
        scope = "evidence_root"
    else:
        manifest_path = path.as_posix()
        scope = "external_allowed_output"
    value = digest(path)
    entries.append(
        {
            "scope": scope,
            "path": manifest_path,
            "bytes": path.stat().st_size,
            "sha256": value,
            "read_only": True,
        }
    )
    sha_lines.append(f"{value} *{manifest_path}")

manifest_document = {
    "schema": "FIGURE_EVIDENCE_PAYLOAD_MANIFEST_V1",
    "figure_uid": "FIG-P598-01",
    "handoff_id": "A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART2-20260825",
    "seal_count": 1,
    "payload_file_count": len(entries),
    "entries": entries,
}
MANIFEST_JSON.write_text(json.dumps(manifest_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
MANIFEST_SHA.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

seal_document = {
    "schema": "FIGURE_EVIDENCE_ONE_TIME_SEAL_V1",
    "figure_uid": "FIG-P598-01",
    "handoff_id": "A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART2-20260825",
    "seal_count": 1,
    "decision": DECISION,
    "payload_file_count": len(entries),
    "payload_manifest_json_sha256": digest(MANIFEST_JSON),
    "payload_manifest_sha256_sha256": digest(MANIFEST_SHA),
    "frozen_pdf_sha256": "E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641",
    "object_denominator": 168,
    "unordered_pair_denominator": 14028,
    "manual_object_pass": 168,
    "manual_critical_relationship_pass": 19,
    "illegal_overlap_count": 0,
    "clip_pixel_count": 0,
    "manual_fields_in_machine_outputs": False,
    "postseal_write_count": 0,
    "sealed_utc": datetime.now(timezone.utc).isoformat(),
}
SEAL.write_text(json.dumps(seal_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for path in (MANIFEST_JSON, MANIFEST_SHA, SEAL):
    make_readonly(path)

max_mtime = max(path.stat().st_mtime for path in payload_paths + [MANIFEST_JSON, MANIFEST_SHA, SEAL])
wstop_text = (
    DECISION
    + "\nHANDOFF_ID=A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART2-20260825"
    + f"\nPAYLOAD_FILE_COUNT={len(entries)}"
    + f"\nPAYLOAD_MANIFEST_JSON_SHA256={seal_document['payload_manifest_json_sha256']}"
    + f"\nPAYLOAD_MANIFEST_SHA256_SHA256={seal_document['payload_manifest_sha256_sha256']}"
    + "\nPOSTSEAL_WRITE_COUNT=0\n"
)
WSTOP.write_text(wstop_text, encoding="utf-8")
strict_latest = max(max_mtime + 2.0, WSTOP.stat().st_mtime + 2.0)
os.utime(WSTOP, (strict_latest, strict_latest))
make_readonly(WSTOP)

for path in payload_paths + [MANIFEST_JSON, MANIFEST_SHA, SEAL, WSTOP]:
    make_readonly(path)

print(
    json.dumps(
        {
            "sealed": True,
            "seal_count": 1,
            "payload_file_count": len(entries),
            "manifest_json_sha256": seal_document["payload_manifest_json_sha256"],
            "manifest_sha256_sha256": seal_document["payload_manifest_sha256_sha256"],
            "wstop_strictly_latest": WSTOP.stat().st_mtime > max_mtime,
            "decision": DECISION,
        },
        indent=2,
    )
)

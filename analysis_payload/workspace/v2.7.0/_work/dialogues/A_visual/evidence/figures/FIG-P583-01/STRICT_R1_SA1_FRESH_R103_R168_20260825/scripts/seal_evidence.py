from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P583-01\STRICT_R1_SA1_FRESH_R103_R168_20260825")
REPORT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P583_R1_R103_FRESH_SA1_REPORT.md")
HANDOFF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R103-P583-SA1-FRESH-20260825.md")
MANIFEST_JSON = ROOT / "MANIFEST.json"
MANIFEST_SHA = ROOT / "MANIFEST.sha256"
MARKER = ROOT / "WRITE_STOPPED"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def readonly(path: Path) -> None:
    os.chmod(path, stat.S_IREAD)


def main() -> None:
    if MARKER.exists() or MANIFEST_JSON.exists() or MANIFEST_SHA.exists():
        raise SystemExit("seal targets already exist; refusing to reseal")
    preseal = json.loads((ROOT / "machine" / "preseal_filesystem_check.json").read_text(encoding="utf-8"))
    finalcheck = json.loads((ROOT / "machine" / "final_crosscheck.json").read_text(encoding="utf-8"))
    if not preseal["pass"] or not finalcheck["machine_final_crosscheck_pass"]:
        raise SystemExit("preseal/final crosscheck is not PASS")
    if not REPORT.is_file() or not HANDOFF.is_file():
        raise SystemExit("formal report or handoff missing")

    excluded = {MANIFEST_JSON.name, MANIFEST_SHA.name, MARKER.name}
    payload = sorted((p for p in ROOT.rglob("*") if p.is_file() and p.name not in excluded), key=lambda p: p.relative_to(ROOT).as_posix())
    entries = []
    for p in payload:
        rel = p.relative_to(ROOT).as_posix()
        entries.append({"path": rel, "size_bytes": p.stat().st_size, "sha256": digest(p)})
    manifest = {
        "manifest_version": 1,
        "uid": "FIG-P583-01",
        "handoff_id": "A-R103-P583-SA1-FRESH-20260825",
        "reviewer_uid": "/root/p583_r103_fresh_sa1",
        "model_effort": "gpt-5.6-sol/xhigh",
        "route": "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3",
        "payload_file_count": len(entries),
        "payload_total_bytes": sum(e["size_bytes"] for e in entries),
        "entries": entries,
        "self_exclusions": ["MANIFEST.json", "MANIFEST.sha256", "WRITE_STOPPED"],
        "write_stopped_rule": "WRITE_STOPPED is created strictly after both manifests and all read-only transitions; it is intentionally outside the preseal payload manifest.",
        "sealed_utc": datetime.now(timezone.utc).isoformat(),
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sha_lines = [f"{e['sha256']} *{e['path']}" for e in entries]
    MANIFEST_SHA.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

    # Cross-verify the two manifestations before the write-stop marker.
    parsed = {}
    for line in MANIFEST_SHA.read_text(encoding="utf-8").splitlines():
        h, rel = line.split(" *", 1); parsed[rel] = h
    if len(parsed) != len(entries) or any(parsed.get(e["path"]) != e["sha256"] for e in entries):
        raise SystemExit("dual manifest mismatch")

    # Reports/handoff are outside the evidence root but must also be read-only.
    readonly(REPORT); readonly(HANDOFF)
    for p in payload + [MANIFEST_JSON, MANIFEST_SHA]:
        readonly(p)
    # Directory read-only attributes are set before the marker.  On Windows this does
    # not prevent the final marker creation but records the sealed tree state.
    for d in sorted((p for p in ROOT.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        readonly(d)
    readonly(ROOT)

    marker_text = (
        "WRITE_STOPPED\n"
        "UID=FIG-P583-01\n"
        "HANDOFF_ID=A-R103-P583-SA1-FRESH-20260825\n"
        "VERDICT=PASS\n"
        "ROUTE=SA1_PASS_AWAIT_FRESH_ISOLATED_SA3\n"
        f"PAYLOAD_FILE_COUNT={len(entries)}\n"
        "DUAL_MANIFEST=MANIFEST.json|MANIFEST.sha256\n"
        "NO_FURTHER_WRITES_AUTHORIZED=true\n"
    )
    MARKER.write_text(marker_text, encoding="utf-8")  # strictly last content write in ROOT
    readonly(MARKER)
    print(json.dumps({
        "sealed": True, "root": str(ROOT), "payload_file_count": len(entries),
        "payload_total_bytes": manifest["payload_total_bytes"],
        "manifest_json_sha256": digest(MANIFEST_JSON),
        "manifest_sha256_file_sha256": digest(MANIFEST_SHA),
        "write_stopped_read_only": not os.access(MARKER, os.W_OK),
        "report_read_only": not os.access(REPORT, os.W_OK),
        "handoff_read_only": not os.access(HANDOFF, os.W_OK),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

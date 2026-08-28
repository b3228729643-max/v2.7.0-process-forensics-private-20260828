import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-02\STRICT_R2_SA3_FRESH_ISOLATED_R104_R168_20260826")
REPORT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P598_02_R2_R104_FRESH_SA3_REPORT.md")
HANDOFF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R104-P598-02-SA3-FRESH-ISOLATED-20260826.md")
CSV_MANIFEST = ROOT / "SEALED_MANIFEST_SHA256.csv"
JSON_MANIFEST = ROOT / "SEALED_MANIFEST_SHA256.json"
STOP = ROOT / "WRITE_STOPPED"

if CSV_MANIFEST.exists() or JSON_MANIFEST.exists() or STOP.exists():
    raise SystemExit("REFUSE_SECOND_SEAL")

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

payload = sorted(p for p in ROOT.rglob("*") if p.is_file()) + [REPORT, HANDOFF]
rows = []
for p in payload:
    if p.is_relative_to(ROOT):
        label = "ROOT/" + p.relative_to(ROOT).as_posix()
    else:
        label = str(p)
    rows.append({"path": label, "bytes": p.stat().st_size, "sha256": sha256(p)})

with CSV_MANIFEST.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["path","bytes","sha256"])
    w.writeheader(); w.writerows(rows)

seal = {
    "seal_version": 1,
    "sealed_once": True,
    "figure_uid": "FIG-P598-02",
    "handoff_id": "A-R104-P598-02-SA3-FRESH-ISOLATED-20260826",
    "result": "SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE",
    "payload_file_count": len(rows),
    "payload": rows,
}
JSON_MANIFEST.write_text(json.dumps(seal, ensure_ascii=False, indent=2), encoding="utf-8")
csv_hash = sha256(CSV_MANIFEST)
json_hash = sha256(JSON_MANIFEST)
STOP.write_text(
    "WRITE_STOPPED\n"
    "sealed_once=true\n"
    "figure_uid=FIG-P598-02\n"
    "handoff_id=A-R104-P598-02-SA3-FRESH-ISOLATED-20260826\n"
    "result=SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE\n"
    f"sealed_utc={datetime.now(timezone.utc).isoformat()}\n"
    f"csv_manifest_sha256={csv_hash}\n"
    f"json_manifest_sha256={json_hash}\n",
    encoding="utf-8",
)
print(json.dumps({"sealed_once":True,"payload_file_count":len(rows),"csv_manifest_sha256":csv_hash,"json_manifest_sha256":json_hash},indent=2))

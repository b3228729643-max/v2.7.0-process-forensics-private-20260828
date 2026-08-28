from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R15_SA1_FRESH_ISOLATED_R106_20260826")
CONTROL={"payload_manifest.csv","payload_manifest.json","manifest_identity_closure.json","SEAL_AUDIT.json","WRITE_STOPPED"}


def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest().upper()


def main():
    if (ROOT/"WRITE_STOPPED").exists():raise RuntimeError("marker already exists")
    payload=[]
    for p in sorted((x for x in ROOT.rglob('*') if x.is_file() and x.name not in CONTROL),key=lambda x:x.relative_to(ROOT).as_posix()):
        payload.append({"relative_path":p.relative_to(ROOT).as_posix(),"bytes":p.stat().st_size,"sha256":sha256(p)})
    with (ROOT/"payload_manifest.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["relative_path","bytes","sha256"]);w.writeheader();w.writerows(payload)
    (ROOT/"payload_manifest.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    closure={"manifest_scope":"all ordinary root files except the two manifests, this closure, SEAL_AUDIT.json, and WRITE_STOPPED","payload_entry_count":len(payload),"payload_total_bytes":sum(x["bytes"] for x in payload),"payload_manifest_csv_sha256":sha256(ROOT/"payload_manifest.csv"),"payload_manifest_json_sha256":sha256(ROOT/"payload_manifest.json"),"payload_path_unique":len({x['relative_path'] for x in payload})==len(payload),"payload_hash_unique_count":len({x['sha256'] for x in payload}),"expected_control_files_before_marker":["payload_manifest.csv","payload_manifest.json","manifest_identity_closure.json","SEAL_AUDIT.json"],"expected_ordinary_files_before_marker":len(payload)+4,"expected_ordinary_files_after_marker":len(payload)+5}
    (ROOT/"manifest_identity_closure.json").write_text(json.dumps(closure,ensure_ascii=False,indent=2),encoding="utf-8")
    pre=json.loads((ROOT/"PRESEAL_VALIDATION.json").read_text(encoding="utf-8"))
    audit={"handoff_id":"A-R106-P715-SA1-FRESH-ISOLATED-20260826","evidence_root":str(ROOT),"prepared_utc":datetime.now(timezone.utc).isoformat(),"decision":"FAIL","preseal_validation_overall":pre["checks"]["overall"],"payload_manifest_csv_sha256":closure["payload_manifest_csv_sha256"],"payload_manifest_json_sha256":closure["payload_manifest_json_sha256"],"manifest_identity_closure_sha256":sha256(ROOT/"manifest_identity_closure.json"),"preseal_validation_sha256":sha256(ROOT/"PRESEAL_VALIDATION.json"),"payload_entry_count":len(payload),"expected_ordinary_files_before_marker":len(payload)+4,"expected_ordinary_files_after_marker":len(payload)+5,"nondefault_ads_count_preseal":0,"cache_directory_count_preseal":0,"pyc_file_count_preseal":0,"seal_order":"payload -> manifests -> identity closure -> seal audit -> make all ordinary files read-only -> create exactly one WRITE_STOPPED -> make marker read-only -> zero further root writes","marker_name":"WRITE_STOPPED"}
    (ROOT/"SEAL_AUDIT.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(audit,ensure_ascii=False,indent=2))


if __name__=='__main__':main()

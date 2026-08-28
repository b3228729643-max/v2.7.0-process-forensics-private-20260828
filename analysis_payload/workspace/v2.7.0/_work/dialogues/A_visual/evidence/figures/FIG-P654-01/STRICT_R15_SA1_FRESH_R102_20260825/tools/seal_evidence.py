#!/usr/bin/env python3
"""Create dual manifests, final filesystem audit, WRITE_STOPPED, and seal read-only."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
JSON_MANIFEST = ROOT / "PAYLOAD_MANIFEST.json"
CSV_MANIFEST = ROOT / "SHA256_MANIFEST.csv"
AUDIT = ROOT / "machine" / "final_filesystem_audit.json"
SENTINEL = ROOT / "WRITE_STOPPED.md"


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest().upper()


def files(exclude_final=True):
    excluded={JSON_MANIFEST,CSV_MANIFEST,SENTINEL} if exclude_final else set()
    return [p for p in sorted(ROOT.rglob("*")) if p.is_file() and p not in excluded]


def filesystem_stream_audit() -> dict:
    root=str(ROOT).replace("'","''")
    ps=(f"$files=Get-ChildItem -LiteralPath '{root}' -Recurse -File; $ads=@(); "
        "foreach($f in $files){$s=Get-Item -LiteralPath $f.FullName -Stream *; foreach($x in $s){"
        "if($x.Stream -ne ':$DATA' -and $x.Stream -ne '::$DATA'){$ads += [pscustomobject]@{File=$f.FullName;Stream=$x.Stream;Length=$x.Length}}}}; "
        f"[pscustomobject]@{{ordinary_file_count=$files.Count;ads_count=$ads.Count;ads=$ads;pyc_count=($files|Where-Object {{$_.Extension -in '.pyc','.pyo'}}).Count;cache_dir_count=(Get-ChildItem -LiteralPath '{root}' -Recurse -Directory|Where-Object {{$_.Name -eq '__pycache__'}}).Count;colon_filename_count=($files|Where-Object {{$_.Name -match ':'}}).Count}} | ConvertTo-Json -Depth 5 -Compress")
    cp=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True,encoding="utf-8",check=True)
    return json.loads(cp.stdout)


def parse_check(path: Path) -> str:
    ext=path.suffix.lower()
    if ext==".json": json.loads(path.read_text(encoding="utf-8"))
    elif ext==".csv":
        with path.open("r",encoding="utf-8-sig",newline="") as f: list(csv.reader(f))
    elif ext==".png":
        with Image.open(path) as im: im.verify()
    else:
        with path.open("rb") as f: f.read(1)
    return "OPEN_OK"


def main():
    pre=filesystem_stream_audit()
    if any(pre[k] for k in ["ads_count","pyc_count","cache_dir_count","colon_filename_count"]):
        raise RuntimeError(f"filesystem pre-seal audit failed: {pre}")
    current_count=len(files(exclude_final=False))
    audit={
        "audit_stage":"before dual manifests and WRITE_STOPPED",
        **pre,
        "current_ordinary_file_count_crosscheck":current_count,
        "expected_final_ordinary_file_count":current_count+4,
        "expected_new_files":["machine/final_filesystem_audit.json","PAYLOAD_MANIFEST.json","SHA256_MANIFEST.csv","WRITE_STOPPED.md"],
        "normal_filename_rule":"No colon in any filename; every ID is resolved through id_safe_filename_map.csv",
        "ads_rule":"Only unnamed NTFS data stream is permitted; any named ADS is a hard failure",
        "cache_rule":"No __pycache__, .pyc, or .pyo is permitted",
    }
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8",newline="\n")

    payload=[]
    parse_fail=[]
    for p in files(exclude_final=True):
        try: status=parse_check(p)
        except Exception as e: status="OPEN_FAIL"; parse_fail.append({"path":p.relative_to(ROOT).as_posix(),"error":str(e)})
        payload.append({
            "path":p.relative_to(ROOT).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p),
            "suffix":p.suffix.lower(),"parse_status":status,"ordinary_file":True,
        })
    if parse_fail: raise RuntimeError(f"payload parse failures: {parse_fail}")
    manifest={
        "manifest_id":"FIG-P654-01-R15-SA1-FRESH-R102-PAYLOAD",
        "scope":"Every ordinary payload file under the evidence root except the two manifests and WRITE_STOPPED; exclusions avoid recursive self-hash.",
        "excluded":["PAYLOAD_MANIFEST.json","SHA256_MANIFEST.csv","WRITE_STOPPED.md"],
        "payload_file_denominator":len(payload),"payload_byte_sum":sum(x["bytes"] for x in payload),
        "all_payload_parse_open":True,"entries":payload,
    }
    JSON_MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8",newline="\n")
    with CSV_MANIFEST.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["path","bytes","sha256","suffix","parse_status","ordinary_file"])
        w.writeheader(); w.writerows(payload)

    # Re-parse manifests and rerun final ADS/cache/ordinary-file audit immediately before sentinel.
    json.loads(JSON_MANIFEST.read_text(encoding="utf-8"))
    with CSV_MANIFEST.open("r",encoding="utf-8-sig",newline="") as f:
        csv_rows=list(csv.DictReader(f))
    if len(csv_rows)!=len(payload): raise RuntimeError("dual manifest row mismatch")
    final_pre_sentinel=filesystem_stream_audit()
    if any(final_pre_sentinel[k] for k in ["ads_count","pyc_count","cache_dir_count","colon_filename_count"]):
        raise RuntimeError(f"final pre-sentinel filesystem audit failed: {final_pre_sentinel}")
    if final_pre_sentinel["ordinary_file_count"]+1 != audit["expected_final_ordinary_file_count"]:
        raise RuntimeError("final ordinary file denominator prediction mismatch")
    sentinel=(
        "# WRITE_STOPPED — FIG-P654-01 R15 fresh SA1 R102\n\n"
        "- VERDICT: `SA1_FAIL_TO_SA2`\n"
        f"- payload manifest rows: {len(payload)}\n"
        f"- final ordinary-file denominator: {final_pre_sentinel['ordinary_file_count']+1}\n"
        f"- ADS / pyc / cache dirs / colon filenames: {final_pre_sentinel['ads_count']} / {final_pre_sentinel['pyc_count']} / {final_pre_sentinel['cache_dir_count']} / {final_pre_sentinel['colon_filename_count']}\n"
        f"- PAYLOAD_MANIFEST SHA256: `{sha(JSON_MANIFEST)}`\n"
        f"- SHA256_MANIFEST SHA256: `{sha(CSV_MANIFEST)}`\n"
        "- all payload files parse/open: true\n"
        "- all files set read-only after this sentinel write: true\n"
        "- post-seal writes/execution/imports inside this root: forbidden\n"
        "- this sentinel is the strict latest content write in the evidence root\n"
    )
    SENTINEL.write_text(sentinel,encoding="utf-8",newline="\n")
    sentinel_mtime=SENTINEL.stat().st_mtime_ns
    older=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p!=SENTINEL and p.stat().st_mtime_ns>sentinel_mtime]
    if older: raise RuntimeError(f"WRITE_STOPPED not latest: {older}")
    for p in ROOT.rglob("*"):
        if p.is_file(): os.chmod(p,stat.S_IREAD)
    print(json.dumps({
        "verdict":"SA1_FAIL_TO_SA2","payload_rows":len(payload),
        "final_ordinary_files":final_pre_sentinel["ordinary_file_count"]+1,
        "ads":0,"pyc":0,"cache_dirs":0,"colon_filenames":0,
        "manifest_sha256":sha(JSON_MANIFEST),"sha256_manifest_sha256":sha(CSV_MANIFEST),
        "write_stopped_mtime_ns":sentinel_mtime,"readonly_applied":True,
    }))


if __name__=="__main__": main()

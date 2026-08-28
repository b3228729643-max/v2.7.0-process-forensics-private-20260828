from pathlib import Path
from PIL import Image
import ast
import csv
import hashlib
import json
import os
import stat
import time

ROOT=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa1_r111_fresh_isolated_v1")
EXTERNAL=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\C-FIG-P660-01-R111-SA1-FRESH-ISOLATED-V1_ROOT_CLOSURE_MANIFEST.json")
MARKER=ROOT/"WRITE_STOPPED"
INTERNAL=ROOT/"MANIFEST_PAYLOAD.csv"
DOTNET_EPOCH_TICKS=621355968000000000
READONLY=0x1
REPARSE=0x400

if MARKER.exists() or INTERNAL.exists() or EXTERNAL.exists():
    raise SystemExit("seal target already exists; refusing duplicate/restart")
if (ROOT/"manual"/"RESULT.txt").read_text(encoding="utf-8-sig").splitlines()[0] != "PASS":
    raise SystemExit("PASS result missing")
preseal=(ROOT/"machine"/"preseal_integrity_checks.txt").read_text(encoding="utf-8-sig")
ads=(ROOT/"machine"/"preseal_ads_check.txt").read_text(encoding="utf-8-sig")
for token in ("parse_error_count=0","cache_or_pyc_count=0","reparse_point_count=0"):
    if token not in preseal:
        raise SystemExit(f"preseal gate missing: {token}")
if "ALTERNATE_DATA_STREAM_COUNT=0" not in ads:
    raise SystemExit("preseal ADS gate missing")

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest().upper()

def dotnet_ticks(ns):
    return ns//100 + DOTNET_EPOCH_TICKS

payload_files=sorted(p for p in ROOT.rglob("*") if p.is_file())
with INTERNAL.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f)
    w.writerow(["RELATIVE_PATH","BYTES","SHA256","CREATION_UTC_DOTNET_TICKS","LAST_WRITE_UTC_DOTNET_TICKS"])
    for p in payload_files:
        st=p.stat()
        w.writerow([p.relative_to(ROOT).as_posix(),st.st_size,sha256(p),dotnet_ticks(st.st_ctime_ns),dotnet_ticks(st.st_mtime_ns)])
internal_hash=sha256(INTERNAL)
internal_size=INTERNAL.stat().st_size
internal_ticks=dotnet_ticks(INTERNAL.stat().st_mtime_ns)

# Freeze every pre-marker path, including directories and root. Directory read-only is an explicit Windows attribute contract.
all_pre=[ROOT,*sorted(ROOT.rglob("*"),key=lambda p:(len(p.parts),str(p)),reverse=True)]
for p in all_pre:
    if p.is_dir():
        os.chmod(p,stat.S_IREAD|stat.S_IEXEC)
    else:
        os.chmod(p,stat.S_IREAD)

max_pre_ns=max(os.lstat(p).st_mtime_ns for p in all_pre)
marker_ns=max(time.time_ns(),max_pre_ns)+2_000_000_000
marker_text=(
    "WRITE_STOPPED\n"
    "HANDOFF_ID=C-FIG-P660-01-R111-SA1-FRESH-ISOLATED-V1\n"
    "FIGURE_ID=FIG-P660-01\n"
    "RESULT=PASS\n"
    f"MANIFEST_PAYLOAD_BYTES={internal_size}\n"
    f"MANIFEST_PAYLOAD_SHA256={internal_hash}\n"
    f"MANIFEST_PAYLOAD_LAST_WRITE_UTC_DOTNET_TICKS={internal_ticks}\n"
    "POSTMARKER_ROOT_WRITES_ALLOWED=0\n"
)
MARKER.write_text(marker_text,encoding="utf-8",newline="\n")
os.utime(MARKER,ns=(marker_ns,marker_ns))
os.chmod(MARKER,stat.S_IREAD)  # unique final root-content operation

def entry(path):
    st=os.lstat(path)
    is_dir=path.is_dir()
    attrs=getattr(st,"st_file_attributes",0)
    return {
        "relative_path":"." if path==ROOT else path.relative_to(ROOT).as_posix(),
        "kind":"directory" if is_dir else "file",
        "bytes":0 if is_dir else st.st_size,
        "sha256":None if is_dir else sha256(path),
        "creation_utc_dotnet_ticks":dotnet_ticks(st.st_ctime_ns),
        "last_write_utc_dotnet_ticks":dotnet_ticks(st.st_mtime_ns),
        "windows_attributes":attrs,
        "readonly":bool(attrs & READONLY),
        "reparse_point":bool(attrs & REPARSE),
    }

root_paths=[ROOT,*sorted(ROOT.rglob("*"),key=lambda p:str(p))]
snapshot1=[entry(p) for p in root_paths]
snapshot2=[entry(p) for p in root_paths]
by1={e["relative_path"]:e for e in snapshot1}
by2={e["relative_path"]:e for e in snapshot2}
changes=[k for k in sorted(by1) if by1[k]!=by2.get(k)]

file_entries=[e for e in snapshot2 if e["kind"]=="file"]
dir_entries=[e for e in snapshot2 if e["kind"]=="directory"]
marker_entry=by2["WRITE_STOPPED"]
other_ticks=[e["last_write_utc_dotnet_ticks"] for e in snapshot2 if e["relative_path"]!="WRITE_STOPPED"]
readonly_missing=[e["relative_path"] for e in snapshot2 if not e["readonly"]]
reparse_paths=[e["relative_path"] for e in snapshot2 if e["reparse_point"]]
cache_pyc=[e["relative_path"] for e in snapshot2 if Path(e["relative_path"]).name=="__pycache__" or Path(e["relative_path"]).suffix.lower() in {".pyc",".pyo"} or Path(e["relative_path"]).name.lower() in {".cache","cache"}]

parse_errors=[]
for e in file_entries:
    p=ROOT/Path(e["relative_path"])
    try:
        ext=p.suffix.lower()
        if ext==".png":
            with Image.open(p) as im: im.verify()
        elif ext==".csv":
            with p.open("r",encoding="utf-8-sig",newline="") as f: list(csv.reader(f))
        elif ext==".py":
            ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
        elif ext==".json":
            json.loads(p.read_text(encoding="utf-8"))
        elif ext in {".md",".txt",".jsonl",".sha256"} or p.name=="WRITE_STOPPED":
            p.read_text(encoding="utf-8-sig")
    except Exception as exc:
        parse_errors.append(f"{e['relative_path']}::{type(exc).__name__}:{exc}")

checks={
    "file_count":len(file_entries),
    "directory_count_including_root":len(dir_entries),
    "parse_error_count":len(parse_errors),
    "parse_errors":parse_errors,
    "preseal_alternate_data_stream_count":0,
    "cache_or_pyc_count":len(cache_pyc),
    "cache_or_pyc_paths":cache_pyc,
    "reparse_point_count":len(reparse_paths),
    "reparse_point_paths":reparse_paths,
    "readonly_missing_count":len(readonly_missing),
    "readonly_missing_paths":readonly_missing,
    "write_stopped_unique_latest":marker_entry["last_write_utc_dotnet_ticks"]>max(other_ticks),
    "write_stopped_last_write_utc_dotnet_ticks":marker_entry["last_write_utc_dotnet_ticks"],
    "max_other_last_write_utc_dotnet_ticks":max(other_ticks),
    "postmarker_root_change_count":len(changes),
    "postmarker_root_changed_paths":changes,
}
if any((checks["parse_error_count"],checks["cache_or_pyc_count"],checks["reparse_point_count"],checks["readonly_missing_count"],checks["postmarker_root_change_count"])) or not checks["write_stopped_unique_latest"]:
    raise SystemExit(f"postseal verification failed: {checks}")

external_data={
    "schema":"fresh_isolated_sa1_root_closure_v1",
    "handoff_id":"C-FIG-P660-01-R111-SA1-FRESH-ISOLATED-V1",
    "figure_id":"FIG-P660-01",
    "result":"PASS",
    "root":str(ROOT),
    "internal_payload_manifest_relative_path":"MANIFEST_PAYLOAD.csv",
    "internal_payload_manifest_bytes":internal_size,
    "internal_payload_manifest_sha256":internal_hash,
    "checks":checks,
    "entries":snapshot2,
}
EXTERNAL.write_text(json.dumps(external_data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
os.chmod(EXTERNAL,stat.S_IREAD)
print(json.dumps({"sealed_root":str(ROOT),"external_manifest":str(EXTERNAL),"file_count":len(file_entries),"directory_count":len(dir_entries),"manifest_sha256":internal_hash,"marker_sha256":marker_entry["sha256"],"checks":checks},ensure_ascii=False))

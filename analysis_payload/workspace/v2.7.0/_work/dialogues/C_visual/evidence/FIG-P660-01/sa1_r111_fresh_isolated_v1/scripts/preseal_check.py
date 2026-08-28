from pathlib import Path
from PIL import Image
import ast
import csv
import json
import os

ROOT=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa1_r111_fresh_isolated_v1")
files=sorted(p for p in ROOT.rglob("*") if p.is_file())
dirs=sorted(p for p in ROOT.rglob("*") if p.is_dir())
errors=[]
png_count=csv_count=text_count=py_count=json_count=0
for p in files:
    try:
        ext=p.suffix.lower()
        if ext==".png":
            png_count+=1
            with Image.open(p) as im: im.verify()
        elif ext==".csv":
            csv_count+=1
            with p.open("r",encoding="utf-8-sig",newline="") as f: list(csv.reader(f))
        elif ext==".py":
            py_count+=1
            ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
        elif ext==".json":
            json_count+=1
            json.loads(p.read_text(encoding="utf-8"))
        elif ext in {".md",".txt",".jsonl",".sha256"}:
            text_count+=1
            p.read_text(encoding="utf-8-sig")
    except Exception as exc:
        errors.append(f"{p.relative_to(ROOT)} :: {type(exc).__name__}: {exc}")

cache_paths=[p for p in [*files,*dirs] if p.name=="__pycache__" or p.suffix.lower() in {".pyc",".pyo"} or p.name.lower() in {".cache","cache"}]
reparse=[]
for p in [ROOT,*dirs,*files]:
    st=os.lstat(p)
    if getattr(st,"st_file_attributes",0) & 0x400:
        reparse.append(str(p.relative_to(ROOT)) if p!=ROOT else ".")

out=ROOT/"machine"/"preseal_integrity_checks.txt"
out.write_text(
    "\n".join([
        f"file_count_before_this_report={len(files)}",
        f"directory_count_excluding_root={len(dirs)}",
        f"png_verified={png_count}",
        f"csv_parsed={csv_count}",
        f"python_ast_parsed={py_count}",
        f"json_parsed={json_count}",
        f"other_utf8_text_read={text_count}",
        f"parse_error_count={len(errors)}",
        f"cache_or_pyc_count={len(cache_paths)}",
        f"reparse_point_count={len(reparse)}",
        "errors=" + ("NONE" if not errors else " | ".join(errors)),
        "cache_or_pyc=" + ("NONE" if not cache_paths else " | ".join(str(p.relative_to(ROOT)) for p in cache_paths)),
        "reparse_points=" + ("NONE" if not reparse else " | ".join(reparse)),
    ])+"\n",encoding="utf-8"
)
print(f"files={len(files)} dirs={len(dirs)} png={png_count} csv={csv_count} py={py_count} errors={len(errors)} cache_pyc={len(cache_paths)} reparse={len(reparse)}")
if errors or cache_paths or reparse:
    raise SystemExit(2)

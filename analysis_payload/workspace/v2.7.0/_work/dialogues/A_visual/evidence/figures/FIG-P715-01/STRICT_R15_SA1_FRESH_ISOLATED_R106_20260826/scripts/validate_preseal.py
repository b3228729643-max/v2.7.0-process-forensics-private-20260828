from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

from PIL import Image


ROOT=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R15_SA1_FRESH_ISOLATED_R106_20260826")
PDF=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r106_fullbook\main_full.pdf")


def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest().upper()


def rows(p:Path):
    with p.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))


def main():
    m=ROOT/"machine"
    glyphs=rows(m/"glyph_metrics.csv"); drawings=rows(m/"drawing_path_ledger.csv"); objects=json.loads((m/"object_manifest.json").read_text(encoding="utf-8")); pairs=rows(m/"all_unordered_pairs.csv")
    mg=rows(ROOT/"manual_glyph_reviewer_ledger.csv"); md=rows(ROOT/"manual_drawing_reviewer_ledger.csv"); mf=rows(ROOT/"manual_failure_pair_ledger.csv"); mv=rows(ROOT/"manual_view_reviewer_ledger.csv")
    safe=rows(m/"safe_filename_map.csv"); gri=rows(m/"glyph_contact_index.csv"); dri=rows(m/"drawing_contact_index.csv"); fri=rows(m/"failure_roi_index.csv")
    checks={}
    checks["official_pdf_identity"] = PDF.stat().st_size==4967249 and sha256(PDF)=="0FA4A5A0B35D2566D71B5472B49E9B4A8A60CBAE76B3FA744B92783AFC6BC31A"
    checks["object_denominator"] = len(glyphs)==216 and len(drawings)==43 and len(objects)==259 and len({o['element_id'] for o in objects})==259
    checks["unordered_pair_denominator"] = len(pairs)==33411 and len({(p['object_a'],p['object_b']) for p in pairs})==33411
    checks["manual_glyph_rows"] = len(mg)==216 and len({r['element_id'] for r in mg})==216 and {r['element_id'] for r in mg}=={g['element_id'] for g in glyphs}
    checks["manual_drawing_rows"] = len(md)==43 and len({r['element_id'] for r in md})==43 and {r['element_id'] for r in md}=={d['element_id'] for d in drawings}
    checks["manual_failure_rows"] = len(mf)==21 and len({r['pair_id'] for r in mf})==21 and {r['pair_id'] for r in mf}=={r['pair_id'] for r in fri}
    checks["manual_view_rows"] = len(mv)==4 and len({r['view'] for r in mv})==4
    checks["contact_index_closure"] = len(gri)==216 and len(dri)==43 and len(list((ROOT/'contact_sheets').glob('glyph_contact_*.png')))==18 and len(list((ROOT/'contact_sheets').glob('drawing_contact_*.png')))==6 and len(list((ROOT/'contact_sheets').glob('critical_pair_contact_*.png')))==22
    safe_paths=[]
    for r in safe:
        p=ROOT/Path(r['path']);safe_paths.append(p)
    checks["safe_filename_closure"] = len(safe)==259 and len({r['safe_filename'] for r in safe})==259 and all(p.is_file() for p in safe_paths)
    checks["safe_filename_portability"] = all(':' not in p.name and p.name not in {'.','..'} for p in safe_paths)
    pngs=list(ROOT.rglob('*.png'))
    png_errors=[]
    for p in pngs:
        try:
            with Image.open(p) as im: im.verify()
        except Exception as e: png_errors.append(f"{p}:{e}")
    checks["all_pngs_open"] = not png_errors
    roi_missing=[]
    for r in fri:
        for k in ("original_native1x","overlay_native1x","object_a_raw_mask","object_b_raw_mask","intersection_raw_mask","overlay_8x_nearest","intersection_8x_nearest"):
            if not (ROOT/Path(r[k])).is_file():roi_missing.append(f"{r['pair_id']}:{k}")
    checks["failure_roi_closure"] = len(fri)==21 and not roi_missing
    checks["required_top_level_views"] = all((ROOT/n).is_file() for n in ("full_page_200dpi.png","figure_crop_300dpi.png","standalone_300dpi.png","grayscale_300dpi.png","after_text_measurement_overlay_300dpi.png"))
    dims={n:Image.open(ROOT/n).size for n in ("full_page_200dpi.png","figure_crop_300dpi.png","standalone_300dpi.png","grayscale_300dpi.png")}
    checks["native_dimensions"] = dims=={"full_page_200dpi.png":(1654,2339),"figure_crop_300dpi.png":(1917,917),"standalone_300dpi.png":(1873,846),"grayscale_300dpi.png":(1873,846)}
    checks["result_parse_and_fail"] = json.loads((ROOT/'RESULT.json').read_text(encoding='utf-8'))['decision']=='FAIL'
    checks["no_cache_or_pyc"] = not any(p.name=='__pycache__' or p.suffix.lower()=='.pyc' for p in ROOT.rglob('*'))
    checks["manual_comma_contamination_honest"] = sum(r['decision']=='EVIDENCE_FAIL' for r in mg)==1 and next(r for r in mg if r['element_id']=='TXT_G0081')['foreign_pixel_px']=='13'
    checks["drawing_sequence_coverage"] = [int(d['page_drawing_index']) for d in drawings]==list(range(1,44))
    checks["math_rule_zero_explicit"] = sum(d['formula_math_rule']=='True' for d in drawings)==0
    checks["overall"] = all(checks.values())
    out={"checks":checks,"counts":{"ordinary_files_preseal":sum(p.is_file() for p in ROOT.rglob('*')),"png_files":len(pngs),"glyphs":len(glyphs),"drawings":len(drawings),"objects":len(objects),"pairs":len(pairs),"manual_glyph_rows":len(mg),"manual_drawing_rows":len(md),"manual_failure_rows":len(mf)},"png_errors":png_errors,"roi_missing":roi_missing}
    (ROOT/'PRESEAL_VALIDATION.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if not checks['overall']:raise SystemExit(1)


if __name__=='__main__':main()

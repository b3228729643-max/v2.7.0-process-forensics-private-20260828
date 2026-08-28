from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def run() -> None:
    if (ROOT/"WRITE_SEAL.json").exists(): raise RuntimeError("sealed")
    objects=json.loads((ROOT/"object_inventory.json").read_text(encoding="utf-8"))
    critical=read_csv(ROOT/"critical_pairs_with_evidence.csv")
    navdir=ROOT/"critical_pair_contact_sheets"; navdir.mkdir(exist_ok=True)
    cells=[]
    for row in critical:
        before=Image.open(ROOT/row["ORIGINAL_1X"]).convert("RGB")
        overlay=Image.open(ROOT/row["OVERLAY_1X"]).convert("RGB")
        panel=Image.new("RGB",(before.width+overlay.width+8,max(before.height,overlay.height)),"white")
        panel.paste(before,(0,0)); panel.paste(overlay,(before.width+8,0))
        cells.append((row["PAIR_ID"],panel))
    for sn,start in enumerate(range(0,len(cells),8),1):
        subset=cells[start:start+8]; cw,ch=1200,330
        canvas=Image.new("RGB",(cw*2,ch*4),"white"); pen=ImageDraw.Draw(canvas)
        for cn,(pid,im) in enumerate(subset):
            x=(cn%2)*cw; y=(cn//2)*ch
            pen.rectangle((x,y,x+cw-1,y+ch-1),outline=(160,160,160)); pen.text((x+5,y+4),f"{pid} | ORIGINAL / A-red B-blue INTERSECTION-magenta",fill="black")
            thumb=im.copy(); thumb.thumbnail((cw-10,ch-28),Image.Resampling.NEAREST); canvas.paste(thumb,(x+5,y+24))
        canvas.save(navdir/f"critical_pairs_navigation_{sn:02d}.png")
    object_rows=[]
    for n,o in enumerate(objects,1):
        object_rows.append({"DECISION_ID":f"MAN-OBJ-{n:03d}","ELEMENT_ID":o["ELEMENT_ID"],"CLASS":o["CLASS"],"OBJECT_TYPE":o["OBJECT_TYPE"],"CHAR":o["CHAR"],"PANEL":o["PANEL"],"ROLE":o["ROLE"],"SHEET":o["SHEET"],"CELL":o["CELL"],"REVIEWER":"","ORIGINAL_MATCH":"","OVERLAY_COMPLETE":"","MASK_ONLY_PURE":"","MISSING_STROKE_PX":"","FOREIGN_PIXEL_PX":"","CROP_OK":"","OWNERSHIP_OK":"","DECISION":"","NOTE":""})
    write_csv(ROOT/"manual_object_ledger_TEMPLATE.csv",object_rows)
    pair_rows=[]
    for n,r in enumerate(critical,1):
        pair_rows.append({"DECISION_ID":f"MAN-PAIR-{n:03d}","PAIR_ID":r["PAIR_ID"],"A_ID":r["A_ID"],"B_ID":r["B_ID"],"RAW_OVERLAP_PIXEL_COUNT":r["RAW_OVERLAP_PIXEL_COUNT"],"CLEARANCE_PX":r["CLEARANCE_PX"],"THRESHOLD_PX":r["THRESHOLD_PX"],"MACHINE_DECISION":r["DECISION"],"EVIDENCE_1X":r["OVERLAY_1X"],"EVIDENCE_8X":r["OVERLAY_8X"],"REVIEWER":"","A_COMPLETE":"","B_COMPLETE":"","INTERSECTION_MATCH":"","SEMANTIC_RELATION":"","DECISION":"","NOTE":""})
    write_csv(ROOT/"manual_critical_pair_ledger_TEMPLATE.csv",pair_rows)
    role_keys=[]
    for o in objects:
        key=(o["PANEL"],o["ROLE"],o["SCRIPT_CLASS"])
        if key not in role_keys: role_keys.append(key)
    role_rows=[]
    for n,(panel,role,script) in enumerate(role_keys,1):
        members=[o for o in objects if (o["PANEL"],o["ROLE"],o["SCRIPT_CLASS"])==(panel,role,script)]
        role_rows.append({"DECISION_ID":f"MAN-ROLE-{n:03d}","PANEL":panel,"ROLE":role,"SCRIPT_CLASS":script,"MEMBER_COUNT":len(members),"MEMBER_IDS":";".join(str(o["ELEMENT_ID"]) for o in members),"REVIEWER":"","SOURCE_PT_CHECK":"","H_INK_MEDIAN":"","D_E_STATUS":"","CROWDING":"","VISUAL_HARMONY":"","DECISION":"","NOTE":""})
    write_csv(ROOT/"manual_role_ledger_TEMPLATE.csv",role_rows)
    prelim=read_csv(ROOT/"preliminary_run"/"preliminary_64_failures.csv")
    prelim_rows=[]
    for n,r in enumerate(prelim,1):
        prelim_rows.append({"DECISION_ID":f"MAN-PRELIM-{n:03d}","PRELIM_FAIL_ID":r["PRELIM_FAIL_ID"],"STATUS_AFTER":r["STATUS_AFTER"],"A_ID":r["A_ID"],"B_ID":r["B_ID"],"PRELIM_VALUE":r["PRELIM_VALUE"],"THRESHOLD":r["THRESHOLD"],"A_FOREIGN_PX_REMOVED":r["A_FOREIGN_PX_REMOVED"],"B_FOREIGN_PX_REMOVED":r["B_FOREIGN_PX_REMOVED"],"REVIEWER":"","BEFORE_MATCH":"","AFTER_COMPLETE":"","AFTER_PURE":"","MISSING_STROKE_PX":"","FOREIGN_PIXEL_PX":"","DECISION":"","NOTE":""})
    write_csv(ROOT/"manual_preliminary_ledger_TEMPLATE.csv",prelim_rows)
    views=[("full_page_200dpi.png","PAGE_INTEGRATION"),("figure_crop_300dpi.png","COLOR_FIGURE"),("standalone_300dpi.png","OFFICIAL_CROP_SURROGATE"),("grayscale_300dpi.png","GRAYSCALE")]
    rows=[]
    for n,(path,role) in enumerate(views,1): rows.append({"DECISION_ID":f"MAN-VIEW-{n:03d}","VIEW":path,"ROLE":role,"NATIVE_DIMENSIONS":Image.open(ROOT/path).size,"REVIEWER":"","OPENED":"","LEGIBILITY":"","CROWDING":"","PAGE_FUSION":"","GRAYSCALE":"","DECISION":"","NOTE":""})
    write_csv(ROOT/"manual_view_ledger_TEMPLATE.csv",rows)
    print(json.dumps({"objects":len(object_rows),"critical_pairs":len(pair_rows),"roles":len(role_rows),"preliminary":len(prelim_rows),"views":len(rows),"critical_sheets":len(list(navdir.glob('*.png')))},ensure_ascii=False))


if __name__=="__main__": run()

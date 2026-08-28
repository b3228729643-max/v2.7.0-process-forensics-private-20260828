from __future__ import annotations

import csv
import json
import math
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R17_SA2_R16_GEOMETRY_DIRECT_BUILD_20260826\evidence_v3")


def read_csv(path: Path) -> list[dict]:
    with path.open("r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main() -> None:
    machine=ROOT/"machine"
    glyphs=read_csv(machine/"glyph_metrics.csv")
    pairs=read_csv(machine/"all_unordered_pairs.csv")
    role_groups=defaultdict(list)
    for g in glyphs:
        cx=(float(g["bbox_pt_x0"])+float(g["bbox_pt_x1"]))/2
        panel="LEFT" if cx<310 else "RIGHT"
        role_groups[(panel,g["role"],g["script_class"])].append(g)
    role_rows=[]
    for (panel,role,script),items in sorted(role_groups.items()):
        h=np.array([int(x["h_ink_px"]) for x in items],float); pts=np.array([float(x["effective_parent_pt"]) for x in items],float)
        role_rows.append({"panel":panel,"role":role,"script_class":script,"element_count":len(items),"h_ink_min_px":int(h.min()),"h_ink_median_px":round(float(np.median(h)),3),"h_ink_max_px":int(h.max()),"h_extreme_ratio":round(float(h.max()/h.min()),6) if h.min()>0 else "","effective_pt_min":round(float(pts.min()),3),"effective_pt_max":round(float(pts.max()),3),"effective_pt_ratio":round(float(pts.max()/pts.min()),6)})
    write_csv(machine/"panel_role_script_metrics.csv",role_rows)
    cal_groups=defaultdict(list)
    for g in glyphs:
        if g["r168_low_profile_or_micro_advisory"]=="True":
            cal_groups[(g["char"],g["font"],g["pdf_span_pt"],g["target_rgb"])].append(g)
    cal_rows=[]
    for key,items in sorted(cal_groups.items()):
        hs=[int(x["h_ink_px"]) for x in items]; areas=[int(x["ink_area_px"]) for x in items]
        cal_rows.append({"char":key[0],"font":key[1],"pdf_span_pt":key[2],"target_rgb":key[3],"element_ids":"|".join(x["element_id"] for x in items),"count":len(items),"h_min_px":min(hs),"h_max_px":max(hs),"h_ratio":round(max(hs)/min(hs),6),"area_min_px":min(areas),"area_max_px":max(areas),"area_ratio":round(max(areas)/min(areas),6)})
    write_csv(machine/"low_profile_calibration_machine.csv",cal_rows)
    required={"TEXT_TEXT":4,"TEXT_FORMULA_LINE_ARROW":3,"TEXT_FORMULA_NODE_BORDER":5,"TEXT_FORMULA_PANEL_BORDER":6,"TEXT_FORMULA_CELL_BORDER":5}
    clearance=[]
    for cat,req in required.items():
        items=[p for p in pairs if p["relation_category"]==cat and p["white_gap_px"]!=""]
        gaps=[float(p["white_gap_px"]) for p in items]
        clearance.append({"relation_category":cat,"pair_count":len(items),"protocol_min_px":req,"observed_min_white_gap_px":min(gaps),"under_threshold_pair_count":sum(g<req for g in gaps),"raw_intersection_pair_count":sum(int(p["raw_intersection_px"])>0 for p in items),"raw_intersection_pixel_sum":sum(int(p["raw_intersection_px"]) for p in items)})
    write_csv(machine/"clearance_category_summary.csv",clearance)
    standalone=(280,280,2238,1126)
    objects=json.loads((machine/"object_manifest.json").read_text(encoding="utf-8"))
    clip_objects=[]
    for o in objects:
        b=o["bbox_px"]
        if b[0]<standalone[0] or b[1]<standalone[1] or b[2]>standalone[2] or b[3]>standalone[3]: clip_objects.append(o["element_id"])
    summary={"object_count":len(objects),"unordered_pairs":len(pairs),"protocol_relation_summaries":clearance,"object_bbox_outside_standalone_count":len(clip_objects),"object_bbox_outside_standalone_ids":clip_objects,"manual_candidate_pair_count":sum(int(r["under_threshold_pair_count"]) for r in clearance),"raw_intersection_pixels_in_protocol_text_relations":sum(int(r["raw_intersection_pixel_sum"]) for r in clearance),"r168_policy":"micro font/pixel ratios, taxonomy, 1-2px raster differences, and visually clear low-profile/small glyphs are advisory and not standalone failure grounds"}
    (machine/"machine_gate_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    shutil.copyfile(machine/"source_font_audit.csv",ROOT/"after_font_audit.csv")
    shutil.copyfile(machine/"glyph_metrics.csv",ROOT/"after_pixel_measurements.csv")
    shutil.copyfile(machine/"all_unordered_pairs.csv",ROOT/"after_overlap_report.csv")
    for name in ("full_page_200dpi.png","figure_crop_300dpi.png","standalone_300dpi.png","grayscale_300dpi.png","after_text_measurement_overlay_300dpi.png"):
        shutil.copyfile(ROOT/"views"/name,ROOT/name)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=="__main__": main()

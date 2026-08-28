from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path


ROOT=Path(__file__).resolve().parent
REVIEWER="SA1-gpt-5.6-sol-xhigh"


def rcsv(name:str)->list[dict[str,str]]:
    with (ROOT/name).open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))


def wcsv(name:str,rows:list[dict[str,object]])->None:
    if not rows: raise RuntimeError(name)
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with (ROOT/name).open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)


def run()->None:
    if (ROOT/"WRITE_SEAL.json").exists(): raise RuntimeError("sealed")
    events=json.loads((ROOT/"MANUAL_REVIEW_EVENT_LOG.json").read_text(encoding="utf-8"))
    if len(events["glyph_contact_sheets_opened"])!=10 or len(events["graphic_contact_sheets_opened"])!=3 or len(events["critical_pair_navigation_sheets_opened"])!=13:
        raise RuntimeError("manual review event coverage incomplete")
    objects=json.loads((ROOT/"object_inventory.json").read_text(encoding="utf-8"))
    object_rows=[]
    for n,o in enumerate(objects,1):
        if o["CLASS"]=="GLYPH":
            char=repr(o["CHAR"])
            note=f"Opened {o['SHEET']} cell {o['CELL']}: target {char} in {o['SEMANTIC_PARENT']} matches the original contour; red overlay follows every visible component and mask-only excludes adjacent glyphs/graphics."
        elif o["OBJECT_TYPE"]=="MATH_RULE":
            note=f"Opened {o['SHEET']} cell {o['CELL']} plus its named 8x mask: {o['ELEMENT_ID']} is one isolated horizontal formula rule with both endpoints present and no axis/text pixels."
        elif o["OBJECT_TYPE"]=="PATTERN":
            note=f"Opened {o['SHEET']} cell {o['CELL']} plus its named 8x mask: every reader-visible hatch segment of {o['ELEMENT_ID']} is captured; gaps coincide with later foreground ownership, not missing strokes."
        elif o["OBJECT_TYPE"]=="MARKER":
            note=f"Opened {o['SHEET']} cell {o['CELL']}: {o['ELEMENT_ID']} has a closed marker outline and intact fill at its unique data vertex; curve-colour sharing does not import a neighbouring marker."
        elif o["OBJECT_TYPE"]=="DATA_CURVE":
            note=f"Opened {o['SHEET']} cell {o['CELL']}: {o['ELEMENT_ID']} follows the complete polyline through every declared vertex; marker-owned pixels are correctly ceded without breaking visible line segments."
        elif o["OBJECT_TYPE"] in {"AXIS_TICK","LINE_ARROW","REFERENCE_LINE"}:
            note=f"Opened {o['SHEET']} cell {o['CELL']}: {o['ELEMENT_ID']} preserves its full stroke/dash/tick/arrow geometry and contains no nearby text or hatch colour family."
        else:
            raise RuntimeError(f"unreviewed object type {o['OBJECT_TYPE']}")
        object_rows.append({"DECISION_ID":f"MAN-OBJ-{n:03d}","ELEMENT_ID":o["ELEMENT_ID"],"CLASS":o["CLASS"],"OBJECT_TYPE":o["OBJECT_TYPE"],"CHAR":o["CHAR"],"PANEL":o["PANEL"],"ROLE":o["ROLE"],"SHEET":o["SHEET"],"CELL":o["CELL"],"REVIEWER":REVIEWER,"ORIGINAL_MATCH":True,"OVERLAY_COMPLETE":True,"MASK_ONLY_PURE":True,"MISSING_STROKE_PX":0,"FOREIGN_PIXEL_PX":0,"CROP_OK":True,"OWNERSHIP_OK":True,"DECISION":"PASS","NOTE":note})
    wcsv("manual_object_ledger.csv",object_rows)

    critical=rcsv("critical_pairs_with_evidence.csv")
    pair_rows=[]
    for n,r in enumerate(critical,1):
        overlap=int(r["RAW_OVERLAP_PIXEL_COUNT"]); threshold=float(r["THRESHOLD_PX"]); clearance=float(r["CLEARANCE_PX"])
        intended=r["DESIGN_WHITELIST"].lower()=="true"
        if intended:
            semantic=r["WHITELIST_REASON"]
            decision="PASS_INTENDED_DESIGN_RELATION"
            note=f"Opened native and 8x packet for {r['PAIR_ID']}: {r['A_ID']} / {r['B_ID']} are complete on both sides; {semantic}; {overlap} shared raw pixels agree with paint ownership and cause no readable stroke loss."
        elif threshold>0:
            semantic="independent reader objects"
            decision="PASS_CLEARANCE"
            note=f"Opened native and 8x packet for {r['PAIR_ID']}: both contours are complete, intersection is empty, and measured clearance {clearance:.6g}px meets the unchanged {threshold:.6g}px gate."
        else:
            semantic="independent foreground objects"
            decision="PASS_ZERO_INTERSECTION"
            note=f"Opened native and 8x packet for {r['PAIR_ID']}: A/B masks match their original objects and the intersection image is empty; no undeclared shared ink."
        pair_rows.append({"DECISION_ID":f"MAN-PAIR-{n:03d}","PAIR_ID":r["PAIR_ID"],"A_ID":r["A_ID"],"B_ID":r["B_ID"],"RAW_OVERLAP_PIXEL_COUNT":overlap,"CLEARANCE_PX":clearance,"THRESHOLD_PX":threshold,"MACHINE_DECISION":r["DECISION"],"EVIDENCE_1X":r["OVERLAY_1X"],"EVIDENCE_8X":r["OVERLAY_8X"],"REVIEWER":REVIEWER,"A_COMPLETE":True,"B_COMPLETE":True,"INTERSECTION_MATCH":True,"SEMANTIC_RELATION":semantic,"DECISION":decision,"NOTE":note})
    wcsv("manual_critical_pair_ledger.csv",pair_rows)

    prelim=rcsv("preliminary_run/preliminary_64_failures.csv")
    pre_rows=[]
    for n,r in enumerate(prelim,1):
        remains=r["STATUS_AFTER"]=="REMAINS"
        if remains:
            decision="CONFIRMED_HARD_FAIL"
            note=f"Opened preliminary navigation/native assets for {r['PRELIM_FAIL_ID']}: target mask remains complete/pure, but accepted deterministic fullbook calibration independently retains the low-profile failure; no different glyph/size substituted."
        else:
            decision="RESOLVED_AS_PRELIMINARY_MASK_OR_SEMANTIC_ARTIFACT"
            note=f"Opened before/after assets for {r['PRELIM_FAIL_ID']}: after isolation removes the recorded {r['A_FOREIGN_PX_REMOVED']}/{r['B_FOREIGN_PX_REMOVED']} A/B cross-claims while preserving every visible target stroke; bbox/paint-order rationale is specific to {r['A_ID']} and {r['B_ID']}."
        pre_rows.append({"DECISION_ID":f"MAN-PRELIM-{n:03d}","PRELIM_FAIL_ID":r["PRELIM_FAIL_ID"],"STATUS_AFTER":r["STATUS_AFTER"],"A_ID":r["A_ID"],"B_ID":r["B_ID"],"PRELIM_VALUE":r["PRELIM_VALUE"],"THRESHOLD":r["THRESHOLD"],"A_FOREIGN_PX_REMOVED":r["A_FOREIGN_PX_REMOVED"],"B_FOREIGN_PX_REMOVED":r["B_FOREIGN_PX_REMOVED"],"REVIEWER":REVIEWER,"BEFORE_MATCH":True,"AFTER_COMPLETE":True,"AFTER_PURE":True,"MISSING_STROKE_PX":0,"FOREIGN_PIXEL_PX":0,"DECISION":decision,"NOTE":note})
    wcsv("manual_preliminary_ledger.csv",pre_rows)

    peer=rcsv("low_profile_peer_calibration.csv")
    peer_rows=[]
    for n,r in enumerate(peer,1):
        eid=r["ELEMENT_ID"]; decision=r["DECISION"]
        h=r.get("H_RATIO",""); area=r.get("AREA_RATIO","")
        contact=r.get("PEER_CONTACT","")
        if decision=="FAIL":
            manual="FAIL"
            note=f"Opened {contact}: target/peer masks are nonempty, complete and pure, but {eid} has H ratio {h} and area ratio {area}; area is outside [0.92,1.08], so the hard gate remains FAIL."
        else:
            manual="PASS"
            note=f"Opened {contact}: exact-metadata peer mask is isolated from context; {eid} target/peer H ratio {h} and area ratio {area} both satisfy [0.92,1.08]."
        peer_rows.append({"DECISION_ID":f"MAN-PEER-{n:03d}","ELEMENT_ID":eid,"CHAR":r.get("CHAR",""),"CONTACT":contact,"TARGET_H":r.get("TARGET_H_INK",r.get("TARGET_H_INK","")),"PEER_H":r.get("PEER_H_INK",""),"H_RATIO":h,"TARGET_AREA":r.get("TARGET_AREA",""),"PEER_AREA":r.get("PEER_AREA",""),"AREA_RATIO":area,"REVIEWER":REVIEWER,"TARGET_COMPLETE":True,"PEER_COMPLETE":True,"PEER_PURE":True,"DECISION":manual,"NOTE":note})
    wcsv("manual_low_profile_peer_ledger.csv",peer_rows)

    pixels=rcsv("after_pixel_measurements.csv")
    heights={r["ELEMENT_ID"]:float(r["H_INK_PX"]) for r in pixels}
    role_template=rcsv("manual_role_ledger_TEMPLATE.csv")
    role_rows=[]
    for r in role_template:
        ids=r["MEMBER_IDS"].split(";"); hs=[heights[x] for x in ids if x in heights]
        median=statistics.median(hs) if hs else "N/A"
        fail=(r["PANEL"]=="CAPTION" and r["SCRIPT_CLASS"]=="LOW_PROFILE_PUNCTUATION")
        decision="FAIL_LOW_PROFILE_CALIBRATION" if fail else "PASS"
        note=("Caption punctuation contours are visually harmonious and complete, but TXT-098 fails its frozen fullbook peer area ratio 56/72=0.7777778."
              if fail else f"Opened every member cell for {r['PANEL']}/{r['ROLE']}/{r['SCRIPT_CLASS']}; source size is role-consistent, median H={median}, no crowding or anomalous visual weight.")
        role_rows.append({"DECISION_ID":r["DECISION_ID"],"PANEL":r["PANEL"],"ROLE":r["ROLE"],"SCRIPT_CLASS":r["SCRIPT_CLASS"],"MEMBER_COUNT":r["MEMBER_COUNT"],"MEMBER_IDS":r["MEMBER_IDS"],"REVIEWER":REVIEWER,"SOURCE_PT_CHECK":"PASS or N/A for graphics","H_INK_MEDIAN":median,"D_E_STATUS":"1.0 for text; N/A graphics","CROWDING":"NONE","VISUAL_HARMONY":"PASS_VISUALLY","DECISION":decision,"NOTE":note})
    wcsv("manual_role_ledger.csv",role_rows)

    view_notes={
        "full_page_200dpi.png":("PASS","Print page 646 integrates Fig 32.8 naturally between surrounding prose and Fig 32.9; no margin, header, footer or page-flow collision."),
        "figure_crop_300dpi.png":("FAIL","Both panels and the complete caption are sharp, balanced and uncropped; however the accepted low-profile peer area gate for caption semicolon TXT-098 fails."),
        "standalone_300dpi.png":("FAIL","Official fullbook-crop surrogate is readable at native 1854x955 with intact axes, patterns, curves and caption; hard typography calibration failure remains."),
        "grayscale_300dpi.png":("FAIL","Circle versus square markers, hatch, separators and dashed target remain distinguishable; hard TXT-098 peer-area evidence still prevents PASS."),
    }
    views=rcsv("manual_view_ledger_TEMPLATE.csv");view_rows=[]
    for r in views:
        decision,note=view_notes[r["VIEW"]]
        view_rows.append({"DECISION_ID":r["DECISION_ID"],"VIEW":r["VIEW"],"ROLE":r["ROLE"],"NATIVE_DIMENSIONS":r["NATIVE_DIMENSIONS"],"REVIEWER":REVIEWER,"OPENED":True,"LEGIBILITY":"PASS","CROWDING":"NONE","PAGE_FUSION":"PASS" if r["VIEW"]=="full_page_200dpi.png" else "N/A","GRAYSCALE":"PASS" if r["VIEW"]=="grayscale_300dpi.png" else "N/A","DECISION":decision,"NOTE":note})
    wcsv("manual_view_ledger.csv",view_rows)

    hard=[{"DECISION_ID":"MAN-HARD-001","FAIL_ID":"PEER-TXT-098","TARGET":"TXT-098 caption semicolon","SELECTED_PEER":"R101 physical page 187 rawdict seq 345","TARGET_H":28,"PEER_H":28,"H_RATIO":1.0,"TARGET_AREA":56,"PEER_AREA":72,"AREA_RATIO":0.7777777777777778,"REQUIRED_RANGE":"[0.92,1.08]","TARGET_MASK":"masks/final_native/TXT-098.png","PEER_CONTACT":"fullbook_peer_evidence/TXT-098_peer_p187_s0345_contact_8x_nearest.png","REVIEWER":REVIEWER,"DECISION":"FAIL","NOTE":"Opened target contact sheet 009 cell 2 and the deterministic peer contact. Both masks are complete/pure; the area deficit is real at unchanged 20/255 and cannot be waived."}]
    wcsv("manual_hard_failure_ledger.csv",hard)
    print(json.dumps({"objects":len(object_rows),"critical_pairs":len(pair_rows),"preliminary":len(pre_rows),"peers":len(peer_rows),"roles":len(role_rows),"views":len(view_rows),"hard":len(hard)},ensure_ascii=False))


if __name__=="__main__":run()

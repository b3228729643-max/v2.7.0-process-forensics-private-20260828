from __future__ import annotations

"""Deterministic replay of the unaccepted first-pass mask algorithm.

This file intentionally preserves the preliminary colour-fit mask and fractional
glyph-bbox behaviour that produced 64 preliminary failures.  It never supplies
the accepted result; its only purpose is before/after provenance.
"""

import csv
import hashlib
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "preliminary_run"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r101_fullbook\main_full.pdf")
PAGE_INDEX = 658
EXPECTED_SHA = "0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing empty CSV {path}")
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def preliminary_colour_mask(rgb: np.ndarray, colors: list[tuple[int, int, int]], min_contrast: int = 20) -> np.ndarray:
    """Exact first-pass algorithm: independent colour fits, no palette ownership."""
    arr = rgb.astype(np.float32)
    q = 255.0 - arr
    contrast = np.max(q, axis=2) >= min_contrast
    out = np.zeros(rgb.shape[:2], dtype=bool)
    for color in colors:
        v = 255.0 - np.array(color, dtype=np.float32)
        alpha = np.sum(q * v[None, None, :], axis=2) / float(np.dot(v, v))
        residual = np.sqrt(np.sum((q - alpha[:, :, None] * v[None, None, :]) ** 2, axis=2))
        out |= contrast & (alpha >= 0.0) & (alpha <= 1.08) & (residual <= 9.0)
    return out


def tight(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    y, x = np.nonzero(mask)
    if not len(x): return None
    return int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1


def gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


def distance(a: np.ndarray, b: np.ndarray) -> float:
    ay, ax = np.nonzero(a); by, bx = np.nonzero(b)
    pa = np.column_stack((ay, ax)); pb = np.column_stack((by, bx))
    if len(pa) > len(pb): pa, pb = pb, pa
    return max(0.0, float(np.min(cKDTree(pb).query(pa, k=1)[0])) - 1.0)


def pre_parent(obj: dict[str, object]) -> str:
    if obj["CLASS"] == "GLYPH" and obj["PANEL"] == "BOTTOM" and obj["ROLE"] == "TICK":
        y0 = float(obj["PDF_BBOX_PT"][1])
        if 398 <= y0 < 413:
            return f"P-BOTTOM-XTICK-{round(float(obj['PDF_BBOX_PT'][0]), 1)}"
    return str(obj["SEMANTIC_PARENT"])


def pre_design(a: dict[str, object], b: dict[str, object]) -> tuple[bool, str]:
    if pre_parent(a) == pre_parent(b):
        if a["CLASS"] == "GLYPH" and b["CLASS"] == "GLYPH":
            return False, "same text parent; overlap remains forbidden"
        return True, "same semantic parent"
    ca, cb = str(a["OBJECT_TYPE"]), str(b["OBJECT_TYPE"])
    pa, pb = str(a["PANEL"]), str(b["PANEL"])
    if pa == pb and {ca, cb} <= {"AXIS_TICK", "LINE_ARROW"}: return True, "axis assembly"
    if pa == pb and {ca, cb} <= {"DATA_CURVE", "MARKER"}: return True, "data assembly"
    if pa == pb and "PATTERN" in {ca, cb} and "GLYPH" not in {ca, cb}: return True, "background pattern"
    if pa == pb and "REFERENCE_LINE" in {ca, cb} and "GLYPH" not in {ca, cb}: return True, "reference line"
    if pa == pb == "TOP" and ({ca, cb} & {"LINE_ARROW"}) and ({ca, cb} & {"DATA_CURVE", "MARKER"}):
        if any("BURNIN-SEPARATOR" in str(n) for n in (a["ELEMENT_ID"], b["ELEMENT_ID"])):
            return True, "burn-in separator"
    return False, ""


def rule(a: dict[str, object], b: dict[str, object]) -> tuple[float, str]:
    if a["CLASS"] == b["CLASS"] == "GLYPH":
        if pre_parent(a) == pre_parent(b): return 0.0, "SAME_TEXT_PARENT_OVERLAP_ONLY"
        return 4.0, "TEXT_TEXT_VECTOR_BBOX"
    if "GLYPH" in {a["CLASS"], b["CLASS"]}: return 3.0, "TEXT_GRAPHIC_RAW_MASK"
    return 0.0, "GRAPHIC_GRAPHIC_OVERLAP_ONLY"


def load_accepted_raw(obj: dict[str, object], shape: tuple[int, int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    x0, y0, x1, y1 = (int(v) for v in obj["RAW_MASK_BBOX_PX"])
    roi = np.array(Image.open(ROOT / str(obj["PRE_NATIVE_MASK"])).convert("L")) > 0
    mask[y0:y1, x0:x1] = roi
    return mask


def save_mask(path: Path, mask: np.ndarray, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    Image.fromarray((mask[y0:y1, x0:x1].astype(np.uint8) * 255), mode="L").save(path)


def run() -> None:
    if (ROOT / "WRITE_SEAL.json").exists(): raise RuntimeError("sealed")
    if sha(PDF) != EXPECTED_SHA: raise RuntimeError("candidate mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = OUT / "before_after"
    evidence.mkdir(parents=True, exist_ok=True)
    objects = json.loads((ROOT / "object_inventory.json").read_text(encoding="utf-8"))
    rgb = np.array(Image.open(ROOT / "figure_crop_300dpi.png").convert("RGB"))
    h, w = rgb.shape[:2]
    old_masks: list[np.ndarray] = []
    for obj in objects:
        x0, y0, x1, y1 = (int(v) for v in obj["PIXEL_SEARCH_BBOX"])
        colors_raw = obj["COLOR_RGB"]
        colors = [tuple(colors_raw)] if colors_raw and isinstance(colors_raw[0], int) else [tuple(c) for c in colors_raw]
        mask = np.zeros((h, w), dtype=bool)
        mask[y0:y1, x0:x1] = preliminary_colour_mask(rgb[y0:y1, x0:x1], colors)
        old_masks.append(mask)
    owner = np.full((h, w), -1, dtype=np.int16)
    for idx in sorted(range(len(objects)), key=lambda i: (int(objects[i]["Z_ORDER"]), i)):
        owner[old_masks[idx]] = idx
    old_final = [old_masks[i] & (owner == i) for i in range(len(objects))]
    accepted_raw = [load_accepted_raw(o, (h, w)) for o in objects]

    with fitz.open(PDF) as doc:
        page = doc[PAGE_INDEX]
        raw = page.get_text("rawdict", sort=False)
        chars = []
        seq = 0
        for block in raw.get("blocks", []):
            if block.get("type") != 0: continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    color_int = int(span.get("color", 0)); color = ((color_int >> 16) & 255, (color_int >> 8) & 255, color_int & 255)
                    for char in span.get("chars", []):
                        chars.append({"seq": seq, "char": char["c"], "bbox": char["bbox"], "font": span.get("font"), "size": span.get("size"), "color": color})
                        seq += 1
    failures: list[dict[str, object]] = []
    peer_detail: dict[str, dict[str, object]] = {}
    for i, obj in enumerate(objects[:112]):
        if obj["SCRIPT_CLASS"] != "LOW_PROFILE_PUNCTUATION": continue
        seq = int(obj["RAWDICT_SEQUENCE"])
        candidates = [c for c in chars if c["seq"] != seq and c["char"] == obj["CHAR"] and c["font"] == obj["FONT"]
                      and c["color"] == tuple(obj["COLOR_RGB"]) and abs(float(c["size"]) - float(obj["PDF_SPAN_SIZE_PT"])) <= 0.25]
        candidates.sort(key=lambda c: (abs(int(c["seq"]) - seq), int(c["seq"])))
        if not candidates:
            row = {"FAIL_ID": f"PEER-{obj['ELEMENT_ID']}", "TYPE": "NO_SAME_PAGE_PEER", "VALUE": 0, "THRESHOLD": 1}
            failures.append(row); peer_detail[row["FAIL_ID"]] = {"candidate": None}; continue
        peer = candidates[0]
        scale = 300 / 72
        bx = tuple(round(float(v) * scale) for v in peer["bbox"])
        bx = (max(0, bx[0]-1), max(0, bx[1]-1), min(2481, bx[2]+1), min(3508, bx[3]+1))
        full = np.array(Image.open(ROOT / "full_page_300dpi.png").convert("RGB"))
        x0, y0, x1, y1 = bx
        pm = preliminary_colour_mask(full[y0:y1, x0:x1], [tuple(peer["color"])])
        pt = tight(pm); tt = tight(old_final[i])
        assert pt is not None and tt is not None
        ph, pa = pt[3] - pt[1], int(pm.sum())
        th, ta = tt[3] - tt[1], int(old_final[i].sum())
        ratios = [th / ph, ta / pa]
        peer_detail[f"PEER-{obj['ELEMENT_ID']}"] = {"candidate": peer, "target_h": th, "target_area": ta, "peer_h": ph, "peer_area": pa, "ratios": ratios}
        if not all(0.92 <= x <= 1.08 for x in ratios):
            failures.append({"FAIL_ID": f"PEER-{obj['ELEMENT_ID']}", "TYPE": "LOW_PROFILE_RATIO", "VALUE": ratios, "THRESHOLD": [0.92, 1.08]})

    pair_detail: dict[str, dict[str, object]] = {}
    for i, a in enumerate(objects):
        at = tight(old_final[i]); assert at is not None
        for j in range(i + 1, len(objects)):
            b = objects[j]; bt = tight(old_final[j]); assert bt is not None
            pair_id = f"PAIR-{i+1:03d}-{j+1:03d}"
            overlap = int((old_masks[i] & old_masks[j]).sum())
            intended, why = pre_design(a, b)
            threshold, rule_name = rule(a, b)
            if rule_name == "TEXT_TEXT_VECTOR_BBOX":
                clearance = gap(tuple(int(v) for v in a["PIXEL_SEARCH_BBOX"]), tuple(int(v) for v in b["PIXEL_SEARCH_BBOX"]))
            else:
                lower = gap(at, bt); clearance = distance(old_final[i], old_final[j]) if lower <= max(12, threshold + 2) else lower
            pair_detail[pair_id] = {"i": i, "j": j, "overlap": overlap, "clearance": clearance, "threshold": threshold, "rule": rule_name, "intended": intended, "reason": why}
            if overlap > 0 and not intended:
                failures.append({"FAIL_ID": pair_id, "TYPE": "ILLEGAL_OVERLAP", "VALUE": overlap, "THRESHOLD": 0})
            elif not intended and threshold > 0 and clearance < threshold:
                failures.append({"FAIL_ID": pair_id, "TYPE": rule_name, "VALUE": clearance, "THRESHOLD": threshold})

    if len(failures) != 64:
        raise RuntimeError(f"preliminary replay mismatch: expected 64, got {len(failures)}")
    current_failures = {x["FAIL_ID"]: x for x in json.loads((ROOT / "hard_failures.json").read_text(encoding="utf-8"))}
    rows: list[dict[str, object]] = []
    thumbnails: list[tuple[str, Image.Image]] = []
    for f in failures:
        fid = str(f["FAIL_ID"]); safe = fid.replace(":", "_")
        if fid.startswith("PAIR-"):
            d = pair_detail[fid]; i, j = int(d["i"]), int(d["j"])
            union = old_masks[i] | old_masks[j] | accepted_raw[i] | accepted_raw[j]
            tb = tight(union); assert tb is not None
            box = (max(0, tb[0]-5), max(0, tb[1]-5), min(w, tb[2]+5), min(h, tb[3]+5))
            paths = {}
            for label, mask in (("A_before", old_masks[i]), ("B_before", old_masks[j]), ("A_after", accepted_raw[i]), ("B_after", accepted_raw[j]),
                                ("intersection_before", old_masks[i] & old_masks[j]), ("intersection_after", accepted_raw[i] & accepted_raw[j])):
                path = evidence / f"{safe}_{label}.png"; save_mask(path, mask, box); paths[label] = str(path.relative_to(ROOT)).replace("\\", "/")
            x0, y0, x1, y1 = box; original = rgb[y0:y1, x0:x1].copy()
            before = original.copy(); before[old_masks[i][y0:y1,x0:x1]] = [255,0,0]; before[old_masks[j][y0:y1,x0:x1]] = [0,80,255]; before[(old_masks[i]&old_masks[j])[y0:y1,x0:x1]]=[255,0,255]
            after = original.copy(); after[accepted_raw[i][y0:y1,x0:x1]]=[255,0,0]; after[accepted_raw[j][y0:y1,x0:x1]]=[0,80,255]; after[(accepted_raw[i]&accepted_raw[j])[y0:y1,x0:x1]]=[255,0,255]
            before_path=evidence/f"{safe}_overlay_before_1x.png"; after_path=evidence/f"{safe}_overlay_after_1x.png"
            Image.fromarray(before).save(before_path); Image.fromarray(after).save(after_path)
            paths["overlay_before"] = str(before_path.relative_to(ROOT)).replace("\\", "/"); paths["overlay_after"] = str(after_path.relative_to(ROOT)).replace("\\", "/")
            accepted_overlap = int((accepted_raw[i]&accepted_raw[j]).sum())
            status = "REMAINS" if fid in current_failures else "RESOLVED"
            reason = "accepted masks assign each >=20/255 pixel to nearest declared colour family and partition only fractional glyph-edge claims"
            if fid == "PAIR-034-035": reason = "raw sequences 306/307 are the two characters of the single x-tick label '15'; same semantic parent plus glyph-edge partition"
            if fid in {"PAIR-117-125", "PAIR-118-125"}: reason = "t=1 path endpoint marker is intentionally centred at x-axis minimum on the y-axis/arrow assembly; accepted pair whitelist, no threshold change"
            rows.append({"PRELIM_FAIL_ID": fid, "TYPE": f["TYPE"], "PRELIM_VALUE": json.dumps(f["VALUE"], ensure_ascii=False), "THRESHOLD": json.dumps(f["THRESHOLD"]),
                         "STATUS_AFTER": status, "A_ID": objects[i]["ELEMENT_ID"], "B_ID": objects[j]["ELEMENT_ID"],
                         "PRELIM_OVERLAP_PX": d["overlap"], "ACCEPTED_OVERLAP_PX": accepted_overlap,
                         "A_FOREIGN_PX_REMOVED": int((old_masks[i]&~accepted_raw[i]).sum()), "B_FOREIGN_PX_REMOVED": int((old_masks[j]&~accepted_raw[j]).sum()),
                         "A_AFTER_NEW_PX": int((accepted_raw[i]&~old_masks[i]).sum()), "B_AFTER_NEW_PX": int((accepted_raw[j]&~old_masks[j]).sum()),
                         "MISSING_STROKE_PX_MANUAL": "PENDING_LEDGER", "FOREIGN_PIXEL_PX_MANUAL": "PENDING_LEDGER",
                         "BBOX_PAINT_ORDER_BASIS": f"A bbox={objects[i]['PIXEL_SEARCH_BBOX']} z={objects[i]['Z_ORDER']}; B bbox={objects[j]['PIXEL_SEARCH_BBOX']} z={objects[j]['Z_ORDER']}",
                         "POLLUTION_SOURCE": f"preliminary cross-claim with {objects[j]['ELEMENT_ID']} / {objects[i]['ELEMENT_ID']}", "REASON": reason,
                         "THRESHOLD_POLICY": "unchanged 20/255 and unchanged hard clearance/overlap gates", **paths})
            nav = Image.new("RGB", (before.shape[1]+after.shape[1]+8, max(before.shape[0],after.shape[0])), "white"); nav.paste(Image.fromarray(before),(0,0)); nav.paste(Image.fromarray(after),(before.shape[1]+8,0)); thumbnails.append((fid,nav))
        else:
            element_id = fid.removeprefix("PEER-"); i = next(k for k,o in enumerate(objects) if o["ELEMENT_ID"] == element_id)
            union = old_masks[i] | accepted_raw[i]; tb=tight(union); assert tb is not None
            box=(max(0,tb[0]-5),max(0,tb[1]-5),min(w,tb[2]+5),min(h,tb[3]+5))
            bp=evidence/f"{safe}_target_before.png"; ap=evidence/f"{safe}_target_after.png"; save_mask(bp,old_masks[i],box); save_mask(ap,accepted_raw[i],box)
            status="REMAINS" if fid in current_failures else "RESOLVED"
            rows.append({"PRELIM_FAIL_ID":fid,"TYPE":f["TYPE"],"PRELIM_VALUE":json.dumps(f["VALUE"],ensure_ascii=False),"THRESHOLD":json.dumps(f["THRESHOLD"]),
                         "STATUS_AFTER":status,"A_ID":element_id,"B_ID":"SAME_PAGE_EXACT_METADATA_PEER","PRELIM_OVERLAP_PX":"N/A","ACCEPTED_OVERLAP_PX":"N/A",
                         "A_FOREIGN_PX_REMOVED":int((old_masks[i]&~accepted_raw[i]).sum()),"B_FOREIGN_PX_REMOVED":"N/A","A_AFTER_NEW_PX":int((accepted_raw[i]&~old_masks[i]).sum()),"B_AFTER_NEW_PX":"N/A",
                         "MISSING_STROKE_PX_MANUAL":"PENDING_LEDGER","FOREIGN_PIXEL_PX_MANUAL":"PENDING_LEDGER","BBOX_PAINT_ORDER_BASIS":f"target bbox={objects[i]['PIXEL_SEARCH_BBOX']} z={objects[i]['Z_ORDER']}",
                         "POLLUTION_SOURCE":"preliminary non-exclusive colour-family fit inside target bbox","REASON":"deterministic same-page exact-metadata peer rule retained; accepted target mask uses exclusive colour ownership; absent peer remains FAIL",
                         "THRESHOLD_POLICY":"unchanged 20/255; peer ratios remain [0.92,1.08]; no different glyph/size substituted","A_before":str(bp.relative_to(ROOT)).replace("\\","/"),"A_after":str(ap.relative_to(ROOT)).replace("\\","/")})
            x0,y0,x1,y1=box; ori=rgb[y0:y1,x0:x1]; thumbnails.append((fid,Image.fromarray(ori)))

    write_csv(OUT / "preliminary_64_failures.csv", rows)
    write_json(OUT / "preliminary_64_failures.json", rows)
    write_json(OUT / "preliminary_failure_raw_values.json", failures)
    semantics = {"label":"15", "pdf_rawdict_sequences":[306,307], "element_ids":["TXT-034","TXT-035"], "character_conservation":"2 rawdict CHAR = 2 glyph objects; no addition/drop", "semantic_basis":"one naturally typeset x-axis tick label at a shared baseline and adjacent bbox", "accepted_parent":"P-BOTTOM-XTICK-15"}
    write_json(OUT / "tick_15_semantic_conservation.json", semantics)
    nav_dir=OUT/"navigation_contact_sheets"; nav_dir.mkdir(exist_ok=True)
    for sn,start in enumerate(range(0,len(thumbnails),8),1):
        subset=thumbnails[start:start+8]; cell_w=900; cell_h=260
        canvas=Image.new("RGB",(cell_w*2,cell_h*4),"white"); pen=ImageDraw.Draw(canvas)
        for cn,(fid,im) in enumerate(subset):
            x=(cn%2)*cell_w; y=(cn//2)*cell_h; pen.text((x+4,y+4),f"{fid}: BEFORE | AFTER (navigation; native assets in ledger)",fill="black")
            thumb=im.copy(); thumb.thumbnail((cell_w-8,cell_h-28),Image.Resampling.NEAREST); canvas.paste(thumb,(x+4,y+24))
        canvas.save(nav_dir/f"preliminary_navigation_{sn:02d}.png")
    identity={"classification":"PRELIMINARY_NOT_ACCEPTED","fixed_command":"python -X utf8 preliminary_algorithm_v1_replay.py","pdf":str(PDF),"pdf_sha256":sha(PDF),
              "pdf_bytes":PDF.stat().st_size,"physical_page_1based":659,"object_inventory_input":str(ROOT/'object_inventory.json'),"object_inventory_sha256":sha(ROOT/'object_inventory.json'),
              "replay_script":str(Path(__file__).resolve()),"replay_script_sha256":sha(Path(__file__).resolve()),"preliminary_failure_count":len(failures),"accepted_threshold_change":False,
              "note":"deterministic replay of the first algorithm; never an accepted result"}
    write_json(OUT / "preliminary_replay_identity.json",identity)
    print(json.dumps({"preliminary_failures":len(failures),"resolved":sum(r["STATUS_AFTER"]=="RESOLVED" for r in rows),"remains":sum(r["STATUS_AFTER"]=="REMAINS" for r in rows)},ensure_ascii=False))


if __name__ == "__main__":
    run()

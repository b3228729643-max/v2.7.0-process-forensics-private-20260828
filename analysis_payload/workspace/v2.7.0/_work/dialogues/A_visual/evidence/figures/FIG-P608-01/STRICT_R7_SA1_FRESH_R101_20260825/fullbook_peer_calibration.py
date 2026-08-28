from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw

import audit_pipeline as ap


ROOT = Path(__file__).resolve().parent
PDF = ap.PDF
TARGET_IDS = ["TXT-072", "TXT-098"]
POLICY = ROOT / "FULLBOOK_PEER_SELECTION_POLICY.json"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields: fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def tight(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    y, x = np.nonzero(mask)
    if not len(x): return None
    return int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1


def scan() -> None:
    if (ROOT / "WRITE_SEAL.json").exists(): raise RuntimeError("sealed")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if not policy.get("frozen_before_fullbook_scan"): raise RuntimeError("selection policy not frozen")
    objects = json.loads((ROOT / "object_inventory.json").read_text(encoding="utf-8"))
    target_by_id = {x["ELEMENT_ID"]: x for x in objects if x["ELEMENT_ID"] in TARGET_IDS}
    candidates: dict[str, list[dict[str, object]]] = {x: [] for x in TARGET_IDS}
    with fitz.open(PDF) as doc:
        for page_index in range(doc.page_count):
            raw = doc[page_index].get_text("rawdict", sort=False)
            seq = 0
            for bi, block in enumerate(raw.get("blocks", [])):
                if block.get("type") != 0: continue
                for li, line in enumerate(block.get("lines", [])):
                    for si, span in enumerate(line.get("spans", [])):
                        value = int(span.get("color", 0)); color = [(value >> 16) & 255, (value >> 8) & 255, value & 255]
                        for ci, char in enumerate(span.get("chars", [])):
                            for target_id, target in target_by_id.items():
                                if char.get("c") != target["CHAR"]: continue
                                if str(span.get("font", "")) != target["FONT"]: continue
                                if color != target["COLOR_RGB"]: continue
                                delta = abs(float(span.get("size", 0.0)) - float(target["PDF_SPAN_SIZE_PT"]))
                                if delta > 0.25: continue
                                if page_index == ap.PAGE_INDEX and seq == int(target["RAWDICT_SEQUENCE"]): continue
                                same_page = page_index == ap.PAGE_INDEX
                                rank = [0, abs(seq - int(target["RAWDICT_SEQUENCE"])), seq, bi, li, si, ci] if same_page else [1, page_index + 1, seq, bi, li, si, ci]
                                candidates[target_id].append({
                                    "TARGET_ID": target_id, "PHYSICAL_PAGE_1BASED": page_index + 1,
                                    "RAWDICT_SEQUENCE": seq, "BLOCK": bi, "LINE": li, "SPAN": si, "CHAR_INDEX": ci,
                                    "CHAR": char.get("c"), "FONT": span.get("font"), "PDF_SPAN_SIZE_PT": float(span.get("size", 0.0)),
                                    "TARGET_SIZE_PT": float(target["PDF_SPAN_SIZE_PT"]), "SIZE_DELTA_PT": delta,
                                    "COLOR_RGB": color, "PDF_BBOX_PT": [float(v) for v in char["bbox"]], "RANK": rank,
                                })
                            seq += 1
    flat = []
    for target_id in TARGET_IDS:
        candidates[target_id].sort(key=lambda x: tuple(x["RANK"]))
        for rank_no, row in enumerate(candidates[target_id], 1):
            row["DETERMINISTIC_RANK_NUMBER"] = rank_no
            row["SELECTED"] = rank_no == 1
            flat.append(row)
    if not flat: raise RuntimeError("fullbook exact-metadata candidate set is empty for every target")
    write_json(ROOT / "fullbook_peer_candidates.json", {"policy": policy, "targets": candidates})
    write_csv(ROOT / "fullbook_peer_candidates.csv", flat)

    output = ROOT / "fullbook_peer_evidence"; output.mkdir(exist_ok=True)
    calibration_rows = []
    hard = [x for x in json.loads((ROOT / "hard_failures.json").read_text(encoding="utf-8")) if x["FAIL_ID"] not in {f"PEER-{x}" for x in TARGET_IDS}]
    with fitz.open(PDF) as doc:
        for target_id in TARGET_IDS:
            target = target_by_id[target_id]
            pool = candidates[target_id]
            if not pool:
                hard.append({"FAIL_ID": f"PEER-{target_id}", "TYPE": "NO_FULLBOOK_EXACT_METADATA_PEER", "VALUE": 0, "THRESHOLD": 1})
                calibration_rows.append({"ELEMENT_ID": target_id, "DECISION": "FAIL", "NOTE": "all-R101 exact-metadata candidate set empty"})
                continue
            selected = pool[0]
            bbox = fitz.Rect(selected["PDF_BBOX_PT"])
            # The calibration raw mask is rendered from the exact rawdict CHAR bbox.
            # Context padding is prohibited here because it can admit an adjacent same-colour glyph.
            pix = doc[int(selected["PHYSICAL_PAGE_1BASED"])-1].get_pixmap(dpi=300, clip=bbox, alpha=False, annots=False)
            peer_rgb = np.array(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
            peer_mask = ap.exclusive_color_mask(peer_rgb, [tuple(selected["COLOR_RGB"])])
            box = tight(peer_mask)
            target_box = target["FINAL_MASK_BBOX_PX"]
            target_h = int(target_box[3]) - int(target_box[1])
            target_area = int(target["FINAL_PIXEL_COUNT"])
            if box is None:
                peer_h = peer_area = 0; h_ratio = area_ratio = 0.0; decision = "FAIL"
                hard.append({"FAIL_ID": f"PEER-{target_id}", "TYPE": "EMPTY_SELECTED_FULLBOOK_PEER_MASK", "VALUE": 0, "THRESHOLD": 1})
            else:
                peer_h = box[3] - box[1]; peer_area = int(peer_mask.sum())
                h_ratio = target_h / peer_h; area_ratio = target_area / peer_area
                decision = "PASS" if 0.92 <= h_ratio <= 1.08 and 0.92 <= area_ratio <= 1.08 else "FAIL"
                if decision == "FAIL": hard.append({"FAIL_ID": f"PEER-{target_id}", "TYPE": "FULLBOOK_LOW_PROFILE_RATIO", "VALUE": [h_ratio, area_ratio], "THRESHOLD": [0.92, 1.08]})
            stem = output / f"{target_id}_peer_p{int(selected['PHYSICAL_PAGE_1BASED']):03d}_s{int(selected['RAWDICT_SEQUENCE']):04d}"
            Image.fromarray(peer_rgb).save(str(stem)+"_original_1x.png")
            overlay = peer_rgb.copy(); overlay[peer_mask] = [255,0,0]
            Image.fromarray(overlay).save(str(stem)+"_overlay_1x.png")
            Image.fromarray((peer_mask.astype(np.uint8)*255),mode="L").save(str(stem)+"_mask_native.png")
            ori=Image.fromarray(peer_rgb).resize((pix.width*8,pix.height*8),Image.Resampling.NEAREST)
            over=Image.fromarray(overlay).resize(ori.size,Image.Resampling.NEAREST)
            only_arr=np.zeros_like(peer_rgb); only_arr[peer_mask]=[255,255,255]
            only=Image.fromarray(only_arr).resize(ori.size,Image.Resampling.NEAREST)
            contact=Image.new("RGB",(ori.width+over.width+only.width+16,max(ori.height,over.height,only.height)+30),"white")
            pen=ImageDraw.Draw(contact); pen.text((4,4),f"{target_id} fullbook peer | ORIGINAL / OVERLAY / MASK ONLY",fill="black")
            vx=4
            for im in (ori,over,only): contact.paste(im,(vx,26)); vx += im.width+4
            contact.save(str(stem)+"_contact_8x_nearest.png")
            calibration_rows.append({
                "ELEMENT_ID":target_id,"CHAR":target["CHAR"],"SELECTION_POLICY_ID":"LP-PEER-R101-EXACTMETA-V1",
                "FULLBOOK_EXACT_CANDIDATE_COUNT":len(pool),"SELECTED_PAGE":selected["PHYSICAL_PAGE_1BASED"],"SELECTED_RAW_SEQUENCE":selected["RAWDICT_SEQUENCE"],
                "SELECTED_FONT":selected["FONT"],"SELECTED_SIZE_PT":selected["PDF_SPAN_SIZE_PT"],"SIZE_DELTA_PT":selected["SIZE_DELTA_PT"],"SELECTED_COLOR_RGB":selected["COLOR_RGB"],
                "TARGET_H_INK":target_h,"PEER_H_INK":peer_h,"H_RATIO":h_ratio,"TARGET_AREA":target_area,"PEER_AREA":peer_area,"AREA_RATIO":area_ratio,
                "MASK_COMPLETENESS_MACHINE":"NONEMPTY_EXACT_BBOX_COLOR_OWNERSHIP" if box is not None else "EMPTY",
                "MASK_PURITY_MANUAL":"PENDING_LEDGER","PEER_CONTACT":str(Path(str(stem)+"_contact_8x_nearest.png").relative_to(ROOT)).replace("\\","/"),"DECISION":decision,
            })
    write_csv(ROOT / "fullbook_peer_calibration.csv", calibration_rows)
    old_rows = [r for r in read_csv(ROOT / "low_profile_peer_calibration.csv") if r.get("ELEMENT_ID") not in TARGET_IDS]
    write_csv(ROOT / "low_profile_peer_calibration.csv", old_rows + calibration_rows)
    pixels = read_csv(ROOT / "after_pixel_measurements.csv")
    dec = {r["ELEMENT_ID"]: r["DECISION"] for r in calibration_rows}
    for row in pixels:
        if row["ELEMENT_ID"] in dec: row["DECISION"] = dec[row["ELEMENT_ID"]]
    write_csv(ROOT / "after_pixel_measurements.csv", pixels)
    write_json(ROOT / "hard_failures.json", hard)
    summary = json.loads((ROOT / "denominator_and_pair_summary.json").read_text(encoding="utf-8"))
    summary["fullbook_peer_policy"] = "LP-PEER-R101-EXACTMETA-V1"
    summary["hard_failure_count"] = len(hard); summary["hard_failures"] = hard
    summary["outcome"] = "FAIL_TO_SA2" if hard else "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3"
    write_json(ROOT / "denominator_and_pair_summary.json", summary)
    print(json.dumps({"candidate_counts":{x:len(candidates[x]) for x in TARGET_IDS},"calibration":calibration_rows,"hard_failures":hard,"outcome":summary["outcome"]},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    scan()

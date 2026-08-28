from __future__ import annotations

import csv
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R5_SA3_FRESH_ISOLATED_R112_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r112_fullbook\main_full.pdf")
PAGE_INDEX0 = 68
PHYSICAL_PAGE1 = 69
DPI = 300
SCALE = DPI / 72.0
FIGURE_CLIP_PT = fitz.Rect(100.0, 64.0, 485.0, 220.0)
STANDALONE_CLIP_PT = fitz.Rect(100.0, 64.0, 485.0, 200.0)


def ensure_dirs() -> None:
    for name in ("views", "roi_1x", "roi_8x", "masks", "contact_sheets", "machine"):
        (ROOT / name).mkdir(parents=True, exist_ok=True)


def pix_to_pil(pix: fitz.Pixmap) -> Image.Image:
    mode = "RGBA" if pix.alpha else "RGB"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples).convert("RGB")


def render_clip(page: fitz.Page, clip: fitz.Rect, dpi: int = 300) -> Image.Image:
    return pix_to_pil(page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), clip=clip, alpha=False))


def rect_to_crop_px(rect: fitz.Rect, clip: fitz.Rect, pad: int = 0) -> tuple[int, int, int, int]:
    x0 = math.floor((rect.x0 - clip.x0) * SCALE) - pad
    y0 = math.floor((rect.y0 - clip.y0) * SCALE) - pad
    x1 = math.ceil((rect.x1 - clip.x0) * SCALE) + pad
    y1 = math.ceil((rect.y1 - clip.y0) * SCALE) + pad
    return x0, y0, x1, y1


def intersect_rect(a: fitz.Rect, b: fitz.Rect) -> bool:
    return a.x1 > b.x0 and a.x0 < b.x1 and a.y1 > b.y0 and a.y0 < b.y1


def semantic_parent(x: float, y: float, ch: str) -> tuple[str, str, str]:
    if y >= 200:
        return "CAPTION", "caption", "caption"
    if y < 132:
        if x < 145:
            return "CDF_AXIS", "axis_text", "upper"
        if x < 380 and 72 <= y <= 95 and ch not in "0123456789":
            return "CDF_NOTE_RIGHT_CONTINUOUS", "annotation", "upper"
        if ch in "𝑝1234" and y > 80:
            return "CDF_MASS_LABELS", "formula", "upper"
        return "CDF_PANEL", "axis_text", "upper"
    if y < 200:
        if x < 150:
            return "PMF_AXIS", "axis_text", "lower"
        if x > 390 and y < 155:
            return "PMF_NOTE_JUMP", "annotation", "lower"
        if y > 180:
            return "PMF_X_LABEL", "axis_title", "lower"
        return "PMF_PANEL", "axis_text", "lower"
    return "FIGURE", "other", "figure"


def char_category(ch: str, parent: str) -> str:
    cp = ord(ch)
    if ch.isspace():
        return "SPACE"
    if 0x4E00 <= cp <= 0x9FFF or ch in "：，。图":
        return "CJK_OR_FULLWIDTH"
    if ch in ".,;:":
        return "LOW_PROFILE_PUNCTUATION"
    if ch in "+=−":
        return "MATH_OPERATOR"
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return "LATIN_CAP_OR_DIGIT"
    if 0x1D400 <= cp <= 0x1D7FF or ("a" <= ch <= "z"):
        return "LATIN_GREEK_LOWER_OR_MATH"
    return "OTHER_VISIBLE"


def pdf_color_to_rgb(value: int) -> tuple[int, int, int]:
    return (value >> 16) & 255, (value >> 8) & 255, value & 255


def target_color_mask(
    roi: Image.Image,
    target_rgb: tuple[int, int, int],
    exact_bbox_in_roi: tuple[int, int, int, int],
    threshold: int = 20,
) -> Image.Image:
    """Separate one PDF text color inside the exact character bbox.

    A rendered antialias pixel is modeled as a convex blend of the span color and
    white page background.  This rejects differently colored axes/guides/curves
    even when they pass through the padded reviewer ROI.
    """
    rgb = roi.convert("RGB")
    out = Image.new("L", rgb.size, 0)
    src = rgb.load()
    dst = out.load()
    bx0, by0, bx1, by1 = exact_bbox_in_roi
    bx0=max(0,bx0); by0=max(0,by0); bx1=min(rgb.width,bx1); by1=min(rgb.height,by1)
    for y in range(by0, by1):
        for x in range(bx0, bx1):
            pixel = src[x, y]
            if 255 - min(pixel) < threshold:
                continue
            alphas=[]
            for pv,tv in zip(pixel,target_rgb):
                if tv < 250:
                    alphas.append((255-pv)/(255-tv))
            if not alphas:
                continue
            if max(alphas)-min(alphas) > 0.028:
                continue
            alpha=sorted(alphas)[len(alphas)//2]
            if alpha <= 0.04 or alpha > 1.12:
                continue
            expected=tuple(round(255*(1-alpha)+tv*alpha) for tv in target_rgb)
            if max(abs(pv-ev) for pv,ev in zip(pixel,expected)) <= 7:
                dst[x,y]=255
    return out


def tight_bbox(mask: Image.Image) -> tuple[int, int, int, int] | None:
    return mask.getbbox()


def mask_stats(mask: Image.Image) -> tuple[int, int, int]:
    box = tight_bbox(mask)
    if box is None:
        return 0, 0, 0
    area = sum(1 for p in mask.getdata() if p)
    return box[3] - box[1], box[2] - box[0], area


def make_contact_cell(roi: Image.Image, mask: Image.Image, label: str) -> Image.Image:
    overlay = roi.convert("RGB").copy()
    red = Image.new("RGB", roi.size, (235, 40, 40))
    overlay.paste(red, mask=mask)
    mask_rgb = Image.new("RGB", roi.size, "white")
    mask_rgb.paste(Image.new("RGB", roi.size, "black"), mask=mask)
    scale = 8
    panels = [roi, overlay, mask_rgb]
    enlarged = [p.resize((p.width * scale, p.height * scale), Image.Resampling.NEAREST) for p in panels]
    label_h = 34
    width = sum(p.width for p in enlarged) + 24
    height = max(p.height for p in enlarged) + label_h + 8
    cell = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(cell)
    draw.text((4, 4), label, fill="black")
    x = 4
    for title, panel in zip(("ORIGINAL", "TARGET", "MASK"), enlarged):
        cell.paste(panel, (x, label_h))
        draw.text((x, label_h - 14), title, fill="black")
        x += panel.width + 8
    return cell


def make_graphic_contact_cell(roi: Image.Image, mask: Image.Image, label: str) -> Image.Image:
    """Show three native 48px samples so long axes remain reviewer-openable."""
    box=mask.getbbox() or (0,0,roi.width,roi.height)
    x0,y0,x1,y1=box
    if (x1-x0) >= (y1-y0):
        centers=[(x0,(y0+y1)//2),((x0+x1)//2,(y0+y1)//2),(max(x0,x1-1),(y0+y1)//2)]
    else:
        centers=[((x0+x1)//2,y0),((x0+x1)//2,(y0+y1)//2),((x0+x1)//2,max(y0,y1-1))]
    samples=[]
    for idx,(cx,cy) in enumerate(centers,1):
        sx0=max(0,min(roi.width-48,cx-24)); sy0=max(0,min(roi.height-48,cy-24))
        sx1=min(roi.width,sx0+48); sy1=min(roi.height,sy0+48)
        sample_roi=roi.crop((sx0,sy0,sx1,sy1))
        sample_mask=mask.crop((sx0,sy0,sx1,sy1))
        samples.append(make_contact_cell(sample_roi,sample_mask,f"{label} SAMPLE-{idx} native[{sx0},{sy0},{sx1},{sy1}]"))
    width=sum(s.width for s in samples)+16
    height=max(s.height for s in samples)+8
    out=Image.new("RGB",(width,height),"white")
    x=4
    for sample in samples:
        out.paste(sample,(x,4)); x+=sample.width+4
    return out


def drawing_mask(page: fitz.Page, drawing: dict, page_rect: fitz.Rect) -> Image.Image:
    doc = fitz.open()
    p = doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = p.new_shape()
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            shape.draw_line(item[1], item[2])
        elif op == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            shape.draw_rect(item[1])
        elif op == "qu":
            shape.draw_quad(item[1])
        else:
            raise RuntimeError(f"Unsupported drawing operator: {op}")
    stroke = drawing.get("color")
    fill = drawing.get("fill")
    stroke_is_visible = stroke is not None and min(stroke) < 0.92
    fill_is_visible = fill is not None and min(fill) < 0.92
    shape.finish(
        color=(0, 0, 0) if stroke_is_visible else None,
        fill=(0, 0, 0) if fill_is_visible else None,
        width=max(float(drawing.get("width") or 0.5), 0.15),
        dashes=drawing.get("dashes") or None,
        closePath=bool(drawing.get("closePath")),
        lineCap=max(drawing.get("lineCap") or (0,)),
        lineJoin=float(drawing.get("lineJoin") or 0),
        fill_opacity=1,
        stroke_opacity=1,
    )
    shape.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=FIGURE_CLIP_PT, colorspace=fitz.csGRAY, alpha=False)
    img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    mask = Image.eval(img, lambda v: 255 if v < 235 else 0)
    doc.close()
    return mask


def main() -> None:
    ensure_dirs()
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX0]
    if page.rect.width < FIGURE_CLIP_PT.x1 or page.rect.height < FIGURE_CLIP_PT.y1:
        raise RuntimeError("Figure clip is outside the official page")

    full300 = pix_to_pil(page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False))
    full200 = pix_to_pil(page.get_pixmap(matrix=fitz.Matrix(200 / 72.0, 200 / 72.0), alpha=False))
    crop300 = render_clip(page, FIGURE_CLIP_PT, 300)
    standalone300 = render_clip(page, STANDALONE_CLIP_PT, 300)
    full300.save(ROOT / "views" / "full_page_300dpi.png")
    full200.save(ROOT / "views" / "full_page_200dpi.png")
    crop300.save(ROOT / "views" / "figure_crop_300dpi.png")
    standalone300.save(ROOT / "views" / "standalone_300dpi.png")
    crop300.convert("L").save(ROOT / "views" / "grayscale_300dpi.png")

    raw = page.get_text("rawdict")
    chars = []
    element_rows = []
    safe_map = []
    char_index = 0
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    ch = char["c"]
                    rect = fitz.Rect(char["bbox"])
                    if ch.isspace() or not intersect_rect(rect, FIGURE_CLIP_PT):
                        continue
                    char_index += 1
                    eid = f"TXT-{char_index:03d}"
                    safe = f"txt_{char_index:03d}"
                    parent, role, panel = semantic_parent(rect.x0, rect.y0, ch)
                    ex0, ey0, ex1, ey1 = rect_to_crop_px(rect, FIGURE_CLIP_PT, pad=0)
                    x0, y0, x1, y1 = rect_to_crop_px(rect, FIGURE_CLIP_PT, pad=3)
                    x0 = max(0, x0); y0 = max(0, y0)
                    x1 = min(crop300.width, x1); y1 = min(crop300.height, y1)
                    roi = crop300.crop((x0, y0, x1, y1))
                    target_rgb=pdf_color_to_rgb(int(span.get("color") or 0))
                    mask = target_color_mask(
                        roi,
                        target_rgb,
                        (ex0-x0,ey0-y0,ex1-x0,ey1-y0),
                    )
                    h, w, area = mask_stats(mask)
                    roi_path = ROOT / "roi_1x" / f"{safe}_original.png"
                    mask_path = ROOT / "masks" / f"{safe}_mask.png"
                    roi8_path = ROOT / "roi_8x" / f"{safe}_nearest8x.png"
                    roi.save(roi_path)
                    mask.save(mask_path)
                    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(roi8_path)
                    row = {
                        "element_id": eid,
                        "safe_filename": safe,
                        "kind": "TEXT_GLYPH",
                        "char": ch,
                        "char_uplus": f"U+{ord(ch):04X}",
                        "parent": parent,
                        "role": role,
                        "panel": panel,
                        "category": char_category(ch, parent),
                        "bbox_pt": [round(v, 4) for v in rect],
                        "bbox_crop_px": [x0, y0, x1, y1],
                        "font": span.get("font"),
                        "size_pt": round(float(span.get("size") or 0), 4),
                        "color": int(span.get("color") or 0),
                        "target_rgb": list(target_rgb),
                        "ink_height_px": h,
                        "ink_width_px": w,
                        "ink_area_px": area,
                        "mask_empty": area == 0,
                        "roi_1x": str(roi_path.relative_to(ROOT)).replace("\\", "/"),
                        "roi_8x": str(roi8_path.relative_to(ROOT)).replace("\\", "/"),
                        "mask": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
                    }
                    chars.append((row, roi, mask))
                    element_rows.append(row)
                    safe_map.append({"element_id": eid, "safe_filename": safe})

    drawings_raw = [d for d in page.get_drawings() if intersect_rect(d["rect"], FIGURE_CLIP_PT)]
    drawing_json = []
    graphic_index = 0
    graphic_masks: dict[str, Image.Image] = {}
    for drawing in drawings_raw:
        stroke = drawing.get("color")
        fill = drawing.get("fill")
        visible_stroke = stroke is not None and min(stroke) < 0.92
        visible_fill = fill is not None and min(fill) < 0.92
        if not (visible_stroke or visible_fill):
            drawing_json.append({"seqno": drawing["seqno"], "classification": "OPAQUE_LIGHT_BACKGROUND", "bbox_pt": list(drawing["rect"])})
            continue
        graphic_index += 1
        eid = f"GFX-{graphic_index:03d}"
        safe = f"gfx_{graphic_index:03d}"
        mask_full = drawing_mask(page, drawing, page.rect)
        box = mask_full.getbbox()
        area = sum(1 for p in mask_full.getdata() if p)
        rect = fitz.Rect(drawing["rect"])
        x0, y0, x1, y1 = rect_to_crop_px(rect, FIGURE_CLIP_PT, pad=5)
        x0=max(0,x0); y0=max(0,y0); x1=min(crop300.width,x1); y1=min(crop300.height,y1)
        roi = crop300.crop((x0,y0,x1,y1))
        local_mask = mask_full.crop((x0,y0,x1,y1))
        roi_path = ROOT / "roi_1x" / f"{safe}_original.png"
        mask_path = ROOT / "masks" / f"{safe}_mask.png"
        roi8_path = ROOT / "roi_8x" / f"{safe}_nearest8x.png"
        roi.save(roi_path)
        local_mask.save(mask_path)
        roi.resize((roi.width*8,roi.height*8), Image.Resampling.NEAREST).save(roi8_path)
        if rect.y1 < 132:
            panel = "upper"
        elif rect.y0 > 130 and rect.y1 < 200:
            panel = "lower"
        else:
            panel = "cross_or_caption"
        row = {
            "element_id": eid,
            "safe_filename": safe,
            "kind": "GRAPHIC_PATH",
            "char": "",
            "char_uplus": "",
            "parent": f"DRAWING_SEQNO_{drawing['seqno']}",
            "role": "vector_foreground",
            "panel": panel,
            "category": "GRAPHIC_PATH",
            "bbox_pt": [round(v,4) for v in rect],
            "bbox_crop_px": [x0,y0,x1,y1],
            "font": "",
            "size_pt": "",
            "color": str(stroke or fill),
            "ink_height_px": 0 if box is None else box[3]-box[1],
            "ink_width_px": 0 if box is None else box[2]-box[0],
            "ink_area_px": area,
            "mask_empty": area == 0,
            "roi_1x": str(roi_path.relative_to(ROOT)).replace("\\", "/"),
            "roi_8x": str(roi8_path.relative_to(ROOT)).replace("\\", "/"),
            "mask": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
        }
        element_rows.append(row)
        graphic_masks[eid] = mask_full
        safe_map.append({"element_id":eid,"safe_filename":safe})
        drawing_json.append({
            "element_id": eid,
            "seqno": drawing["seqno"],
            "type": drawing["type"],
            "bbox_pt": [round(v,4) for v in rect],
            "stroke": stroke,
            "fill": fill,
            "width_pt": drawing.get("width"),
            "dashes": drawing.get("dashes"),
            "closePath": drawing.get("closePath"),
            "item_count": len(drawing["items"]),
        })

    # Whole-figure text bbox overlay for reviewer navigation.
    overlay = crop300.copy()
    od = ImageDraw.Draw(overlay)
    for row in element_rows:
        x0,y0,x1,y1 = row["bbox_crop_px"]
        color = (220,30,30) if row["kind"] == "TEXT_GLYPH" else (20,110,220)
        od.rectangle((x0,y0,x1-1,y1-1), outline=color, width=1)
        od.text((x0,max(0,y0-10)),row["element_id"],fill=color)
    overlay.save(ROOT / "views" / "after_text_measurement_overlay_300dpi.png")

    # Contact sheets contain 12 reviewer cells each.  Manual decisions are not generated here.
    cells = [make_contact_cell(roi, mask, f"{row['element_id']} {row['char']} {row['char_uplus']}") for row,roi,mask in chars]
    contact_paths=[]
    for sheet_no in range(math.ceil(len(cells)/12)):
        subset=cells[sheet_no*12:(sheet_no+1)*12]
        w=max(c.width for c in subset)+16
        h=sum(c.height for c in subset)+16+8*(len(subset)-1)
        sheet=Image.new("RGB",(w,h),"white")
        y=8
        for c in subset:
            sheet.paste(c,(8,y)); y+=c.height+8
        path=ROOT/"contact_sheets"/f"text_contact_sheet_{sheet_no+1:02d}.png"
        sheet.save(path)
        contact_paths.append(str(path.relative_to(ROOT)).replace("\\","/"))

    # Graphic contact sheets.
    graphic_cells=[]
    for row in [r for r in element_rows if r["kind"]=="GRAPHIC_PATH"]:
        roi=Image.open(ROOT/row["roi_1x"]).convert("RGB")
        mask=Image.open(ROOT/row["mask"]).convert("L")
        graphic_cells.append(make_graphic_contact_cell(roi,mask,f"{row['element_id']} {row['parent']}"))
    graphic_contact_paths=[]
    for sheet_no in range(math.ceil(len(graphic_cells)/4)):
        subset=graphic_cells[sheet_no*4:(sheet_no+1)*4]
        w=max(c.width for c in subset)+16
        h=sum(c.height for c in subset)+16+8*(len(subset)-1)
        sheet=Image.new("RGB",(w,h),"white")
        y=8
        for c in subset:
            sheet.paste(c,(8,y)); y+=c.height+8
        path=ROOT/"contact_sheets"/f"graphic_contact_sheet_{sheet_no+1:02d}.png"
        sheet.save(path)
        graphic_contact_paths.append(str(path.relative_to(ROOT)).replace("\\","/"))

    # Freeze all unordered relationships exactly once at the visible-element level.
    pairs=[]
    for pair_index,(a,b) in enumerate(itertools.combinations(element_rows,2),1):
        ar=fitz.Rect(a["bbox_pt"]); br=fitz.Rect(b["bbox_pt"])
        dx=max(br.x0-ar.x1, ar.x0-br.x1, 0)
        dy=max(br.y0-ar.y1, ar.y0-br.y1, 0)
        clearance_pt=math.hypot(dx,dy)
        same_parent=a["parent"]==b["parent"]
        pair_class="DESIGN_INTERNAL_SAME_PARENT" if same_parent else f"{a['kind']}--{b['kind']}"
        pairs.append({
            "pair_id":f"PAIR-{pair_index:05d}",
            "element_a":a["element_id"],
            "element_b":b["element_id"],
            "pair_class":pair_class,
            "same_semantic_parent":same_parent,
            "bbox_intersects":intersect_rect(ar,br),
            "bbox_clearance_pt":round(clearance_pt,4),
            "bbox_clearance_px":round(clearance_pt*SCALE,2),
        })

    fields=list(element_rows[0].keys())
    with (ROOT/"machine"/"visible_elements.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(element_rows)
    with (ROOT/"machine"/"all_unordered_pairs.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0].keys())); w.writeheader(); w.writerows(pairs)
    (ROOT/"machine"/"visible_elements.json").write_text(json.dumps(element_rows,ensure_ascii=False,indent=2),encoding="utf-8")
    (ROOT/"machine"/"all_unordered_pairs.json").write_text(json.dumps(pairs,ensure_ascii=False,indent=2),encoding="utf-8")
    (ROOT/"machine"/"id_safe_filename_map.json").write_text(json.dumps(safe_map,ensure_ascii=False,indent=2),encoding="utf-8")
    (ROOT/"machine"/"drawing_inventory.json").write_text(json.dumps(drawing_json,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    identity={
        "handoff_id":"A-R112-P067-SA3-FRESH-ISOLATED-20260827",
        "uid":"FIG-P067-01",
        "role":"fresh isolated R112 SA3",
        "official_pdf":str(PDF),
        "official_round":"R112",
        "located_from_caption":True,
        "page_index0":PAGE_INDEX0,
        "physical_page1":PHYSICAL_PAGE1,
        "page_size_pt":[page.rect.width,page.rect.height],
        "full_page_300dpi_px":list(full300.size),
        "full_page_200dpi_px":list(full200.size),
        "figure_clip_pt":list(FIGURE_CLIP_PT),
        "figure_crop_300dpi_px":list(crop300.size),
        "standalone_clip_pt":list(STANDALONE_CLIP_PT),
        "standalone_300dpi_px":list(standalone300.size),
        "visible_text_glyph_count":len(chars),
        "visible_graphic_path_count":graphic_index,
        "visible_denominator":len(element_rows),
        "all_unordered_pairs":len(pairs),
        "expected_pair_formula":len(element_rows)*(len(element_rows)-1)//2,
        "text_contact_sheets":contact_paths,
        "graphic_contact_sheets":graphic_contact_paths,
    }
    (ROOT/"machine"/"identity_and_denominator.json").write_text(json.dumps(identity,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(identity,ensure_ascii=True))


if __name__ == "__main__":
    main()

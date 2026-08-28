from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import csv
import math
import pdfplumber
import numpy as np

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa1_r111_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf")
PAGE_PNG = ROOT / "render" / "page709_native300dpi.png"
PAGE_INDEX = 708

image = Image.open(PAGE_PNG).convert("RGB")
arr = np.asarray(image)

with pdfplumber.open(PDF) as pdf:
    page = pdf.pages[PAGE_INDEX]
    page_w, page_h = float(page.width), float(page.height)
    chars = list(page.chars)

sx = image.width / page_w
sy = image.height / page_h

def group_element(oid, pred):
    selected = [c for c in chars if pred(c)]
    if not selected:
        raise RuntimeError(f"no chars for {oid}")
    return selected

elements = {
    "T01": group_element("T01", lambda c: 116 <= c["x0"] <= 147 and 150 <= c["top"] < 163),
    "T02": group_element("T02", lambda c: 235 <= c["x0"] <= 266 and 150 <= c["top"] < 163),
    "T03": group_element("T03", lambda c: 207 <= c["x0"] <= 237 and 280 <= c["top"] < 292),
    "T04": group_element("T04", lambda c: 247 <= c["x0"] <= 316 and 178 <= c["top"] < 190),
    "T05": group_element("T05", lambda c: 164 <= c["x0"] <= 216 and 70 <= c["top"] < 82.5),
    "T06": group_element("T06", lambda c: 164 <= c["x0"] <= 216 and 82.5 <= c["top"] < 94),
    "T07": group_element("T07", lambda c: 64 <= c["x0"] <= 117 and 278 <= c["top"] < 291.1),
    "T08": group_element("T08", lambda c: 64 <= c["x0"] <= 117 and 291.1 <= c["top"] < 302),
    "T09": group_element("T09", lambda c: 263 <= c["x0"] <= 315 and 278 <= c["top"] < 291.1),
    "T10": group_element("T10", lambda c: 263 <= c["x0"] <= 315 and 291.1 <= c["top"] < 302),
    "T11": group_element("T11", lambda c: 362 <= c["x0"] <= 503 and 132 <= c["top"] < 146.2),
    "T12": group_element("T12", lambda c: 362 <= c["x0"] <= 416 and 146.2 <= c["top"] < 159),
    "T13": group_element("T13", lambda c: 362 <= c["x0"] <= 477 and 193 <= c["top"] < 205),
    "T14": group_element("T14", lambda c: 362 <= c["x0"] <= 477 and 205 <= c["top"] < 216),
    "T15": group_element("T15", lambda c: 362 <= c["x0"] <= 477 and 216 <= c["top"] < 228),
    "T16": group_element("T16", lambda c: 362 <= c["x0"] <= 510 and 257 <= c["top"] < 269),
    "T17": group_element("T17", lambda c: 362 <= c["x0"] <= 510 and 269 <= c["top"] < 280),
    "T18": group_element("T18", lambda c: 362 <= c["x0"] <= 423 and 280 <= c["top"] < 292),
    "T19": group_element("T19", lambda c: 60 <= c["x0"] < 100 and 308 <= c["top"] < 322),
    "T20": group_element("T20", lambda c: 100 <= c["x0"] <= 525 and 308 <= c["top"] < 322),
    "T21": group_element("T21", lambda c: 60 <= c["x0"] <= 410 and 322 <= c["top"] < 336),
}

names = {
    "T01":"theta2_label", "T02":"theta1_label", "T03":"theta3_label", "T04":"theta_vector",
    "T05":"e3_formula", "T06":"e3_category", "T07":"e1_formula", "T08":"e1_category",
    "T09":"e2_formula", "T10":"e2_category", "T11":"simplex_definition", "T12":"simplex_dimension",
    "T13":"faces_interior", "T14":"faces_edge", "T15":"faces_vertex",
    "T16":"conclusion_line1", "T17":"conclusion_line2", "T18":"conclusion_line3",
    "T19":"caption_tag", "T20":"caption_line1", "T21":"caption_line2",
}

source_lines = {
    "T01":39,"T02":37,"T03":41,"T04":48,"T05":46,"T06":46,"T07":44,"T08":44,
    "T09":45,"T10":45,"T11":50,"T12":51,"T13":53,"T14":53,"T15":53,"T16":55,
    "T17":55,"T18":55,"T19":57,"T20":57,"T21":57,
}

roles = {
    "T01":"COMPONENT_LABEL","T02":"COMPONENT_LABEL","T03":"COMPONENT_LABEL","T04":"POINT_LABEL",
    "T05":"VERTEX_FORMULA","T06":"VERTEX_DESCRIPTION","T07":"VERTEX_FORMULA","T08":"VERTEX_DESCRIPTION",
    "T09":"VERTEX_FORMULA","T10":"VERTEX_DESCRIPTION","T11":"DEFINITION_FORMULA","T12":"DIMENSION_FORMULA",
    "T13":"FACE_DESCRIPTION","T14":"FACE_DESCRIPTION","T15":"FACE_DESCRIPTION",
    "T16":"CONCLUSION","T17":"CONCLUSION","T18":"CONCLUSION",
    "T19":"CAPTION_TAG","T20":"CAPTION_TEXT","T21":"CAPTION_TEXT",
}

text_mask = np.zeros((image.height, image.width), dtype=np.uint8)
overlay = image.copy()
draw = ImageDraw.Draw(overlay)
rows = []
glyph_rows = []
atlas_items = []

for oid, cs in elements.items():
    x0_pdf = min(c["x0"] for c in cs)
    x1_pdf = max(c["x1"] for c in cs)
    y0_pdf = min(c["top"] for c in cs)
    y1_pdf = max(c["bottom"] for c in cs)
    x0 = max(0, math.floor(x0_pdf * sx) - 2)
    x1 = min(image.width, math.ceil(x1_pdf * sx) + 2)
    y0 = max(0, math.floor(y0_pdf * sy) - 2)
    y1 = min(image.height, math.ceil(y1_pdf * sy) + 2)
    sub = arr[y0:y1, x0:x1]
    chroma = sub.max(axis=2) - sub.min(axis=2)
    dark = (sub.mean(axis=2) <= 210) & (chroma <= 55)
    ys, xs = np.where(dark)
    ink_h = int(ys.max() - ys.min() + 1) if len(ys) else 0
    ink_w = int(xs.max() - xs.min() + 1) if len(xs) else 0
    ink_x0 = x0 + int(xs.min()) if len(xs) else x0
    ink_y0 = y0 + int(ys.min()) if len(ys) else y0
    ink_x1 = x0 + int(xs.max()) + 1 if len(xs) else x0
    ink_y1 = y0 + int(ys.max()) + 1 if len(ys) else y0
    dark_count = int(dark.sum())
    text_mask[y0:y1, x0:x1] |= dark.astype(np.uint8) * 255
    draw.rectangle((x0,y0,x1-1,y1-1), outline="#ff0000", width=3)
    draw.text((x0+2,max(0,y0-17)),oid,fill="#ff0000")
    extracted = "".join(c["text"] for c in cs)
    sizes = [float(c["size"]) for c in cs]
    rows.append([oid,names[oid],roles[oid],source_lines[oid],extracted,f"{min(sizes):.5f}",f"{max(sizes):.5f}",f"{x0_pdf:.3f}",f"{y0_pdf:.3f}",f"{x1_pdf:.3f}",f"{y1_pdf:.3f}",x0,y0,x1,y1,ink_x0,ink_y0,ink_x1,ink_y1,ink_h,ink_w,dark_count])
    atlas_items.append((oid, image.crop((x0,y0,x1,y1))))
    for k,c in enumerate(cs,1):
        codepoints=" ".join(f"U+{ord(ch):04X}" for ch in c["text"])
        gx0=max(0,math.floor(float(c["x0"])*sx)-1); gx1=min(image.width,math.ceil(float(c["x1"])*sx)+1)
        gy0=max(0,math.floor(float(c["top"])*sy)-1); gy1=min(image.height,math.ceil(float(c["bottom"])*sy)+1)
        gsub=arr[gy0:gy1,gx0:gx1]
        gchroma=gsub.max(axis=2)-gsub.min(axis=2)
        gdark=(gsub.mean(axis=2)<=210)&(gchroma<=55)
        gys,gxs=np.where(gdark)
        gh=int(gys.max()-gys.min()+1) if len(gys) else 0
        gw=int(gxs.max()-gxs.min()+1) if len(gxs) else 0
        glyph_rows.append([oid,f"{oid}-C{k:02d}",c["text"],codepoints,c.get("fontname",""),f"{float(c['size']):.5f}",f"{float(c['x0']):.3f}",f"{float(c['top']):.3f}",f"{float(c['x1']):.3f}",f"{float(c['bottom']):.3f}",gx0,gy0,gx1,gy1,gh,gw,int(gdark.sum())])

with (ROOT/"machine"/"text_elements_machine.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["ELEMENT_ID","NAME","ROLE","SOURCE_LINE","EXTRACTED_TEXT","PDF_FONT_SIZE_MIN_PT","PDF_FONT_SIZE_MAX_PT","PDF_X0","PDF_TOP","PDF_X1","PDF_BOTTOM","PX_X0","PX_Y0","PX_X1","PX_Y1","INK_PX_X0","INK_PX_Y0","INK_PX_X1","INK_PX_Y1","H_INK_PX","W_INK_PX","DARK_PIXEL_COUNT"]); w.writerows(rows)
with (ROOT/"machine"/"glyph_codepoints_machine.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["ELEMENT_ID","GLYPH_ID","EXTRACTED_TEXT","CODEPOINTS","PDF_FONT","PDF_SIZE_PT","PDF_X0","PDF_TOP","PDF_X1","PDF_BOTTOM","PX_X0","PX_Y0","PX_X1","PX_Y1","H_INK_PX","W_INK_PX","DARK_PIXEL_COUNT"]); w.writerows(glyph_rows)

figure_box=(250,250,2225,1415)
overlay.crop(figure_box).save(ROOT/"overlays"/"text_measurement_overlay_300dpi.png")
Image.fromarray(text_mask).crop(figure_box).save(ROOT/"masks"/"text_mask_figure_300dpi.png")

gray=np.asarray(image.convert("L"))
foreground=(gray <= 235).astype(np.uint8)*255
Image.fromarray(foreground).crop(figure_box).save(ROOT/"masks"/"foreground_mask_figure_300dpi.png")
geometry=foreground.copy(); geometry[text_mask>0]=0
Image.fromarray(geometry).crop(figure_box).save(ROOT/"masks"/"geometry_residual_mask_figure_300dpi.png")

semantic=image.copy()
sem=np.asarray(semantic).copy()
tm=text_mask>0; gm=geometry>0
sem[gm]=[0,180,255]
sem[tm]=[255,0,0]
Image.fromarray(sem).crop(figure_box).save(ROOT/"overlays"/"semantic_mask_overlay_300dpi.png")

# Native-pixel element atlas; labels occupy their own margin and crops are not resized.
cell_w=760; pad=18; y=pad
heights=[max(60,c.height+2*pad) for _,c in atlas_items]
atlas=Image.new("RGB",(cell_w,sum(heights)+pad),"white")
d=ImageDraw.Draw(atlas)
for (oid,crop),h in zip(atlas_items,heights):
    d.text((pad,y+4),oid,fill="black")
    atlas.paste(crop,(100,y+pad//2))
    d.rectangle((98,y+pad//2-2,100+crop.width+2,y+pad//2+crop.height+2),outline="#777777",width=1)
    y+=h
atlas.save(ROOT/"rois"/"glyph_atlas_native1x.png")

with (ROOT/"machine"/"pdf_page_identity.txt").open("w",encoding="utf-8") as f:
    f.write(f"pdf_physical_page_1based=709\npdf_page_index_0based=708\nprinted_page=696\npage_width_pt={page_w}\npage_height_pt={page_h}\npng_width_px={image.width}\npng_height_px={image.height}\nscale_x_px_per_pt={sx:.9f}\nscale_y_px_per_pt={sy:.9f}\n")

print(f"elements={len(rows)} glyph_records={len(glyph_rows)} sx={sx:.6f} sy={sy:.6f}")

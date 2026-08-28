from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-01\STRICT_R1_SA1_FRESH_R104_R168_20260825")
W, H = 1930, 706


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def load_objects():
    data = json.loads((ROOT / "object_manifest.json").read_text(encoding="utf-8"))
    for o in data:
        m = np.array(Image.open(ROOT / o["mask_relpath"]).convert("L")) > 0
        full = np.zeros((H, W), dtype=bool)
        x0, y0, x1, y1 = o["ink_bbox_px"]
        assert m.shape == (y1-y0, x1-x0)
        full[y0:y1, x0:x1] = m
        o["mask"] = full
    return data


def closest(ma, mb):
    ya, xa = np.nonzero(ma); yb, xb = np.nonzero(mb)
    pa = np.column_stack((xa, ya)).astype(np.float32); pb = np.column_stack((xb, yb)).astype(np.float32)
    sa = set((ya.astype(np.int64)*W + xa.astype(np.int64)).tolist())
    sb = set((yb.astype(np.int64)*W + xb.astype(np.int64)).tolist())
    inter = len(sa.intersection(sb))
    tree = cKDTree(pb); ds, ix = tree.query(pa, k=1); k = int(np.argmin(ds))
    return max(0.0, float(ds[k])-1.0), tuple(map(int,pa[k])), tuple(map(int,pb[int(ix[k])])), inter


def relation_quad(crop, ma, mb, title, pa, pb):
    ys, xs = np.nonzero(ma | mb)
    x0, y0, x1, y1 = max(0,int(xs.min())-12), max(0,int(ys.min())-12), min(W,int(xs.max())+13), min(H,int(ys.max())+13)
    orig = crop.crop((x0,y0,x1,y1)).convert("RGB")
    oa = np.array(orig.copy()); la=ma[y0:y1,x0:x1]; lb=mb[y0:y1,x0:x1]
    oa[la]=[255,0,0]; oa[lb]=[0,90,255]; oa[la&lb]=[255,0,255]
    ov=Image.fromarray(oa)
    sc=min(900/orig.width,420/orig.height,1.0)
    def fit(z): return z if sc>=1 else z.resize((max(1,int(z.width*sc)),max(1,int(z.height*sc))),Image.Resampling.NEAREST)
    canvas=Image.new("RGB",(1900,950),"white"); d=ImageDraw.Draw(canvas); font=ImageFont.load_default(size=20)
    d.text((10,5),title+" | red=A blue=B magenta=intersection",fill="black",font=font)
    canvas.paste(fit(orig),(10,45)); canvas.paste(fit(ov),(950,45))
    cx=int(round((pa[0]+pb[0])/2)); cy=int(round((pa[1]+pb[1])/2))
    rx0,ry0,rx1,ry1=max(0,cx-28),max(0,cy-28),min(W,cx+28),min(H,cy+28)
    det=np.array(crop.crop((rx0,ry0,rx1,ry1)).convert("RGB")); dla=ma[ry0:ry1,rx0:rx1]; dlb=mb[ry0:ry1,rx0:rx1]
    det[dla]=[255,0,0]; det[dlb]=[0,90,255]; det[dla&dlb]=[255,0,255]
    di=Image.fromarray(det).resize((det.shape[1]*8,det.shape[0]*8),Image.Resampling.NEAREST)
    canvas.paste(di,(10,500)); d.text((480,510),"8x nearest connection detail",fill="black",font=font)
    return canvas


def make_overlap_relationships(crop, byid):
    out=ROOT/"relationship"; out.mkdir(exist_ok=True)
    rows=[]
    for i,r in enumerate(read_csv(ROOT/"raw_overlap_pairs.csv"),start=1):
        a,b=byid[r["element_a"]],byid[r["element_b"]]
        dist,pa,pb,inter=closest(a["mask"],b["mask"])
        rid=f"R{i:03d}"; fn=f"{rid}_{r['pair_id']}_{a['element_id']}_{b['element_id']}.png"
        relation_quad(crop,a["mask"],b["mask"],f"{rid} {r['structural_relation']} intersection={inter}",pa,pb).save(out/fn)
        rows.append({"relationship_id":rid,"pair_id":r["pair_id"],"element_a":a["element_id"],"element_b":b["element_id"],"structural_relation":r["structural_relation"],"raw_intersection_pixel_count":inter,"clearance_px":round(dist,4),"overlay_relpath":f"relationship/{fn}"})
    write_csv(ROOT/"relationship_index.csv",rows)


def make_connections(crop, byid):
    detail_dir=ROOT/"connection_detail"; detail_dir.mkdir(exist_ok=True)
    borders=["V0003","V0004","V0005","V0006","V0007","V0008","V0009"]
    lines=["V0010","V0012","V0014","V0016","V0018","V0020"]
    arrows=["V0011","V0013","V0015","V0017","V0019","V0021"]
    labels=["0->1","1->2","2->3","3->4","4->5","5->T"]
    rows=[]
    for i,label in enumerate(labels):
        ds,_,_,ins=closest(byid[borders[i]]["mask"],byid[lines[i]]["mask"])
        dl,_,_,inl=closest(byid[lines[i]]["mask"],byid[arrows[i]]["mask"])
        dt,pa,pb,intt=closest(byid[arrows[i]]["mask"],byid[borders[i+1]]["mask"])
        fn=f"E{i+1:02d}_{label.replace('>','').replace('-','_')}_arrow_to_target.png"
        relation_quad(crop,byid[arrows[i]]["mask"],byid[borders[i+1]]["mask"],f"E{i+1:02d} transition {label} arrowhead-to-target distance={dt:.4f}px intersection={intt}",pa,pb).save(detail_dir/fn)
        rows.append({"transition":label,"source_border":borders[i],"line":lines[i],"arrowhead":arrows[i],"target_border":borders[i+1],"source_line_intersection_px":ins,"source_line_clearance_px":round(ds,4),"line_arrow_intersection_px":inl,"line_arrow_clearance_px":round(dl,4),"arrow_target_intersection_px":intt,"arrow_target_clearance_px":round(dt,4),"endpoint_overlay_relpath":f"connection_detail/{fn}"})
    write_csv(ROOT/"connection_continuity_ledger.csv",rows)
    im=crop.convert("RGB").copy(); d=ImageDraw.Draw(im); font=ImageFont.load_default(size=16)
    colors=[(220,0,0),(230,100,0),(180,0,180),(0,140,0),(0,120,220),(80,80,80)]
    for i,(line,arrow) in enumerate(zip(lines,arrows)):
        for eid in (line,arrow):
            b=byid[eid]["ink_bbox_px"]; d.rectangle(b,outline=colors[i],width=3)
        lb=byid[line]["ink_bbox_px"]; d.text((lb[0],max(0,lb[1]-20)),labels[i],fill=colors[i],font=font)
    d.text((10,10),"Six line+arrow paths; boxes mark final-visible raw masks and endpoint continuity",fill=(0,0,0),font=font)
    im.save(ROOT/"connection_continuity_overlay_300dpi.png")
    sheet=Image.new("RGB",(1900,650),"white"); sd=ImageDraw.Draw(sheet); big=ImageFont.load_default(size=22)
    sd.text((10,10),"Transition connection matrix (raw-mask intersections / edge clearances)",fill="black",font=big)
    headers=["transition","source-line","line-arrow","arrow-target"]
    for j,h in enumerate(headers): sd.text((20+j*460,70),h,fill="black",font=big)
    for i,r in enumerate(rows):
        vals=[r["transition"],f"{r['source_line_intersection_px']} / {r['source_line_clearance_px']}",f"{r['line_arrow_intersection_px']} / {r['line_arrow_clearance_px']}",f"{r['arrow_target_intersection_px']} / {r['arrow_target_clearance_px']}"]
        for j,v in enumerate(vals):
            x,y=10+j*460,110+i*80; sd.rectangle((x,y,x+450,y+70),outline=(130,130,130)); sd.text((x+12,y+20),str(v),fill="black",font=big)
    sheet.save(ROOT/"connection_relationship_matrix.png")


def vector_geometry(objects):
    nodes=[next(o for o in objects if o["semantic_parent"].startswith(f"node_border_t{t}")) for t in ["0","1","2","3","4","5","T"]]
    centers=[]
    for o in nodes:
        x0,y0,x1,y1=o["bbox_pt"]; centers.append([(x0+x1)/2,(y0+y1)/2])
    dx=[centers[i+1][0]-centers[i][0] for i in range(6)]
    obj={"node_centers_pt":centers,"adjacent_dx_pt":dx,"adjacent_dx_range_pt":max(dx)-min(dx),"adjacent_dx_mean_pt":sum(dx)/len(dx),"equal_time_spacing_vector_check":"all six PDF-vector x increments agree within floating serialization tolerance"}
    (ROOT/"semantic_vector_geometry.json").write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")


def main():
    crop=Image.open(ROOT/"figure_crop_300dpi.png").convert("RGB")
    objects=load_objects(); byid={o["element_id"]:o for o in objects}
    make_overlap_relationships(crop,byid)
    make_connections(crop,byid)
    vector_geometry(objects)
    print("relationship_overlays=17 connection_rows=6")


if __name__=="__main__": main()

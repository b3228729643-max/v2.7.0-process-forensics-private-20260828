import csv
import importlib.util
import json
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-01\STRICT_R1_SA1_FRESH_R104_R168_20260825")
PAIRS=[("OCC001","V0004","t1"),("OCC002","V0005","t2"),("OCC003","V0006","t3"),("OCC004","V0007","t4")]


def main():
    crop=Image.open(ROOT/"figure_crop_300dpi.png").convert("RGB")
    objs={o["element_id"]:o for o in json.loads((ROOT/"object_manifest.json").read_text(encoding="utf-8"))}
    occ={r["occlusion_id"]:r for r in csv.DictReader((ROOT/"occlusion_path_inventory.csv").open("r",encoding="utf-8-sig",newline=""))}
    spec=importlib.util.spec_from_file_location("machine_builder",ROOT/"build_machine_evidence.py")
    machine=importlib.util.module_from_spec(spec); spec.loader.exec_module(machine)
    page=fitz.open(machine.PDF)[machine.PAGE_INDEX]; drawings=page.get_drawings(); arr=np.array(crop)
    sheet=Image.new("RGB",(2000,1600),"white"); font=ImageFont.load_default(size=22)
    rows=[]
    for i,(oid,vid,tlabel) in enumerate(PAIRS):
        v=objs[vid]; x0,y0,x1,y1=v["ink_bbox_px"]
        final=np.array(Image.open(ROOT/v["mask_relpath"]).convert("L"))>0
        di=int(occ[oid]["draw_index"]); support=machine.drawing_support(drawings[di],arr.shape[:2],False)
        full_o=support & (np.min(arr,axis=2)>=245)
        oyx=np.nonzero(full_o); ox0,oy0,ox1,oy1=int(oyx[1].min()),int(oyx[0].min()),int(oyx[1].max())+1,int(oyx[0].max())+1
        Image.fromarray((full_o[oy0:oy1,ox0:ox1].astype(np.uint8)*255)).save(ROOT/occ[oid]["mask_relpath"])
        full_f=np.zeros((706,1930),dtype=bool); full_f[y0:y1,x0:x1]=final
        pre=full_f|full_o
        ys,xs=np.nonzero(pre); bx0,by0,bx1,by1=max(0,int(xs.min())-12),max(0,int(ys.min())-12),min(1930,int(xs.max())+13),min(706,int(ys.max())+13)
        original=crop.crop((bx0,by0,bx1,by1))
        views=[original,Image.fromarray((pre[by0:by1,bx0:bx1]*255).astype(np.uint8)).convert("RGB"),Image.fromarray((~full_o[by0:by1,bx0:bx1]*255).astype(np.uint8)).convert("RGB"),Image.fromarray((~full_f[by0:by1,bx0:bx1]*255).astype(np.uint8)).convert("RGB")]
        cell=Image.new("RGB",(1000,800),"white"); d=ImageDraw.Draw(cell); d.text((10,10),f"{oid} {tlabel} | ORIGINAL | PRE SUPPORT | WHITE OCCLUDER | FINAL BORDER",fill="black",font=font)
        for j,z in enumerate(views):
            z=z.resize((z.width*6,z.height*6),Image.Resampling.NEAREST); cell.paste(z,((j%2)*490+10,(j//2)*360+55))
        sheet.paste(cell,((i%2)*1000,(i//2)*800))
        pre_path=ROOT/"masks/occlusion"/f"{oid}_pre_support.png"; Image.fromarray((pre.astype(np.uint8)*255)).crop((bx0,by0,bx1,by1)).save(pre_path)
        rows.append({"occlusion_id":oid,"repeat_border_id":vid,"time":tlabel,"pre_support_relpath":f"masks/occlusion/{oid}_pre_support.png","opaque_separator_relpath":occ[oid]["mask_relpath"],"opaque_separator_bbox_px":json.dumps([ox0,oy0,ox1,oy1]),"final_visible_border_relpath":v["mask_relpath"],"sheet":"occlusion_contact_sheet.png","cell":i+1})
    sheet.save(ROOT/"occlusion_contact_sheet.png")
    with (ROOT/"occlusion_triplet_index.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("occlusion_triplets=4")


if __name__=="__main__": main()

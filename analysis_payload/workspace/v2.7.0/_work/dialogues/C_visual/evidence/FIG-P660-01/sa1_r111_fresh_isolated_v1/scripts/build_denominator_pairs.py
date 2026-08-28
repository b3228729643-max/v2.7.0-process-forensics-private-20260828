from pathlib import Path
from PIL import Image, ImageDraw
import csv
import math

ROOT=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa1_r111_fresh_isolated_v1")
PAGE=Image.open(ROOT/"render"/"page709_native300dpi.png").convert("RGB")

def line_box(p,q,pad=4):
    return (min(p[0],q[0])-pad,min(p[1],q[1])-pad,max(p[0],q[0])+pad,max(p[1],q[1])+pad)

e1=(376,1132); e2=(1205,1132); e3=(790,414); th=(832,773)
geometry=[
    ("G01","FILL","simplex_interior_fill",23,376,414,1205,1132),
    ("G02","BOUNDARY","simplex_left_boundary",24,*line_box(e1,e3,5)),
    ("G03","BOUNDARY","simplex_right_boundary",24,*line_box(e3,e2,5)),
    ("G04","BOUNDARY","simplex_bottom_boundary",24,*line_box(e1,e2,5)),
]
gid=5
for t in (0.2,0.4,0.6,0.8):
    p=(round(e1[0]+t*(e2[0]-e1[0])),round(e1[1]+t*(e2[1]-e1[1])))
    q=(round(e3[0]+t*(e2[0]-e3[0])),round(e3[1]+t*(e2[1]-e3[1])))
    geometry.append((f"G{gid:02d}","GRID",f"grid_family_A_t{t:.1f}",27,*line_box(p,q,3))); gid+=1
    p=(round(e2[0]+t*(e3[0]-e2[0])),round(e2[1]+t*(e3[1]-e2[1])))
    q=(round(e1[0]+t*(e3[0]-e1[0])),round(e1[1]+t*(e3[1]-e1[1])))
    geometry.append((f"G{gid:02d}","GRID",f"grid_family_B_t{t:.1f}",29,*line_box(p,q,3))); gid+=1
    p=(round(e3[0]+t*(e1[0]-e3[0])),round(e3[1]+t*(e1[1]-e3[1])))
    q=(round(e2[0]+t*(e1[0]-e2[0])),round(e2[1]+t*(e1[1]-e2[1])))
    geometry.append((f"G{gid:02d}","GRID",f"grid_family_C_t{t:.1f}",31,*line_box(p,q,3))); gid+=1

assert gid==17
geometry += [
    ("G17","COMPONENT_GUIDE","theta1_projection_guide",36,*line_box(th,(956,701),4)),
    ("G18","COMPONENT_GUIDE","theta2_projection_guide",38,*line_box(th,(625,701),4)),
    ("G19","COMPONENT_GUIDE","theta3_projection_guide",40,*line_box(th,(832,1132),4)),
    ("G20","MARKER","theta_point_marker",42,816,757,848,789),
    ("G21","CARD_BORDER","definition_card_border",49,1466,522,2193,685),
    ("G22","CARD_BORDER","faces_card_border",52,1466,785,2193,973),
    ("G23","CARD_BORDER","conclusion_card_border",54,1466,1040,2193,1236),
]

objects=[]
for oid,cls,name,line,x0,y0,x1,y1 in geometry:
    objects.append({"OBJECT_ID":oid,"CLASS":cls,"NAME":name,"SOURCE_LINE":line,"X0":x0,"Y0":y0,"X1":x1,"Y1":y1})

with (ROOT/"machine"/"text_elements_machine.csv").open("r",encoding="utf-8-sig",newline="") as f:
    for row in csv.DictReader(f):
        objects.append({"OBJECT_ID":row["ELEMENT_ID"],"CLASS":row["ROLE"],"NAME":row["NAME"],"SOURCE_LINE":int(row["SOURCE_LINE"]),"X0":int(row["INK_PX_X0"]),"Y0":int(row["INK_PX_Y0"]),"X1":int(row["INK_PX_X1"]),"Y1":int(row["INK_PX_Y1"])})

assert len(objects)==44

with (ROOT/"machine"/"frozen_visible_object_denominator.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["OBJECT_ID","CLASS","NAME","SOURCE_LINE","X0","Y0","X1","Y1"]); w.writeheader(); w.writerows(objects)

pair_lookup={}
pair_rows=[]
pid=0
for i,a in enumerate(objects):
    for b in objects[i+1:]:
        pid+=1; pair_id=f"P{pid:04d}"
        ax0,ay0,ax1,ay1=[a[k] for k in ("X0","Y0","X1","Y1")]
        bx0,by0,bx1,by1=[b[k] for k in ("X0","Y0","X1","Y1")]
        ix=max(0,min(ax1,bx1)-max(ax0,bx0)); iy=max(0,min(ay1,by1)-max(ay0,by0))
        gx=max(0,max(ax0,bx0)-min(ax1,bx1)); gy=max(0,max(ay0,by0)-min(ay1,by1))
        gap=(gx*gx+gy*gy)**0.5
        row={"PAIR_ID":pair_id,"OBJECT_A":a["OBJECT_ID"],"OBJECT_B":b["OBJECT_ID"],"CLASS_A":a["CLASS"],"CLASS_B":b["CLASS"],"BBOX_INTERSECTION_AREA_PX":ix*iy,"BBOX_GAP_X_PX":gx,"BBOX_GAP_Y_PX":gy,"BBOX_EUCLIDEAN_GAP_PX":f"{gap:.3f}","MACHINE_BBOX_RELATION":"INTERSECTS_OR_TOUCHES" if gx==0 and gy==0 else "DISJOINT"}
        pair_rows.append(row); pair_lookup[frozenset((a["OBJECT_ID"],b["OBJECT_ID"]))]=row
assert pid==946

with (ROOT/"machine"/"all_unordered_pairs_evidence.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(pair_rows[0].keys())); w.writeheader(); w.writerows(pair_rows)

critical=[
    ("G18","T01"),("G17","T02"),("G19","T03"),("G17","T04"),("G20","T04"),
    ("G02","T05"),("G03","T05"),("G02","T06"),("G03","T06"),
    ("G02","T07"),("G04","T07"),("G02","T08"),("G04","T08"),
    ("G03","T09"),("G04","T09"),("G03","T10"),("G04","T10"),
    ("G21","T11"),("G21","T12"),("G22","T13"),("G22","T14"),("G22","T15"),
    ("G23","T16"),("G23","T17"),("G23","T18"),
    ("T05","T06"),("T07","T08"),("T09","T10"),("T11","T12"),("T13","T14"),("T14","T15"),("T16","T17"),("T17","T18"),
    ("T19","T20"),("T20","T21"),("T07","T19"),("T08","T19"),("T09","T20"),("T10","T20"),("G23","T20"),("G23","T21"),
]

by_id={o["OBJECT_ID"]:o for o in objects}
idx_rows=[]; panels=[]
for a_id,b_id in critical:
    row=pair_lookup[frozenset((a_id,b_id))]
    a=by_id[a_id]; b=by_id[b_id]
    x0=max(0,min(a["X0"],b["X0"])-35); y0=max(0,min(a["Y0"],b["Y0"])-35)
    x1=min(PAGE.width,max(a["X1"],b["X1"])+35); y1=min(PAGE.height,max(a["Y1"],b["Y1"])+35)
    crop=PAGE.crop((x0,y0,x1,y1)); d=ImageDraw.Draw(crop)
    d.rectangle((a["X0"]-x0,a["Y0"]-y0,a["X1"]-x0,a["Y1"]-y0),outline="#ff0000",width=3)
    d.rectangle((b["X0"]-x0,b["Y0"]-y0,b["X1"]-x0,b["Y1"]-y0),outline="#0066ff",width=3)
    label=f"{row['PAIR_ID']} {a_id}-{b_id}"
    idx_rows.append([row["PAIR_ID"],a_id,b_id,x0,y0,x1,y1,row["BBOX_INTERSECTION_AREA_PX"],row["BBOX_EUCLIDEAN_GAP_PX"]])
    panels.append((label,crop))

with (ROOT/"machine"/"critical_pair_contact_sheet_index.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["PAIR_ID","OBJECT_A","OBJECT_B","ROI_X0","ROI_Y0","ROI_X1","ROI_Y1","BBOX_INTERSECTION_AREA_PX","BBOX_EUCLIDEAN_GAP_PX"]); w.writerows(idx_rows)

cell_w=820; cell_h=420; cols=2; rows_n=math.ceil(len(panels)/cols)
sheet=Image.new("RGB",(cell_w*cols,cell_h*rows_n),"white"); d=ImageDraw.Draw(sheet)
for k,(label,crop) in enumerate(panels):
    col=k%cols; row=k//cols; ox=col*cell_w; oy=row*cell_h
    maxw=cell_w-30; maxh=cell_h-50
    scale=min(1.0,maxw/crop.width,maxh/crop.height)
    shown=crop if scale==1 else crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
    d.text((ox+12,oy+8),label,fill="black")
    sheet.paste(shown,(ox+12,oy+34))
sheet.save(ROOT/"overlays"/"critical_pair_contact_sheet.png")

chunk_size=8
for chunk_start in range(0,len(panels),chunk_size):
    chunk=panels[chunk_start:chunk_start+chunk_size]
    chunk_rows=math.ceil(len(chunk)/cols)
    chunk_img=Image.new("RGB",(cell_w*cols,cell_h*chunk_rows),"white")
    cd=ImageDraw.Draw(chunk_img)
    for kk,(label,crop) in enumerate(chunk):
        col=kk%cols; row=kk//cols; ox=col*cell_w; oy=row*cell_h
        maxw=cell_w-30; maxh=cell_h-50
        scale=min(1.0,maxw/crop.width,maxh/crop.height)
        shown=crop if scale==1 else crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
        cd.text((ox+12,oy+8),label,fill="black")
        chunk_img.paste(shown,(ox+12,oy+34))
    chunk_img.save(ROOT/"overlays"/f"critical_pair_contact_sheet_{chunk_start//chunk_size+1:02d}.png")

with (ROOT/"machine"/"denominator_pair_counts.txt").open("w",encoding="utf-8") as f:
    f.write(f"visible_object_count={len(objects)}\nunordered_pair_count={pid}\ncritical_pair_contact_sheet_count={len(critical)}\n")

print(f"objects={len(objects)} pairs={pid} critical={len(critical)} sheet={sheet.size}")

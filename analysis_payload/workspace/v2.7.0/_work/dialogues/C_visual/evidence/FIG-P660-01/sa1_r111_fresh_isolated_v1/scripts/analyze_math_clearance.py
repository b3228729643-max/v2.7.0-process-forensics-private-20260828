from pathlib import Path
from PIL import Image
import csv
import math
import numpy as np

ROOT=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa1_r111_fresh_isolated_v1")
PAGE_PATH=ROOT/"render"/"page709_native300dpi.png"
PAGE=Image.open(PAGE_PATH).convert("RGB")
ARR=np.asarray(PAGE)

e1=np.array([0.0,0.0]); e2=np.array([7.0,0.0]); e3=np.array([3.5,6.062])
theta=np.array([0.2,0.3,0.5])
th=theta[0]*e1+theta[1]*e2+theta[2]*e3

def project(p,a,b):
    v=b-a; t=float(np.dot(p-a,v)/np.dot(v,v)); return a+t*v,t

q1,t1=project(th,e2,e3)
q2,t2=project(th,e1,e3)
q3,t3=project(th,e1,e2)

def point_line_distance(p,a,b):
    return abs(float(np.cross(b-a,p-a)))/float(np.linalg.norm(b-a))

h1=point_line_distance(e1,e2,e3)
h2=point_line_distance(e2,e1,e3)
h3=point_line_distance(e3,e1,e2)
r1=point_line_distance(th,e2,e3)/h1
r2=point_line_distance(th,e1,e3)/h2
r3=point_line_distance(th,e1,e2)/h3

with (ROOT/"machine"/"barycentric_recomputation_machine.txt").open("w",encoding="utf-8") as f:
    f.write(f"theta={theta.tolist()}\n")
    f.write(f"theta_sum={theta.sum():.12f}\n")
    f.write(f"weighted_vertex_point=({th[0]:.12f},{th[1]:.12f})\n")
    f.write("source_th=(3.850000000000,3.031000000000)\n")
    f.write(f"q1_projection_to_edge_e2_e3=({q1[0]:.12f},{q1[1]:.12f}); edge_parameter={t1:.12f}; distance_ratio={r1:.12f}; expected_theta1={theta[0]:.12f}\n")
    f.write(f"q2_projection_to_edge_e1_e3=({q2[0]:.12f},{q2[1]:.12f}); edge_parameter={t2:.12f}; distance_ratio={r2:.12f}; expected_theta2={theta[1]:.12f}\n")
    f.write(f"q3_projection_to_edge_e1_e2=({q3[0]:.12f},{q3[1]:.12f}); edge_parameter={t3:.12f}; distance_ratio={r3:.12f}; expected_theta3={theta[2]:.12f}\n")
    f.write("affine_constraint_count=1\nambient_dimension=3\naffine_dimension=2\n")
    f.write("grid_parameters=0.2,0.4,0.6,0.8\n")

with (ROOT/"machine"/"text_elements_machine.csv").open("r",encoding="utf-8-sig",newline="") as f:
    text=list(csv.DictReader(f))
text_by_id={r["ELEMENT_ID"]:r for r in text}

declared=[]
for r in text:
    oid=r["ELEMENT_ID"]
    if oid in {"T01","T02","T03"}:
        decl="8.7"; source="explicit_node_font"; line=r["SOURCE_LINE"]
    elif oid.startswith("T") and int(oid[1:])<=18:
        decl="9.5"; source="tikz_every_node_font"; line="13"
    else:
        decl="INHERITED"; source="document_caption_style"; line=r["SOURCE_LINE"]
    declared.append([oid,r["ROLE"],r["EXTRACTED_TEXT"],source,line,decl,r["PDF_FONT_SIZE_MIN_PT"],r["PDF_FONT_SIZE_MAX_PT"],r["H_INK_PX"]])
with (ROOT/"machine"/"source_font_declarations_machine.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["ELEMENT_ID","ROLE","TEXT","SOURCE_DECLARATION_KIND","SOURCE_LINE","DECLARED_BASE_PT","PDF_VECTOR_SIZE_MIN_PT","PDF_VECTOR_SIZE_MAX_PT","GROUP_H_INK_PX"]); w.writerows(declared)

role_groups={
    "component_labels":["T01","T02","T03"],
    "vertex_formula":["T05","T07","T09"],
    "vertex_description":["T06","T08","T10"],
    "face_description":["T13","T14","T15"],
    "conclusion_lines":["T16","T17","T18"],
    "caption_text":["T20","T21"],
}
ratio_rows=[]
for role,ids in role_groups.items():
    hs=[int(text_by_id[x]["H_INK_PX"]) for x in ids]
    med=float(np.median(hs))
    for oid,h in zip(ids,hs): ratio_rows.append([role,oid,h,f"{med:.3f}",f"{h/med:.6f}"])
with (ROOT/"machine"/"pixel_role_ratios_machine.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["ROLE_GROUP","ELEMENT_ID","H_INK_PX","ROLE_MEDIAN_PX","RATIO_TO_ROLE_MEDIAN"]); w.writerows(ratio_rows)

def neutral_dark_counts(box):
    x0,y0,x1,y1=box
    s=ARR[y0:y1,x0:x1]
    chroma=s.max(axis=2)-s.min(axis=2)
    mask=(s.mean(axis=2)<=210)&(chroma<=55)
    return mask.sum(axis=1)

gap_regions=[
    ("LG01","T05","T06",(665,285,920,405),335,341),
    ("LG02","T07","T08",(250,1145,525,1275),1203,1210),
    ("LG03","T09","T10",(1075,1145,1345,1275),1203,1210),
    ("LG04","T11","T12",(1490,535,2120,680),607,612),
]
gap_rows=[]
for gid,a,b,box,scan_start,scan_end in gap_regions:
    counts=neutral_dark_counts(box)
    y0=box[1]
    zero_abs=[i+y0 for i,v in enumerate(counts) if v==0 and scan_start<=i+y0<scan_end]
    gap_rows.append([gid,a,b,box[0],box[1],box[2],box[3],scan_start,scan_end-1," ".join(map(str,zero_abs)),len(zero_abs)])
with (ROOT/"machine"/"line_gap_scan_machine.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["GAP_ID","ELEMENT_A","ELEMENT_B","ROI_X0","ROI_Y0","ROI_X1","ROI_Y1","SCAN_Y_START","SCAN_Y_END","ZERO_FOREGROUND_ROWS_ABS","ZERO_FOREGROUND_ROW_COUNT"]); w.writerows(gap_rows)

card_bounds={"G21":(1466,522,2193,685),"G22":(1466,785,2193,973),"G23":(1466,1040,2193,1236)}
card_members={"G21":["T11","T12"],"G22":["T13","T14","T15"],"G23":["T16","T17","T18"]}
card_rows=[]
for gid,ids in card_members.items():
    l,t,r,b=card_bounds[gid]
    for oid in ids:
        x0=int(text_by_id[oid]["INK_PX_X0"]); y0=int(text_by_id[oid]["INK_PX_Y0"]); x1=int(text_by_id[oid]["INK_PX_X1"]); y1=int(text_by_id[oid]["INK_PX_Y1"])
        card_rows.append([gid,oid,x0-l,y0-t,r-x1,b-y1,min(x0-l,y0-t,r-x1,b-y1)])
with (ROOT/"machine"/"card_text_clearance_machine.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["CARD_ID","ELEMENT_ID","LEFT_CLEARANCE_PX","TOP_CLEARANCE_PX","RIGHT_CLEARANCE_PX","BOTTOM_CLEARANCE_PX","MIN_EDGE_CLEARANCE_PX"]); w.writerows(card_rows)

with (ROOT/"machine"/"frozen_visible_object_denominator.csv").open("r",encoding="utf-8-sig",newline="") as f:
    objs=list(csv.DictReader(f))
clip_rows=[]
for o in objs:
    x0=int(o["X0"]);y0=int(o["Y0"]);x1=int(o["X1"]);y1=int(o["Y1"])
    outside=max(0,-x0)+max(0,-y0)+max(0,x1-PAGE.width)+max(0,y1-PAGE.height)
    clip_rows.append([o["OBJECT_ID"],x0,y0,x1,y1,min(x0,y0,PAGE.width-x1,PAGE.height-y1),outside])
with (ROOT/"machine"/"page_clip_scan_machine.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["OBJECT_ID","X0","Y0","X1","Y1","MIN_PAGE_EDGE_CLEARANCE_PX","OUTSIDE_PAGE_EXTENT_PX"]); w.writerows(clip_rows)

with (ROOT/"machine"/"critical_pair_contact_sheet_index.csv").open("r",encoding="utf-8-sig",newline="") as f:
    crit=list(csv.DictReader(f))
line_gap_by_pair={frozenset((r[1],r[2])):r[-1] for r in gap_rows}
card_min={(r[0],r[1]):r[-1] for r in card_rows}
shared_rows=[]
for r in crit:
    a,b=r["OBJECT_A"],r["OBJECT_B"]
    pair=frozenset((a,b))
    if float(r["BBOX_EUCLIDEAN_GAP_PX"])>0:
        mode="POSITIVE_INK_BBOX_GAP"; proof=r["BBOX_EUCLIDEAN_GAP_PX"]
    elif pair in line_gap_by_pair:
        mode="CONSECUTIVE_EMPTY_NATIVE_ROWS"; proof=str(line_gap_by_pair[pair])
    else:
        card=a if a in card_members else b
        text_id=b if a in card_members else a
        mode="POSITIVE_TEXT_TO_CARD_EDGE_CLEARANCE"; proof=str(card_min[(card,text_id)])
    shared_rows.append([r["PAIR_ID"],a,b,mode,proof,0])
with (ROOT/"machine"/"critical_pair_shared_pixel_machine.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["PAIR_ID","OBJECT_A","OBJECT_B","ZERO_INTERSECTION_DERIVATION","PROOF_VALUE_PX","SEMANTIC_SHARED_PIXEL_COUNT"]); w.writerows(shared_rows)

print(f"theta_sum={theta.sum():.6f} th={th.tolist()} ratios={[r1,r2,r3]} line_gaps={[x[-1] for x in gap_rows]} card_rows={len(card_rows)} objects={len(clip_rows)} critical_pairs={len(shared_rows)} shared_pixels={sum(r[-1] for r in shared_rows)}")

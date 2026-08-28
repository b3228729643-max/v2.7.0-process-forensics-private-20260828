from pathlib import Path
from PIL import Image
import numpy as np

root = Path(r"D:\Users\ASUS\Desktop\机器学习")
p = root / "v2.7.0" / "_work" / "evidence" / "figures" / "FIG-P634-01" / "STRICT_R5_SA1_R94" / "renders" / "official_page_682_300dpi.png"
im = np.asarray(Image.open(p).convert("RGB"))
# physical node 1 interior after its border, around (120..157 pt, 472..499 pt)
arr = im[1975:2075, 500:670]
q = ((arr.reshape(-1,3)//4)*4)
colors, counts = np.unique(q, axis=0, return_counts=True)
for i in np.argsort(counts)[-40:][::-1]:
    print(tuple(int(v) for v in colors[i]), int(counts[i]))

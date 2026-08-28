from pathlib import Path
from PIL import Image

ROOT=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R15_SA1_FRESH_ISOLATED_R106_20260826")
full=Image.open(ROOT/"views/full_page_300dpi_native.png").convert("RGB")
crop=(280,280,2153,1126)
stand=full.crop(crop)
stand.save(ROOT/"views/standalone_300dpi.png",dpi=(300,300))
stand.convert("L").save(ROOT/"views/grayscale_300dpi.png",dpi=(300,300))
print({"crop":crop,"dimensions":stand.size})

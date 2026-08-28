import csv
import hashlib
import json
import re
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P609-01\sa2_r108_r168_readonly_adjudication_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_autocorrelation_ess.tex")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


document = fitz.open(PDF)
page = document[660]
page_text = page.get_text("text", sort=True)
(ROOT / "page661_extracted_text.txt").write_text(page_text, encoding="utf-8", newline="\n")

spans = []
for block in page.get_text("dict")["blocks"]:
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            if span["bbox"][1] >= 500:
                spans.append(span)

with (ROOT / "page661_figure_text_spans.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["SPAN_ID", "FONT_SIZE_PT", "FONT", "BBOX_X0_PT", "BBOX_Y0_PT", "BBOX_X1_PT", "BBOX_Y1_PT", "TEXT", "CODEPOINTS"])
    for index, span in enumerate(spans, start=1):
        x0, y0, x1, y1 = span["bbox"]
        text = span["text"]
        writer.writerow([
            f"S{index:03d}",
            f"{span['size']:.3f}",
            span["font"],
            f"{x0:.3f}",
            f"{y0:.3f}",
            f"{x1:.3f}",
            f"{y1:.3f}",
            text,
            " ".join(f"U+{ord(char):04X}" for char in text),
        ])

source_text = SOURCE.read_text(encoding="utf-8")
font_declarations = []
for line_number, line in enumerate(source_text.splitlines(), start=1):
    for size, leading in re.findall(r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}", line):
        font_declarations.append({"line": line_number, "size_pt": float(size), "leading_pt": float(leading)})

rho = np.array([1.00, 0.86, 0.74, 0.64, 0.55, 0.47, 0.40])
toeplitz = np.fromfunction(lambda i, j: rho[np.abs(i - j).astype(int)], (7, 7))

view_dimensions = {}
for path in sorted(ROOT.glob("*.png")):
    with Image.open(path) as image:
        view_dimensions[path.name] = {"width_px": image.width, "height_px": image.height, "mode": image.mode}

metrics = {
    "official_pdf": {
        "path": str(PDF),
        "bytes": PDF.stat().st_size,
        "sha256": sha256(PDF),
        "pages": len(document),
        "page_size_pt": [page.rect.width, page.rect.height],
    },
    "current_sole_source": {
        "path": str(SOURCE),
        "bytes": SOURCE.stat().st_size,
        "sha256": sha256(SOURCE),
        "font_declarations": font_declarations,
        "token_counts": {
            "resizebox": source_text.count("\\resizebox"),
            "scalebox": source_text.count("\\scalebox"),
            "transform_shape": source_text.count("transform shape"),
            "explicit_tikz_scale_option": len(re.findall(r"(?<![A-Za-z])scale\s*=", source_text)),
        },
    },
    "locator": {
        "physical_page": 661,
        "printed_page_visible": 648,
        "figure_label_visible": "图 32.9",
        "caption_visible": "固定窗口内的正经验自相关增大方差权重，因而使同长度轨迹的有效样本量减小。",
    },
    "acf_semantics": {
        "lags": [0, 1, 2, 3, 4, 5, 6],
        "rho_hat": rho.tolist(),
        "sum_rho_hat_k1_to_6": float(rho[1:].sum()),
        "sum_k_times_rho_hat_k1_to_6": float(np.dot(np.arange(1, 7), rho[1:])),
        "tau_hat_symbolic": "8.32 - 22.42/n",
        "tau_hat_at_smallest_integer_n_gt_6": float(8.32 - 22.42 / 7),
        "n_eff_over_n_at_n_7": float(1 / (8.32 - 22.42 / 7)),
        "toeplitz_7x7_eigenvalues": [float(value) for value in np.linalg.eigvalsh(toeplitz)],
    },
    "figure_region_span_count": len(spans),
    "view_dimensions": view_dimensions,
}
(ROOT / "objective_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


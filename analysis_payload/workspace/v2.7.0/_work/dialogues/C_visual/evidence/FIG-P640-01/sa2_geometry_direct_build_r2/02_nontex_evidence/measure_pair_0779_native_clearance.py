from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
AXIS = ROOT / "pair_0779_axis_mask_300dpi.png"
MARKER = ROOT / "pair_0779_marker_mask_300dpi.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


axis = np.asarray(Image.open(AXIS)) > 0
marker = np.asarray(Image.open(MARKER)) > 0
axis_y, axis_x = np.where(axis)
marker_y, marker_x = np.where(marker)
axis_points = np.stack([axis_y, axis_x], axis=1)
marker_points = np.stack([marker_y, marker_x], axis=1)

best_squared: int | None = None
nearest_axis: list[int] | None = None
nearest_marker: list[int] | None = None
for marker_point in marker_points:
    distances = ((axis_points - marker_point) ** 2).sum(axis=1)
    index = int(distances.argmin())
    candidate = int(distances[index])
    if best_squared is None or candidate < best_squared:
        best_squared = candidate
        nearest_axis = axis_points[index].tolist()
        nearest_marker = marker_point.tolist()

if best_squared is None or nearest_axis is None or nearest_marker is None:
    raise RuntimeError("empty mask")

dy = abs(nearest_axis[0] - nearest_marker[0])
dx = abs(nearest_axis[1] - nearest_marker[1])
chebyshev = max(dx, dy)
result = {
    "evidence_kind": "PAIR_0779_NATIVE300DPI_MASK_CLEARANCE",
    "axis_mask": {"path": str(AXIS), "bytes": AXIS.stat().st_size, "sha256": sha256(AXIS)},
    "marker_mask": {"path": str(MARKER), "bytes": MARKER.stat().st_size, "sha256": sha256(MARKER)},
    "shared_foreground_pixel_count": int((axis & marker).sum()),
    "nearest_axis_pixel_yx": nearest_axis,
    "nearest_marker_pixel_yx": nearest_marker,
    "euclidean_foreground_center_distance_px": best_squared ** 0.5,
    "chebyshev_foreground_center_distance_px": chebyshev,
    "manhattan_foreground_center_distance_px": dx + dy,
    "orthogonal_blank_pixel_gap": max(0, chebyshev - 1),
    "required_orthogonal_blank_pixel_gap": 3,
    "axis_foreground_bbox_xy_inclusive": [int(axis_x.min()), int(axis_y.min()), int(axis_x.max()), int(axis_y.max())],
    "marker_foreground_bbox_xy_inclusive": [int(marker_x.min()), int(marker_y.min()), int(marker_x.max()), int(marker_y.max())],
}
(ROOT / "pair_0779_native_clearance.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=True, indent=2))

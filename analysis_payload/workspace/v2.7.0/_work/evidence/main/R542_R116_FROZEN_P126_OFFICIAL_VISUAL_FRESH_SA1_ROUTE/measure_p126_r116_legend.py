from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def runs(bits: np.ndarray) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(bits.tolist() + [False]):
        if value and start is None:
            start = index
        elif not value and start is not None:
            result.append((start, index - 1))
            start = None
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    image = Image.open(args.image).convert("RGB")
    rgb = np.asarray(image)
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)

    # The project palette makes the x2 key green-dominant and the x1 key
    # blue-dominant.  Black label glyphs and the gray axis fail both masks.
    teal = (r < 120) & (g > 75) & (b > 55) & (g >= b)
    blue = (r < 120) & (b > 75) & (b >= g + 12)

    # Only the upper 70% of this dedicated legend ROI can contain the samples.
    cutoff = int(image.height * 0.70)
    teal_cols = teal[:cutoff, :].any(axis=0)
    blue_cols = blue[:cutoff, :].any(axis=0)
    teal_runs = runs(teal_cols)
    blue_runs = runs(blue_cols)

    teal_lengths = [end - start + 1 for start, end in teal_runs]
    teal_gaps = [teal_runs[i + 1][0] - teal_runs[i][1] - 1 for i in range(len(teal_runs) - 1)]
    blue_lengths = [end - start + 1 for start, end in blue_runs]

    report = {
        "schema_version": 1,
        "image": str(args.image.resolve()),
        "image_size_px": [image.width, image.height],
        "teal_occupied_runs_xy": [list(item) for item in teal_runs],
        "teal_run_lengths_px": teal_lengths,
        "teal_internal_blank_runs_px": teal_gaps,
        "blue_occupied_runs_xy": [list(item) for item in blue_runs],
        "blue_run_lengths_px": blue_lengths,
        "expected_teal_run_count": 4,
        "expected_blue_run_count": 1,
        "result": "PASS"
        if len(teal_runs) == 4
        and len(blue_runs) == 1
        and min(teal_gaps, default=0) >= 4
        else "FAIL",
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

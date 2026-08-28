from __future__ import annotations

import csv
import math
import re
from pathlib import Path

import numpy as np


ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa2_r111_r168_readonly_adjudication_v1"
)
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_simplex_geometry.tex"
)


def point_line_distance(point: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    edge = b - a
    return abs(float(np.cross(edge, point - a))) / float(np.linalg.norm(edge))


def orthogonal_projection(point: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    edge = b - a
    return a + edge * float(np.dot(point - a, edge) / np.dot(edge, edge))


def main() -> None:
    e1 = np.array([0.0, 0.0])
    e2 = np.array([7.0, 0.0])
    e3 = np.array([3.5, 6.062])
    theta_point = np.array([3.85, 3.031])

    affine = np.array(
        [
            [e1[0], e2[0], e3[0]],
            [e1[1], e2[1], e3[1]],
            [1.0, 1.0, 1.0],
        ]
    )
    target = np.array([theta_point[0], theta_point[1], 1.0])
    weights = np.linalg.solve(affine, target)

    opposite_edges = [(e2, e3), (e1, e3), (e1, e2)]
    vertices = [e1, e2, e3]
    labels = ["theta_1", "theta_2", "theta_3"]
    claimed = [0.2, 0.3, 0.5]

    geometry_path = ROOT / "06_machine_tables" / "simplex_geometry_machine.csv"
    with geometry_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "coordinate",
                "barycentric_weight",
                "claimed_label_value",
                "distance_ratio_to_opposite_edge",
                "projection_x",
                "projection_y",
                "absolute_difference_weight_vs_claim",
                "absolute_difference_distance_ratio_vs_claim",
            ]
        )
        for label, weight, expected, vertex, (a, b) in zip(
            labels, weights, claimed, vertices, opposite_edges
        ):
            point_distance = point_line_distance(theta_point, a, b)
            altitude = point_line_distance(vertex, a, b)
            ratio = point_distance / altitude
            projection = orthogonal_projection(theta_point, a, b)
            writer.writerow(
                [
                    label,
                    f"{weight:.12f}",
                    f"{expected:.12f}",
                    f"{ratio:.12f}",
                    f"{projection[0]:.12f}",
                    f"{projection[1]:.12f}",
                    f"{abs(weight - expected):.3e}",
                    f"{abs(ratio - expected):.3e}",
                ]
            )

    summary_path = ROOT / "06_machine_tables" / "simplex_geometry_summary_machine.txt"
    side_lengths = [
        float(np.linalg.norm(e2 - e1)),
        float(np.linalg.norm(e3 - e2)),
        float(np.linalg.norm(e1 - e3)),
    ]
    summary_path.write_text(
        "\n".join(
            [
                f"SIDE_E1_E2={side_lengths[0]:.12f}",
                f"SIDE_E2_E3={side_lengths[1]:.12f}",
                f"SIDE_E3_E1={side_lengths[2]:.12f}",
                f"MAX_SIDE_MIN_SIDE_RATIO={max(side_lengths) / min(side_lengths):.12f}",
                f"BARYCENTRIC_SUM={float(weights.sum()):.12f}",
                f"BARYCENTRIC_MIN={float(weights.min()):.12f}",
                f"BARYCENTRIC_MAX={float(weights.max()):.12f}",
                f"AFFINE_RECONSTRUCTION_X={float(weights @ np.array([e1[0], e2[0], e3[0]])):.12f}",
                f"AFFINE_RECONSTRUCTION_Y={float(weights @ np.array([e1[1], e2[1], e3[1]])):.12f}",
                "MACHINE_FIELDS_ONLY=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    source = SOURCE.read_text(encoding="utf-8")
    alt_match = re.search(r"alt=\{对象—关系—结论：(.*?)\}\]", source, re.DOTALL)
    caption_match = re.search(r"\\caption\{(.*?)\}\s*\\label", source, re.DOTALL)
    if alt_match is None or caption_match is None:
        raise RuntimeError("Could not parse current alt/caption strings")
    alt_semantics = re.sub(r"\s+", "", alt_match.group(1))
    caption_semantics = re.sub(r"\s+", "", caption_match.group(1))
    semantics_path = ROOT / "06_machine_tables" / "alt_caption_machine_comparison.csv"
    with semantics_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "alt_semantics",
                "caption_semantics",
                "normalized_exact_equal",
                "alt_character_count",
                "caption_character_count",
            ]
        )
        writer.writerow(
            [
                alt_semantics,
                caption_semantics,
                str(alt_semantics == caption_semantics).lower(),
                len(alt_semantics),
                len(caption_semantics),
            ]
        )


if __name__ == "__main__":
    main()

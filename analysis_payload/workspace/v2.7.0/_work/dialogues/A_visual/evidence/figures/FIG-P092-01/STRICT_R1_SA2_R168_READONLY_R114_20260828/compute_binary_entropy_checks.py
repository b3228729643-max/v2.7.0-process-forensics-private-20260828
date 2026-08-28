from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P092-01\STRICT_R1_SA2_R168_READONLY_R114_20260828")


def h2(p: float) -> float:
    if p in (0.0, 1.0):
        return 0.0
    return -(p * math.log(p) + (1.0 - p) * math.log(1.0 - p)) / math.log(2.0)


def first_derivative(p: float) -> float:
    return math.log((1.0 - p) / p) / math.log(2.0)


def second_derivative(p: float) -> float:
    return -1.0 / (math.log(2.0) * p * (1.0 - p))


def main() -> None:
    sample_points = [0.0, 0.001, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 0.999, 1.0]
    with (ROOT / "machine_binary_entropy_samples.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(["p", "H2_bits", "H2_1_minus_p", "symmetry_abs_residual"])
        for p in sample_points:
            value = h2(p)
            reflected = h2(1.0 - p)
            writer.writerow(
                [
                    f"{p:.12g}",
                    f"{value:.15g}",
                    f"{reflected:.15g}",
                    f"{abs(value - reflected):.3e}",
                ]
            )

    interior = [0.001, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 0.999]
    checks = {
        "formula": "-(p*ln(p)+(1-p)*ln(1-p))/ln(2)",
        "endpoint_values": {"H2(0)": h2(0.0), "H2(1)": h2(1.0)},
        "center_value": {"H2(0.5)": h2(0.5)},
        "first_derivative_at_center": first_derivative(0.5),
        "second_derivative_samples": {
            f"p={p:g}": second_derivative(p) for p in interior
        },
        "maximum_sample_value": max(h2(p) for p in sample_points),
        "maximum_sample_locations": [
            p for p in sample_points if h2(p) == max(h2(x) for x in sample_points)
        ],
        "maximum_symmetry_abs_residual": max(abs(h2(p) - h2(1.0 - p)) for p in sample_points),
        "source_domain_contract": "curve samples p in [0.001,0.999]; explicit markers supply p=0 and p=1 endpoint values",
    }
    (ROOT / "machine_binary_entropy_checks.json").write_text(
        json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(checks, ensure_ascii=True))


if __name__ == "__main__":
    main()

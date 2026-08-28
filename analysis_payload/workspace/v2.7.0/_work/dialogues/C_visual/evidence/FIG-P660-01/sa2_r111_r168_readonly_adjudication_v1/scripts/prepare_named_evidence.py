from __future__ import annotations

import csv
import shutil
from pathlib import Path


ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa2_r111_r168_readonly_adjudication_v1"
)


def expand_span_refs(value: str) -> list[str]:
    result: list[str] = []
    for part in value.split(" plus ")[0].split(","):
        part = part.strip()
        if not part.startswith("S"):
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            for number in range(int(start[1:]), int(end[1:]) + 1):
                result.append(f"S{number:03d}")
        else:
            result.append(part)
    return result


def main() -> None:
    copies = {
        ROOT / "03_renders" / "r111_integration_200dpi-709.png": ROOT
        / "03_renders"
        / "after_full_page_200dpi.png",
        ROOT / "03_renders" / "after_figure_crop_native_300dpi.png": ROOT
        / "03_renders"
        / "after_figure_crop_300dpi.png",
        ROOT / "03_renders" / "after_grayscale_native_300dpi.png": ROOT
        / "03_renders"
        / "after_grayscale_300dpi.png",
        ROOT / "04_overlays_masks" / "text_measurement_overlay_native_300dpi.png": ROOT
        / "04_overlays_masks"
        / "after_text_measurement_overlay_300dpi.png",
        ROOT / "06_machine_tables" / "object_pixel_metrics.csv": ROOT
        / "06_machine_tables"
        / "after_pixel_measurements.csv",
        ROOT / "06_machine_tables" / "all_unordered_pairs_machine.csv": ROOT
        / "06_machine_tables"
        / "after_overlap_report.csv",
    }
    for source, target in copies.items():
        shutil.copyfile(source, target)

    with (ROOT / "07_manual" / "visible_object_denominator.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        objects = list(csv.DictReader(handle))
    with (ROOT / "06_machine_tables" / "page709_text_spans.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        spans = {row["span_id"]: row for row in csv.DictReader(handle)}
    with (ROOT / "06_machine_tables" / "object_pixel_metrics.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        metrics = {row["object_id"]: row for row in csv.DictReader(handle)}

    output = ROOT / "06_machine_tables" / "after_font_audit.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "element_id",
                "source_lines",
                "semantic_role",
                "text_sample",
                "declared_pt_if_in_figure_source",
                "graphics_scale_if_in_figure_source",
                "effective_pt_if_in_figure_source",
                "pdf_base_span_size_pt_max",
                "pdf_base_span_size_pt_median",
                "pdf_span_refs",
            ]
        )
        for obj in objects:
            object_id = obj["object_id"]
            if obj["kind"] not in {"TEXT", "FORMULA"}:
                continue
            ref_ids = expand_span_refs(obj["pdf_refs"])
            sizes = sorted(float(spans[ref]["font_size_pt"]) for ref in ref_ids if ref in spans)
            median = ""
            if sizes:
                middle = len(sizes) // 2
                median = sizes[middle] if len(sizes) % 2 else (sizes[middle - 1] + sizes[middle]) / 2
            metric = metrics[object_id]
            writer.writerow(
                [
                    object_id,
                    obj["source_lines"],
                    obj["semantic_role"],
                    obj["content_or_scope"],
                    metric["declared_pt_if_in_figure_source"],
                    metric["graphics_scale"],
                    metric["effective_pt_if_in_figure_source"],
                    f"{max(sizes):.4f}" if sizes else "",
                    f"{median:.4f}" if sizes else "",
                    ";".join(ref_ids),
                ]
            )

    summary = ROOT / "06_machine_tables" / "named_evidence_machine.txt"
    summary.write_text(
        "\n".join(
            [
                "after_full_page_200dpi.png=copy of native Poppler physical-page-709 integration render",
                "after_figure_crop_300dpi.png=copy of native 300 dpi page crop without resizing",
                "after_grayscale_300dpi.png=grayscale conversion of the same native crop",
                "after_text_measurement_overlay_300dpi.png=copy of object-linked text bbox overlay",
                "after_font_audit.csv=machine source/PDF span font table without verdict fields",
                "after_pixel_measurements.csv=machine native-pixel object measurements without verdict fields",
                "after_overlap_report.csv=machine enumeration of all 435 unordered object pairs without manual fields",
                "MACHINE_FIELDS_ONLY=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

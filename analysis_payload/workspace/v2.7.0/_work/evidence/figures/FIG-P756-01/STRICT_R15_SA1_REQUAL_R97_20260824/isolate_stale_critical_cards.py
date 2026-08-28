"""Isolate prior critical-card generations without touching current evidence."""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

OUT = Path(__file__).resolve().parent
CURRENT_INDEX = OUT / "critical_pair_index.csv"
CURRENT_CARD_INDEX = OUT / "critical_pair_review_card_index.csv"
SUPER = OUT / "SUPERSEDED__DO_NOT_USE"

def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False

def move(src: Path, dst: Path) -> None:
    if not inside(src, OUT) or not inside(dst, OUT):
        raise RuntimeError(f"unsafe path: {src} -> {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise RuntimeError(f"refuse overwrite: {dst}")
    shutil.move(str(src), str(dst))

def main() -> None:
    current = list(csv.DictReader(CURRENT_INDEX.open(encoding="utf-8-sig")))
    card_index = list(csv.DictReader(CURRENT_CARD_INDEX.open(encoding="utf-8-sig")))
    if len(current) != 32 or len(card_index) != 32:
        raise RuntimeError(f"current final critical cardinality is not 32: index={len(current)}, cards={len(card_index)}")
    current_review_names = {Path(r["CARD"]).name for r in card_index}
    current_direct_names = set()
    for row in current:
        for rel in row["PIXEL_EVIDENCE"].split(";"):
            current_direct_names.add(Path(rel).name)
    if len(current_direct_names) != 160:
        raise RuntimeError(f"expected 32x5 current direct evidence files, got {len(current_direct_names)}")
    movements = []
    review_dir = OUT / "critical_pair_review_cards"
    for src in sorted(review_dir.glob("*.png")):
        if src.name in current_review_names:
            continue
        pair = src.stem.replace("_5up", "")
        generation = "PRIOR_69_OBJECT_35_CARD_SET" if pair in {"PAIR_0473", "PAIR_0711", "PAIR_1423"} else "PRIOR_64_OBJECT_OR_PRE_ZORDER_CARD_SET"
        dst = SUPER / "critical_pair_review_cards" / src.name
        move(src, dst)
        movements.append({"KIND": "REVIEW_5UP", "PAIR_ID": pair, "GENERATION": generation,
                          "OLD_PATH": str(src.relative_to(OUT)), "SUPERSEDED_PATH": str(dst.relative_to(OUT))})
    direct_dir = OUT / "critical_pair_cards"
    for src in sorted(direct_dir.glob("*.png")):
        if src.name in current_direct_names:
            continue
        dst = SUPER / "critical_pair_cards" / src.name
        move(src, dst)
        movements.append({"KIND": "DIRECT_COMPONENT", "PAIR_ID": "", "GENERATION": "PRIOR_64_OBJECT_OR_PRE_ZORDER_CARD_SET",
                          "OLD_PATH": str(src.relative_to(OUT)), "SUPERSEDED_PATH": str(dst.relative_to(OUT))})
    with (SUPER / "critical_card_supersession.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["KIND", "PAIR_ID", "GENERATION", "OLD_PATH", "SUPERSEDED_PATH"])
        writer.writeheader(); writer.writerows(movements)
    # These rows are not omitted relations. They remain in object_pair_report;
    # native final-mask remeasurement moved them beyond the <12px review-card
    # trigger used by the final 69-object run.
    all_pairs = {r["PAIR_ID"]: r for r in csv.DictReader((OUT / "object_pair_report.csv").open(encoding="utf-8-sig"))}
    delta = []
    for pair, why in [
        ("PAIR_0473", "badge-1 digit to station-1 rim: final native clearance 25.079872px; badge FILL/STROKE split and z-order ownership removed the pre-split parent-mask candidate"),
        ("PAIR_0711", "badge-5 digit to station-5 rim: final native clearance 25.079872px; badge FILL/STROKE split and z-order ownership removed the pre-split parent-mask candidate"),
        ("PAIR_1423", "station-1 rim to feedback shaft: final native clearance 17.029386px; final z-order mask leaves the feedback route clear of the station"),
    ]:
        r = all_pairs[pair]
        delta.append({"PAIR_ID": pair, "OBJECT_A": r["OBJECT_A"], "OBJECT_B": r["OBJECT_B"],
                      "FINAL_NATIVE_OVERLAP_PX": r["OVERLAP_PIXELS"], "FINAL_NATIVE_CLEARANCE_PX": r["MIN_CLEARANCE_PX"],
                      "FINAL_STATUS": r["STATUS"], "REMOVAL_REASON": why,
                      "RETAINED_IN_FULL_PAIR_TABLE": "YES", "CURRENT_CRITICAL_CARD": "NO (>=12px trigger)"})
    with (OUT / "critical_set_delta_35_to_32.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(delta[0])); writer.writeheader(); writer.writerows(delta)
    remaining_review = sorted(review_dir.glob("*.png"))
    remaining_direct = sorted(direct_dir.glob("*.png"))
    if len(remaining_review) != 32 or {p.name for p in remaining_review} != current_review_names:
        raise RuntimeError("current review-card directory did not reduce exactly to the current 32")
    if len(remaining_direct) != 160 or {p.name for p in remaining_direct} != current_direct_names:
        raise RuntimeError("current direct-card directory did not reduce exactly to the current 32x5")
    print(f"isolated={len(movements)} current_review={len(remaining_review)} current_direct={len(remaining_direct)}")

if __name__ == "__main__":
    main()

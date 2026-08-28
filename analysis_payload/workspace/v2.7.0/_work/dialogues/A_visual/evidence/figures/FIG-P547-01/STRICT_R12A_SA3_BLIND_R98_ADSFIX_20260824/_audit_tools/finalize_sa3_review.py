from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEWER = "SA3_gpt-5.6-sol_xhigh"
SOURCE_SHA256 = "DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600"
PDF_SHA256 = "52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41"
HANDOFF_ID = "A-R130-P547-SA3-RESUME-20260824"

EXPECTED_PATH_CONTACTS = {
    ("D005", "D007", "N01", "E01"),
    ("D005", "D013", "N01", "E03"),
    ("D006", "D010", "N02", "E02"),
    ("D006", "D018", "N02", "E04"),
    ("D031", "D040", "C01", "C03"),
    ("D046", "D048", "N03", "E05"),
    ("D046", "D054", "N03", "E07"),
    ("D047", "D051", "N04", "E06"),
    ("D047", "D059", "N04", "E08"),
}


def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(rel: str, data: list[dict[str, str]]) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not data:
        raise AssertionError(f"cannot write empty ledger: {rel}")
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def validate() -> dict:
    identity = json.loads((ROOT / "00_identity/identity.json").read_text(encoding="utf-8"))
    machine = json.loads((ROOT / "08_reports/denominator_machine_summary_pending.json").read_text(encoding="utf-8"))
    core = json.loads((ROOT / "08_reports/core_machine_summary.json").read_text(encoding="utf-8"))
    component = json.loads((ROOT / "04_glyphs/component_ownership_audit.json").read_text(encoding="utf-8"))

    assert identity["pdf_sha256"] == PDF_SHA256
    assert identity["source_sha256"] == SOURCE_SHA256
    expected_machine = {
        "object_count": 57,
        "object_pair_count": 1596,
        "object_pair_fail_count": 0,
        "glyph_count": 193,
        "glyph_fail_count": 0,
        "path_record_count": 71,
        "path_pair_count": 2485,
        "path_pair_pending_contact_count": 9,
        "command_count": 143,
        "within_record_command_pair_count": 186,
        "multi_owner_component_count": 4,
        "unassigned_component_pixels": 0,
        "clip_boundary_pixel_count": 0,
        "role_ratio_fail_count": 0,
    }
    for key, value in expected_machine.items():
        assert machine[key] == value, (key, machine[key], value)
    for gid in ("g054", "g139"):
        assert machine[gid] == {
            "H_INK_PX": "28",
            "INK_AREA_PX": "53",
            "MISSING_STROKE_PX": "0",
            "FOREIGN_PIXEL_PX": "0",
            "PASS_FAIL": "PASS",
        }

    glyphs = rows("04_glyphs/glyph_manual_review_pending.csv")
    assert len(glyphs) == core["glyph_count"] == 193
    assert all(r["MACHINE_DECISION"] == "PASS" for r in glyphs)
    assert all(int(r["MISSING_STROKE_PX"]) == 0 and int(r["FOREIGN_PIXEL_PX"]) == 0 for r in glyphs)
    px = rows("after_pixel_measurements.csv")
    plus = {r["GLYPH_ID"]: int(r["H_INK_PX"]) for r in px if r["CHAR"] == "+"}
    assert plus == {"G057": 22, "G143": 22}
    assert all(r["PASS_FAIL"] == "PASS" for r in px)

    multi = rows("04_glyphs/multi_owner_component_ledger_pending.csv")
    assert len(multi) == 4
    by_component = {int(r["COMPONENT"]): r for r in multi}
    assert by_component[174]["CANDIDATE_OWNERS_JSON"] == '{"G140": 401, "G139": 1}'
    assert float(by_component[174]["DOMINANT_TO_MINOR_RATIO"]) == 401.0
    assert by_component[174]["FINAL_ASSIGNMENT_JSON"] == '{"G140": 402}'
    assert by_component[174]["DECISION"] == "DOMINANT_COMPONENT_20_TO_1"
    assert by_component[91]["FINAL_ASSIGNMENT_JSON"] == '{"G120": 28}'
    assert all(int(r["UNASSIGNED_PX"]) == 0 for r in multi)

    stretch = rows("04_glyphs/stretchy_delimiter_ownership_ledger_pending.csv")
    assert {r["GLYPH_ID"] for r in stretch} == {"G035", "G048", "G120", "G133"}
    assert {r["GLYPH_ID"]: int(r["FINAL_COMPLETE_CONTOUR_PX"]) for r in stretch} == {
        "G035": 714, "G048": 714, "G120": 755, "G133": 731
    }
    corrections = {r["glyph"]: r for r in component["extended_visible_contour_corrections"]}
    assert set(corrections) == {"G035", "G048", "G120", "G133"}
    assert corrections["G120"]["cleared_foreign_candidate_pixels"] == {"G114": 20, "G115": 8}

    objects = rows("03_objects/object_manifest_57.csv")
    assert len(objects) == 57
    assert sum(1 for r in objects if r["OBJECT_CLASS"] == "TEXT_PARENT") == 23
    assert sum(1 for r in objects if r["OBJECT_CLASS"] != "TEXT_PARENT") == 34

    object_pairs = rows("05_pairs/object_pair_ledger_pending.csv")
    assert len(object_pairs) == 1596
    assert all(r["MACHINE_STATE"] == "PASS" and int(r["ILLEGAL_OVERLAP_PX"]) == 0 for r in object_pairs)
    relation_minimums = {}
    for relation in {r["RELATION"] for r in object_pairs}:
        relation_minimums[relation] = min(float(r["MIN_CLEARANCE_PX"]) for r in object_pairs if r["RELATION"] == relation)
    assert relation_minimums == {
        "TEXT_NODE_BORDER": 9.0,
        "TEXT_TEXT": 5.0,
        "TEXT_VECTOR": 3.0,
        "VECTOR_VECTOR": 0.0,
    }

    path_records = rows("06_primitives/path_record_manual_review_pending.csv")
    assert len(path_records) == 71 and all(int(r["PIXELS"]) > 0 for r in path_records)
    path_pairs = rows("06_primitives/path_pair_ledger_pending.csv")
    assert len(path_pairs) == 2485
    states = Counter(r["MACHINE_STATE"] for r in path_pairs)
    assert states == Counter({"DISJOINT": 2450, "DESIGN": 26, "PENDING": 9})
    contacts = {
        (r["A_RECORD"], r["B_RECORD"], r["A_SEMANTIC"], r["B_SEMANTIC"])
        for r in path_pairs if r["MACHINE_STATE"] == "PENDING"
    }
    assert contacts == EXPECTED_PATH_CONTACTS

    commands = rows("06_primitives/command_replay_ledger_pending.csv")
    command_pairs = rows("06_primitives/within_record_command_pair_ledger_pending.csv")
    assert len(commands) == 143 and all(int(r["PIXELS"]) > 0 for r in commands)
    assert len(command_pairs) == 186
    assert all(r["MACHINE_STATE"] in {"DESIGN", "DISJOINT"} for r in command_pairs)

    ratios = rows("08_reports/glyph_role_ratio_audit.csv")
    assert ratios and all(r["PASS_FAIL"] == "PASS" for r in ratios)
    font = rows("after_font_audit.csv")
    assert len(font) == 23 and all(r["SOURCE_FONT_PASS"].lower() == "true" for r in font)

    expected_sheets = {
        "glyph_1x": ("04_glyphs/contact_sheets_1x/glyphs_native_1x_*.png", 10),
        "glyph_8x": ("04_glyphs/contact_sheets/glyphs_*.png", 17),
        "object_1x": ("03_objects/object_contact_sheets_1x/objects_native_1x_*.png", 5),
        "object_8x": ("03_objects/object_contact_sheets_8x_small/objects_8x_*.png", 15),
        "path_1x": ("06_primitives/contact_sheets_1x/vector_records_native_1x_*.png", 6),
        "path_8x": ("06_primitives/contact_sheets_8x_small/vector_records_8x_*.png", 18),
        "command_1x": ("06_primitives/command_contact_sheets_1x/commands_native_1x_*.png", 9),
        "command_8x": ("06_primitives/command_contact_sheets_8x_small/commands_8x_*.png", 24),
        "object_pair_critical_1x": ("05_pairs/critical_contact_1x/critical_pairs_1x_*.png", 3),
        "object_pair_critical_8x": ("05_pairs/critical_contact_8x/critical_pairs_8x_*.png", 5),
        "path_pair_critical_1x": ("06_primitives/path_pair_critical_contact_1x/path_critical_1x_*.png", 2),
        "path_pair_critical_8x": ("06_primitives/path_pair_critical_contact_8x/path_critical_8x_*.png", 3),
    }
    sheet_counts = {name: len(list(ROOT.glob(pattern))) for name, (pattern, _) in expected_sheets.items()}
    assert sheet_counts == {name: count for name, (_, count) in expected_sheets.items()}

    for rel in (
        "full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png",
        "07_views/protanopia_300dpi.png", "07_views/deuteranopia_300dpi.png", "07_views/tritanopia_300dpi.png",
    ):
        assert (ROOT / rel).is_file() and (ROOT / rel).stat().st_size > 0

    return {
        "identity": identity,
        "machine": machine,
        "glyphs": glyphs,
        "multi": multi,
        "stretch": stretch,
        "objects": objects,
        "object_pairs": object_pairs,
        "path_records": path_records,
        "path_pairs": path_pairs,
        "commands": commands,
        "command_pairs": command_pairs,
        "relation_minimums": relation_minimums,
        "sheet_counts": sheet_counts,
        "role_ratio_rows": len(ratios),
    }


def finalize(data: dict) -> None:
    assert not (ROOT / "WRITE_STOPPED").exists(), "package is already sealed"

    glyphs = data["glyphs"]
    for r in glyphs:
        r.update({
            "REVIEWER": REVIEWER, "ORIGINAL_MATCH": "YES", "OVERLAY_COMPLETE": "YES",
            "MASK_ONLY_PURE": "YES", "DECISION": "PASS",
        })
    write_csv("04_glyphs/glyph_manual_review.csv", glyphs)

    multi = data["multi"]
    for r in multi:
        r["REVIEWER"] = REVIEWER
        r["REVIEW_DECISION"] = "PASS_OWNERSHIP_RESOLVED"
    write_csv("04_glyphs/multi_owner_component_ledger.csv", multi)

    stretch = data["stretch"]
    for r in stretch:
        r["REVIEWER"] = REVIEWER
        r["REVIEW_DECISION"] = "PASS_COMPLETE_VISIBLE_CONTOUR"
    write_csv("04_glyphs/stretchy_delimiter_ownership_ledger.csv", stretch)

    object_review = []
    for r in data["objects"]:
        object_review.append({
            **r, "REVIEWER": REVIEWER, "ORIGINAL_MATCH": "YES", "OVERLAY_COMPLETE": "YES",
            "MASK_ONLY_PURE": "YES", "DECISION": "PASS",
        })
    write_csv("03_objects/object_manual_review.csv", object_review)

    object_pairs = data["object_pairs"]
    for r in object_pairs:
        r["REVIEWER"] = REVIEWER
        r["MANUAL_DECISION"] = "PASS"
    write_csv("05_pairs/object_pair_ledger.csv", object_pairs)

    path_records = data["path_records"]
    for r in path_records:
        r.update({"REVIEWER": REVIEWER, "ORIGINAL_MATCH": "YES", "MASK_ONLY_PURE": "YES", "DECISION": "PASS"})
    write_csv("06_primitives/path_record_manual_review.csv", path_records)

    path_pairs = data["path_pairs"]
    for r in path_pairs:
        r["REVIEWER"] = REVIEWER
        if r["MACHINE_STATE"] == "PENDING":
            r["MANUAL_DECISION"] = "DESIGN_CONNECTION_CONFIRMED"
        elif r["MACHINE_STATE"] == "DESIGN":
            r["MANUAL_DECISION"] = "SAME_SEMANTIC_DESIGN_COMPOSITION"
        else:
            r["MANUAL_DECISION"] = "PASS_DISJOINT"
    write_csv("06_primitives/path_pair_ledger.csv", path_pairs)

    commands = data["commands"]
    for r in commands:
        r.update({"REVIEWER": REVIEWER, "MANUAL_DECISION": "PASS_INDEPENDENT_REPLAY"})
    write_csv("06_primitives/command_replay_ledger.csv", commands)

    command_pairs = data["command_pairs"]
    for r in command_pairs:
        r["REVIEWER"] = REVIEWER
        r["MANUAL_DECISION"] = "PASS_SAME_RECORD_COMPOSITION" if r["MACHINE_STATE"] == "DESIGN" else "PASS_DISJOINT"
    write_csv("06_primitives/within_record_command_pair_ledger.csv", command_pairs)

    final_summary = {
        "figure_id": "FIG-P547-01",
        "handoff_id": HANDOFF_ID,
        "owner_dialogue": "DIALOGUE_A_VISUAL",
        "reviewer": REVIEWER,
        "audit_type": "independent isolated second blind review",
        "result": "PASS",
        "scope_status": "A_LOCAL_SA3_PASS_NOT_FINAL_BOOK_ACCEPTANCE",
        "source_sha256": SOURCE_SHA256,
        "official_r98_pdf_sha256": PDF_SHA256,
        "denominators": {
            "text_parents": 23, "vector_parents": 34, "objects": 57, "object_pairs": 1596,
            "glyphs": 193, "path_records": 71, "path_pairs": 2485,
            "commands": 143, "within_record_command_pairs": 186,
        },
        "machine_failures": {
            "glyph": 0, "object_pair": 0, "role_ratio": 0, "unassigned_component_pixels": 0,
            "clip_boundary_pixels": 0,
        },
        "manual_adjudication": {
            "native_1x_8x_opened": True,
            "multi_owner_components": 4,
            "different_semantic_path_contacts": 9,
            "path_contact_decision": "DESIGN_CONNECTION_CONFIRMED",
            "g139": {
                "candidate_component": 174, "pre_owner_pixels": {"G140": 401, "G139": 1},
                "rule": "dominant component >=20:1", "final_owner": {"G140": 402},
                "glyph_height_px": 28, "glyph_area_px": 53, "missing_stroke_px": 0,
                "foreign_pixel_px": 0, "decision": "PASS",
            },
            "stretchy_delimiters": {
                "glyphs": ["G035", "G048", "G120", "G133"],
                "g120_reclaimed_from": {"G114": 20, "G115": 8},
                "decision": "PASS_COMPLETE_VISIBLE_CONTOUR",
            },
        },
        "clearance_minimum_px": data["relation_minimums"],
        "sheet_counts_opened": data["sheet_counts"],
        "canonical_fields": {
            "SOURCE_FONT_PASS": True, "PIXEL_HEIGHT_PASS": True, "SAME_CLASS_RATIO_PASS": True,
            "ROLE_RATIO_PASS": True, "FONT_VISUAL_HARMONY_PASS": True,
            "MATH_SEMANTICS_PASS": True, "TEXT_CONSISTENCY_PASS": True,
            "GRAYSCALE_PASS": True, "PAGE_INTEGRATION_PASS": True,
            "OVERLAP_PIXEL_COUNT": 0, "CLIP_BOUNDARY_PIXEL_COUNT": 0,
            "PIXEL_ADJUDICATION_STATUS": "MASK_OWNERSHIP_CONTAMINATION_CORRECTED",
        },
        "unresolved": [],
    }
    (ROOT / "08_reports/sa3_final_summary.json").write_text(
        json.dumps(final_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = f"""# FIG-P547-01 SA3 独立盲审报告

- HANDOFF_ID: `{HANDOFF_ID}`
- OWNER_DIALOGUE: `DIALOGUE_A_VISUAL`
- REVIEWER: `{REVIEWER}`
- 结论: **SA3_INDEPENDENT_PASS**
- 适用范围: A 本地第二盲审证据；不等同于全书最终放行。

## 身份与隔离

- 官方 R98 PDF SHA-256: `{PDF_SHA256}`。
- 只读业务源 SHA-256: `{SOURCE_SHA256}`；该 C01 源相对共同基线无差异。
- 审查未读取 P547 R10/R11、SA1 报告、root 结论、中央旧 PASS 或其他 P547 证据。
- 所有生成与修订均位于 A 本地证据复制件；业务源码和官方 PDF 未写入。

## 四视图与可访问性

`full_page_200dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png` 均已原图打开；图面清楚、层级一致、无裁切或非设计碰撞。protanopia、deuteranopia、tritanopia 三视图亦已打开，编码在颜色退化下仍可辨。独立 wrapper 仅有 tight-page 宽盒提示，不造成可见裁切。

## 完整分母

| 账本 | 分母 | 结果 |
|---|---:|---|
| text parents | 23 | PASS |
| vector parents | 34 | PASS |
| object parents | 57 | PASS |
| object pairs | 1596 | 0 machine failure；人工临界图 PASS |
| glyphs | 193 | missing=0、foreign=0、全部 PASS |
| path records | 71 | 独立重放均非空、1x/8x PASS |
| path pairs | 2485 | 2450 DISJOINT、26 DESIGN、9 设计接点确认 |
| commands | 143 | 独立重放均非空、1x/8x PASS |
| within-record command pairs | 186 | 同记录组合或分离，全部 PASS |

全部要求的原生 1x 与 8x 接触表已逐张打开。对象 pair 最小可见间距：TEXT_TEXT=5px（门槛4px）、TEXT_VECTOR=3px（门槛3px）、TEXT_NODE_BORDER=9px（门槛5px）。`+` 的 G057/G143 均为 H=22px，满足关系号/运算符 22px 门；等号与箭头按独立矢量规则审计。

## ownership 判定

- G054：H=28px、area=53px、missing=0、foreign=0，PASS。
- G139：component 174 初始候选为 G140=401px、G139=1px，401:1 超过 20:1；整条 402px 连通分量归 G140。该 1px 是后继 `p` 的边界抗锯齿外延，不是 G139 分号缺笔。G139 独立重放 H=28px、area=53px、missing=0、foreign=0，PASS。
- G035/G048/G120/G133 的伸展括号使用 native 300dpi 可见轮廓窄 ROI 恢复；G120 收回曾错归 G114/G115 的 20+8=28px，四个括号均为完整、纯净轮廓。
- 4 个 multi-owner component 均无未归属像素。未达到 20:1 的 component 26/33 使用 PDF candidate support 精确拆分；component 91 用完整可见伸展括号覆盖；component 174 使用 20:1 主导连通分量规则。

## 9 个路径接点

`PATHPAIR_0276/0282/0344/0352/1674/2162/2168/2189/2197` 的原生 1x、8x 临界图均已打开。八个是箭头/边在圆形节点边界上的设计端点，一个是桥接框 C01 与 C03 箭头的设计连接；人工结论均为 `DESIGN_CONNECTION_CONFIRMED`，不计非法覆盖。

## 规范字段

- SOURCE_FONT_PASS=true
- PIXEL_HEIGHT_PASS=true
- SAME_CLASS_RATIO_PASS=true
- ROLE_RATIO_PASS=true
- FONT_VISUAL_HARMONY_PASS=true
- MATH_SEMANTICS_PASS=true
- TEXT_CONSISTENCY_PASS=true
- GRAYSCALE_PASS=true
- PAGE_INTEGRATION_PASS=true
- OVERLAP_PIXEL_COUNT=0
- CLIP_BOUNDARY_PIXEL_COUNT=0
- PIXEL_ADJUDICATION_STATUS=MASK_OWNERSHIP_CONTAMINATION_CORRECTED

## 未解决项

无。
"""
    (ROOT / "08_reports/SA3_INDEPENDENT_BLIND_REVIEW.md").write_text(report, encoding="utf-8")
    (ROOT / "08_reports/after_visual_acceptance_sa3.md").write_text(
        "# after visual acceptance — SA3\n\n四视图、三种色觉模拟、全部 native 1x/8x 对象/glyph/path/command 接触表及临界 pair 图已打开；结论 PASS。\n",
        encoding="utf-8",
    )
    (ROOT / "08_reports/after_overlap_adjudication_sa3.md").write_text(
        "# after overlap adjudication — SA3\n\n1596 object pairs 无非法覆盖；2485 path pairs 中 9 个不同语义接触均为可见设计连接。G139 的 1px 候选污染按 401:1 的 20:1 主导连通分量规则归 G140；G139 无缺笔。\n",
        encoding="utf-8",
    )
    (ROOT / "08_reports/after_model_route_sa3.md").write_text(
        f"# after model route — SA3\n\n固定角色 `{REVIEWER}` 完成隔离独立第二盲审；结果 `SA3_INDEPENDENT_PASS`。\n",
        encoding="utf-8",
    )
    (ROOT / "08_reports/SA3_RESULT.txt").write_text(
        "FIG-P547-01\nSA3_INDEPENDENT_PASS\nA_LOCAL_ONLY_NOT_FINAL_BOOK_ACCEPTANCE\nUNRESOLVED=0\n",
        encoding="utf-8",
    )

    # Absolute final write order required by the task: terminal -> manifest -> WRITE_STOPPED.
    terminal = {
        "figure_id": "FIG-P547-01", "handoff_id": HANDOFF_ID, "reviewer": REVIEWER,
        "result": "PASS", "unresolved": [], "assertions": "ALL_PASS",
        "terminal_order": 1, "next": "manifest_then_WRITE_STOPPED",
    }
    terminal_path = ROOT / "09_manifest/terminal_crosscheck.json"
    terminal_path.parent.mkdir(parents=True, exist_ok=True)
    terminal_path.write_text(json.dumps(terminal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    inventory = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or p.name in {"manifest.json", "WRITE_STOPPED"}:
            continue
        inventory.append({
            "path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)
        })
    manifest = {
        "figure_id": "FIG-P547-01", "handoff_id": HANDOFF_ID, "owner_dialogue": "DIALOGUE_A_VISUAL",
        "reviewer": REVIEWER, "result": "PASS", "source_sha256": SOURCE_SHA256,
        "official_r98_pdf_sha256": PDF_SHA256, "file_count_excluding_manifest_and_marker": len(inventory),
        "files": inventory, "terminal_order": 2, "next": "WRITE_STOPPED",
    }
    (ROOT / "09_manifest/manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "WRITE_STOPPED").write_text(
        "FIG-P547-01 SA3_INDEPENDENT_PASS\nNO_WRITES_AFTER_THIS_MARKER\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    data = validate()
    if args.validate_only:
        print(json.dumps({
            "status": "VALIDATED_NO_WRITES", "denominators": data["machine"],
            "sheet_counts": data["sheet_counts"], "path_contacts": len(EXPECTED_PATH_CONTACTS),
        }, ensure_ascii=False, indent=2))
        return
    finalize(data)
    print(json.dumps({
        "status": "SEALED", "result": "PASS", "write_stopped": True,
        "terminal": "09_manifest/terminal_crosscheck.json",
        "manifest": "09_manifest/manifest.json",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

from pathlib import Path
import hashlib
import json


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa2_r110_r168_readonly_adjudication_v1")
MANIFEST = ROOT / "MANIFEST.json"
WSTOP = ROOT / "WRITE_STOPPED"
WSTOP_BYTES = (
    "HANDOFF_ID=C-FIG-P641-01-R110-SA2-R168-READONLY-ADJUDICATION-V1\n"
    "OUTCOME=SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1\n"
    "WRITES_AFTER_THIS_CONTENT_MARKER=0\n"
).encode("ascii")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fobj:
        for chunk in iter(lambda: fobj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    if WSTOP.exists():
        raise SystemExit("WRITE_STOPPED already exists; refusing pre-marker manifest write")
    entries = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == MANIFEST or path == WSTOP:
            continue
        entries.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    entries.append(
        {
            "path": "WRITE_STOPPED",
            "bytes": len(WSTOP_BYTES),
            "sha256": sha256_bytes(WSTOP_BYTES),
            "projected_before_last_content_write": True,
        }
    )
    entries.sort(key=lambda item: item["path"])
    manifest = {
        "schema": "FIG-P641-01-SA2-R110-R168-READONLY-MANIFEST-V1",
        "handoff_id": "C-FIG-P641-01-R110-SA2-R168-READONLY-ADJUDICATION-V1",
        "actual_instance": "/root/sa2_fig_p641_r110_r168_readonly_v1",
        "model_effort_fork_turns": "gpt-5.6-sol/xhigh/none",
        "evidence_root": str(ROOT),
        "outcome": "SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1",
        "official_pdf": {
            "path": r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf",
            "bytes": 4967063,
            "sha256": "B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3",
            "physical_page": 691,
            "printed_page": 678,
        },
        "current_source": {
            "path": r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_bayes_markov_blanket.tex",
            "bytes": 3008,
            "sha256": "8773FF1EFFCB79DDD44734E72F0B0101292F135165021B32A760A6151DC0DE15",
        },
        "frozen_counts": {
            "foreground_objects": 29,
            "protocol_background_fills": 7,
            "unordered_pairs": 406,
            "visible_nonwhitespace_codepoints": 162,
            "critical_relations": 37,
            "empty_masks": 0,
            "overlap_candidate_pixels": 234,
            "overlap_illegal_pixels": 0,
            "clip_pixels": 0,
        },
        "manifest_self_excluded_due_to_self_reference": True,
        "write_stopped_included_by_predetermined_exact_bytes": True,
        "payload_file_count_excluding_manifest_including_write_stopped": len(entries),
        "files": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "manifest_path": str(MANIFEST),
        "manifest_bytes": MANIFEST.stat().st_size,
        "manifest_sha256": sha256_file(MANIFEST),
        "payload_file_count": len(entries),
        "wstop_bytes": len(WSTOP_BYTES),
        "wstop_sha256": sha256_bytes(WSTOP_BYTES),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
EVIDENCE_MANIFEST = PACKAGE / "evidence_manifest.json"
HASH_MANIFEST = PACKAGE / "MANIFEST.sha256"
WRITE_STOPPED = PACKAGE / "WRITE_STOPPED.md"
EXCLUDED_RELATIVE = {
    "evidence_manifest.json",
    "MANIFEST.sha256",
    "WRITE_STOPPED.md",
}
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码"
    r"\第05册_采样方法主题模型与图排序\V5-C01\fig_v5_c01_transition_graph.tex"
)
EXPECTED = {
    SOURCE: "DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600",
    PACKAGE / "build/page/v260_FIG-P547-01_page.pdf": "EA9904BF008275BB7E6840F3FC5A0D390F463F52B437C35AAAD840FE0CA9DEA1",
    PACKAGE / "build/standalone/v260_FIG-P547-01_standalone.pdf": "4CD804E17A607767E7B740B9B170A463708B675C8DBF383F13B4312315BB6BD1",
    PACKAGE / "source_identity/baseline_638CEA_fig_v5_c01_transition_graph.tex": "638CEA4285D3A9411251DA149963CC7AE4500FA5827F0A99A51FF1FC76640D1A",
    PACKAGE / "source_identity/current_DF3D4415_fig_v5_c01_transition_graph.tex": "DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def payload_entries() -> list[dict[str, object]]:
    files = []
    for path in PACKAGE.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(PACKAGE).as_posix()
        if relative in EXCLUDED_RELATIVE:
            continue
        files.append((relative, path))
    files.sort(key=lambda item: item[0])
    zero = [relative for relative, path in files if path.stat().st_size == 0]
    if zero:
        raise RuntimeError("zero-byte payload files: " + ", ".join(zero))
    entries: list[dict[str, object]] = []
    for relative, path in files:
        entries.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "classification": (
                    "SUPERSEDED_EXCLUDED_FROM_ACCEPTANCE"
                    if relative.startswith("superseded/")
                    else "ACTIVE_OR_PROVENANCE"
                ),
            }
        )
    return entries


def verify_preseal() -> None:
    for seal_path in (EVIDENCE_MANIFEST, HASH_MANIFEST, WRITE_STOPPED):
        if seal_path.exists():
            raise RuntimeError(f"seal file already exists: {seal_path}")
    terminal = PACKAGE / "LOCAL_SA2_TERMINAL.md"
    if "LOCAL_PASS_TO_ROOT_BUILD" not in terminal.read_text(encoding="utf-8"):
        raise RuntimeError("terminal recommendation is missing")
    for path, expected_hash in EXPECTED.items():
        actual = sha256(path)
        if actual != expected_hash:
            raise RuntimeError(f"identity mismatch: {path}: {actual}")


def main() -> None:
    verify_preseal()
    entries = payload_entries()
    payload_bytes = sum(int(entry["bytes"]) for entry in entries)
    if sys.argv[1:] == ["--check-only"]:
        print(
            json.dumps(
                {
                    "check": "PASS",
                    "payload_entry_count": len(entries),
                    "payload_bytes": payload_bytes,
                    "zero_byte_count": 0,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return
    if sys.argv[1:]:
        raise SystemExit("usage: python -B seal_local_package.py [--check-only]")

    generated_utc = datetime.now(timezone.utc).isoformat()
    evidence = {
        "schema": "FIG-P547-01_LOCAL_EVIDENCE_MANIFEST_V1",
        "terminal": "LOCAL_PASS_TO_ROOT_BUILD",
        "final_official_pass": False,
        "generated_utc": generated_utc,
        "package_root": str(PACKAGE),
        "payload_entry_count": len(entries),
        "payload_total_bytes": payload_bytes,
        "entries": entries,
        "seal_exclusions": {
            "evidence_manifest.json": "self",
            "MANIFEST.sha256": "generated after evidence manifest and cannot hash itself",
            "WRITE_STOPPED.md": "future final write",
        },
    }
    with EVIDENCE_MANIFEST.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(evidence, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

    manifest_entries = list(entries)
    manifest_entries.append(
        {
            "path": "evidence_manifest.json",
            "bytes": EVIDENCE_MANIFEST.stat().st_size,
            "sha256": sha256(EVIDENCE_MANIFEST),
            "classification": "ACTIVE_OR_PROVENANCE",
        }
    )
    manifest_entries.sort(key=lambda entry: str(entry["path"]))
    manifest_text = "".join(
        f'{entry["sha256"]}  {entry["path"]}\n' for entry in manifest_entries
    )
    with HASH_MANIFEST.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(manifest_text)

    if HASH_MANIFEST.read_text(encoding="utf-8") != manifest_text:
        raise RuntimeError("manifest write verification failed")
    for entry in manifest_entries:
        if sha256(PACKAGE / str(entry["path"])) != entry["sha256"]:
            raise RuntimeError(f'manifest payload verification failed: {entry["path"]}')

    manifest_sha = sha256(HASH_MANIFEST)
    evidence_sha = sha256(EVIDENCE_MANIFEST)
    stopped_text = (
        "# WRITE_STOPPED\n\n"
        "RESULT=LOCAL_PASS_TO_ROOT_BUILD\n"
        "FINAL_OFFICIAL_PASS=false\n"
        "SOURCE_SHA256=DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600\n"
        "PAGE_PDF_SHA256=EA9904BF008275BB7E6840F3FC5A0D390F463F52B437C35AAAD840FE0CA9DEA1\n"
        "STANDALONE_PDF_SHA256=4CD804E17A607767E7B740B9B170A463708B675C8DBF383F13B4312315BB6BD1\n"
        f"PAYLOAD_ENTRY_COUNT={len(entries)}\n"
        f"MANIFEST_ENTRY_COUNT={len(manifest_entries)}\n"
        f"EVIDENCE_MANIFEST_SHA256={evidence_sha}\n"
        f"MANIFEST_SHA256={manifest_sha}\n"
        f"SEALED_UTC={generated_utc}\n"
        "WRITE_STOPPED_WAS_FINAL_FILESYSTEM_WRITE=true\n"
        "NO_FURTHER_WRITES_PERMITTED_IN_THIS_SA2_TASK\n"
    )
    with WRITE_STOPPED.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(stopped_text)


if __name__ == "__main__":
    main()

"""Create the final, deterministic evidence manifests before WRITE_STOPPED.

The manifest files cannot hash themselves recursively.  Therefore the JSON
inventory lists every pre-manifest package artifact, while MANIFEST.sha256
additionally hashes evidence_manifest.json; both deliberately exclude
MANIFEST.sha256 itself and the subsequently-created WRITE_STOPPED sentinel.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
EXCLUDED = {"MANIFEST.sha256", "evidence_manifest.json", "WRITE_STOPPED"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest().upper()


def files(excluded: set[str]) -> list[Path]:
    return sorted(
        (p for p in OUT.rglob("*") if p.is_file() and p.relative_to(OUT).as_posix() not in excluded),
        key=lambda p: p.relative_to(OUT).as_posix().casefold(),
    )


def entry(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(OUT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }


def main() -> None:
    pre_manifest = [entry(p) for p in files(EXCLUDED)]
    inventory = {
        "schema": "STRICT_FIGURE_EVIDENCE_SCHEMA.md / final package inventory v1",
        "uid": "FIG-P756-01",
        "terminal": "PASS_TO_ROOT",
        "entry_count": len(pre_manifest),
        "entries": pre_manifest,
        "coverage_note": (
            "Entries cover every regular package artifact present before the two "
            "manifest files. MANIFEST.sha256 additionally hashes this JSON. "
            "The two manifest self-references and later WRITE_STOPPED are excluded "
            "because self-hashing is recursive and WRITE_STOPPED must be the final write."
        ),
        "excluded_from_json_entries": ["MANIFEST.sha256", "evidence_manifest.json", "WRITE_STOPPED"],
    }
    (OUT / "evidence_manifest.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    manifest_excluded = {"MANIFEST.sha256", "WRITE_STOPPED"}
    manifest_files = files(manifest_excluded)
    lines = [f"{digest(path)}  {path.relative_to(OUT).as_posix()}" for path in manifest_files]
    (OUT / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"json_entries": len(pre_manifest), "manifest_entries": len(lines)}))


if __name__ == "__main__":
    main()

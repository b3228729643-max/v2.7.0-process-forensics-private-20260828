from __future__ import annotations

import hashlib
import json
import os
import stat
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST_JSON = ROOT / "MANIFEST.json"
MANIFEST_SHA = ROOT / "MANIFEST.sha256"
STOP = ROOT / "WRITE_STOPPED"
EXCLUDED = {MANIFEST_JSON.name, MANIFEST_SHA.name, STOP.name}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    if MANIFEST_JSON.exists() or MANIFEST_SHA.exists() or STOP.exists():
        raise RuntimeError("seal artifacts already exist; refusing to overwrite")
    cross = json.loads((ROOT / "FINAL_CROSSCHECK.json").read_text(encoding="utf-8"))
    if cross.get("decision") != "PASS" or cross.get("route") != "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3":
        raise RuntimeError("final cross-check is not the expected PASS route")

    payload = sorted(
        (p for p in ROOT.rglob("*") if p.is_file() and p.name not in EXCLUDED),
        key=lambda p: p.relative_to(ROOT).as_posix(),
    )
    entries = [
        {
            "path": p.relative_to(ROOT).as_posix(),
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
        }
        for p in payload
    ]
    manifest = {
        "handoff_id": "A-R103-P654-SA1-FRESH-20260825",
        "uid": "FIG-P654-01",
        "candidate": "R103",
        "physical_page": 704,
        "decision": "PASS",
        "route": "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3",
        "scope": "all payload files under this evidence root except the two manifests and WRITE_STOPPED",
        "payload_file_count": len(entries),
        "entries": entries,
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MANIFEST_SHA.write_text("".join(f"{e['sha256']} *{e['path']}\n" for e in entries), encoding="utf-8")
    manifest_json_sha = sha256(MANIFEST_JSON)
    manifest_sha_sha = sha256(MANIFEST_SHA)
    time.sleep(0.05)
    now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    STOP.write_text(
        "HANDOFF_ID=A-R103-P654-SA1-FRESH-20260825\n"
        "DECISION=PASS\n"
        "ROUTE=SA1_PASS_AWAIT_FRESH_ISOLATED_SA3\n"
        f"SEALED_AT={now}\n"
        f"PAYLOAD_FILE_COUNT={len(entries)}\n"
        f"MANIFEST_JSON_SHA256={manifest_json_sha}\n"
        f"MANIFEST_SHA256_SHA256={manifest_sha_sha}\n"
        "LAST_CONTENT_WRITE=WRITE_STOPPED\n"
        "POST_SEAL_WRITES_ALLOWED=0\n",
        encoding="utf-8",
    )

    # Attribute-only sealing occurs after the final content write.
    all_paths = sorted(ROOT.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    for p in all_paths:
        try:
            if p.is_file():
                os.chmod(p, stat.S_IREAD)
        except OSError:
            pass
    try:
        os.chmod(ROOT, stat.S_IREAD | stat.S_IEXEC)
    except OSError:
        pass
    print(json.dumps({
        "sealed": True,
        "payload_file_count": len(entries),
        "manifest_json_sha256": manifest_json_sha,
        "manifest_sha256_sha256": manifest_sha_sha,
        "write_stopped": str(STOP),
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()

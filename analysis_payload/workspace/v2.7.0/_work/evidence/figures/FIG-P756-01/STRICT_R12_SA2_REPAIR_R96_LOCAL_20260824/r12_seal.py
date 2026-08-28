"""One-shot terminal seal: terminal -> manifest -> WRITE_STOPPED (last write)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\full_course_synthesis_map.tex")
AFTER_SHA = "00213AE30379E4337830B1C4957BE4CB7B1E99BE88144E2D7D262998E1B6CAAA"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    terminal = ROOT / "TERMINAL_STATUS.md"
    manifest = ROOT / "MANIFEST.sha256"
    stopped = ROOT / "WRITE_STOPPED"
    require(not terminal.exists() and not manifest.exists() and not stopped.exists(), "seal already exists; refusing second write")
    require(sha(SOURCE) == AFTER_SHA, "source changed after final machine check")
    check = json.loads((ROOT / "R12_MACHINE_FINAL_CHECK.json").read_text(encoding="utf-8"))
    require(check["result"] == "PRETERMINAL_PASS__LOCAL_PASS_TO_ROOT_BUILD", "machine check is not preterminal PASS")
    require(check["final_official_pass"] is False, "local evidence must not claim final official PASS")
    require(not (ROOT / "build" / "texmf-var").exists() and not (ROOT / "__pycache__").exists(), "transient cache returned before seal")
    now = datetime.now(timezone.utc).isoformat()
    terminal_text = f"""# FIG-P756-01 R12 SA2 terminal status

- `RESULT=LOCAL_PASS_TO_ROOT_BUILD`
- `FINAL_OFFICIAL_PASS=false`
- Scope: repaired source plus local page/standalone wrappers only.
- Source SHA256: `{AFTER_SHA}`.
- P1408: overlap 0px; independent final-visible clearance 20px; PASS; no shared-boundary declaration.
- Glyphs: 378/378 local pixel PASS; G0208=`出` 34px, G0212=`入` 35px, G0222=`入` 35px.
- Low profile: 20/20 targets PASS through 10 exact local-candidate embedded-font/CID calibration groups.
- Relations: 1,485/1,485 unordered pairs PASS, including 378 graphic-graphic pairs; 1,107/1,107 mandatory relations PASS.
- D/E, font-role, clip, mask integrity, and build-log failures: 0.
- Final machine check: `R12_MACHINE_FINAL_CHECK.json`.
- Required next gate: root official full-book build and independent SA1/SA3 strict requalification.
- Sealed UTC: `{now}`.
"""
    terminal.write_text(terminal_text, encoding="utf-8")

    excluded = {manifest.name, stopped.name}
    files = sorted(
        (path for path in ROOT.rglob("*") if path.is_file() and path.name not in excluded),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )
    require(terminal in files and len(files) > 3000, f"unexpected evidence file count before manifest: {len(files)}")
    lines = [f"{sha(path)}  {path.relative_to(ROOT).as_posix()}" for path in files]
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Read-only self-verification after manifest creation, before the final write.
    require(len(lines) == len(set(line.split("  ", 1)[1] for line in lines)), "manifest path duplication")
    require(all(sha(ROOT / line.split("  ", 1)[1]) == line.split("  ", 1)[0] for line in lines), "manifest hash self-check failure")
    manifest_sha = sha(manifest)
    stopped.write_text(
        "WRITE_STOPPED\n"
        f"RESULT=LOCAL_PASS_TO_ROOT_BUILD\n"
        f"FINAL_OFFICIAL_PASS=false\n"
        f"SOURCE_SHA256={AFTER_SHA}\n"
        f"MANIFEST_SHA256={manifest_sha}\n"
        f"MANIFEST_ENTRY_COUNT={len(lines)}\n"
        f"SEALED_UTC={now}\n"
        "NO_FURTHER_WRITES_PERMITTED_IN_THIS_SA2_TASK\n",
        encoding="utf-8",
    )
    print(json.dumps({"result": "LOCAL_PASS_TO_ROOT_BUILD", "manifest_entries": len(lines), "manifest_sha256": manifest_sha, "write_stopped": True}))


if __name__ == "__main__":
    main()

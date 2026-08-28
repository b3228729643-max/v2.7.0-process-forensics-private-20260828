#!/usr/bin/env python3
"""Build a text-only replay of the frozen page for RUN7 isolation validation.

The PDF page keeps its original resources and every original BT...ET sequence.
Only non-text paint operators are removed; graphics-state operators needed by
the text (q/Q, cm, colour, ExtGState, line state) remain.  This is a native-PDF
content replay, not OCR or an invented glyph image.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


BASE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("SA1_RUN_OUT", str(BASE / "RUN7_TEXT_ISOLATION_R2"))).resolve()
OUT.mkdir(exist_ok=True)
WORK = BASE.parents[4]
PDF = WORK / "source" / "v2.7.0" / "src" / "build" / "strict_current_r94_fullbook" / "main_full.pdf"
PAGE_INDEX = 627
DPI = 300
SCALE = DPI / 72.0

# Operators whose operands must survive outside BT...ET for later text blocks.
STATE_OPS = {
    b"q", b"Q", b"cm", b"w", b"J", b"j", b"M", b"d", b"ri", b"i",
    b"g", b"G", b"rg", b"RG", b"k", b"K", b"cs", b"CS", b"sc", b"SC",
    b"scn", b"SCN", b"gs", b"BMC", b"BDC", b"EMC",
}
OPERATORS = STATE_OPS | {
    b"m", b"l", b"c", b"v", b"y", b"h", b"re", b"S", b"s", b"f", b"F", b"f*",
    b"B", b"B*", b"b", b"b*", b"n", b"W", b"W*", b"Do", b"sh", b"BI", b"ID", b"EI",
    b"BT", b"ET", b"MP", b"DP",
}
PATH_CONSTRUCTION_OPS = {b"m", b"l", b"c", b"v", b"y", b"h", b"re"}
CLIP_OPS = {b"W", b"W*"}
PATH_END_OPS = {b"S", b"s", b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*", b"n"}
NUMBER = re.compile(rb"[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][+-]?\d+)?$")


def skip_ws_comment(data: bytes, pos: int) -> int:
    size = len(data)
    while pos < size:
        if data[pos] in b" \t\r\n\x0c\x00":
            pos += 1
        elif data[pos] == 37:  # % comment
            while pos < size and data[pos] not in b"\r\n":
                pos += 1
        else:
            break
    return pos


def scan_literal(data: bytes, pos: int) -> int:
    # Balanced literal string, including escaped parentheses.
    depth = 0
    size = len(data)
    while pos < size:
        byte = data[pos]
        if byte == 92:  # backslash
            pos += 2
            continue
        if byte == 40:
            depth += 1
        elif byte == 41:
            depth -= 1
            if depth == 0:
                return pos + 1
        pos += 1
    raise RuntimeError("unterminated PDF literal string")


def scan_composite(data: bytes, pos: int, opening: bytes, closing: bytes) -> int:
    # Arrays and dictionaries are copied as complete operands; nested forms and
    # literal strings are handled so operator-like bytes within them are inert.
    depth = 0
    size = len(data)
    while pos < size:
        if data.startswith(opening, pos):
            depth += 1
            pos += len(opening)
            continue
        if data.startswith(closing, pos):
            depth -= 1
            pos += len(closing)
            if depth == 0:
                return pos
            continue
        if data[pos] == 40:
            pos = scan_literal(data, pos)
            continue
        if data[pos] == 37:
            pos = skip_ws_comment(data, pos)
            continue
        pos += 1
    raise RuntimeError("unterminated PDF composite object")


def token(data: bytes, pos: int) -> tuple[bytes, int]:
    pos = skip_ws_comment(data, pos)
    if pos >= len(data):
        return b"", pos
    start = pos
    if data.startswith(b"<<", pos):
        end = scan_composite(data, pos, b"<<", b">>")
        return data[start:end], end
    if data[pos] == 91:  # [
        end = scan_composite(data, pos, b"[", b"]")
        return data[start:end], end
    if data[pos] == 40:
        end = scan_literal(data, pos)
        return data[start:end], end
    if data[pos] == 47:  # / PDF name object
        pos += 1
        while pos < len(data) and data[pos] not in b" \t\r\n\x0c\x00[]<>()/%":
            pos += 1
        return data[start:pos], pos
    if data[pos] == 60:  # hexadecimal string
        end = data.find(b">", pos + 1)
        if end < 0:
            raise RuntimeError("unterminated PDF hex string")
        return data[start:end + 1], end + 1
    while pos < len(data) and data[pos] not in b" \t\r\n\x0c\x00[]<>()/%":
        pos += 1
    if pos == start:
        raise RuntimeError(f"unsupported token at byte {start}: {data[start:start+16]!r}")
    return data[start:pos], pos


def is_operator(value: bytes) -> bool:
    if value in OPERATORS:
        return True
    if value in {b"true", b"false", b"null"} or NUMBER.match(value) or value.startswith(b"/"):
        return False
    # This restricted page has no unlisted non-text operator; fail closed.
    return bool(re.fullmatch(rb"[A-Za-z*'\"]+", value))


def text_only_content(stream: bytes) -> tuple[bytes, dict[str, object]]:
    out: list[bytes] = []
    pending: list[bytes] = []
    pos = 0
    text_blocks = 0
    dropped: dict[str, int] = {}
    path_buffer: list[bytes] = []
    clip_pending = False
    preserved_clip_paths = 0
    while True:
        start = skip_ws_comment(stream, pos)
        value, end = token(stream, start)
        if not value:
            break
        if value == b"BT":
            # Preserve the original raw bytes through the matching ET token.
            block_start = start
            scan = end
            while True:
                inner_start = skip_ws_comment(stream, scan)
                inner, inner_end = token(stream, inner_start)
                if not inner:
                    raise RuntimeError("unterminated BT text block")
                scan = inner_end
                if inner == b"ET":
                    out.append(stream[block_start:inner_end])
                    text_blocks += 1
                    pos = inner_end
                    pending.clear()
                    break
            continue
        if is_operator(value):
            operator_bytes = b" ".join(pending + [value])
            if value in PATH_CONSTRUCTION_OPS:
                path_buffer.append(operator_bytes)
            elif value in CLIP_OPS:
                path_buffer.append(operator_bytes)
                clip_pending = True
            elif value in PATH_END_OPS:
                if value == b"n" and clip_pending:
                    out.extend(path_buffer)
                    out.append(operator_bytes)
                    preserved_clip_paths += 1
                else:
                    key = value.decode("latin1")
                    dropped[key] = dropped.get(key, 0) + 1
                path_buffer.clear()
                clip_pending = False
            elif value in STATE_OPS:
                out.append(b" ".join(pending + [value]))
            else:
                key = value.decode("latin1")
                dropped[key] = dropped.get(key, 0) + 1
            pending.clear()
        else:
            pending.append(value)
        pos = end
    return b"\n".join(out) + b"\n", {
        "text_blocks": text_blocks,
        "dropped_operators": dropped,
        "preserved_clipping_paths": preserved_clip_paths,
        "unclosed_path_buffer_entries": len(path_buffer),
    }


def chars(page: fitz.Page) -> list[tuple[str, tuple[float, float, float, float]]]:
    out = []
    for block in page.get_text("rawdict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for item in span["chars"]:
                    out.append((item["c"], tuple(round(float(v), 4) for v in item["bbox"])))
    return out


def trace_properties(page: fitz.Page) -> list[tuple[object, ...]]:
    """Properties that prove replay retained text transform, colour and alpha."""
    result: list[tuple[object, ...]] = []
    for span in page.get_texttrace():
        fixed = (
            str(span["font"]),
            round(float(span["size"]), 5),
            tuple(round(float(item), 6) for item in span["color"]),
            round(float(span.get("opacity", 1.0)), 6),
            tuple(round(float(item), 6) for item in span["dir"]),
            int(span["wmode"]),
        )
        for item in span["chars"]:
            result.append(
                (
                    chr(int(item[0])),
                    tuple(round(float(value), 4) for value in item[3]),
                    *fixed,
                )
            )
    return result


def pxbbox(box: tuple[float, float, float, float], width: int, height: int) -> tuple[int, int, int, int]:
    return (
        max(0, math.floor(box[0] * SCALE)), max(0, math.floor(box[1] * SCALE)),
        min(width, math.ceil(box[2] * SCALE)), min(height, math.ceil(box[3] * SCALE)),
    )


def main() -> None:
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    xrefs = page.get_contents()
    if len(xrefs) != 1:
        raise RuntimeError(f"expected one frozen content stream, got {xrefs}")
    original_chars = chars(page)
    original_trace = trace_properties(page)
    filtered, parser_report = text_only_content(doc.xref_stream(xrefs[0]))
    text_pdf = OUT / "frozen_page628_text_only_replay.pdf"
    doc.select([PAGE_INDEX])
    doc.update_stream(xrefs[0], filtered)
    doc.save(text_pdf, garbage=4, deflate=True)
    doc.close()
    text_png = OUT / "frozen_page628_text_only_replay_300dpi.png"
    subprocess.run([
        "pdftoppm", "-f", "1", "-l", "1", "-r", "300", "-png", "-singlefile",
        str(text_pdf), str(text_png.with_suffix("")),
    ], check=True)
    isolated = Image.open(text_png).convert("RGB")
    if isolated.size != (2481, 3508):
        raise RuntimeError(f"unexpected native text-layer grid {isolated.size}")
    replay = fitz.open(text_pdf)
    replay_chars = chars(replay[0])
    replay_trace = trace_properties(replay[0])
    replay.close()
    mismatch = []
    for index, (before, after) in enumerate(zip(original_chars, replay_chars)):
        if before != after:
            mismatch.append({"index": index, "before": before, "after": after})
            if len(mismatch) >= 20:
                break
    trace_mismatch = []
    for index, (before, after) in enumerate(zip(original_trace, replay_trace)):
        if before != after:
            trace_mismatch.append({"index": index, "before": before, "after": after})
            if len(trace_mismatch) >= 20:
                break
    target = (1109, 1644, 1151, 1689)  # E026 fullwidth colon G0147 probe
    arr = np.asarray(isolated, dtype=np.int16)
    mask = np.max(np.abs(arr - 255), axis=2) >= 20
    tx0, ty0, tx1, ty1 = target
    report = {
        "run": OUT.name,
        "source": str(PDF),
        "content_stream_xref": xrefs[0],
        "original_character_count": len(original_chars),
        "replay_character_count": len(replay_chars),
        "first_character_mismatches": mismatch,
        "character_stream_exact": len(original_chars) == len(replay_chars) and not mismatch,
        "original_texttrace_character_count": len(original_trace),
        "replay_texttrace_character_count": len(replay_trace),
        "first_texttrace_property_mismatches": trace_mismatch,
        "text_trace_visual_properties_exact": len(original_trace) == len(replay_trace) and not trace_mismatch,
        "parser": parser_report,
        "render": {"engine": "pdftoppm", "dpi": 300, "native_grid": list(isolated.size), "resize": False},
        "G0147_text_only_pixels": int(mask[ty0:ty1, tx0:tx1].sum()),
    }
    (OUT / "text_only_replay_probe.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

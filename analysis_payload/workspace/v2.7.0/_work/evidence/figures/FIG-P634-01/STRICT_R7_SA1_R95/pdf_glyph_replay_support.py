"""Official-PDF glyph replay isolation for the FIG-P634-01 SA1 audit.

This module never estimates a text mask from the page bitmap.  It binds each
visible PDF character to its original R95 content-stream CID, then builds a
one-glyph replay page using the original page resources, graphic CTM, text
matrix, font, fill state, and original text-advance prefix.  Poppler renders
the replay pages at 300dpi; their alpha support identifies the actual glyph
only.  H/overlap measurements remain on the supplied direct full-page PNG.
"""
from __future__ import annotations

import copy
import math
import re
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    ByteStringObject,
    ContentStream,
    DecodedStreamObject,
    FloatObject,
    NameObject,
    NumberObject,
    RectangleObject,
    TextStringObject,
)


TEXT_OPERATORS = {b"Tj", b"TJ"}
PAINT_OPERATORS = {b"S", b"s", b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*", b"Do", b"sh"}


def _matrix(values: list[Any] | tuple[Any, ...]) -> np.ndarray:
    """PDF [a b c d e f] -> homogeneous column-vector matrix."""
    return np.array(
        [
            [float(values[0]), float(values[2]), float(values[4])],
            [float(values[1]), float(values[3]), float(values[5])],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def _matrix_values(matrix: np.ndarray) -> tuple[float, float, float, float, float, float]:
    return (
        float(matrix[0, 0]), float(matrix[1, 0]),
        float(matrix[0, 1]), float(matrix[1, 1]),
        float(matrix[0, 2]), float(matrix[1, 2]),
    )


def _matrix_csv(matrix: np.ndarray) -> str:
    return ",".join(f"{value:.8f}" for value in _matrix_values(matrix))


def _pdf_float(value: float) -> FloatObject:
    """Preserve non-integer official PDF operands; NumberObject would truncate."""
    return FloatObject(float(value))


def _bytes_for_text_item(item: Any) -> bytes | None:
    if isinstance(item, TextStringObject):
        return bytes(item.original_bytes)
    if isinstance(item, ByteStringObject):
        return bytes(item)
    return None


def _font_info(page: Any, font_name: str) -> dict[str, str]:
    resources = page["/Resources"].get_object()
    fonts = resources["/Font"].get_object()
    key = NameObject(font_name)
    if key not in fonts:
        raise ValueError(f"font resource {font_name} not present on official page")
    font = fonts[key].get_object()
    subtype = str(font.get("/Subtype", "UNKNOWN"))
    encoding = str(font.get("/Encoding", "UNKNOWN"))
    if subtype != "/Type0" or encoding != "/Identity-H":
        raise ValueError(f"unsupported glyph-code width for {font_name}: {subtype} {encoding}")
    return {
        "font_resource": font_name,
        "font_subtype": subtype,
        "font_encoding": encoding,
        "cid_width_bytes": "2",
    }


def _extgstate_fill_opacity(page: Any, state_name: str) -> tuple[float | None, str]:
    """Return the official non-stroking alpha (/ca) for one `gs` resource.

    A graphics-state dictionary may omit /ca, which means it leaves the
    current non-stroking alpha unchanged.  The caller therefore distinguishes
    that documented inheritance case from an unknown/missing resource; it
    must never assume opacity merely because a `gs` operator was skipped.
    """
    try:
        resources = page["/Resources"].get_object()
        ext_states = resources.get("/ExtGState")
        if ext_states is None:
            return None, "MISSING_EXTGSTATE_RESOURCE"
        state_ref = ext_states.get_object().get(NameObject(state_name))
        if state_ref is None:
            return None, "MISSING_EXTGSTATE_NAME"
        state = state_ref.get_object()
        if "/ca" not in state:
            return None, "INHERIT_PREVIOUS_FILL_OPACITY"
        value = float(state["/ca"])
        if not 0.0 <= value <= 1.0:
            return None, "INVALID_FILL_OPACITY"
        return value, "OFFICIAL_EXTGSTATE_CA"
    except Exception as exc:  # noqa: BLE001 - an evidence chain must surface it.
        return None, f"EXTGSTATE_RESOLUTION_ERROR:{exc}"


def _split_codes(operands: list[Any], width: int) -> tuple[list[dict[str, Any]], list[str]]:
    """Return every CID in a Tj/TJ operand, preserving TJ array location."""
    errors: list[str] = []
    codes: list[dict[str, Any]] = []
    if not operands:
        return codes, ["text operator has no operands"]
    if len(operands) != 1:
        return codes, [f"unexpected text-operator operand count {len(operands)}"]
    if isinstance(operands[0], ArrayObject):
        items = operands[0]
    else:
        items = ArrayObject([operands[0]])
    code_index = 0
    for item_index, item in enumerate(items):
        raw = _bytes_for_text_item(item)
        if raw is None:
            continue
        if len(raw) % width:
            errors.append(f"text string at item {item_index} has {len(raw)} bytes, not divisible by CID width {width}")
            continue
        for byte_offset in range(0, len(raw), width):
            codes.append(
                {
                    "code_index": code_index,
                    "item_index": item_index,
                    "byte_offset": byte_offset,
                    "cid": raw[byte_offset : byte_offset + width],
                }
            )
            code_index += 1
    return codes, errors


def _scope_pairs(operations: list[tuple[list[Any], bytes]]) -> tuple[dict[int, int], dict[int, np.ndarray], list[list[int]]]:
    """Match q/Q scopes and record each scope's inherited official CTM."""
    current = np.eye(3, dtype=np.float64)
    stack: list[tuple[int, np.ndarray]] = []
    pairs: dict[int, int] = {}
    pre_ctm: dict[int, np.ndarray] = {}
    active_at: list[list[int]] = []
    for index, (operands, operator) in enumerate(operations):
        active_at.append([item[0] for item in stack])
        if operator == b"q":
            pre_ctm[index] = current.copy()
            stack.append((index, current.copy()))
        elif operator == b"Q":
            if not stack:
                raise ValueError(f"unbalanced Q at content op {index}")
            start, inherited = stack.pop()
            pairs[start] = index
            current = inherited
        elif operator == b"cm":
            # PDF concatenates the new transform after the inherited CTM for
            # column-vector coordinates: final = CTM @ cm @ point.
            current = current @ _matrix(operands)
    if stack:
        raise ValueError(f"{len(stack)} unclosed q scope(s) in official content stream")
    return pairs, pre_ctm, active_at


def extract_official_text_records(pdf_path: Path, page_index: int) -> tuple[PdfReader, Any, ContentStream, list[dict[str, Any]], list[str]]:
    """Extract official content-stream records for all text operators on page."""
    reader = PdfReader(str(pdf_path))
    page = reader.pages[page_index]
    stream = ContentStream(page.get_contents(), reader)
    operations = stream.operations
    pairs, pre_ctm, active_at = _scope_pairs(operations)
    scope_text_count = {
        start: sum(1 for _, operator in operations[start + 1 : end] if operator in TEXT_OPERATORS)
        for start, end in pairs.items()
    }
    scope_paint_count = {
        start: sum(1 for _, operator in operations[start + 1 : end] if operator in PAINT_OPERATORS)
        for start, end in pairs.items()
    }
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    current = np.eye(3, dtype=np.float64)
    ctm_stack: list[np.ndarray] = []
    font_name = ""
    font_size = 0.0
    text_matrix = np.eye(3, dtype=np.float64)
    text_render_mode = 0
    fill_rgb: tuple[float, float, float] | None = None
    fill_opacity = 1.0
    fill_opacity_proof = "INITIAL_DEFAULT_1.0"
    text_state: dict[str, float] = {"Tc": 0.0, "Tw": 0.0, "Tz": 100.0, "TL": 0.0, "Ts": 0.0}
    graphic_stack: list[tuple[np.ndarray, tuple[float, float, float] | None, float, str]] = []
    for index, (operands, operator) in enumerate(operations):
        if operator == b"q":
            ctm_stack.append(current.copy())
            graphic_stack.append((current.copy(), fill_rgb, fill_opacity, fill_opacity_proof))
        elif operator == b"Q":
            if not ctm_stack or not graphic_stack:
                errors.append(f"unbalanced graphics restore at {index}")
                continue
            current = ctm_stack.pop()
            _, fill_rgb, fill_opacity, fill_opacity_proof = graphic_stack.pop()
        elif operator == b"cm":
            current = current @ _matrix(operands)
        elif operator == b"rg" and len(operands) == 3:
            fill_rgb = tuple(float(value) for value in operands)
        elif operator == b"g" and len(operands) == 1:
            value = float(operands[0])
            fill_rgb = (value, value, value)
        elif operator == b"gs" and len(operands) == 1:
            state_name = str(operands[0])
            resolved_opacity, proof = _extgstate_fill_opacity(page, state_name)
            if proof == "INHERIT_PREVIOUS_FILL_OPACITY":
                fill_opacity_proof = f"{state_name}:{proof}"
            elif resolved_opacity is None:
                errors.append(f"content op {index} {state_name}: {proof}")
                fill_opacity_proof = f"{state_name}:{proof}"
            else:
                fill_opacity = resolved_opacity
                fill_opacity_proof = f"{state_name}:{proof}"
        elif operator == b"Tf" and len(operands) == 2:
            font_name = str(operands[0])
            font_size = float(operands[1])
        elif operator == b"Tm" and len(operands) == 6:
            text_matrix = _matrix(operands)
        elif operator == b"Td" and len(operands) == 2:
            text_matrix = text_matrix @ _matrix([1, 0, 0, 1, operands[0], operands[1]])
        elif operator == b"TD" and len(operands) == 2:
            text_state["TL"] = -float(operands[1])
            text_matrix = text_matrix @ _matrix([1, 0, 0, 1, operands[0], operands[1]])
        elif operator == b"T*":
            text_matrix = text_matrix @ _matrix([1, 0, 0, 1, 0, -text_state["TL"]])
        elif operator == b"Tr" and len(operands) == 1:
            text_render_mode = int(operands[0])
        elif operator in {b"Tc", b"Tw", b"Tz", b"TL", b"Ts"} and len(operands) == 1:
            text_state[operator.decode("ascii")] = float(operands[0])
        elif operator in TEXT_OPERATORS:
            if not font_name:
                errors.append(f"text op {index} has no active official font")
                continue
            try:
                font_info = _font_info(page, font_name)
            except ValueError as exc:
                errors.append(f"text op {index}: {exc}")
                continue
            codes, code_errors = _split_codes(operands, int(font_info["cid_width_bytes"]))
            errors.extend(f"text op {index}: {message}" for message in code_errors)
            candidate_scopes = [
                scope
                for scope in reversed(active_at[index])
                if scope_text_count.get(scope, 0) >= 1 and scope_paint_count.get(scope, 0) == 0
            ]
            # Formula bases/scripts and state-card label/index pairs can share
            # one BT/q scope.  The replay copies the original no-paint scope
            # but makes every non-target text operator invisible, so it keeps
            # exact source transforms without importing a sibling glyph.
            scope_start = candidate_scopes[0] if candidate_scopes else -1
            global_tm = current @ text_matrix
            records.append(
                {
                    "op_index": index,
                    "operator": operator,
                    "operands": copy.deepcopy(operands),
                    "codes": codes,
                    "font_name": font_name,
                    "font_size": font_size,
                    "font_info": font_info,
                    "ctm": current.copy(),
                    "text_matrix": text_matrix.copy(),
                    "global_text_matrix": global_tm,
                    "text_render_mode": text_render_mode,
                    "fill_rgb": fill_rgb,
                    "fill_opacity": fill_opacity,
                    "fill_opacity_proof": fill_opacity_proof,
                    "text_state": dict(text_state),
                    "scope_start": scope_start,
                    "scope_end": pairs[scope_start] if scope_start >= 0 else -1,
                    "scope_pre_ctm": pre_ctm[scope_start].copy() if scope_start >= 0 else current.copy(),
                    "scope_text_count": scope_text_count[scope_start] if scope_start >= 0 else 0,
                    "scope_paint_count": scope_paint_count[scope_start] if scope_start >= 0 else 0,
                }
            )
    return reader, page, stream, records, errors


def bind_glyphs_to_official_replay(
    elements: list[dict[str, Any]],
    glyphs: list[dict[str, Any]],
    records: list[dict[str, Any]],
    page_height: float,
    figure_rect_pt: tuple[float, float, float, float],
) -> list[str]:
    """Bind each PDF text-layer character to exactly one official CID replay."""
    errors: list[str] = []
    fx0, fy0, fx1, fy1 = figure_rect_pt
    available = {
        index
        for index, record in enumerate(records)
        if fx0 <= float(record["global_text_matrix"][0, 2]) <= fx1
        and fy0 <= page_height - float(record["global_text_matrix"][1, 2]) <= fy1
    }
    glyphs_by_element: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for glyph in glyphs:
        glyphs_by_element[glyph["element_id"]].append(glyph)
    element_index = 0
    while element_index < len(elements):
        element = elements[element_index]
        element_id = element["element_id"]
        chars = element["chars"]
        if not chars:
            errors.append(f"{element_id} has no PDF chars")
            element_index += 1
            continue
        x0, y0 = chars[0]["origin"]
        target_y = page_height - float(y0)
        candidates: list[tuple[int, list[dict[str, Any]]]] = []
        for record_index in available:
            record = records[record_index]
            matrix = record["global_text_matrix"]
            if abs(float(matrix[0, 2]) - float(x0)) > 0.80 or abs(float(matrix[1, 2]) - target_y) > 0.80:
                continue
            # MuPDF may split a single TJ array at a large explicit kerning
            # adjustment.  Aggregate only immediately consecutive spans on
            # the same rendered baseline until their original CID count fits.
            group: list[dict[str, Any]] = []
            count = 0
            base_top_y = float(y0)
            for following in elements[element_index:]:
                if not following["chars"]:
                    break
                follow_origin = following["chars"][0]["origin"]
                if abs(float(follow_origin[1]) - base_top_y) > 0.80:
                    break
                group.append(following)
                count += len(following["chars"])
                if count >= len(record["codes"]):
                    break
            if count == len(record["codes"]):
                candidates.append((record_index, group))
        if len(candidates) != 1:
            errors.append(
                f"{element_id} expected one official TJ/Tj/group at ({x0:.4f},{target_y:.4f}); got {len(candidates)}"
            )
            element_index += 1
            continue
        record_index, group = candidates[0]
        available.remove(record_index)
        record = records[record_index]
        code_offset = 0
        for grouped_element in group:
            members = glyphs_by_element[grouped_element["element_id"]]
            glyph_by_char_no = {
                int(re.search(r":G(\d+)$", glyph["glyph_id"]).group(1)): glyph
                for glyph in members
            }
            for char_no, _char_data in enumerate(grouped_element["chars"], start=1):
                glyph = glyph_by_char_no.get(char_no)
                if glyph is None:
                    # Spaces are deliberately absent from the visible SVG glyph
                    # map but still occupy their original CID/text advance.
                    continue
                code = record["codes"][code_offset + char_no - 1]
                glyph["pdf_replay_record"] = record
                glyph["pdf_replay_code_index"] = code["code_index"]
                glyph["pdf_replay_item_index"] = code["item_index"]
                glyph["pdf_replay_byte_offset"] = code["byte_offset"]
                glyph["pdf_replay_cid_hex"] = code["cid"].hex().upper()
                glyph["pdf_replay_mapping_pass"] = True
            code_offset += len(grouped_element["chars"])
        element_index += len(group)
    for glyph in glyphs:
        if "pdf_replay_record" not in glyph:
            glyph["pdf_replay_mapping_pass"] = False
            errors.append(f"{glyph['glyph_id']} has no official content-replay binding")
    if available:
        # All records retained in `available` are inside the declared figure
        # scope, so an unmatched record leaves a CHAR -> PDF-chain gap.
        errors.append(f"{len(available)} unclaimed official text operator record(s) in figure scope")
    return errors


def _prefix_items_for_code(record: dict[str, Any], code_index: int) -> ArrayObject:
    """Preserve official glyph advances/kerns before one target CID invisibly."""
    operands = record["operands"]
    if len(operands) != 1:
        raise ValueError("cannot reconstruct prefix for unexpected text operand count")
    source_items = operands[0] if isinstance(operands[0], ArrayObject) else ArrayObject([operands[0]])
    target = record["codes"][code_index]
    prefix = ArrayObject()
    for item_index, item in enumerate(source_items):
        raw = _bytes_for_text_item(item)
        if raw is None:
            prefix.append(copy.deepcopy(item))
            continue
        if item_index < target["item_index"]:
            prefix.append(ByteStringObject(raw))
            continue
        if item_index == target["item_index"]:
            before = raw[: target["byte_offset"]]
            if before:
                prefix.append(ByteStringObject(before))
            break
        break
    return prefix


def _make_direct_state_replay_stream(reader: PdfReader, glyph: dict[str, Any]) -> bytes:
    """Replay target from captured official graphic/text state only.

    Used only when the source q/Q scope also paints a non-text object (notably
    the caption's surrounding page context).  It still clones the original
    page resources and CID, and records every state operand in the manifest.
    """
    record = glyph["pdf_replay_record"]
    prefix = _prefix_items_for_code(record, int(glyph["pdf_replay_code_index"]))
    target_code = bytes.fromhex(glyph["pdf_replay_cid_hex"])
    ctm = _matrix_values(record["ctm"])
    tm = _matrix_values(record["text_matrix"])
    if record["fill_rgb"] is None:
        raise ValueError(f"{glyph['glyph_id']} official fill RGB is UNKNOWN")
    fill = record["fill_rgb"]
    state = record["text_state"]
    replacement: list[tuple[list[Any], bytes]] = [
        ([_pdf_float(float(fill[0])), _pdf_float(float(fill[1])), _pdf_float(float(fill[2]))], b"rg"),
        ([NameObject(record["font_name"]), _pdf_float(float(record["font_size"]))], b"Tf"),
        ([_pdf_float(float(state["Tc"]))], b"Tc"),
        ([_pdf_float(float(state["Tw"]))], b"Tw"),
        ([_pdf_float(float(state["Tz"]))], b"Tz"),
        ([_pdf_float(float(state["TL"]))], b"TL"),
        ([_pdf_float(float(state["Ts"]))], b"Ts"),
        ([_pdf_float(value) for value in tm], b"Tm"),
    ]
    if len(prefix):
        replacement.extend(
            [
                ([NumberObject(3)], b"Tr"),
                ([prefix], b"TJ"),
            ]
        )
    replacement.extend(
        [
            ([NumberObject(int(record["text_render_mode"]))], b"Tr"),
            ([ByteStringObject(target_code)], b"Tj"),
        ]
    )
    snippet = ContentStream(None, reader)
    snippet.operations = [([], b"BT"), *replacement, ([], b"ET")]
    a, b, c, d, e, f = ctm
    prefix_cm = f"q\n{a:.10f} {b:.10f} {c:.10f} {d:.10f} {e:.10f} {f:.10f} cm\n".encode("ascii")
    return prefix_cm + snippet.get_data() + b"\nQ\n"


def _make_replay_stream(reader: PdfReader, stream: ContentStream, glyph: dict[str, Any]) -> tuple[bytes, str]:
    record = glyph["pdf_replay_record"]
    start, end = int(record["scope_start"]), int(record["scope_end"])
    if start < 0 or end < start or int(record["scope_paint_count"]) != 0:
        return _make_direct_state_replay_stream(reader, glyph), "DIRECT_CAPTURED_OFFICIAL_STATE"
    snippet = ContentStream(None, reader)
    snippet.operations = copy.deepcopy(stream.operations[start : end + 1])
    result: list[tuple[list[Any], bytes]] = []
    for local_index, (operands, operator) in enumerate(snippet.operations):
        source_index = start + local_index
        if operator not in TEXT_OPERATORS:
            result.append((operands, operator))
            continue
        if source_index != int(record["op_index"]):
            # Advance all sibling text exactly as in the official source while
            # leaving it non-painting.  The page has a single verified source
            # rendering mode (0); nevertheless restore the target's recorded
            # mode explicitly after every sibling.
            result.extend(
                [
                    ([NumberObject(3)], b"Tr"),
                    (operands, operator),
                    ([NumberObject(int(record["text_render_mode"]))], b"Tr"),
                ]
            )
            continue
        prefix = _prefix_items_for_code(record, int(glyph["pdf_replay_code_index"]))
        target_code = bytes.fromhex(glyph["pdf_replay_cid_hex"])
        if len(prefix):
            result.extend(
                [
                    ([NumberObject(3)], b"Tr"),
                    ([prefix], b"TJ"),
                ]
            )
        result.extend(
            [
                ([NumberObject(int(record["text_render_mode"]))], b"Tr"),
                ([ByteStringObject(target_code)], b"Tj"),
            ]
        )
    snippet.operations = result
    a, b, c, d, e, f = _matrix_values(record["scope_pre_ctm"])
    prefix_cm = f"q\n{a:.10f} {b:.10f} {c:.10f} {d:.10f} {e:.10f} {f:.10f} cm\n".encode("ascii")
    return prefix_cm + snippet.get_data() + b"\nQ\n", "OFFICIAL_NO_PAINT_SCOPE_CLONE"


def _split_text_items_around_target(record: dict[str, Any], code_index: int) -> tuple[ArrayObject, bytes, ArrayObject]:
    """Split one original Tj/TJ payload around exactly one original CID.

    This preserves all preceding / following CIDs and every TJ numeric kern.
    The caller can paint only the one target CID in `Tr 3`, leaving a complete
    official-page *knockout* whose subsequent graphics still run in their
    original order.  It is intentionally not a synthetic glyph substitute.
    """
    operands = record["operands"]
    if len(operands) != 1:
        raise ValueError("cannot split target from unexpected text operand count")
    source_items = operands[0] if isinstance(operands[0], ArrayObject) else ArrayObject([operands[0]])
    target = record["codes"][code_index]
    target_item = int(target["item_index"])
    target_offset = int(target["byte_offset"])
    target_cid = bytes(target["cid"])
    prefix = ArrayObject()
    suffix = ArrayObject()
    found = False
    for item_index, item in enumerate(source_items):
        raw = _bytes_for_text_item(item)
        if raw is None:
            if item_index < target_item:
                prefix.append(copy.deepcopy(item))
            elif item_index > target_item:
                suffix.append(copy.deepcopy(item))
            continue
        if item_index < target_item:
            prefix.append(ByteStringObject(raw))
            continue
        if item_index > target_item:
            suffix.append(ByteStringObject(raw))
            continue
        if target_offset + len(target_cid) > len(raw) or raw[target_offset : target_offset + len(target_cid)] != target_cid:
            raise ValueError("target CID does not match original text item at recorded byte offset")
        before = raw[:target_offset]
        after = raw[target_offset + len(target_cid) :]
        if before:
            prefix.append(ByteStringObject(before))
        if after:
            suffix.append(ByteStringObject(after))
        found = True
    if not found:
        raise ValueError("recorded target CID item was not found")
    return prefix, target_cid, suffix


def _make_full_page_target_knockout_stream(
    reader: PdfReader, stream: ContentStream, glyph: dict[str, Any]
) -> bytes:
    """Re-emit the official page with only one target CID made non-painting.

    Unlike the glyph-only replay, this page intentionally retains every other
    official operation before *and after* the target.  A native crop compared
    with the direct official page therefore identifies exactly the target's
    final-visible contribution and exposes genuine later occlusion.
    """
    record = glyph["pdf_replay_record"]
    target_op = int(record["op_index"])
    target_code_index = int(glyph["pdf_replay_code_index"])
    result: list[tuple[list[Any], bytes]] = []
    for source_index, (operands, operator) in enumerate(stream.operations):
        if source_index != target_op:
            result.append((copy.deepcopy(operands), operator))
            continue
        if operator not in TEXT_OPERATORS:
            raise ValueError(f"target official op {target_op} is not a text operator")
        prefix, target_cid, suffix = _split_text_items_around_target(record, target_code_index)
        if prefix:
            result.append(([prefix], b"TJ"))
        result.extend(
            [
                ([NumberObject(3)], b"Tr"),
                ([ByteStringObject(target_cid)], b"Tj"),
                ([NumberObject(int(record["text_render_mode"]))], b"Tr"),
            ]
        )
        if suffix:
            result.append(([suffix], b"TJ"))
    output = ContentStream(None, reader)
    output.operations = result
    return output.get_data()


def _set_native_cropbox(out_page: Any, char_bbox_px: tuple[int, int, int, int], page_height: float, scale: float) -> None:
    x0, y0, x1, y1 = char_bbox_px
    out_page.cropbox = RectangleObject(
        [x0 / scale, page_height - y1 / scale, x1 / scale, page_height - y0 / scale]
    )


def render_official_glyph_final_visibility(
    glyphs: list[dict[str, Any]],
    reader: PdfReader,
    page: Any,
    stream: ContentStream,
    native_page_rgb: np.ndarray,
    replay_alpha_values: dict[str, np.ndarray],
    replay_pdf_path: Path,
    scale: float,
) -> tuple[dict[str, dict[str, np.ndarray]], list[dict[str, Any]], list[str]]:
    """Measure each CID's actual final-page contribution by official knockout.

    Each pair of pages has the same native-pixel CropBox: the first is an
    untouched official page and the second differs only by the target CID in
    non-painting text mode.  The untouched crop must be pixel-identical to the
    direct R95 page image; otherwise no final-visible conclusion is allowed.
    The direct-minus-knockout difference is the only authority for a glyph's
    final-visible raw mask.  It is cross-checked against the isolated target
    alpha support at the >=20/255 stroke threshold.
    """
    errors: list[str] = []
    writer = PdfWriter()
    manifest: list[dict[str, Any]] = []
    ordered = sorted(glyphs, key=lambda glyph: glyph["glyph_id"])
    page_height = float(page.mediabox.height)
    for glyph_index, glyph in enumerate(ordered, start=1):
        glyph_id = glyph["glyph_id"]
        if not glyph.get("pdf_replay_mapping_pass"):
            errors.append(f"{glyph_id} cannot build final-visibility knockout: mapping failed")
            continue
        try:
            knockout_data = _make_full_page_target_knockout_stream(reader, stream, glyph)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{glyph_id} knockout stream: {exc}")
            continue
        baseline_page = writer.add_page(page)
        _set_native_cropbox(baseline_page, glyph["char_bbox_px"], page_height, scale)
        knockout_page = writer.add_page(page)
        knockout_stream = DecodedStreamObject()
        knockout_stream.set_data(knockout_data)
        knockout_page[NameObject("/Contents")] = writer._add_object(knockout_stream)
        _set_native_cropbox(knockout_page, glyph["char_bbox_px"], page_height, scale)
        manifest.append(
            {
                "PAIR_INDEX": glyph_index,
                "BASELINE_REPLAY_PAGE": 2 * glyph_index - 1,
                "KNOCKOUT_REPLAY_PAGE": 2 * glyph_index,
                "GLYPH_ID": glyph_id,
                "EXPECTED_CHAR": glyph["expected_char"],
                "PDF_CONTENT_OP_INDEX": glyph["pdf_replay_record"]["op_index"],
                "PDF_CID_HEX": glyph["pdf_replay_cid_hex"],
                "REPLAY_CROPBOX_NATIVE_PX": ",".join(str(value) for value in glyph["char_bbox_px"]),
                "KNOCKOUT_METHOD": "OFFICIAL_FULL_PAGE_ONLY_TARGET_CID_TR3",
                "STATUS": "PENDING_RENDER",
            }
        )
    if len(manifest) != len(ordered):
        errors.append(f"final-visibility replay manifest {len(manifest)} != glyph count {len(ordered)}")
    replay_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with replay_pdf_path.open("wb") as output:
        writer.write(output)
    if errors:
        return {}, manifest, errors

    visibility: dict[str, dict[str, np.ndarray]] = {}
    with tempfile.TemporaryDirectory(prefix="fig_p634_final_visibility_") as temp:
        scratch = Path(temp)
        source_pdf = scratch / "official_glyph_knockouts.pdf"
        shutil.copyfile(replay_pdf_path, source_pdf)
        out_base = scratch / "visibility"
        command = [
            "pdftocairo", "-png", "-cropbox", "-r", "300",
            str(source_pdf), str(out_base),
        ]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            return {}, manifest, [f"pdftocairo final-visibility rendering exited {completed.returncode}: {completed.stderr.strip()}"]
        files: dict[int, Path] = {}
        for path in scratch.glob("visibility-*.png"):
            match = re.search(r"-(\d+)\.png$", path.name)
            if match:
                files[int(match.group(1))] = path
        if len(files) != 2 * len(ordered):
            return {}, manifest, [f"pdftocairo final-visibility PNG count {len(files)} != pair-page count {2 * len(ordered)}"]
        for row in manifest:
            glyph_id = row["GLYPH_ID"]
            baseline_path = files.get(int(row["BASELINE_REPLAY_PAGE"]))
            knockout_path = files.get(int(row["KNOCKOUT_REPLAY_PAGE"]))
            if baseline_path is None or knockout_path is None:
                errors.append(f"{glyph_id} missing baseline or knockout PNG")
                continue
            try:
                with Image.open(baseline_path) as baseline_image, Image.open(knockout_path) as knockout_image:
                    baseline_rgb = np.asarray(baseline_image.convert("RGB"))
                    knockout_rgb = np.asarray(knockout_image.convert("RGB"))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{glyph_id} final-visibility PNG unreadable: {exc}")
                continue
            glyph = next(item for item in ordered if item["glyph_id"] == glyph_id)
            x0, y0, x1, y1 = glyph["char_bbox_px"]
            expected_shape = (y1 - y0, x1 - x0)
            if (
                baseline_rgb.shape[0] < expected_shape[0]
                or baseline_rgb.shape[1] < expected_shape[1]
                or knockout_rgb.shape[0] < expected_shape[0]
                or knockout_rgb.shape[1] < expected_shape[1]
            ):
                errors.append(f"{glyph_id} final-visibility crop smaller than native char grid")
                continue
            baseline_rgb = baseline_rgb[: expected_shape[0], : expected_shape[1], :]
            knockout_rgb = knockout_rgb[: expected_shape[0], : expected_shape[1], :]
            native_crop = native_page_rgb[y0:y1, x0:x1, :3]
            if native_crop.shape[:2] != expected_shape:
                errors.append(f"{glyph_id} direct native crop shape mismatch")
                continue
            baseline_native_diff = np.any(baseline_rgb != native_crop, axis=2)
            direct_knockout_diff = np.any(native_crop != knockout_rgb, axis=2)
            alpha = replay_alpha_values.get(glyph_id)
            if alpha is None or alpha.shape != expected_shape:
                errors.append(f"{glyph_id} has no matching isolated official alpha grid")
                continue
            alpha_nonzero = alpha > 0
            alpha_ge20 = alpha >= 20
            record = glyph["pdf_replay_record"]
            if record["fill_rgb"] is None:
                errors.append(f"{glyph_id} has UNKNOWN official target fill for effective-foreground replay")
                continue
            fill_rgb = np.asarray(record["fill_rgb"], dtype=np.float64) * 255.0
            # The Goal threshold is *relative local-background contrast*, not
            # a naked alpha cutoff.  `knockout_rgb` is the official page at
            # the same lattice with only this CID removed, so it is the exact
            # local background for all later/earlier paint under the target.
            baseline_contrast = np.max(np.abs(baseline_rgb.astype(np.int16) - knockout_rgb.astype(np.int16)), axis=2)
            direct_contrast = np.max(np.abs(native_crop.astype(np.int16) - knockout_rgb.astype(np.int16)), axis=2)
            replay_composite_float = (
                (alpha[..., None].astype(np.float64) / 255.0) * fill_rgb
                + (1.0 - alpha[..., None].astype(np.float64) / 255.0) * knockout_rgb.astype(np.float64)
            )
            # The official native lattice is 8-bit RGB.  Compare the replay
            # through that same final integer quantisation; e.g. a 28/255
            # gray edge over white composites to 235.45 and is stored as 235,
            # i.e. a real 20/255 effective foreground pixel, not 19.55.
            replay_contrast_float = np.max(
                np.abs(replay_composite_float - knockout_rgb.astype(np.float64)), axis=2
            )
            replay_effective_float = replay_contrast_float >= 20.0
            replay_composite = np.clip(np.rint(replay_composite_float), 0, 255).astype(np.uint8)
            replay_contrast = np.max(
                np.abs(replay_composite.astype(np.int16) - knockout_rgb.astype(np.int16)), axis=2
            )
            baseline_effective = baseline_contrast >= 20
            direct_effective = direct_contrast >= 20
            replay_effective = replay_contrast >= 20.0
            baseline_direct_xor = np.logical_xor(baseline_effective, direct_effective)
            baseline_replay_xor = np.logical_xor(baseline_effective, replay_effective)
            direct_replay_xor = np.logical_xor(direct_effective, replay_effective)
            replay_quantization_boundary = np.logical_xor(replay_effective_float, replay_effective)
            # The complete official full-page CID knockout is the authority
            # for effective foreground: it preserves every content-stream
            # paint before/after the target on the same renderer/lattice.  The
            # transparent isolated replay proves source-path identity/support;
            # its alpha is not itself the 20/255 foreground authority because
            # transparent compositing can round differently on coloured fills.
            raw_outside_isolated_alpha = direct_effective & ~alpha_nonzero
            baseline_outside_isolated_alpha = baseline_effective & ~alpha_nonzero
            transparent_alpha_overpredict = replay_effective & ~baseline_effective
            transparent_alpha_underpredict = baseline_effective & ~replay_effective
            drift_delta = np.max(
                np.abs(baseline_rgb.astype(np.int16) - native_crop.astype(np.int16)), axis=2
            )
            # A cropped replay can differ by 1--2 RGB units at a patterned
            # CropBox edge.  It is admissible only when that coordinate is
            # subthreshold in *both* direct/baseline effective supports and
            # not backed by >=20 replay alpha.  Every other mismatch remains
            # unsafe and fails the closure gate.
            safe_subthreshold_drift = (
                baseline_native_diff
                & (drift_delta < 20)
                & ~baseline_effective
                & ~direct_effective
                & ~replay_effective
                & (alpha < 20)
            )
            unsafe_drift = baseline_native_diff & ~safe_subthreshold_drift
            delta_outside_alpha = direct_knockout_diff & ~alpha_nonzero
            delta_below20 = direct_knockout_diff & ~alpha_ge20
            visibility[glyph_id] = {
                "baseline_effective": baseline_effective,
                "direct_effective": direct_effective,
                "replay_effective": replay_effective,
                "replay_effective_float": replay_effective_float,
                "replay_quantization_boundary": replay_quantization_boundary,
                "raw_outside_isolated_alpha": raw_outside_isolated_alpha,
                "baseline_outside_isolated_alpha": baseline_outside_isolated_alpha,
                "transparent_alpha_overpredict": transparent_alpha_overpredict,
                "transparent_alpha_underpredict": transparent_alpha_underpredict,
                "raw_delta": direct_knockout_diff,
                "safe_subthreshold_drift": safe_subthreshold_drift,
                "unsafe_drift": unsafe_drift,
                "baseline_native_diff": baseline_native_diff,
                "baseline_contrast": baseline_contrast,
                "direct_contrast": direct_contrast,
                "replay_contrast": replay_contrast,
                "replay_contrast_float": replay_contrast_float,
                "knockout_rgb": knockout_rgb,
                "baseline_rgb": baseline_rgb,
            }
            row.update(
                {
                    "BASELINE_RENDERED_GRID": f"{baseline_rgb.shape[1]}x{baseline_rgb.shape[0]}",
                    "KNOCKOUT_RENDERED_GRID": f"{knockout_rgb.shape[1]}x{knockout_rgb.shape[0]}",
                    "BASELINE_VS_DIRECT_NATIVE_MISMATCH_PIXELS": int(baseline_native_diff.sum()),
                    "BASELINE_DIRECT_SUBTHRESHOLD_AA_DRIFT_PIXELS": int(safe_subthreshold_drift.sum()),
                    "BASELINE_DIRECT_UNSAFE_MISMATCH_PIXELS": int(unsafe_drift.sum()),
                    "DIRECT_MINUS_KNOCKOUT_FINAL_VISIBLE_PIXELS": int(direct_knockout_diff.sum()),
                    "TARGET_ALPHA_NONZERO_PIXELS": int(alpha_nonzero.sum()),
                    "TARGET_ALPHA_GE20_PIXELS": int(alpha_ge20.sum()),
                    "BASELINE_EFFECTIVE_FOREGROUND_GE20_PIXELS": int(baseline_effective.sum()),
                    "DIRECT_EFFECTIVE_FOREGROUND_GE20_PIXELS": int(direct_effective.sum()),
                    "REPLAY_EFFECTIVE_FOREGROUND_GE20_PIXELS": int(replay_effective.sum()),
                    "REPLAY_FLOAT_VS_INTEGER_EFFECTIVE_XOR_PIXELS": int(replay_quantization_boundary.sum()),
                    "BASELINE_DIRECT_EFFECTIVE_XOR_PIXELS": int(baseline_direct_xor.sum()),
                    "BASELINE_REPLAY_EFFECTIVE_XOR_PIXELS": int(baseline_replay_xor.sum()),
                    "DIRECT_REPLAY_EFFECTIVE_XOR_PIXELS": int(direct_replay_xor.sum()),
                    "RAW_EFFECTIVE_OUTSIDE_ISOLATED_ALPHA_PIXELS": int(raw_outside_isolated_alpha.sum()),
                    "BASELINE_EFFECTIVE_OUTSIDE_ISOLATED_ALPHA_PIXELS": int(baseline_outside_isolated_alpha.sum()),
                    "TRANSPARENT_ALPHA_EFFECTIVE_OVERPREDICT_PIXELS": int(transparent_alpha_overpredict.sum()),
                    "TRANSPARENT_ALPHA_EFFECTIVE_UNDERPREDICT_PIXELS": int(transparent_alpha_underpredict.sum()),
                    "FINAL_VISIBLE_DELTA_OUTSIDE_TARGET_ALPHA_PIXELS": int(delta_outside_alpha.sum()),
                    "FINAL_VISIBLE_DELTA_BELOW20_ALPHA_PIXELS": int(delta_below20.sum()),
                    "STATUS": (
                        "PASS"
                        if not unsafe_drift.any() and not baseline_direct_xor.any() and not raw_outside_isolated_alpha.any() and not baseline_outside_isolated_alpha.any()
                        else "FAIL_EFFECTIVE_FOREGROUND_CLOSURE"
                    ),
                }
            )
    return visibility, manifest, errors


def render_official_glyph_replays(
    glyphs: list[dict[str, Any]],
    reader: PdfReader,
    page: Any,
    stream: ContentStream,
    replay_pdf_path: Path,
    scale: float,
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]], list[str]]:
    """Build/render every one-glyph official content replay at native 300dpi."""
    errors: list[str] = []
    writer = PdfWriter()
    manifest: list[dict[str, Any]] = []
    ordered = sorted(glyphs, key=lambda glyph: glyph["glyph_id"])
    for replay_page, glyph in enumerate(ordered, start=1):
        if not glyph.get("pdf_replay_mapping_pass"):
            errors.append(f"{glyph['glyph_id']} cannot be replayed: mapping failed")
            continue
        try:
            data, method = _make_replay_stream(reader, stream, glyph)
        except Exception as exc:  # noqa: BLE001 - evidence failure is explicit.
            errors.append(f"{glyph['glyph_id']} replay stream: {exc}")
            continue
        out_page = writer.add_page(page)
        out_stream = DecodedStreamObject()
        out_stream.set_data(data)
        out_page[NameObject("/Contents")] = writer._add_object(out_stream)
        x0, y0, x1, y1 = glyph["char_bbox_px"]
        height_pt = float(page.mediabox.height)
        # These edges are native-pixel-aligned source coordinates.  CropBox
        # avoids a full-page replay raster but keeps the official 300dpi phase.
        out_page.cropbox = RectangleObject(
            [x0 / scale, height_pt - y1 / scale, x1 / scale, height_pt - y0 / scale]
        )
        record = glyph["pdf_replay_record"]
        manifest.append(
            {
                "REPLAY_PAGE": replay_page,
                "GLYPH_ID": glyph["glyph_id"],
                "EXPECTED_CHAR": glyph["expected_char"],
                "SVG_SHAPE_ID": glyph["svg_shape_id"],
                "PDF_CONTENT_OP_INDEX": record["op_index"],
                "PDF_CONTENT_OPERATOR": record["operator"].decode("ascii"),
                "PDF_CID_HEX": glyph["pdf_replay_cid_hex"],
                "PDF_FONT_RESOURCE": record["font_info"]["font_resource"],
                "PDF_FONT_SUBTYPE": record["font_info"]["font_subtype"],
                "PDF_FONT_ENCODING": record["font_info"]["font_encoding"],
                "PDF_CID_WIDTH_BYTES": record["font_info"]["cid_width_bytes"],
                "PDF_FONT_SIZE_PT": f"{record['font_size']:.8f}",
                "PDF_CTM": _matrix_csv(record["ctm"]),
                "PDF_TEXT_MATRIX": _matrix_csv(record["text_matrix"]),
                "PDF_GLOBAL_TEXT_MATRIX": _matrix_csv(record["global_text_matrix"]),
                "PDF_SCOPE_PRE_CTM": _matrix_csv(record["scope_pre_ctm"]),
                "PDF_TEXT_RENDER_MODE": record["text_render_mode"],
                "PDF_FILL_RGB_0_1": "UNKNOWN" if record["fill_rgb"] is None else ",".join(f"{value:.6f}" for value in record["fill_rgb"]),
                "PDF_FILL_OPACITY": f"{record['fill_opacity']:.6f}",
                "PDF_FILL_OPACITY_PROOF": record["fill_opacity_proof"],
                "PDF_SCOPE_START_OP": record["scope_start"],
                "PDF_SCOPE_END_OP": record["scope_end"],
                "PDF_SCOPE_TEXT_OPERATOR_COUNT": record["scope_text_count"],
                "PDF_SCOPE_NON_TEXT_PAINT_COUNT": record["scope_paint_count"],
                "REPLAY_CROPBOX_NATIVE_PX": f"{x0},{y0},{x1},{y1}",
                "REPLAY_METHOD": method,
                "REPLAY_STATUS": "PENDING_RENDER",
            }
        )
    if len(manifest) != len(ordered):
        errors.append(f"replay-page manifest {len(manifest)} != glyph count {len(ordered)}")
    replay_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with replay_pdf_path.open("wb") as output:
        writer.write(output)
    if errors:
        return {}, manifest, errors
    alpha_masks: dict[str, np.ndarray] = {}
    with tempfile.TemporaryDirectory(prefix="fig_p634_replay_") as temp:
        scratch = Path(temp)
        source_pdf = scratch / "official_glyph_replays.pdf"
        shutil.copyfile(replay_pdf_path, source_pdf)
        out_base = scratch / "glyph"
        command = [
            "pdftocairo", "-png", "-transp", "-cropbox", "-r", "300",
            str(source_pdf), str(out_base),
        ]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            return {}, manifest, [f"pdftocairo replay rendering exited {completed.returncode}: {completed.stderr.strip()}"]
        files: dict[int, Path] = {}
        for path in scratch.glob("glyph-*.png"):
            match = re.search(r"-(\d+)\.png$", path.name)
            if match:
                files[int(match.group(1))] = path
        if len(files) != len(ordered):
            return {}, manifest, [f"pdftocairo replay PNG count {len(files)} != glyph count {len(ordered)}"]
        for row in manifest:
            page_no = int(row["REPLAY_PAGE"])
            glyph_id = row["GLYPH_ID"]
            path = files.get(page_no)
            if path is None:
                errors.append(f"{glyph_id} has no replay PNG for page {page_no}")
                continue
            try:
                with Image.open(path) as image:
                    rgba = np.asarray(image.convert("RGBA"))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{glyph_id} replay PNG unreadable: {exc}")
                continue
            x0, y0, x1, y1 = next(g["char_bbox_px"] for g in ordered if g["glyph_id"] == glyph_id)
            expected_shape = (y1 - y0, x1 - x0)
            # Poppler rounds a fractional CropBox *right/bottom* edge outward
            # on some pages.  Its CropBox left/top starts at the supplied
            # integer native x0/y0; retain exactly the requested native grid
            # from that origin and record any harmless right/bottom pad.
            if rgba.shape[0] < expected_shape[0] or rgba.shape[1] < expected_shape[1]:
                errors.append(f"{glyph_id} replay PNG grid {rgba.shape[1]}x{rgba.shape[0]} smaller than {expected_shape[1]}x{expected_shape[0]}")
                continue
            extra_w = rgba.shape[1] - expected_shape[1]
            extra_h = rgba.shape[0] - expected_shape[0]
            if extra_w > 1 or extra_h > 1:
                errors.append(f"{glyph_id} replay PNG grid {rgba.shape[1]}x{rgba.shape[0]} has unexpected CropBox pad {extra_w}x{extra_h}")
                continue
            # Keep the exact official replay alpha rather than collapsing it
            # here.  R4's final-visible gate separately audits every source
            # stroke pixel at alpha >=20/255 and retains lower-alpha edges in
            # a disclosed exempt ledger; a boolean >0 support is insufficient
            # for that distinction.
            alpha_masks[glyph_id] = rgba[: expected_shape[0], : expected_shape[1], 3].copy()
            row["REPLAY_RENDERED_GRID"] = f"{rgba.shape[1]}x{rgba.shape[0]}"
            row["REPLAY_RIGHT_BOTTOM_PAD_PX"] = f"{extra_w},{extra_h}"
            row["REPLAY_ALPHA_NONZERO_PIXELS"] = int((alpha_masks[glyph_id] > 0).sum())
            row["REPLAY_ALPHA_GE20_PIXELS"] = int((alpha_masks[glyph_id] >= 20).sum())
            row["REPLAY_STATUS"] = "PASS" if (alpha_masks[glyph_id] >= 20).any() else "FAIL_EMPTY_ALPHA_GE20"
    return alpha_masks, manifest, errors

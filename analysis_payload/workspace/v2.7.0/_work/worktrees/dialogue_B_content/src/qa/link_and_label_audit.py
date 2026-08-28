"""Audit concrete LaTeX labels, references, and internal hyperlink targets.

This complements the compiled-PDF link check: it catches misspelled or removed
anchors before a build and ignores only genuinely dynamic macro arguments.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
TARGET_RE = re.compile(r"\\hypertarget\{([^{}]+)\}")
REFERENCE_RE = re.compile(
    r"\\(?:ref|eqref|pageref|vref|Vref|cref|Cref|autoref|nameref)\{([^{}]+)\}"
)
HYPERREF_RE = re.compile(r"\\hyperref\[([^\]]+)\]")
HYPERLINK_RE = re.compile(r"\\hyperlink\{([^{}]+)\}")


@dataclass(frozen=True)
class Finding:
    code: str
    file: str
    line: int
    message: str


@dataclass(frozen=True)
class AuditResult:
    source_root: str
    files: int
    labels: int
    targets: int
    references: int
    hyperlinks: int
    findings: tuple[Finding, ...]

    @property
    def passed(self) -> bool:
        return not self.findings

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "source_root": self.source_root,
            "passed": self.passed,
            "summary": {
                "files": self.files,
                "labels": self.labels,
                "targets": self.targets,
                "references": self.references,
                "hyperlinks": self.hyperlinks,
                "findings": len(self.findings),
            },
            "findings": [asdict(item) for item in self.findings],
        }


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _strip_comments(text: str) -> str:
    chars = list(text)
    line_start = 0
    while line_start < len(chars):
        line_end = text.find("\n", line_start)
        if line_end < 0:
            line_end = len(chars)
        for index in range(line_start, line_end):
            if chars[index] != "%":
                continue
            slash_count = 0
            cursor = index - 1
            while cursor >= line_start and chars[cursor] == "\\":
                slash_count += 1
                cursor -= 1
            if slash_count % 2 == 0:
                for blank in range(index, line_end):
                    chars[blank] = " "
                break
        line_start = line_end + 1
    return "".join(chars)


def _source_files(source_root: Path) -> tuple[list[Path], Path]:
    roots = [source_root]
    drawing_root = source_root.parent / "绘图源码"
    if source_root.name == "讲义源码" and drawing_root.is_dir():
        roots.append(drawing_root)
    files = sorted({
        path
        for root in roots
        for suffix in ("*.tex", "*.sty", "*.cls")
        for path in root.rglob(suffix)
    })
    display_root = source_root.parent if len(roots) > 1 else source_root
    return files, display_root


def _is_dynamic(value: str) -> bool:
    return any(token in value for token in ("#", "\\", "{", "}"))


def _split_reference_group(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _balanced_brace_content(text: str, opening: int) -> tuple[str, int]:
    if opening < 0 or opening >= len(text) or text[opening] != "{":
        raise ValueError("expected opening brace")
    depth = 0
    for index in range(opening, len(text)):
        escaped = index > 0 and text[index - 1] == "\\"
        if text[index] == "{" and not escaped:
            depth += 1
        elif text[index] == "}" and not escaped:
            depth -= 1
            if depth == 0:
                return text[opening + 1:index], index + 1
    raise ValueError("unbalanced macro argument")


def _section_macro_labels(text: str) -> list[tuple[str, int]]:
    """Return labels created by the shared section-heading macros."""
    specifications = {
        r"\SLLevelSection": 3,
        r"\SLDirectSection": 2,
        r"\SLReviewSection": 2,
        r"\SLTeachSection": 2,
        r"\SLAdvancedSection": 2,
    }
    labels: list[tuple[str, int]] = []
    for macro, arity in specifications.items():
        cursor = 0
        while True:
            start = text.find(macro, cursor)
            if start < 0:
                break
            # Ignore the macro's own definition, which contains parameter tokens.
            if start > 0 and text[max(0, start - 20):start].find(r"\newcommand{") >= 0:
                cursor = start + len(macro)
                continue
            position = start + len(macro)
            arguments: list[str] = []
            try:
                for _ in range(arity):
                    while position < len(text) and text[position].isspace():
                        position += 1
                    argument, position = _balanced_brace_content(text, position)
                    arguments.append(argument.strip())
            except ValueError:
                cursor = start + len(macro)
                continue
            label = arguments[-1]
            if label and not _is_dynamic(label):
                labels.append((label, start))
            cursor = position
    return labels


def audit_links(source_root: Path) -> AuditResult:
    source_root = source_root.resolve()
    files, display_root = _source_files(source_root)
    label_locations: dict[str, list[tuple[str, int]]] = defaultdict(list)
    target_locations: dict[str, list[tuple[str, int]]] = defaultdict(list)
    reference_locations: list[tuple[str, str, int]] = []
    hyperlink_locations: list[tuple[str, str, int]] = []

    for path in files:
        text = _strip_comments(path.read_text(encoding="utf-8"))
        rel = path.relative_to(display_root).as_posix()
        for match in LABEL_RE.finditer(text):
            value = match.group(1).strip()
            if not _is_dynamic(value):
                label_locations[value].append((rel, _line_number(text, match.start())))
        for value, offset in _section_macro_labels(text):
            label_locations[value].append((rel, _line_number(text, offset)))
        for match in TARGET_RE.finditer(text):
            value = match.group(1).strip()
            if not _is_dynamic(value):
                target_locations[value].append((rel, _line_number(text, match.start())))
        for match in REFERENCE_RE.finditer(text):
            line = _line_number(text, match.start())
            for value in _split_reference_group(match.group(1)):
                if not _is_dynamic(value):
                    reference_locations.append((value, rel, line))
        for match in HYPERREF_RE.finditer(text):
            value = match.group(1).strip()
            if not _is_dynamic(value):
                reference_locations.append((value, rel, _line_number(text, match.start())))
        for match in HYPERLINK_RE.finditer(text):
            value = match.group(1).strip()
            if not _is_dynamic(value):
                hyperlink_locations.append((value, rel, _line_number(text, match.start())))

    findings: list[Finding] = []
    for label, locations in sorted(label_locations.items()):
        if len(locations) > 1:
            rendered = ", ".join(f"{file}:{line}" for file, line in locations)
            findings.append(Finding("duplicate_label", locations[0][0], locations[0][1],
                                    f"label {label!r} occurs at {rendered}"))
    for target, locations in sorted(target_locations.items()):
        if len(locations) > 1:
            rendered = ", ".join(f"{file}:{line}" for file, line in locations)
            findings.append(Finding("duplicate_target", locations[0][0], locations[0][1],
                                    f"hypertarget {target!r} occurs at {rendered}"))

    label_names = set(label_locations)
    target_names = set(target_locations)
    for value, rel, line in reference_locations:
        if value not in label_names:
            findings.append(Finding("unresolved_reference", rel, line,
                                    f"reference {value!r} has no concrete label"))
    for value, rel, line in hyperlink_locations:
        if value not in target_names and value not in label_names:
            findings.append(Finding("unresolved_hyperlink", rel, line,
                                    f"hyperlink {value!r} has no concrete target or label"))

    findings.sort(key=lambda item: (item.file, item.line, item.code, item.message))
    return AuditResult(
        source_root=str(source_root),
        files=len(files),
        labels=len(label_locations),
        targets=len(target_locations),
        references=len(reference_locations),
        hyperlinks=len(hyperlink_locations),
        findings=tuple(findings),
    )


def _default_source_root() -> Path:
    return Path(__file__).resolve().parents[1] / "讲义源码"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=_default_source_root())
    parser.add_argument("--json", type=Path, dest="json_path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    result = audit_links(args.source_root)
    payload = result.to_json()
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(rendered, encoding="utf-8")
    print(json.dumps({"passed": result.passed, **payload["summary"]}, ensure_ascii=False))
    for finding in result.findings:
        print(f"{finding.file}:{finding.line}: {finding.code}: {finding.message}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

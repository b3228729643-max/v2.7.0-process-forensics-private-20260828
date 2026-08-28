"""Project-wide source audit for the v2.7.0 candidate source tree.

The audit is intentionally source driven: it never treats a successful PDF
build as evidence that an algorithm contract is complete.  It can be run
during development (where a non-zero exit documents remaining work) and is
    required to return zero only after Gate B candidate integration is ready.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REQUIRED_FIELDS = frozenset({
    "input", "output", "preconditions", "initialization", "loop", "update",
    "domain", "failure", "stop", "budget", "status", "iterations",
    "diagnostics", "complexity",
})
ALLOWED_STATUSES = frozenset({
    "completed", "converged", "budget_stop", "invalid_input",
    "numerical_failure", "line_search_failed", "random_source_failure",
})
FORBIDDEN_SIZING = (r"\tiny", r"\scriptsize", r"\resizebox")
PLACEHOLDER_RE = re.compile(r"TODO|TBD|待补|占位", re.IGNORECASE)
LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
CHAPTER_RE = re.compile(r"\\chapter\{")
ALGORITHM_BEGIN_RE = re.compile(r"\\begin\{algorithm\}(?:\[[^\]]*\])?")
ALGORITHM_END = r"\end{algorithm}"
CONTRACT_BEGIN = r"\begin{AlgorithmContract}"
CONTRACT_END = r"\end{AlgorithmContract}"


@dataclass(frozen=True)
class Finding:
    code: str
    file: str
    line: int
    message: str


@dataclass(frozen=True)
class AlgorithmRecord:
    file: str
    line: int
    labels: tuple[str, ...]
    has_contract: bool


@dataclass(frozen=True)
class AuditResult:
    source_root: str
    chapter_files: int
    chapters: int
    algorithms: int
    contracted_algorithms: int
    labels: int
    findings: tuple[Finding, ...]
    algorithm_records: tuple[AlgorithmRecord, ...]

    @property
    def passed(self) -> bool:
        return not self.findings

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "source_root": self.source_root,
            "passed": self.passed,
            "summary": {
                "chapter_files": self.chapter_files,
                "chapters": self.chapters,
                "algorithms": self.algorithms,
                "contracted_algorithms": self.contracted_algorithms,
                "labels": self.labels,
                "findings": len(self.findings),
            },
            "findings": [asdict(item) for item in self.findings],
            "algorithm_records": [asdict(item) for item in self.algorithm_records],
        }


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _strip_comments(text: str) -> str:
    """Blank LaTeX comments while preserving offsets and line numbers."""
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


def _balanced_brace_content(text: str, opening: int) -> tuple[str, int]:
    if opening < 0 or opening >= len(text) or text[opening] != "{":
        raise ValueError("expected an opening brace")
    depth = 0
    for index in range(opening, len(text)):
        char = text[index]
        escaped = index > 0 and text[index - 1] == "\\"
        if char == "{" and not escaped:
            depth += 1
        elif char == "}" and not escaped:
            depth -= 1
            if depth == 0:
                return text[opening + 1:index], index + 1
    raise ValueError("unbalanced brace group")


def _parse_fields(config: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    cursor = 0
    while cursor < len(config):
        while cursor < len(config) and (config[cursor].isspace() or config[cursor] == ","):
            cursor += 1
        if cursor == len(config):
            break
        match = re.match(r"([a-z_]+)\s*=\s*", config[cursor:])
        if match is None:
            raise ValueError(f"cannot parse contract near {config[cursor:cursor + 60]!r}")
        key = match.group(1)
        cursor += match.end()
        if cursor >= len(config) or config[cursor] != "{":
            raise ValueError(f"field {key!r} is not brace-delimited")
        value, cursor = _balanced_brace_content(config, cursor)
        if key in fields:
            raise ValueError(f"duplicate field {key!r}")
        fields[key] = value.strip()
    return fields


def _status_tokens(value: str) -> set[str]:
    normalized = value.replace(r"\_", "_")
    return set(re.findall(r"(?<!\\)\b[a-z][a-z_]+\b", normalized))


def _chapter_files(source_root: Path) -> list[Path]:
    return sorted(
        path for path in source_root.rglob("*.tex")
        if "chapters" in path.parts
    )


def _source_files(source_root: Path) -> list[Path]:
    return sorted((*source_root.rglob("*.tex"), *source_root.rglob("*.sty"), *source_root.rglob("*.cls")))


def audit_source(source_root: Path) -> AuditResult:
    source_root = source_root.resolve()
    chapter_files = _chapter_files(source_root)
    findings: list[Finding] = []
    algorithms: list[AlgorithmRecord] = []
    label_locations: dict[str, list[tuple[str, int]]] = {}
    chapter_count = 0

    for path in _source_files(source_root):
        text = _strip_comments(path.read_text(encoding="utf-8"))
        rel = path.relative_to(source_root).as_posix()
        for match in LABEL_RE.finditer(text):
            label_locations.setdefault(match.group(1), []).append((rel, _line_number(text, match.start())))

    for label, locations in sorted(label_locations.items()):
        if len(locations) > 1:
            first_file, first_line = locations[0]
            rendered = ", ".join(f"{file}:{line}" for file, line in locations)
            findings.append(Finding("duplicate_label", first_file, first_line,
                                    f"label {label!r} occurs at {rendered}"))

    for path in chapter_files:
        text = _strip_comments(path.read_text(encoding="utf-8"))
        rel = path.relative_to(source_root).as_posix()
        chapter_count += len(CHAPTER_RE.findall(text))

        for token in FORBIDDEN_SIZING:
            for match in re.finditer(re.escape(token) + r"\b", text):
                findings.append(Finding("forbidden_sizing", rel, _line_number(text, match.start()),
                                        f"forbidden source sizing command {token}"))

        contract_ranges: list[tuple[int, int, dict[str, str] | None, int]] = []
        cursor = 0
        while True:
            start = text.find(CONTRACT_BEGIN, cursor)
            if start < 0:
                break
            config_open = text.find("{", start + len(CONTRACT_BEGIN))
            try:
                config, config_end = _balanced_brace_content(text, config_open)
                fields = _parse_fields(config)
            except ValueError as exc:
                findings.append(Finding("contract_parse_error", rel, _line_number(text, start), str(exc)))
                fields = None
                config_end = max(config_open + 1, start + len(CONTRACT_BEGIN))
            end_marker = text.find(CONTRACT_END, config_end)
            if end_marker < 0:
                findings.append(Finding("unterminated_contract", rel, _line_number(text, start),
                                        "AlgorithmContract has no closing marker"))
                end = len(text)
                cursor = len(text)
            else:
                end = end_marker + len(CONTRACT_END)
                cursor = end
            contract_ranges.append((start, end, fields, config_end))

        for match in ALGORITHM_BEGIN_RE.finditer(text):
            start = match.start()
            end_marker = text.find(ALGORITHM_END, match.end())
            if end_marker < 0:
                findings.append(Finding("unterminated_algorithm", rel, _line_number(text, start),
                                        "algorithm has no closing marker"))
                body = text[start:]
                end = len(text)
            else:
                end = end_marker + len(ALGORITHM_END)
                body = text[start:end]
            labels = tuple(LABEL_RE.findall(body))
            line = _line_number(text, start)
            enclosing = [item for item in contract_ranges if item[0] < start and end <= item[1]]
            has_contract = len(enclosing) == 1
            algorithms.append(AlgorithmRecord(rel, line, labels, has_contract))

            identity = labels[0] if labels else f"algorithm at line {line}"
            if not labels:
                findings.append(Finding("algorithm_missing_label", rel, line,
                                        "numbered algorithm has no label"))
            if not has_contract:
                code = "algorithm_multiple_contracts" if len(enclosing) > 1 else "algorithm_missing_contract"
                findings.append(Finding(code, rel, line,
                                        f"{identity} must be enclosed by exactly one AlgorithmContract"))
                continue

            _, _, fields, _ = enclosing[0]
            if fields is None:
                continue
            actual = set(fields)
            if actual != REQUIRED_FIELDS:
                missing = sorted(REQUIRED_FIELDS - actual)
                extra = sorted(actual - REQUIRED_FIELDS)
                findings.append(Finding("contract_field_set", rel, line,
                                        f"{identity}: missing={missing}, extra={extra}"))
            for name in sorted(REQUIRED_FIELDS & actual):
                value = fields[name]
                if not value:
                    findings.append(Finding("contract_empty_field", rel, line,
                                            f"{identity}: empty field {name}"))
                elif PLACEHOLDER_RE.search(value):
                    findings.append(Finding("contract_placeholder", rel, line,
                                            f"{identity}: placeholder in field {name}"))
            if "status" in fields:
                statuses = _status_tokens(fields["status"])
                if not statuses:
                    findings.append(Finding("contract_status_missing", rel, line,
                                            f"{identity}: status field has no normalized status"))
                unknown = statuses - ALLOWED_STATUSES
                if unknown:
                    findings.append(Finding("contract_status_invalid", rel, line,
                                            f"{identity}: non-standard statuses {sorted(unknown)}"))

    if len(chapter_files) != 37:
        findings.append(Finding("chapter_file_count", ".", 1,
                                f"expected 37 chapter files, found {len(chapter_files)}"))
    if chapter_count != 37:
        findings.append(Finding("chapter_count", ".", 1,
                                f"expected 37 chapter declarations, found {chapter_count}"))
    # v2.7.0 contains 66 distinct numbered algorithms.  The older threshold
    # of 70 counted proposed compatible splits that were never separate
    # algorithm environments; duplicating algorithms to meet it would corrupt
    # the authoritative source/object inventory.
    if len(algorithms) != 66:
        findings.append(Finding("algorithm_count", ".", 1,
                                f"expected exactly 66 authoritative algorithms, found {len(algorithms)}"))

    findings.sort(key=lambda item: (item.file, item.line, item.code, item.message))
    return AuditResult(
        source_root=str(source_root),
        chapter_files=len(chapter_files),
        chapters=chapter_count,
        algorithms=len(algorithms),
        contracted_algorithms=sum(record.has_contract for record in algorithms),
        labels=len(label_locations),
        findings=tuple(findings),
        algorithm_records=tuple(algorithms),
    )


def _default_source_root() -> Path:
    return Path(__file__).resolve().parents[1] / "讲义源码"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=_default_source_root())
    parser.add_argument("--json", type=Path, dest="json_path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    result = audit_source(args.source_root)
    payload = result.to_json()
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(rendered, encoding="utf-8")

    summary = payload["summary"]
    print(json.dumps({"passed": result.passed, **summary}, ensure_ascii=False))
    for finding in result.findings:
        print(f"{finding.file}:{finding.line}: {finding.code}: {finding.message}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

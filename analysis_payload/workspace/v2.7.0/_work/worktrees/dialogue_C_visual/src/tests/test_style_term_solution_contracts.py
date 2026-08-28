from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
SOURCE = ROOT / "讲义源码"
STYLE = SOURCE / "common" / "statlearnbook.sty"
RELEASE_MANIFEST = PROJECT_ROOT / "manifests" / "release_version.tex"


def active_latex_source(source: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in source.splitlines())


class StyleTermSolutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.style = STYLE.read_text(encoding="utf-8")
        cls.release_manifest = RELEASE_MANIFEST.read_text(encoding="utf-8")
        cls.tex_files = sorted(SOURCE.rglob("*.tex"))
        cls.chapter_files = sorted(SOURCE.glob("第*册_*/chapters/V*-C*.tex"))

    def test_canonical_term_macros_are_defined_and_used(self) -> None:
        for macro in (
            "DirichletMultinomial",
            "MetropolisHastings",
            "PageRank",
            "kNN",
            "kMeans",
            "kFold",
        ):
            self.assertRegex(
                self.style,
                rf"\\DeclareRobustCommand\{{\\{macro}\}}",
                macro,
            )

        corpus = "\n".join(path.read_text(encoding="utf-8") for path in self.tex_files)
        minimum_uses = {
            "DirichletMultinomial": 10,
            "MetropolisHastings": 24,
            "PageRank": 85,
            "kNN": 20,
            "kMeans": 40,
            "kFold": 7,
        }
        for macro, minimum in minimum_uses.items():
            self.assertGreaterEqual(corpus.count(rf"\{macro}"), minimum, macro)
            self.assertNotRegex(corpus, rf"\\{macro}(?!\{{\}})", f"unterminated {macro}")

    def test_release_version_is_canonical_on_cover_metadata_and_student_link(self) -> None:
        manifest_versions = re.findall(
            r"\\newcommand\s*\{\\SLReleaseVersion\}\s*\{(v\d+\.\d+\.\d+)\}",
            active_latex_source(self.release_manifest),
        )
        self.assertEqual(len(manifest_versions), 1)
        self.assertEqual(
            len(
                re.findall(
                    r"\\SLReleaseVersion\b",
                    active_latex_source(self.release_manifest),
                )
            ),
            1,
        )
        release_version = manifest_versions[0]

        definition_pattern = re.compile(
            r"\\(?:newcommand|renewcommand|providecommand)\s*"
            r"\{\\SLReleaseVersion\}"
        )
        version_sources = {RELEASE_MANIFEST, STYLE}
        for source_root in (SOURCE, PROJECT_ROOT / "styles", PROJECT_ROOT / "manifests"):
            for suffix in ("*.tex", "*.sty"):
                version_sources.update(source_root.rglob(suffix))
        definition_locations = [
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in sorted(version_sources)
            for _ in definition_pattern.finditer(
                active_latex_source(path.read_text(encoding="utf-8"))
            )
        ]
        self.assertEqual(definition_locations, ["manifests/release_version.tex"])

        self.assertIn(
            r"\InputIfFileExists{../../../manifests/release_version.tex}",
            self.style,
        )
        self.assertNotRegex(active_latex_source(self.style), definition_pattern)
        self.assertNotIn(release_version, self.style)

        pdf_name_definition = re.search(
            r"\\newcommand\{\\SLReleasePDFName\}\{(?P<name>[^}]*)\}",
            self.style,
        )
        self.assertIsNotNone(pdf_name_definition)
        self.assertIn(r"\SLReleaseVersion", pdf_name_definition.group("name"))
        self.assertNotRegex(pdf_name_definition.group("name"), r"v\d+\.\d+\.\d+")
        self.assertIn(r"\SLReleaseVersion\enspace·\enspace\SLBuildEditionLabel", self.style)
        self.assertIn(r"pdftitle={#2——#3（\SLReleaseVersion", self.style)
        self.assertIn(r"pdfsubject={统计学习方法初学者讲义 \SLReleaseVersion", self.style)
        self.assertIn(r"\href{run:\SLReleasePDFName}{完整解析版}", self.style)
        self.assertNotRegex(self.style, r"合并总册v\d+\.\d+\.\d+_完整解析版\.pdf")

    def test_no_visible_handwritten_term_variants_remain(self) -> None:
        forbidden = {
            "Dirichlet-multinomial dash": re.compile(r"Dirichlet(?:--|—|–|-)多项"),
            "Metropolis-Hastings dash": re.compile(r"Metropolis(?:--|—|–|-)Hastings"),
            "PageRank": re.compile(r"(?<!\\)PageRank"),
            "mathematical k term": re.compile(r"(?:\$[kK]\$|(?<![A-Za-z\\])[kK]|𝑘)(?:近邻|均值|折)"),
        }
        hits: list[str] = []
        for path in self.tex_files:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("%") or r"\hyphenation{" in line:
                    continue
                sort_separator = line.find("@") if (r"\index{" in line or r"\knowledgeanchor{" in line) else -1
                for label, pattern in forbidden.items():
                    for match in pattern.finditer(line):
                        if sort_separator >= 0 and match.start() < sort_separator:
                            continue
                        hits.append(f"{path.relative_to(ROOT)}:{number}:{label}:{match.group(0)}")
        self.assertEqual(hits, [], "\n".join(hits))

    def test_distribution_names_have_no_ascii_cjk_gap(self) -> None:
        pattern = re.compile(r"(?:Gamma|Beta|Dirichlet)[ \u3000]+[\u3400-\u9fff]")
        hits = []
        for path in self.tex_files:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.lstrip().startswith("%") and pattern.search(line):
                    hits.append(f"{path.relative_to(ROOT)}:{number}:{line.strip()}")
        self.assertEqual(hits, [], "\n".join(hits))

    def test_worked_answers_use_semantic_stages_without_a_generic_strip(self) -> None:
        stages = {
            "SolGiven": "已知与合法条件",
            "SolPlan": "方法选择",
            "SolDerive": "推导/计算",
            "SolCheck": "独立核验",
            "SolBoundary": "边界与易错点",
            "SolAnswer": "结论",
        }
        for macro, label in stages.items():
            self.assertIn(rf"\newcommand{{\{macro}}}", self.style)
            self.assertIn(label, self.style)
        worked_solution = re.search(
            r"\\newtcolorbox\{solution\}\{(?P<body>[\s\S]*?)\n\}",
            self.style,
        )
        self.assertIsNotNone(worked_solution)
        self.assertIn("enhanced,breakable", worked_solution.group("body"))
        self.assertNotIn(r"\SLSolutionStageGuide", worked_solution.group("body"))

        chapter_solution = re.search(
            r"\\newtcolorbox\{chapterexercisesolution\}\[1\]\{(?P<body>[\s\S]*?)\n\}",
            self.style,
        )
        self.assertIsNotNone(chapter_solution)
        self.assertIn("enhanced,breakable", chapter_solution.group("body"))
        self.assertIn(r"title after break={练习~\ref{#1}~解析（续）}", chapter_solution.group("body"))

        worked_beginnings = worked_endings = 0
        chapter_beginnings = chapter_endings = 0
        for path in self.chapter_files:
            source = path.read_text(encoding="utf-8")
            worked_beginnings += source.count(r"\begin{solution}")
            worked_endings += source.count(r"\end{solution}")
            chapter_beginnings += source.count(r"\begin{chapterexercisesolution}")
            chapter_endings += source.count(r"\end{chapterexercisesolution}")
        self.assertEqual(worked_beginnings, worked_endings)
        self.assertEqual(worked_beginnings, 66)
        self.assertEqual(chapter_beginnings, chapter_endings)
        self.assertEqual(chapter_beginnings, 553)


if __name__ == "__main__":
    unittest.main()

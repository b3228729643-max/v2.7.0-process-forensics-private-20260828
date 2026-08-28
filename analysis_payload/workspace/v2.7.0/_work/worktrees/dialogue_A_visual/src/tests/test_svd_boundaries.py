"""Independent boundary checks for Definition 26.3 (truncated SVD)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "讲义源码"
CHAPTER_SOURCE = (
    SOURCE_ROOT
    / "第04册_无监督学习与矩阵分解"
    / "chapters"
    / "V4-C03.tex"
)


def truncated_svd(matrix: np.ndarray, k: int) -> tuple[np.ndarray, int]:
    """Compute the rank-k SVD reconstruction after checking 1 <= k <= rank(A)."""
    matrix = np.asarray(matrix, dtype=float)
    rank = int(np.linalg.matrix_rank(matrix))
    if not 1 <= k <= rank:
        raise ValueError(f"k must satisfy 1 <= k <= rank(A)={rank}")
    u, singular_values, vt = np.linalg.svd(matrix, full_matrices=False)
    reconstruction = (u[:, :k] * singular_values[:k]) @ vt[:k, :]
    return reconstruction, rank


class TruncatedSVDBoundaryTests(unittest.TestCase):
    def assertReconstructs(self, actual: np.ndarray, expected: np.ndarray) -> None:
        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)

    def test_rank_one_matrix_has_exact_k_equals_r_reconstruction(self) -> None:
        matrix = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])
        reconstruction, rank = truncated_svd(matrix, k=1)
        self.assertEqual(rank, 1)
        self.assertReconstructs(reconstruction, matrix)

    def test_rank_two_k_one_is_not_exact(self) -> None:
        matrix = np.diag([3.0, 1.0])
        reconstruction, rank = truncated_svd(matrix, k=1)
        self.assertEqual(rank, 2)
        self.assertGreater(np.linalg.norm(matrix - reconstruction), 1e-12)

    def test_k_equals_r_exactly_reconstructs_a_full_rank_rectangular_matrix(self) -> None:
        matrix = np.array([[2.0, 1.0], [1.0, 3.0], [4.0, -1.0]])
        reconstruction, rank = truncated_svd(matrix, k=2)
        self.assertEqual(rank, min(matrix.shape))
        self.assertReconstructs(reconstruction, matrix)

    def test_k_domain_rejects_zero_and_values_above_rank(self) -> None:
        matrix = np.diag([2.0, 1.0])
        with self.assertRaisesRegex(ValueError, r"1 <= k <= rank\(A\)=2"):
            truncated_svd(matrix, k=0)
        with self.assertRaisesRegex(ValueError, r"1 <= k <= rank\(A\)=2"):
            truncated_svd(matrix, k=3)

    def test_definition_states_both_boundary_equivalences(self) -> None:
        source = CHAPTER_SOURCE.read_text(encoding="utf-8")
        self.assertRegex(source, r"1\\leq k\\leq r")
        self.assertRegex(source, r"A_k=A\\iff k=r")
        self.assertRegex(
            source,
            r"1\\leq k<r\\Longrightarrow A_k\\ne A",
        )

    def test_no_latex_source_retains_the_old_tail_zero_condition(self) -> None:
        old_tail_zero_condition = re.compile(
            r"\\sigma_\{k\+1\}\s*=\s*\\cdots\s*=\s*\\sigma_r\s*=\s*0"
        )
        offenders = []
        for path in SOURCE_ROOT.rglob("*.tex"):
            if old_tail_zero_condition.search(path.read_text(encoding="utf-8")):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [], f"旧尾部全零矛盾条件仍存在于: {offenders}")


if __name__ == "__main__":
    unittest.main()

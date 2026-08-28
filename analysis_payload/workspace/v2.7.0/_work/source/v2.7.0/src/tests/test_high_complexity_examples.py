"""Independent numerical checks for the high-risk probabilistic examples.

The references below are executable mathematical implementations.  They do
not parse constants from the lecture notes, so agreement is evidence beyond
typesetting or repeating the same worked answer.
"""

from __future__ import annotations

import itertools
import math
import unittest

import numpy as np


def log_multibeta(parameters: np.ndarray) -> float:
    values = np.asarray(parameters, dtype=float)
    return sum(math.lgamma(float(value)) for value in values) - math.lgamma(float(values.sum()))


def dirichlet_multinomial_closed_probability(alpha: np.ndarray, counts: np.ndarray) -> float:
    alpha = np.asarray(alpha, dtype=float)
    counts = np.asarray(counts, dtype=int)
    total = int(counts.sum())
    log_probability = (
        math.lgamma(total + 1)
        - sum(math.lgamma(int(count) + 1) for count in counts)
        + log_multibeta(alpha + counts)
        - log_multibeta(alpha)
    )
    return math.exp(log_probability)


def dirichlet_multinomial_by_predictive_sequences(alpha: np.ndarray, counts: np.ndarray) -> float:
    """Enumerate ordered sequences and use only one-step posterior prediction."""
    labels = tuple(
        label
        for label, count in enumerate(np.asarray(counts, dtype=int))
        for _ in range(int(count))
    )
    total_probability = 0.0
    for sequence in set(itertools.permutations(labels)):
        observed = np.zeros_like(alpha, dtype=float)
        probability = 1.0
        for label in sequence:
            probability *= float(alpha[label] + observed[label]) / float(alpha.sum() + observed.sum())
            observed[label] += 1.0
        total_probability += probability
    return total_probability


def lda_conditional(
    document_topic: np.ndarray,
    topic_word: np.ndarray,
    topic_totals: np.ndarray,
    *,
    document: int,
    word: int,
    alpha: np.ndarray,
    beta: np.ndarray,
) -> np.ndarray:
    weights = (
        (document_topic[document] + alpha)
        * (topic_word[:, word] + beta[word])
        / (topic_totals + beta.sum())
    )
    if not np.all(np.isfinite(weights)) or np.any(weights <= 0):
        raise ValueError("collapsed Gibbs weights must be finite and positive")
    return weights / weights.sum()


def collapsed_lda_log_joint(
    document_topic: np.ndarray,
    topic_word: np.ndarray,
    alpha: np.ndarray,
    beta: np.ndarray,
) -> float:
    result = 0.0
    for counts in document_topic:
        result += log_multibeta(counts + alpha) - log_multibeta(alpha)
    for counts in topic_word:
        result += log_multibeta(counts + beta) - log_multibeta(beta)
    return result


def pagerank_power(adjacency: np.ndarray, damping: float, preference: np.ndarray,
                   tolerance: float = 1e-13, budget: int = 10_000) -> tuple[np.ndarray, int]:
    adjacency = np.asarray(adjacency, dtype=float)
    preference = np.asarray(preference, dtype=float)
    column_sums = adjacency.sum(axis=0)
    transition = np.empty_like(adjacency)
    for column, total in enumerate(column_sums):
        transition[:, column] = preference if total == 0 else adjacency[:, column] / total
    rank = preference.copy()
    for iteration in range(1, budget + 1):
        candidate = damping * transition @ rank + (1.0 - damping) * preference
        if np.linalg.norm(candidate - rank, ord=1) <= tolerance:
            return candidate, iteration
        rank = candidate
    raise AssertionError("reference PageRank did not converge within its test budget")


def pagerank_linear_system(adjacency: np.ndarray, damping: float, preference: np.ndarray) -> np.ndarray:
    adjacency = np.asarray(adjacency, dtype=float)
    preference = np.asarray(preference, dtype=float)
    transition = np.empty_like(adjacency)
    for column, total in enumerate(adjacency.sum(axis=0)):
        transition[:, column] = preference if total == 0 else adjacency[:, column] / total
    return np.linalg.solve(
        np.eye(adjacency.shape[0]) - damping * transition,
        (1.0 - damping) * preference,
    )


def plsa_log_likelihood(counts: np.ndarray, topic_word: np.ndarray, document_topic: np.ndarray) -> float:
    probabilities = topic_word @ document_topic
    if np.any(probabilities <= 0) or not np.all(np.isfinite(probabilities)):
        raise ValueError("PLSA probabilities must be finite and positive")
    return float(np.sum(counts * np.log(probabilities)))


def plsa_em_step(counts: np.ndarray, topic_word: np.ndarray,
                 document_topic: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    vocabulary, documents = counts.shape
    topics = topic_word.shape[1]
    responsibilities = np.empty((vocabulary, documents, topics), dtype=float)
    for word in range(vocabulary):
        for document in range(documents):
            weights = topic_word[word, :] * document_topic[:, document]
            responsibilities[word, document, :] = weights / weights.sum()

    expected = counts[:, :, None] * responsibilities
    new_topic_word = expected.sum(axis=1)
    new_topic_word /= new_topic_word.sum(axis=0, keepdims=True)
    new_document_topic = expected.sum(axis=0).T
    new_document_topic /= new_document_topic.sum(axis=0, keepdims=True)
    return new_topic_word, new_document_topic


class DirichletMultinomialEvidenceTests(unittest.TestCase):
    def test_closed_evidence_matches_predictive_sequence_enumeration(self) -> None:
        alpha = np.array([0.7, 1.3, 2.1])
        counts = np.array([2, 1, 1])
        closed = dirichlet_multinomial_closed_probability(alpha, counts)
        enumerated = dirichlet_multinomial_by_predictive_sequences(alpha, counts)
        self.assertAlmostEqual(closed, enumerated, places=13)
        self.assertGreater(closed, 0.0)
        self.assertLess(closed, 1.0)


class CollapsedGibbsTests(unittest.TestCase):
    def test_conditional_matches_collapsed_joint_ratios_and_preserves_counts(self) -> None:
        alpha = np.array([0.4, 0.9])
        beta = np.array([0.3, 0.5, 0.7])
        # Counts after removing the token being resampled.
        document_topic = np.array([[2, 1], [0, 2]], dtype=int)
        topic_word = np.array([[1, 1, 0], [0, 1, 2]], dtype=int)
        topic_totals = topic_word.sum(axis=1)
        conditional = lda_conditional(
            document_topic, topic_word, topic_totals,
            document=0, word=2, alpha=alpha, beta=beta,
        )

        log_joints = []
        for topic in range(2):
            dt = document_topic.copy()
            tw = topic_word.copy()
            dt[0, topic] += 1
            tw[topic, 2] += 1
            log_joints.append(collapsed_lda_log_joint(dt, tw, alpha, beta))
        shifted = np.exp(np.asarray(log_joints) - max(log_joints))
        brute = shifted / shifted.sum()
        np.testing.assert_allclose(conditional, brute, rtol=1e-13, atol=1e-13)

        chosen = int(np.argmax(conditional))
        before_tokens = int(document_topic.sum())
        document_topic[0, chosen] += 1
        topic_word[chosen, 2] += 1
        self.assertEqual(int(document_topic.sum()), before_tokens + 1)
        self.assertEqual(int(topic_word.sum()), before_tokens + 1)
        self.assertAlmostEqual(float(conditional.sum()), 1.0, places=15)


class PageRankTests(unittest.TestCase):
    def test_dangling_power_iteration_matches_linear_system(self) -> None:
        # Column 2 is dangling; the other columns form a directed cycle fragment.
        adjacency = np.array([
            [0.0, 0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ])
        preference = np.array([0.4, 0.3, 0.2, 0.1])
        damping = 0.85
        power, iterations = pagerank_power(adjacency, damping, preference)
        exact = pagerank_linear_system(adjacency, damping, preference)
        np.testing.assert_allclose(power, exact, rtol=1e-11, atol=1e-12)
        self.assertGreater(iterations, 0)
        self.assertAlmostEqual(float(power.sum()), 1.0, places=12)
        self.assertTrue(np.all(power >= 0))


class PLSAEMTests(unittest.TestCase):
    def test_em_is_monotone_and_keeps_both_probability_simplexes(self) -> None:
        counts = np.array([
            [5.0, 0.0, 1.0],
            [3.0, 1.0, 0.0],
            [0.0, 4.0, 1.0],
            [0.0, 2.0, 5.0],
        ])
        topic_word = np.array([
            [0.40, 0.10],
            [0.35, 0.15],
            [0.15, 0.35],
            [0.10, 0.40],
        ])
        document_topic = np.array([
            [0.75, 0.30, 0.45],
            [0.25, 0.70, 0.55],
        ])
        trajectory = [plsa_log_likelihood(counts, topic_word, document_topic)]
        for _ in range(25):
            topic_word, document_topic = plsa_em_step(counts, topic_word, document_topic)
            trajectory.append(plsa_log_likelihood(counts, topic_word, document_topic))

        increments = np.diff(np.asarray(trajectory))
        self.assertGreaterEqual(float(increments.min()), -1e-11)
        self.assertGreater(trajectory[-1], trajectory[0] + 1e-3)
        np.testing.assert_allclose(topic_word.sum(axis=0), np.ones(2), atol=1e-13)
        np.testing.assert_allclose(document_topic.sum(axis=0), np.ones(3), atol=1e-13)
        self.assertTrue(np.all(topic_word >= 0))
        self.assertTrue(np.all(document_topic >= 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)

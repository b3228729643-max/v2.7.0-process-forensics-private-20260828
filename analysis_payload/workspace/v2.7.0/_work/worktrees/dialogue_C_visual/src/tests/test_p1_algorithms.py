"""Independent executable contract tests for v1.9.0 P1 algorithms.

The small reference implementations below model the mathematical/control-flow
contracts.  They do not parse the LaTeX or copy numerical answers from it.
"""

from __future__ import annotations

import math
import unittest
from collections.abc import Callable, Sequence
from typing import Any


def _finite_real(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def fixed_step_gradient_descent(
    f: Callable[[float], float],
    grad: Callable[[float], float],
    x0: float,
    step: float,
    tolerance: float,
    budget: int,
) -> dict[str, Any]:
    """One-dimensional reference for the final-point/status contract."""

    x = x0
    updates = 0

    def evaluate(point: float) -> tuple[float, float]:
        value = f(point)
        gradient = grad(point)
        if not (_finite_real(value) and _finite_real(gradient)):
            raise ArithmeticError("non-finite objective or gradient")
        return float(value), float(gradient)

    def finish(status: str, failure_location: Any = None, diagnostic: str = "") -> dict[str, Any]:
        # This fresh call is intentional: every normal exit is certified at the
        # point actually returned, never with a gradient cached at an old point.
        value, gradient = evaluate(x)
        return {
            "x": x,
            "f_final": value,
            "gradient_norm": abs(gradient),
            "updates": updates,
            "status": status,
            "failure_location": failure_location,
            "diagnostic": diagnostic,
        }

    if not _finite_real(x0):
        return {
            "x": None,
            "f_final": None,
            "gradient_norm": None,
            "updates": 0,
            "status": "invalid_input",
            "failure_location": "x0",
            "diagnostic": "x0 must be finite",
        }
    if not _finite_real(step) or step <= 0:
        return finish("invalid_input", "step", "step must be finite and positive")
    if not _finite_real(tolerance) or tolerance <= 0:
        return finish("invalid_input", "tolerance", "tolerance must be finite and positive")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
        return finish("invalid_input", "budget", "budget must be a non-negative integer")

    try:
        evaluate(x)
    except (ArithmeticError, OverflowError, ValueError, ZeroDivisionError) as exc:
        return {
            "x": None,
            "f_final": None,
            "gradient_norm": None,
            "updates": 0,
            "status": "numerical_failure",
            "failure_location": x,
            "diagnostic": f"initial evaluation failed: {exc}",
        }

    while True:
        _, gradient = evaluate(x)
        if abs(gradient) <= tolerance:
            return finish("converged")
        if updates == budget:
            return finish("budget_stop", diagnostic="update budget exhausted")

        candidate = x - step * gradient
        try:
            evaluate(candidate)
        except (ArithmeticError, OverflowError, ValueError, ZeroDivisionError) as exc:
            return finish(
                "numerical_failure",
                failure_location=candidate,
                diagnostic=f"candidate evaluation failed: {exc}",
            )
        x = candidate
        updates += 1


def dirichlet_multinomial_update(
    alpha: Sequence[float],
    *,
    categories: Sequence[int] | None = None,
    counts: Sequence[int] | None = None,
    total: int | None = None,
) -> dict[str, Any]:
    """Reference for the mutually exclusive sequence/counts contract."""

    k = len(alpha)
    if k < 1 or any(not _finite_real(a) or a <= 0 for a in alpha):
        return {"status": "invalid_input", "diagnostic": "invalid_alpha"}

    has_sequence = categories is not None
    has_counts = counts is not None
    if has_sequence == has_counts:
        return {"status": "invalid_input", "diagnostic": "provide_exactly_one_input"}

    if has_sequence:
        working_counts = [0] * k
        assert categories is not None
        for position, category in enumerate(categories, start=1):
            if (
                isinstance(category, bool)
                or not isinstance(category, int)
                or not 1 <= category <= k
            ):
                return {
                    "status": "invalid_input",
                    "diagnostic": "invalid_class",
                    "position": position,
                }
            working_counts[category - 1] += 1
    else:
        assert counts is not None
        if len(counts) != k:
            return {"status": "invalid_input", "diagnostic": "length_mismatch"}
        if any(isinstance(n, bool) or not isinstance(n, int) or n < 0 for n in counts):
            return {"status": "invalid_input", "diagnostic": "invalid_count"}
        working_counts = list(counts)

    sample_total = sum(working_counts)
    if total is not None and total != sample_total:
        return {"status": "invalid_input", "diagnostic": "total_mismatch"}

    posterior = [float(a + n) for a, n in zip(alpha, working_counts)]
    posterior_total = sum(posterior)
    predictive = [a / posterior_total for a in posterior]

    def log_multibeta(parameters: Sequence[float]) -> float:
        return sum(math.lgamma(a) for a in parameters) - math.lgamma(sum(parameters))

    log_evidence = (
        math.lgamma(sample_total + 1)
        - sum(math.lgamma(n + 1) for n in working_counts)
        + log_multibeta(posterior)
        - log_multibeta(alpha)
    )
    return {
        "status": "completed",
        "N": sample_total,
        "counts": working_counts,
        "posterior": posterior,
        "posterior_total": posterior_total,
        "predictive": predictive,
        "log_evidence": log_evidence,
    }


def rejection_sample_budgeted(
    p: Callable[[float], float],
    q: Callable[[float], float],
    proposal_source: Callable[[], float],
    uniform_source: Callable[[], float],
    *,
    envelope: float,
    target: int,
    budget: int,
) -> dict[str, Any]:
    """Reference for Algorithm 31.3B, including all required exits."""

    samples: list[float] = []
    proposals = 0
    accepted = 0

    def result(status: str, diagnostic: str = "", location: Any = None) -> dict[str, Any]:
        return {
            "samples": samples.copy(),
            "proposals": proposals,
            "accepted": accepted,
            "status": status,
            "diagnostic": diagnostic,
            "failure_location": location,
        }

    if (
        isinstance(target, bool)
        or not isinstance(target, int)
        or target < 0
        or isinstance(budget, bool)
        or not isinstance(budget, int)
        or budget < 0
        or not _finite_real(envelope)
        or envelope < 1
    ):
        return result("invalid_input", "invalid target, budget, or envelope")
    if target == 0:
        return result("completed", "no random source called")
    if budget == 0:
        return result("budget_stop", "proposal budget is zero")

    while accepted < target and proposals < budget:
        try:
            candidate = proposal_source()
        except Exception as exc:  # A source failure is an explicit algorithm state.
            return result("random_source_failure", f"proposal source failed: {exc}")
        if not _finite_real(candidate):
            return result("random_source_failure", "proposal is non-finite", candidate)
        proposals += 1

        try:
            uniform = uniform_source()
        except Exception as exc:
            return result("random_source_failure", f"uniform source failed: {exc}", proposals)
        if not _finite_real(uniform) or not 0 < uniform < 1:
            return result("random_source_failure", "uniform must lie in (0, 1)", uniform)

        try:
            p_value = p(candidate)
            q_value = q(candidate)
        except Exception as exc:
            return result("numerical_failure", f"density evaluation failed: {exc}", candidate)
        if (
            not _finite_real(p_value)
            or not _finite_real(q_value)
            or p_value < 0
            or q_value <= 0
        ):
            return result("numerical_failure", "invalid density value", candidate)

        ratio = p_value / (envelope * q_value)
        if not _finite_real(ratio):
            return result("numerical_failure", "non-finite acceptance ratio", candidate)
        if not 0 <= ratio <= 1:
            return result("invalid_input", "envelope_condition_failure", candidate)
        if uniform <= ratio:
            samples.append(float(candidate))
            accepted += 1

    if accepted == target:
        return result("completed")
    return result("budget_stop", "proposal budget exhausted")


class FixedStepGradientDescentTests(unittest.TestCase):
    def test_one_update_budget_stop_uses_true_final_gradient(self) -> None:
        result = fixed_step_gradient_descent(
            lambda x: 0.5 * x * x,
            lambda x: x,
            x0=2.0,
            step=0.25,
            tolerance=1e-12,
            budget=1,
        )
        self.assertEqual(result["status"], "budget_stop")
        self.assertEqual(result["updates"], 1)
        self.assertAlmostEqual(result["x"], 1.5)
        self.assertAlmostEqual(result["gradient_norm"], abs(result["x"]))
        self.assertAlmostEqual(result["f_final"], 0.5 * result["x"] ** 2)

    def test_initial_point_can_converge_without_update(self) -> None:
        result = fixed_step_gradient_descent(
            lambda x: x * x,
            lambda x: 2 * x,
            x0=1e-10,
            step=0.1,
            tolerance=1e-8,
            budget=5,
        )
        self.assertEqual(result["status"], "converged")
        self.assertEqual(result["updates"], 0)
        self.assertEqual(result["x"], 1e-10)

    def test_domain_failure_returns_last_legal_point_and_location(self) -> None:
        result = fixed_step_gradient_descent(
            math.log,
            lambda x: 1 / x,
            x0=1.0,
            step=2.0,
            tolerance=1e-12,
            budget=3,
        )
        self.assertEqual(result["status"], "numerical_failure")
        self.assertEqual(result["x"], 1.0)
        self.assertEqual(result["failure_location"], -1.0)
        self.assertAlmostEqual(result["f_final"], 0.0)
        self.assertAlmostEqual(result["gradient_norm"], 1.0)

    def test_invalid_step_and_tolerance(self) -> None:
        bad_step = fixed_step_gradient_descent(lambda x: x * x, lambda x: 2 * x, 1.0, 0.0, 1e-6, 1)
        bad_tolerance = fixed_step_gradient_descent(
            lambda x: x * x, lambda x: 2 * x, 1.0, 0.1, math.nan, 1
        )
        self.assertEqual(bad_step["status"], "invalid_input")
        self.assertEqual(bad_step["failure_location"], "step")
        self.assertEqual(bad_tolerance["status"], "invalid_input")
        self.assertEqual(bad_tolerance["failure_location"], "tolerance")


class DirichletMultinomialTests(unittest.TestCase):
    def test_sequence_only_and_counts_only_are_identical(self) -> None:
        from_sequence = dirichlet_multinomial_update([1.0, 2.0, 3.0], categories=[1, 3, 1, 2])
        from_counts = dirichlet_multinomial_update([1.0, 2.0, 3.0], counts=[2, 1, 1])
        self.assertEqual(from_sequence["status"], "completed")
        self.assertEqual(from_counts["status"], "completed")
        for key in ("N", "counts", "posterior", "posterior_total", "predictive"):
            self.assertEqual(from_sequence[key], from_counts[key])
        self.assertAlmostEqual(from_sequence["log_evidence"], from_counts["log_evidence"])

    def test_both_and_neither_are_invalid(self) -> None:
        both = dirichlet_multinomial_update([1.0, 1.0], categories=[1], counts=[1, 0])
        neither = dirichlet_multinomial_update([1.0, 1.0])
        self.assertEqual(both["status"], "invalid_input")
        self.assertEqual(neither["status"], "invalid_input")
        self.assertEqual(both["diagnostic"], "provide_exactly_one_input")
        self.assertEqual(neither["diagnostic"], "provide_exactly_one_input")

    def test_invalid_category(self) -> None:
        result = dirichlet_multinomial_update([1.0, 1.0], categories=[1, 3])
        self.assertEqual(result["status"], "invalid_input")
        self.assertEqual(result["diagnostic"], "invalid_class")
        self.assertEqual(result["position"], 2)

    def test_negative_count_length_and_total_mismatches(self) -> None:
        negative = dirichlet_multinomial_update([1.0, 1.0], counts=[1, -1])
        length = dirichlet_multinomial_update([1.0, 1.0], counts=[1, 0, 0])
        total = dirichlet_multinomial_update([1.0, 1.0], counts=[1, 0], total=2)
        self.assertEqual((negative["status"], negative["diagnostic"]), ("invalid_input", "invalid_count"))
        self.assertEqual((length["status"], length["diagnostic"]), ("invalid_input", "length_mismatch"))
        self.assertEqual((total["status"], total["diagnostic"]), ("invalid_input", "total_mismatch"))


class BudgetedRejectionSamplingTests(unittest.TestCase):
    @staticmethod
    def source(values: Sequence[float]) -> Callable[[], float]:
        iterator = iter(values)
        return lambda: next(iterator)

    def test_zero_target_completes_without_random_calls(self) -> None:
        calls = {"proposal": 0, "uniform": 0}

        def proposal() -> float:
            calls["proposal"] += 1
            return 0.0

        def uniform() -> float:
            calls["uniform"] += 1
            return 0.5

        result = rejection_sample_budgeted(
            lambda _: 1.0, lambda _: 1.0, proposal, uniform, envelope=1.0, target=0, budget=0
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual((result["proposals"], result["accepted"]), (0, 0))
        self.assertEqual(calls, {"proposal": 0, "uniform": 0})

    def test_zero_budget_for_positive_target(self) -> None:
        result = rejection_sample_budgeted(
            lambda _: 1.0,
            lambda _: 1.0,
            self.source([0.0]),
            self.source([0.5]),
            envelope=1.0,
            target=1,
            budget=0,
        )
        self.assertEqual(result["status"], "budget_stop")
        self.assertEqual(result["samples"], [])

    def test_success_reports_actual_proposals_and_acceptances(self) -> None:
        result = rejection_sample_budgeted(
            lambda _: 1.0,
            lambda _: 1.0,
            self.source([10.0, 20.0]),
            self.source([0.2, 0.8]),
            envelope=1.0,
            target=2,
            budget=5,
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["samples"], [10.0, 20.0])
        self.assertEqual((result["proposals"], result["accepted"]), (2, 2))

    def test_budget_exhaustion_returns_partial_prefix(self) -> None:
        result = rejection_sample_budgeted(
            lambda _: 0.5,
            lambda _: 1.0,
            self.source([10.0, 20.0, 30.0]),
            self.source([0.25, 0.75, 0.1]),
            envelope=1.0,
            target=3,
            budget=3,
        )
        self.assertEqual(result["status"], "budget_stop")
        self.assertEqual(result["samples"], [10.0, 30.0])
        self.assertEqual((result["proposals"], result["accepted"]), (3, 2))

    def test_ratio_violation_is_invalid_input_not_rejection(self) -> None:
        result = rejection_sample_budgeted(
            lambda _: 1.2,
            lambda _: 1.0,
            self.source([4.0]),
            self.source([0.9]),
            envelope=1.0,
            target=1,
            budget=1,
        )
        self.assertEqual(result["status"], "invalid_input")
        self.assertEqual(result["diagnostic"], "envelope_condition_failure")
        self.assertEqual(result["samples"], [])
        self.assertEqual((result["proposals"], result["accepted"]), (1, 0))
        self.assertEqual(result["failure_location"], 4.0)

    def test_random_source_failure_preserves_partial_state(self) -> None:
        def broken_source() -> float:
            raise RuntimeError("rng unavailable")

        result = rejection_sample_budgeted(
            lambda _: 1.0,
            lambda _: 1.0,
            broken_source,
            self.source([0.5]),
            envelope=1.0,
            target=1,
            budget=1,
        )
        self.assertEqual(result["status"], "random_source_failure")
        self.assertEqual((result["proposals"], result["accepted"]), (0, 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)

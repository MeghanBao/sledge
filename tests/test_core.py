"""Logic tests that need no Isabelle install — a FakeRunner stands in for it.

They pin down the honest behaviour: VERIFIED only when a proof checks, REFUTED
only on a real counterexample, UNKNOWN for everything else (including "Isabelle
not installed").
"""

import pytest

from sledge import (
    REFUTED,
    UNKNOWN,
    VERIFIED,
    RunResult,
    StatementError,
    build_theory,
    check_theory,
    parse_counterexample,
    parse_sledgehammer,
    prove,
    refute,
    validate_statement,
)


class FakeRunner:
    """Stands in for a real Isabelle installation."""

    def __init__(self, *, is_available=True, ok_proofs=(), sledge_output="",
                 nitpick_output="", quickcheck_output=""):
        self._available = is_available
        self.ok_proofs = list(ok_proofs)
        self.sledge_output = sledge_output
        self.nitpick_output = nitpick_output
        self.quickcheck_output = quickcheck_output

    def available(self):
        return self._available

    def build(self, theory_text, timeout=60):
        if " sledgehammer" in theory_text:
            return RunResult(False, self.sledge_output)
        if " nitpick" in theory_text:
            return RunResult(False, self.nitpick_output)
        if " quickcheck" in theory_text:
            return RunResult(False, self.quickcheck_output)
        for proof in self.ok_proofs:
            if proof in theory_text:
                return RunResult(True, "")
        return RunResult(False, "")


# --------------------------------------------------------------------------- #
# theory generation
# --------------------------------------------------------------------------- #
def test_build_theory_shape():
    thy = build_theory("(a::nat) + b = b + a", ["Main"], "by simp")
    assert "theory Scratch" in thy
    assert "imports Main" in thy
    assert 'lemma "(a::nat) + b = b + a"' in thy
    assert "by simp" in thy
    assert thy.strip().endswith("end")


# --------------------------------------------------------------------------- #
# statement validation / escaping
# --------------------------------------------------------------------------- #
def test_validate_strips_outer_quotes():
    assert validate_statement('"(a::nat) + b = b + a"') == "(a::nat) + b = b + a"


def test_validate_keeps_unicode():
    assert validate_statement("∀x. x = x") == "∀x. x = x"


def test_validate_rejects_inner_quote():
    with pytest.raises(StatementError):
        validate_statement('foo = ''"''s bar')   # contains a stray double quote


def test_prove_invalid_statement_is_unknown_not_crash():
    r = prove('a = "x"', runner=FakeRunner(ok_proofs=["by simp"]))
    assert r.status == UNKNOWN
    assert "invalid statement" in r.reason


# --------------------------------------------------------------------------- #
# output parsing (pure)
# --------------------------------------------------------------------------- #
def test_parse_sledgehammer_extracts_proof():
    out = '\nSledgehammering...\n"z3": Try this: by (metis add.commute) (0.2 s)\n'
    assert parse_sledgehammer(out) == "by (metis add.commute)"


def test_parse_sledgehammer_none_when_no_proof():
    assert parse_sledgehammer("Sledgehammer: no proof found") is None


def test_parse_counterexample_detected():
    out = "Nitpick found a counterexample:\n  Free variables:\n    a = 0\n    b = 1\n"
    ce = parse_counterexample(out)
    assert ce and "counterexample" in ce and "a = 0" in ce


def test_parse_counterexample_absent():
    assert parse_counterexample("Nitpick found no counterexample.") is None


# --------------------------------------------------------------------------- #
# prove / refute / check_theory with the FakeRunner
# --------------------------------------------------------------------------- #
def test_prove_by_cheap_tactic():
    r = prove("(a::nat) + b = b + a", runner=FakeRunner(ok_proofs=["by auto"]))
    assert r.status == VERIFIED
    assert r.detail["method"] == "by auto"


def test_prove_via_sledgehammer():
    runner = FakeRunner(
        ok_proofs=["by (metis add.commute)"],
        sledge_output='"z3": Try this: by (metis add.commute) (0.2 s)',
    )
    r = prove("(a::int) + b = b + a", runner=runner)
    assert r.status == VERIFIED
    assert r.detail["source"] == "sledgehammer"


def test_prove_refuted_by_counterexample():
    runner = FakeRunner(nitpick_output="Nitpick found a counterexample:\n    n = 0")
    r = prove("(n::nat) > 0", runner=runner)
    assert r.status == REFUTED
    assert "n = 0" in r.detail["counterexample"]


def test_prove_unknown_when_nothing_works():
    r = prove("hard_conjecture x", runner=FakeRunner())
    assert r.status == UNKNOWN


def test_prove_unknown_without_isabelle():
    r = prove("True", runner=FakeRunner(is_available=False))
    assert r.status == UNKNOWN
    assert "Isabelle is not available" in r.reason


def test_refute_finds_counterexample():
    runner = FakeRunner(nitpick_output="Nitpick found a counterexample:\n    x = 1")
    assert refute("x = (0::nat)", runner=runner).status == REFUTED


def test_refute_unknown_is_not_a_proof():
    # no counterexample found must NOT be reported as VERIFIED
    assert refute("(a::nat) + b = b + a", runner=FakeRunner()).status == UNKNOWN


def test_check_theory_ok_and_fail():
    thy = build_theory("True", ["Main"], "by simp")
    assert check_theory(thy, runner=FakeRunner(ok_proofs=["by simp"])).status == VERIFIED
    # a build failure is UNKNOWN, never REFUTED
    assert check_theory(thy, runner=FakeRunner()).status == UNKNOWN

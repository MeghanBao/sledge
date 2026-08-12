"""Integration tests against a *real* Isabelle installation.

These are skipped automatically unless the `isabelle` tool is available (on PATH
or via ISABELLE_BINARY). Run them once you have Isabelle installed to validate —
and, if needed, tune — the runner and the output parsers on your version.

    ISABELLE_BINARY=/path/to/isabelle pytest tests/test_integration.py -v
"""

import pytest

from sledge import REFUTED, VERIFIED, IsabelleRunner, prove, refute

pytestmark = pytest.mark.skipif(
    not IsabelleRunner().available(),
    reason="Isabelle not installed (set ISABELLE_BINARY or add `isabelle` to PATH)",
)

# Real Isabelle builds are slow; give each step room.
TIMEOUT = 300


def test_trivial_truth_verified():
    assert prove("True", timeout=TIMEOUT).status == VERIFIED


def test_arithmetic_commutativity_verified():
    r = prove("(a::nat) + b = b + a", timeout=TIMEOUT)
    assert r.status == VERIFIED
    assert "method" in r.detail


def test_needs_sledgehammer_verified():
    # Not closed by a single cheap tactic on all setups → exercises Sledgehammer.
    r = prove("(a::int) * (b + c) = a * b + a * c", timeout=TIMEOUT)
    assert r.status == VERIFIED


def test_false_statement_refuted():
    r = prove("(n::nat) > 0", timeout=TIMEOUT)
    assert r.status == REFUTED
    assert r.detail.get("counterexample")


def test_refute_finds_counterexample():
    assert refute("(x::nat) = 1", timeout=TIMEOUT).status == REFUTED

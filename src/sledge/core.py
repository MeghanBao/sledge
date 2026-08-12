"""The proving front-end.

Public entry points:

- :func:`prove` — try to prove an Isabelle/HOL proposition. First a battery of
  cheap automatic tactics, then **Sledgehammer** (Isabelle's killer feature: it
  hands the goal to external ATPs and reports back a one-line proof). Returns
  VERIFIED with the proof that actually machine-checked.
- :func:`refute` — look for a counterexample with Nitpick/Quickcheck; REFUTED if
  one is found.
- :func:`check_theory` — build a full user-supplied theory as-is.

The heavy lifting is delegated to :class:`~sledge.runner.IsabelleRunner`; the
theory-building and output-parsing are pure functions so they can be tested
without an Isabelle installation.
"""

from __future__ import annotations

import re
from typing import List, Optional, Sequence

from .result import REFUTED, UNKNOWN, VERIFIED, Result
from .runner import IsabelleRunner

# Cheap tactics tried before reaching for the hammer, in rough order of speed.
DEFAULT_METHODS: List[str] = [
    "simp", "auto", "blast", "fastforce", "force",
    "arith", "linarith", "presburger", "metis", "meson",
]

_NO_ISABELLE = (
    "Isabelle is not available. Install it and put `isabelle` on PATH "
    "(or set ISABELLE_BINARY) — until then this check is UNKNOWN."
)


# --------------------------------------------------------------------------- #
# pure: theory generation
# --------------------------------------------------------------------------- #
def build_theory(statement: str, imports: Sequence[str], proof: str,
                 name: str = "Scratch") -> str:
    """Wrap a proposition and a proof/command into a self-contained theory."""
    imports_str = " ".join(imports) if imports else "Main"
    return (
        f"theory {name}\n"
        f"imports {imports_str}\n"
        "begin\n\n"
        f'lemma "{statement}"\n'
        f"  {proof}\n\n"
        "end\n"
    )


# --------------------------------------------------------------------------- #
# pure: output parsing
# --------------------------------------------------------------------------- #
_TRY_THIS = re.compile(r"Try this:\s*(.+)")
_TIMING = re.compile(r"\s*\(\s*[<>]?\s*[\d.]+\s*m?s\s*\)\s*$")


def parse_sledgehammer(output: str) -> Optional[str]:
    """Extract the first proof Sledgehammer suggests, e.g. ``by (metis foo)``.

    Returns None when Sledgehammer reported no proof.
    """
    for line in output.splitlines():
        m = _TRY_THIS.search(line)
        if not m:
            continue
        proof = _TIMING.sub("", m.group(1).strip())
        # keep only proper proof scripts
        if proof.startswith(("by", "apply", "using", "unfolding", "proof")):
            return proof.strip()
    return None


_COUNTEREX = re.compile(r"(Nitpick|Quickcheck) found a counterexample", re.I)


def parse_counterexample(output: str) -> Optional[str]:
    """Return the counterexample block if Nitpick/Quickcheck found one."""
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if _COUNTEREX.search(line):
            block = [line.strip()]
            for extra in lines[i + 1:]:
                if extra.strip() and (extra.startswith((" ", "\t")) or "=" in extra):
                    block.append(extra.strip())
                else:
                    break
            return "\n".join(block)
    return None


# --------------------------------------------------------------------------- #
# proving
# --------------------------------------------------------------------------- #
def prove(
    statement: str,
    *,
    imports: Sequence[str] = ("Main",),
    methods: Sequence[str] = DEFAULT_METHODS,
    sledgehammer: bool = True,
    timeout: int = 60,
    runner: Optional[IsabelleRunner] = None,
) -> Result:
    """Attempt to prove ``statement``; return VERIFIED / REFUTED / UNKNOWN."""
    runner = runner or IsabelleRunner()
    if not runner.available():
        return Result.unknown(_NO_ISABELLE, statement=statement)

    tried: List[str] = []

    # 1) cheap automatic tactics
    for method in methods:
        proof = f"by {method}"
        res = runner.build(build_theory(statement, imports, proof), timeout=timeout)
        tried.append(method)
        if res.ok:
            return Result.verified(
                f"proved by {method}", statement=statement, method=proof)

    # 2) Sledgehammer: find a proof, then machine-check the suggestion
    if sledgehammer:
        out = runner.build(build_theory(statement, imports, "sledgehammer"),
                           timeout=timeout)
        suggestion = parse_sledgehammer(out.output)
        if suggestion:
            res = runner.build(build_theory(statement, imports, suggestion),
                              timeout=timeout)
            if res.ok:
                return Result.verified(
                    "proved via Sledgehammer", statement=statement,
                    method=suggestion, source="sledgehammer")

    # 3) maybe it's actually false
    ce = _find_counterexample(statement, imports, timeout, runner)
    if ce:
        return Result.refuted(
            "counterexample found", statement=statement, counterexample=ce)

    return Result.unknown(
        "no proof found by tactics or Sledgehammer, and no counterexample",
        statement=statement, tried=tried,
        timed_out=out.timed_out if sledgehammer else False)


def refute(
    statement: str,
    *,
    imports: Sequence[str] = ("Main",),
    timeout: int = 60,
    runner: Optional[IsabelleRunner] = None,
) -> Result:
    """Look only for a counterexample; REFUTED if found, else UNKNOWN."""
    runner = runner or IsabelleRunner()
    if not runner.available():
        return Result.unknown(_NO_ISABELLE, statement=statement)
    ce = _find_counterexample(statement, imports, timeout, runner)
    if ce:
        return Result.refuted(
            "counterexample found", statement=statement, counterexample=ce)
    return Result.unknown(
        "no counterexample found (this is not a proof of truth)",
        statement=statement)


def _find_counterexample(statement, imports, timeout, runner) -> Optional[str]:
    for command in ("nitpick", "quickcheck"):
        out = runner.build(build_theory(statement, imports, command), timeout=timeout)
        ce = parse_counterexample(out.output)
        if ce:
            return ce
    return None


def check_theory(
    theory_text: str,
    *,
    timeout: int = 120,
    runner: Optional[IsabelleRunner] = None,
) -> Result:
    """Build a complete, user-supplied theory verbatim."""
    runner = runner or IsabelleRunner()
    if not runner.available():
        return Result.unknown(_NO_ISABELLE)
    res = runner.build(theory_text, timeout=timeout)
    if res.ok:
        return Result.verified("theory builds and all proofs check")
    if res.timed_out:
        return Result.unknown("theory build timed out", timeout=timeout)
    # A build failure (syntax error, unproved goal, missing lemma) is *not* a
    # disproof — it just didn't check. Stay honest: UNKNOWN, not REFUTED.
    return Result.unknown("theory failed to build", output_tail=res.output[-2000:])

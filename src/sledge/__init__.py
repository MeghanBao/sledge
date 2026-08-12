"""sledge — hand an AI agent Isabelle's Sledgehammer.

An agent proposes an Isabelle/HOL statement; sledge tries to *prove* it (cheap
tactics, then Sledgehammer's external ATPs) and returns one honest state:
VERIFIED (machine-checked), REFUTED (counterexample found), or UNKNOWN. Failing
to find a proof is never mistaken for a disproof.
"""

from .core import (
    DEFAULT_METHODS,
    StatementError,
    build_theory,
    check_theory,
    parse_counterexample,
    parse_sledgehammer,
    prove,
    refute,
    validate_statement,
)
from .result import REFUTED, UNKNOWN, VERIFIED, Result
from .runner import IsabelleRunner, RunResult

__all__ = [
    "prove",
    "refute",
    "check_theory",
    "build_theory",
    "parse_sledgehammer",
    "parse_counterexample",
    "validate_statement",
    "StatementError",
    "DEFAULT_METHODS",
    "IsabelleRunner",
    "RunResult",
    "Result",
    "VERIFIED",
    "REFUTED",
    "UNKNOWN",
]

__version__ = "0.1.0"

"""The tri-state result every check returns.

A prover front-end must not bluff. Every answer is exactly one of:

- ``VERIFIED`` — Isabelle machine-checked a proof of the statement.
- ``REFUTED``  — the statement is false (Nitpick/Quickcheck found a
  counterexample, or its negation was proved).
- ``UNKNOWN``  — no proof was found, the search timed out, or Isabelle is not
  available. **Crucially, failing to find a proof is not a disproof** — an
  unproved statement stays UNKNOWN, never REFUTED.

The agent proposes a statement; sledge only *checks* it. Only Isabelle can emit
``VERIFIED``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

VERIFIED = "VERIFIED"
REFUTED = "REFUTED"
UNKNOWN = "UNKNOWN"


@dataclass
class Result:
    status: str
    reason: str
    detail: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def verified(cls, reason: str, **detail: Any) -> "Result":
        return cls(VERIFIED, reason, dict(detail))

    @classmethod
    def refuted(cls, reason: str, **detail: Any) -> "Result":
        return cls(REFUTED, reason, dict(detail))

    @classmethod
    def unknown(cls, reason: str, **detail: Any) -> "Result":
        return cls(UNKNOWN, reason, dict(detail))

    @property
    def ok(self) -> bool:
        return self.status == VERIFIED

    def __bool__(self) -> bool:
        return self.ok

    def __str__(self) -> str:
        return f"{self.status}: {self.reason}"

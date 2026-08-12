"""Talking to a real Isabelle installation (or honestly reporting its absence).

``IsabelleRunner`` shells out to the ``isabelle`` tool to *build* a throwaway
session containing one theory, and reports whether it checked, plus the captured
output (which is where Sledgehammer / Nitpick print their findings).

If Isabelle is not installed, :meth:`available` is False and callers degrade to
UNKNOWN — nothing is faked.

Set ``ISABELLE_BINARY`` to point at the ``isabelle`` executable if it is not on
``PATH``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_THEORY_NAME_FALLBACK = "Scratch"


@dataclass
class RunResult:
    ok: bool           # did the session build (all proofs checked)?
    output: str        # combined stdout + stderr (Sledgehammer/Nitpick live here)
    timed_out: bool = False
    error: str = ""    # runner-level error (e.g. Isabelle missing)


def _theory_name(theory_text: str) -> str:
    import re

    m = re.search(r"\btheory\s+([A-Za-z][\w']*)", theory_text)
    return m.group(1) if m else _THEORY_NAME_FALLBACK


class IsabelleRunner:
    """Runs ``isabelle build`` on a single generated theory."""

    def __init__(self, binary: Optional[str] = None, session_parent: str = "HOL"):
        self.binary = binary or os.environ.get("ISABELLE_BINARY") or shutil.which("isabelle")
        self.session_parent = session_parent

    def available(self) -> bool:
        return bool(self.binary)

    def build(self, theory_text: str, timeout: int = 120) -> RunResult:
        """Write the theory into a temp session and build it."""
        if not self.available():
            return RunResult(False, "", error="isabelle not found")

        name = _theory_name(theory_text)
        with tempfile.TemporaryDirectory(prefix="sledge_") as tmp:
            root = Path(tmp)
            (root / f"{name}.thy").write_text(theory_text, encoding="utf-8")
            (root / "ROOT").write_text(
                f'session "{name}" = "{self.session_parent}" +\n'
                f"  theories\n    {name}\n",
                encoding="utf-8",
            )
            try:
                proc = subprocess.run(
                    [self.binary, "build", "-D", str(root)],
                    capture_output=True, text=True, timeout=timeout,
                )
            except subprocess.TimeoutExpired as exc:
                out = (exc.stdout or "") + (exc.stderr or "")
                return RunResult(False, out if isinstance(out, str) else out.decode("utf-8", "ignore"),
                                 timed_out=True)
            except OSError as exc:  # pragma: no cover - defensive
                return RunResult(False, "", error=str(exc))

            output = (proc.stdout or "") + (proc.stderr or "")
            return RunResult(proc.returncode == 0, output)

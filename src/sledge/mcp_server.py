"""MCP server — hand an AI agent Isabelle's Sledgehammer.

Run it as ``sledge-mcp`` (stdio). An agent can propose a formal statement and
get an *independent* verdict — VERIFIED only if Isabelle machine-checked a
proof, UNKNOWN if it couldn't (never a bluff).

Install the extra: ``pip install "sledge[mcp]"``.

Client config (Claude Desktop / Claude Code):

    {
      "mcpServers": {
        "sledge": { "command": "sledge-mcp" }
      }
    }
"""

from __future__ import annotations

from typing import Any, Dict, List

from .core import prove, refute

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover
    raise SystemExit("The MCP extra is not installed. Run:  pip install 'sledge[mcp]'") from exc

mcp = FastMCP("sledge")


@mcp.tool()
def prove_statement(statement: str, imports: List[str] = ["Main"],
                    sledgehammer: bool = True, timeout: int = 60) -> Dict[str, Any]:
    """Try to prove an Isabelle/HOL proposition.

    Args:
        statement: the proposition, e.g. "(a::nat) + b = b + a".
        imports: theories to import (default ["Main"]).
        sledgehammer: also try Sledgehammer's external ATPs (default True).
        timeout: per-step timeout in seconds.

    Returns {status: VERIFIED|REFUTED|UNKNOWN, reason, detail}. VERIFIED means
    Isabelle machine-checked a proof; UNKNOWN means none was found (NOT that the
    statement is false).
    """
    r = prove(statement, imports=tuple(imports), sledgehammer=sledgehammer, timeout=timeout)
    return {"status": r.status, "reason": r.reason, "detail": r.detail}


@mcp.tool()
def find_counterexample(statement: str, imports: List[str] = ["Main"],
                        timeout: int = 60) -> Dict[str, Any]:
    """Look for a counterexample to a statement with Nitpick/Quickcheck.

    Returns {status, reason, detail}. REFUTED with a concrete counterexample if
    found; UNKNOWN otherwise (absence of a counterexample is not a proof).
    """
    r = refute(statement, imports=tuple(imports), timeout=timeout)
    return {"status": r.status, "reason": r.reason, "detail": r.detail}


def main() -> None:
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()

"""Command-line interface: ``sledge prove`` / ``sledge refute`` / ``sledge check``.

Exit codes mirror the tri-state: 0 = VERIFIED, 1 = REFUTED, 2 = UNKNOWN.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from . import __version__
from .core import check_theory, prove, refute
from .result import REFUTED, UNKNOWN, VERIFIED, Result

_EXIT = {VERIFIED: 0, REFUTED: 1, UNKNOWN: 2}
_MARK = {VERIFIED: "✓", REFUTED: "✗", UNKNOWN: "?"}


def _emit(result: Result, as_json: bool) -> int:
    if as_json:
        print(json.dumps({"status": result.status, "reason": result.reason,
                          "detail": result.detail}, ensure_ascii=False, indent=2))
    else:
        print(f"{_MARK.get(result.status, '?')} {result.status}: {result.reason}")
        for key, val in result.detail.items():
            print(f"    {key}: {val}")
    return _EXIT.get(result.status, 2)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sledge",
        description="Prove Isabelle/HOL statements: VERIFIED / REFUTED / UNKNOWN.",
    )
    parser.add_argument("--version", action="version", version=f"sledge {__version__}")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prove", help="try to prove a proposition")
    p.add_argument("statement", help='e.g. "(a::nat) + b = b + a"')
    p.add_argument("-i", "--import", dest="imports", action="append", default=["Main"],
                   metavar="THEORY", help="an imported theory (repeatable; default Main)")
    p.add_argument("--no-sledgehammer", action="store_true",
                   help="use only the cheap automatic tactics")
    p.add_argument("-t", "--timeout", type=int, default=60, help="per-step timeout (s)")

    r = sub.add_parser("refute", help="look for a counterexample only")
    r.add_argument("statement")
    r.add_argument("-i", "--import", dest="imports", action="append", default=["Main"],
                   metavar="THEORY")
    r.add_argument("-t", "--timeout", type=int, default=60)

    c = sub.add_parser("check", help="build a complete .thy theory file")
    c.add_argument("file", help="path to a .thy file")
    c.add_argument("-t", "--timeout", type=int, default=120)

    args = parser.parse_args(argv)

    if args.cmd == "prove":
        result = prove(args.statement, imports=args.imports,
                       sledgehammer=not args.no_sledgehammer, timeout=args.timeout)
    elif args.cmd == "refute":
        result = refute(args.statement, imports=args.imports, timeout=args.timeout)
    elif args.cmd == "check":
        result = check_theory(Path(args.file).read_text(encoding="utf-8"),
                              timeout=args.timeout)
    else:  # pragma: no cover
        parser.error("unknown command")

    return _emit(result, args.json)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

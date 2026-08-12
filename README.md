# sledge — hand an agent Isabelle's hammer

**English** · [中文](README.zh.md) · [Deutsch](README.de.md)

`sledge` gives an AI agent (or you) an *independent* way to settle a formal
mathematical statement, using the [Isabelle](https://isabelle.in.tum.de/) proof
assistant and its **Sledgehammer** automation. You hand it a statement; it
answers one of exactly three things:

- ✅ **VERIFIED** — Isabelle machine-checked a proof.
- ✗ **REFUTED** — the statement is false (a counterexample was found).
- ❓ **UNKNOWN** — no proof was found (or Isabelle isn’t installed).

**Failing to find a proof is never mistaken for a disproof.** An unproved
statement stays UNKNOWN — sledge does not bluff.

> Package name on PyPI: `sledge-prover`. Import name and commands: `sledge`.

---

## For non-experts: what is this, really?

A **proof assistant** like Isabelle is a computer program that checks
mathematical proofs with total rigour — it only accepts a statement once every
tiny logical step has been verified. Nothing gets through on vibes.

**Sledgehammer** is Isabelle’s most famous feature: you point it at a goal and it
fires the problem off to a battery of powerful automated provers, then hands back
a proof that Isabelle can check. It’s like a metal detector for proofs.

Why wire this to an AI? Because language models (ChatGPT, Claude, …) are fluent
but **make things up** — they’ll “prove” things that are wrong. So instead of
trusting the model, you let the model *propose* a precise statement and let
**Isabelle be the judge**. If Isabelle checks it, it’s genuinely true. If not,
sledge says **UNKNOWN** — honestly, not pretending.

**One-line picture:**

> The AI proposes a statement. Isabelle’s hammer decides — VERIFIED, REFUTED, or an honest UNKNOWN.

---

## Why it exists

The gap between “sounds right” and “is provably right” is exactly where AI
reasoning breaks. Verifiers close that gap: a model proposes, a *checker* that
cannot lie decides. `sledge` is that checker for **formal** statements — and it
leans on the one thing Isabelle does better than any other prover: Sledgehammer’s
automation, which can close many goals with no human proof at all.

It follows the same principle as its sibling tool
[`wtns`](https://github.com/MeghanBao/wtns) (which checks *answers* with SymPy/Z3):
**a producer must not certify its own output**, and uncertainty is reported as
UNKNOWN, never faked.

---

## Requirements

`sledge` drives a **real Isabelle installation** — it does not ship one.

1. Install Isabelle: <https://isabelle.in.tum.de/> (a multi-GB download).
2. Make sure the `isabelle` tool is on your `PATH`, or set `ISABELLE_BINARY` to
   its full path.

Without Isabelle, every check honestly returns **UNKNOWN** (the library and CLI
still install and run — they just can’t prove anything yet).

## Install

```bash
pip install sledge-prover           # core (pure Python, no deps)
pip install "sledge-prover[mcp]"    # + MCP server for agents
```

For development from a clone: `pip install -e ".[dev]"`. Requires Python ≥ 3.9.

## Quickstart (command line)

```bash
# Try to prove a proposition (Isabelle/HOL syntax):
sledge prove "(a::nat) + b = b + a"
# ✓ VERIFIED: proved by simp        (with Isabelle installed)

# Harder goals fall through to Sledgehammer's external provers automatically.
sledge prove "(a::int) + b = b + a"

# Look for a counterexample instead:
sledge refute "(n::nat) > 0"
# ✗ REFUTED: counterexample found (n = 0)

# Build a complete .thy theory file as-is:
sledge check mytheory.thy
```

Exit codes mirror the verdict: **0 = VERIFIED, 1 = REFUTED, 2 = UNKNOWN**. Add
`--json` for machine-readable output; `--no-sledgehammer` to use only the cheap
tactics; `-i THEORY` to add imports; `-t SECONDS` for the timeout.

## Quickstart (Python)

```python
from sledge import prove, refute

prove("(a::nat) + b = b + a")                 # VERIFIED (proof method in .detail)
prove("distinct [a, b] ⟹ a ≠ b")             # tries tactics, then Sledgehammer
refute("(n::nat) > 0")                         # REFUTED with counterexample
```

Every call returns a `Result` with `.status`, `.reason`, `.detail`, truthy only
when VERIFIED.

## Use it as an MCP server (for agents)

```bash
pip install "sledge-prover[mcp]"
```

```json
{
  "mcpServers": {
    "sledge": { "command": "sledge-mcp" }
  }
}
```

The agent gets two tools: `prove_statement` and `find_counterexample`, each
returning `{status, reason, detail}`. An agent can now check a lemma *before*
claiming it — and gets an honest UNKNOWN when Isabelle can’t settle it.

## How it works

Given a statement, `prove`:

1. tries a battery of cheap Isabelle tactics (`simp`, `auto`, `blast`, `metis`, …);
2. if none work, invokes **Sledgehammer**, parses the proof it suggests
   (`Try this: by (metis …)`) and **re-checks that proof** so VERIFIED always
   means a proof that actually machine-checked;
3. if still open, runs **Nitpick/Quickcheck** to look for a counterexample →
   REFUTED;
4. otherwise → **UNKNOWN**.

## What it deliberately does **not** do

- It does **not autoformalize** natural language. You give it Isabelle/HOL
  syntax; turning English into that is a separate, harder problem.
- It does **not** treat “no proof found” as “false”. That’s the cardinal sin of
  naive provers; here it is always **UNKNOWN**.
- It does **not** ship or manage an Isabelle install.

## Status

The proving/parsing logic is covered by tests using a stand-in for Isabelle
(13 passing, no install needed). The output parsers target Sledgehammer/Nitpick’s
standard formats; when you run it against your Isabelle version, expect to tune
`parse_sledgehammer` / `parse_counterexample` for any local wording differences.

## Where it fits

- **Agents** — an MCP tool that lets an agent verify formal claims before asserting them.
- **RLVR** — a verifiable reward for formal-math generation (proof checks or it doesn’t).
- **Autoformalization pipelines** — the *verification* half: given a candidate
  Isabelle statement, does it actually prove?

## Develop & test

```bash
pip install -e ".[dev]"
pytest -q          # 13 tests, no Isabelle required
```

## License

MIT — see [LICENSE](LICENSE).

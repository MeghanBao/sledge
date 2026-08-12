# sledge — gib einem Agenten Isabelles Hammer

[English](README.md) · [中文](README.zh.md) · **Deutsch**

`sledge` gibt einem KI-Agenten (oder dir) einen *unabhängigen* Weg, eine formale
mathematische Aussage zu entscheiden — mit dem Beweisassistenten
[Isabelle](https://isabelle.in.tum.de/) und seiner **Sledgehammer**-Automatik. Du
gibst ihm eine Aussage; er antwortet mit genau einem von drei Ergebnissen:

- ✅ **VERIFIED** — Isabelle hat einen Beweis maschinell geprüft.
- ✗ **REFUTED** — die Aussage ist falsch (ein Gegenbeispiel wurde gefunden).
- ❓ **UNKNOWN** — kein Beweis gefunden (oder Isabelle ist nicht installiert).

**Keinen Beweis zu finden wird nie als Widerlegung missverstanden.** Eine
unbewiesene Aussage bleibt UNKNOWN — sledge blufft nicht.

> Paketname auf PyPI: `sledge-prover`. Import-Name und Befehle: `sledge`.

---

## Für Nicht-Fachleute: was ist das eigentlich?

Ein **Beweisassistent** wie Isabelle ist ein Programm, das mathematische Beweise
mit völliger Strenge prüft — es akzeptiert eine Aussage erst, wenn jeder winzige
logische Schritt verifiziert ist. Nichts geht „nach Gefühl“ durch.

**Sledgehammer** ist Isabelles berühmteste Funktion: du richtest sie auf ein Ziel,
sie schickt das Problem an eine Riege starker automatischer Beweiser und liefert
einen Beweis zurück, den Isabelle prüfen kann. Wie ein Metalldetektor für Beweise.

Warum an eine KI koppeln? Weil Sprachmodelle (ChatGPT, Claude …) eloquent sind,
aber **Dinge erfinden** — sie „beweisen“ auch Falsches. Statt dem Modell zu
vertrauen, lässt du es eine präzise Aussage *vorschlagen* und **Isabelle
urteilen**. Prüft Isabelle sie, ist sie wirklich wahr; wenn nicht, sagt sledge
ehrlich **UNKNOWN**.

**In einem Satz:**

> Die KI schlägt eine Aussage vor. Isabelles Hammer entscheidet — VERIFIED, REFUTED oder ein ehrliches UNKNOWN.

---

## Warum es das gibt

Die Lücke zwischen „klingt richtig“ und „ist beweisbar richtig“ ist genau die
Stelle, an der KI-Schlussfolgern scheitert. Prüfer schließen sie: ein Modell
schlägt vor, ein *Prüfer*, der nicht lügen kann, entscheidet. `sledge` ist dieser
Prüfer für **formale** Aussagen — und stützt sich auf das, was Isabelle besser
kann als jeder andere Beweiser: Sledgehammers Automatik, die viele Ziele ganz
ohne menschlichen Beweis schließt.

Gleiches Prinzip wie das Schwesterwerkzeug
[`wtns`](https://github.com/MeghanBao/wtns) (prüft *Antworten* mit SymPy/Z3):
**ein Erzeuger darf seine eigene Ausgabe nicht zertifizieren**, und Unsicherheit
wird als UNKNOWN gemeldet, nie vorgetäuscht.

---

## Voraussetzungen

`sledge` steuert eine **echte Isabelle-Installation** — es bringt keine mit.

1. Installiere Isabelle: <https://isabelle.in.tum.de/> (mehrere GB).
2. Sorge dafür, dass das `isabelle`-Werkzeug im `PATH` liegt, oder setze
   `ISABELLE_BINARY` auf seinen vollen Pfad.

Ohne Isabelle liefert jede Prüfung ehrlich **UNKNOWN** (Bibliothek und CLI lassen
sich trotzdem installieren und ausführen — sie können nur noch nichts beweisen).

## Installation

```bash
pip install sledge-prover           # Kern (reines Python, ohne Abhängigkeiten)
pip install "sledge-prover[mcp]"    # + MCP-Server für Agenten
```

Aus einem Klon, für die Entwicklung: `pip install -e ".[dev]"`. Python ≥ 3.9.

## Schnellstart (Kommandozeile)

```bash
# Versuche, eine Aussage zu beweisen (Isabelle/HOL-Syntax):
sledge prove "(a::nat) + b = b + a"
# ✓ VERIFIED: proved by simp        (mit installiertem Isabelle)

# Schwerere Ziele fallen automatisch an Sledgehammers externe Beweiser.
sledge prove "(a::int) + b = b + a"

# Stattdessen ein Gegenbeispiel suchen:
sledge refute "(n::nat) > 0"
# ✗ REFUTED: Gegenbeispiel gefunden (n = 0)

# Eine vollständige .thy-Theorie unverändert bauen:
sledge check mytheory.thy
```

Die Exit-Codes spiegeln das Urteil: **0 = VERIFIED, 1 = REFUTED, 2 = UNKNOWN**.
`--json` für maschinenlesbare Ausgabe; `--no-sledgehammer` für nur die billigen
Taktiken; `-i THEORY` für Importe; `-t SEKUNDEN` für das Timeout.

## Schnellstart (Python)

```python
from sledge import prove, refute

prove("(a::nat) + b = b + a")                 # VERIFIED (Beweismethode in .detail)
prove("distinct [a, b] ⟹ a ≠ b")             # erst Taktiken, dann Sledgehammer
refute("(n::nat) > 0")                         # REFUTED mit Gegenbeispiel
```

Jeder Aufruf liefert ein `Result` mit `.status`, `.reason`, `.detail`, nur bei
VERIFIED „wahr“.

## Als MCP-Server nutzen (für Agenten)

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

Der Agent erhält zwei Werkzeuge: `prove_statement` und `find_counterexample`, je
mit `{status, reason, detail}`. Ein Agent kann ein Lemma nun prüfen, *bevor* er es
behauptet — und bekommt ein ehrliches UNKNOWN, wenn Isabelle es nicht klären kann.

## Wie es funktioniert

Für eine Aussage tut `prove`:

1. probiert eine Reihe billiger Isabelle-Taktiken (`simp`, `auto`, `blast`,
   `metis`, …);
2. wenn keine greift, ruft es **Sledgehammer** auf, liest den vorgeschlagenen
   Beweis (`Try this: by (metis …)`) und **prüft diesen Beweis erneut** — VERIFIED
   heißt also stets ein tatsächlich maschinell geprüfter Beweis;
3. wenn immer noch offen, sucht **Nitpick/Quickcheck** ein Gegenbeispiel → REFUTED;
4. sonst → **UNKNOWN**.

## Was es **bewusst nicht** tut

- Es **formalisiert keine** natürliche Sprache. Du gibst Isabelle/HOL-Syntax;
  Englisch/Deutsch in diese zu übersetzen ist ein anderes, schwereres Problem.
- Es hält „kein Beweis gefunden“ **nicht** für „falsch“. Das ist die Todsünde
  naiver Beweiser; hier ist es stets **UNKNOWN**.
- Es liefert oder verwaltet **keine** Isabelle-Installation.

## Status

Die Beweis-/Parsing-Logik ist mit einem Isabelle-Platzhalter getestet
(13 bestanden, ohne Installation). Die Parser zielen auf die Standardformate von
Sledgehammer/Nitpick; auf deiner Isabelle-Version musst du evtl.
`parse_sledgehammer` / `parse_counterexample` an lokale Formulierungen anpassen.

## Wo es passt

- **Agenten** — ein MCP-Werkzeug, mit dem ein Agent formale Aussagen vor der
  Behauptung prüft.
- **RLVR** — eine verifizierbare Belohnung für formale Mathematik-Generierung.
- **Autoformalisierungs-Pipelines** — die *Verifikations*-Hälfte: beweist eine
  vorgeschlagene Isabelle-Aussage tatsächlich?

## Entwickeln & Testen

```bash
pip install -e ".[dev]"
pytest -q          # 13 Tests, kein Isabelle nötig
```

## Lizenz

MIT — siehe [LICENSE](LICENSE).

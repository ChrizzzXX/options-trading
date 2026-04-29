---
title: 'csp.daily_brief() + Idea.format_fbg_mail() — Tagesbrief (slice 7)'
type: 'feature'
created: '2026-04-29'
status: 'done'
baseline_commit: '35113f6'
context:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/project-context.md'
  - '_bmad-output/implementation-artifacts/spec-fmp-client.md'
  - '_bmad-output/implementation-artifacts/spec-lifecycle-persistence.md'
---

<frozen-after-approval reason="YOLO batch — Chris waived approval">

## Intent

**Problem:** `csp.scan` + `csp.macro_snapshot` + `csp.list_open_positions` existieren — aber Chris muss sie heute alle einzeln rufen und manuell zusammensetzen. PRD FR3/FR15/FR18 verlangen ein einzelnes `csp.daily_brief()`-Objekt plus die FBG-Mail-Renderung pro `Idea` (FR15) für Order-Vorbereitung.

**Approach:** Neues `Idea.format_fbg_mail(*, contracts, reasoning)` als Methode (D12 schließt). `csp.ui.formatters` als zentrale Quelle für deutsche Locale-Konvertierung (`format_usd`, `format_pct`, `format_date_de`). Neuer `DailyBrief` Pydantic-Modell (frozen) und `csp.daily_brief()` als sync-Komposition über `macro_snapshot` + `scan` + `list_open_positions` plus deutsche Action-Strings (Earnings-Warnung, Sektor-Anteil-Warnung, Override-Trade-Audit-Hinweis). `DailyBrief.to_markdown()` rendert die §7.2-Brief-Skizze als ASCII-Markdown — Claude rendert direkt.

## Boundaries & Constraints

**Always:**
- Public surface: `csp.daily_brief`, `csp.DailyBrief`, `Idea.format_fbg_mail`, `csp.ui.formatters` (`format_usd`, `format_pct`, `format_signed_int`, `format_date_de`, `_group_thousands`).
- `Idea` extended mit zwei neuen Pflichtfeldern: `under_price: float (>0)` und `iv_rank_1y_pct: float (>=0)`. `build_idea` populiert sie aus `core.under_price` und `core.ivr`.
- `format_fbg_mail` rendert Brief §7.1 in deutscher Locale (USD `1.234,56`, Prozente `13,3 %`, Datum `27.04.2026`). Override-Pfad markiert Header mit `(Override aktiv)` + listet `Bypassed (Override):`-Block. Pflichtregel-Fail-Pfad listet `Verstöße:`-Block.
- `DailyBrief` frozen, mit Feldern: `as_of`, `macro`, `open_positions`, `ranked_ideas`, `actions`. Default-empty Listen erlauben "leer-State"-Renderung.
- `daily_brief()` validiert `max_ideas > 0`, ruft `macro_snapshot()`, `scan(max_results=...)`, `list_open_positions()` sequentiell — sequenziell ist OK weil DB-Call lokal ist und macro+scan Vendor-Calls nur 1× macro + N×ORATS.
- Action-Heuristiken (MVP): pro ranked Idea Earnings ≤ 8 Tage WARN; Sektor-Anteil > 50 % WARN; pro offene Override-Position INFO.
- Alle User-Strings deutsch; alle Identifier englisch (project rule).

**Ask First:** N/A.

**Never:**
- Kein `rich`/`textual` — ASCII-Markdown reicht; Claude rendert.
- Keine automatischen TP/SL-Triggers — `actions` sind nur Hinweise, nicht Aufträge.
- Kein Sheets-Push (FR-NFR6 fire-and-forget) — `export_to_sheets` ist deferred (D31).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior |
|---|---|---|
| Empty state | leere DB, 1 passing Idea via Scan | `DailyBrief(open_positions=[], ranked_ideas=[idea1], actions=[])` |
| With open position | 1 offener Trade + 1 Idea via Scan | `DailyBrief.open_positions` length 1 |
| Override-Trade open | offen mit `bypassed_rules` non-empty | `actions` enthält "ℹ … Override-Trade — beim monatlichen Review prüfen." |
| Earnings ≤ 8 ranked | Idea mit `earnings_distance_days=3` | `actions` enthält "⚠ … Earnings in 3 Tagen — keine Position eröffnen." |
| `max_ideas=0` | — | `ValueError` |
| `format_fbg_mail` passing | clean Idea | Header ohne `(Override aktiv)`, `Pflichtregeln: OK` |
| `format_fbg_mail` override | `bypassed_rules` non-empty | Header `(Override aktiv)`, `Pflichtregeln: NICHT BESTANDEN`, `Bypassed (Override):`-Block |
| `format_fbg_mail` fail | `pflichtregeln_passed=False`, reasons | `Verstöße:`-Block, `Pflichtregeln: NICHT BESTANDEN` |
| `to_markdown` empty | leere Listen | `_keine offenen Positionen_`, `_keine Pflichtregeln-bestandenen Kandidaten_` |
| `to_markdown` voll | Trade + Idea + Actions | ASCII-Tabellen für beide Listen + `## Aktionen`-Block |

</frozen-after-approval>

## Tasks & Acceptance

**Done:**
- `Idea` extended (`under_price`, `iv_rank_1y_pct` neu, populiert von `build_idea`); test fixtures aktualisiert.
- `csp.ui.formatters` mit `format_usd`/`format_pct`/`format_signed_int`/`format_date_de`/`_group_thousands` (100 % coverage).
- `Idea.format_fbg_mail(*, contracts=1, reasoning=None) -> str` mit Override- + Fail-Pfaden.
- `DailyBrief` Pydantic-Modell + `to_markdown()`.
- `csp.daily_brief(*, max_ideas=10) -> DailyBrief` Public-Wrapper.
- 40 neue Tests; total 321 passed, 99.25 % coverage; ruff + mypy strict + format clean.
- D12 closed; D38–D40 deferred.

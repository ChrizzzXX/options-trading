# Deferred Work

Findings surfaced during slice review that aren't this story's problem. Each entry names the slice/condition where it lands.

## From `spec-pflichtregeln-gate.md` review (2026-04-29)

- **D1 — NOW-78 fixture is self-fulfilling.** Six of eight `OratsCore` fields and two of five `OratsStrike` fields are tagged `inferred-plausible`. The "regression" test asserts the values picked to pass... pass. Acknowledged in spec Design Notes. **Lands with:** ORATS-client slice — replace fixture with the real `tests/cassettes/orats/cores_NOW.yaml` + `strikes_NOW.yaml` from 2026-04-24, recorded once with `pytest --record-mode=once`. PRD FR29 / NFR18 require this for CI gating.

- **D2 — Per-file 100% coverage gate not enforced in CI.** `pyproject.toml` `addopts` carries the 80% overall floor only (pytest honors a single `--cov-fail-under` value). The 100% `pflichtregeln.py` gate exists today only because someone runs `coverage report --include='src/csp/filters/pflichtregeln.py' --fail-under=100` separately. **Lands with:** CI/CD slice (when GitHub Actions / similar arrives) — add a second `coverage report --include=… --fail-under=100` step. Same applies to the future `lifecycle/state_machine.py` 100% gate.

- **D3 — `override=True` has no DB persistence stub.** Per FR9, override decisions must be logged in DuckDB for monthly review. Currently we emit a `loguru` WARN only. **Lands with:** lifecycle slice (DuckDB schema, `INSERT OR REPLACE` on overrides table). Spec Boundaries §Never explicitly defers this.

- **D4 — `mkt_cap_thousands` uses `float` at 9-figure scale.** Numerically fine at this magnitude (50B threshold has plenty of float headroom), but the field semantics ("thousands of USD" stored as float) invite rounding when ORATS surfaces integer thousands. **Lands with:** ORATS-client slice — type `mkt_cap_thousands: int` (matching the vendor) and consider `Decimal` (or scaled int) for the threshold setting.

- **D5 — Global NaN-input handling policy.** Comparison-based rules silently fail with literal `"nan"` in messages; no `math.isfinite` validators on `OratsCore` / `OratsStrike` / `MacroSnapshot`. **Lands with:** ORATS-client slice — Pydantic validators that scrub NaN/±inf at the vendor boundary, or a `validate_finite` decorator applied to all numeric fields. Cross-cutting; doesn't belong in the gate slice.

---

## How to clear an entry

When a slice closes one of these items: edit this file, move the entry from "active" to a `## Closed` section with a `closed: <date> via <commit-or-spec>` tag, and reference back in that slice's Spec Change Log.

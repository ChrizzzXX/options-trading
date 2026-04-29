# csp — Pflichtregeln-Gate

Slice 1 of the `options-trading` library: bootstrap + the 9-rule deterministic gate
(`csp.passes_csp_filters`). Vendor clients, persistence, daily-brief, and Sheets export
arrive in subsequent slices.

## Install (development)

```bash
uv sync
```

## Public API surface (this slice)

```python
import csp

passed, reasons = csp.passes_csp_filters(core, strike, macro, portfolio, settings)
```

See `_bmad-output/implementation-artifacts/spec-pflichtregeln-gate.md` for scope and constraints.

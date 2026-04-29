# Archive — `docs/archive/`

Documents in this folder were authoritative inputs at one point in time but have been **superseded** by later artifacts. They are kept for historical reference only.

## Files

### `Projekt-Brief-2026-04-27.md`

The original 900-line project specification authored as input to the PRD-creation workflow. **Superseded by:**

- **`_bmad-output/planning-artifacts/prd.md`** — the authoritative spec for MVP scope, FRs, NFRs, and architectural decisions.
- **`_bmad-output/project-context.md`** — the binding implementation rules for AI agents (extracted, distilled, and updated from the brief).

#### What's in the brief that the PRD doesn't have

The brief retains some operational reference value the PRD doesn't duplicate:

- **§3 Verified API endpoints** — ORATS and FMP endpoint inventory with field semantics. Useful when wiring up the clients. (Note: IVolatility was added later — see PRD § Domain-Specific Requirements for that vendor's notes.)
- **§6.1 Pflichtregeln pseudocode** — the `passes_csp_filters` reference implementation.
- **§7.1 CSP-idea format** — the canonical brief §7.1 layout used by `Idea.format_fbg_mail()`.
- **§16 curl examples** — for ad-hoc API verification.
- **§17 state-machine stress-test scenarios** — useful when authoring tests for `lifecycle/state_machine.py`.

#### What's in the brief that is wrong/superseded

- **§1.4** — "CLI-first" language. Pivoted to library-first; Claude Code is the user surface.
- **§4.1** — `csp daily-brief`, `csp scan`, `csp idea`, `csp positions`, `csp roll`, `csp tax-report` shell commands. Replaced by Python library functions (`csp.daily_brief()`, `csp.scan()`, etc.).
- **§5.1 architecture diagram** — includes `src/csp/ui/` (deleted, no UI) and `src/csp/reporting/tax.py` (deleted, tax export removed entirely from project scope). Add `src/csp/clients/ivolatility.py` (added later).
- **§10.1** — `csp tax-report` command. Removed entirely.
- **§10.3** — `.env` template. Missing `IVOLATILITY_API_KEY` and `IVOLATILITY_BASE_URL`.
- **§12** — 6-phase roadmap. Restructured into MVP / Growth / Vision in `prd.md § Product Scope`.
- **§13** — Acceptance criteria framed as CLI-command checks. Reframed as library-function performance targets in `prd.md § Non-Functional Requirements`.
- **§15** — "What Claude Code should ask at start" — questions about `typer` vs `poetry`, sheet ID, etc. Still partially relevant for first-session bootstrap.

#### Rule of thumb

If a section in the brief contradicts the PRD or `project-context.md`, **the PRD wins**. The brief is a snapshot from before architectural pivots; treat it as historical context, not specification.

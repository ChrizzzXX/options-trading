"""`csp.export_to_sheets()` — pusht den DailyBrief in Google Sheets (Slice 10, FR).

Nutzt das `gws sheets`-CLI (bereits OAuth-authentifiziert beim User) per
`subprocess` — bewusst keine neuen Python-Deps (`gspread` etc.). Schickt drei
append-Calls gegen die `Ideas` / `Positions` / `Macro`-Tabs des Spreadsheets;
die Tabs müssen vorab existieren (siehe README für initial-Setup).

Format-Konventionen (project rule "user-facing strings German"):
- Spalten-Header: deutsch (siehe Setup).
- Werte: deutsche Locale via `csp.ui.formatters` — USD `1.234,56 USD`,
  Prozente `13,3 %`, Daten `27.04.2026`.
- Append-Modus: jede `export_to_sheets`-Aufruf hängt eine Run-Zeile pro
  Datensegment ans Tab-Ende. Historie bleibt erhalten.

Slice-10-Scope (bewusst eng): nur das Schreiben. Lesen / Reconciliation gegen
Sheets folgt erst, wenn ein konkreter Bedarf entsteht (deferred D-Eintrag).
"""

from __future__ import annotations

import json
import subprocess
from decimal import Decimal

from loguru import logger

from csp.config import Settings
from csp.exceptions import ConfigError
from csp.models.daily_brief import DailyBrief
from csp.models.idea import Idea
from csp.models.trade import Trade
from csp.ui.formatters import format_date_de, format_pct, format_usd


def export_to_sheets(brief: DailyBrief, *, spreadsheet_id: str | None = None) -> str:
    """Pusht den `DailyBrief` in das Google-Spreadsheet — Append-Modus pro Tab.

    Args:
        brief: vorab via `csp.daily_brief()` erzeugt; KEIN impliziter Aufruf hier
            (klare Trennung der Verantwortung; `daily_brief` bleibt netzwerkleicht).
        spreadsheet_id: optional override; sonst `Settings.google_sheet_id`.

    Returns:
        Spreadsheet-URL als String.

    Raises:
        ConfigError: wenn weder `spreadsheet_id` noch `Settings.google_sheet_id` gesetzt sind.
        RuntimeError: wenn das `gws sheets`-CLI mit non-zero Exit Code zurückkehrt.
    """
    settings = Settings.load()
    sid = (spreadsheet_id or settings.google_sheet_id).strip()
    if not sid:
        raise ConfigError(
            "GOOGLE_SHEET_ID nicht gesetzt — weder als Argument noch in `Settings.google_sheet_id`."
        )

    ideas_rows = [_idea_to_row(brief.as_of, i) for i in brief.ranked_ideas]
    positions_rows = [_trade_to_row(t) for t in brief.open_positions]
    macro_rows = [[format_date_de(brief.as_of), format_pct(brief.macro.vix_close, decimals=2)]]

    if ideas_rows:
        _append(sid, "Ideas", ideas_rows)
    if positions_rows:
        _append(sid, "Positions", positions_rows)
    _append(sid, "Macro", macro_rows)

    url = f"https://docs.google.com/spreadsheets/d/{sid}/edit"
    logger.info(
        "export_to_sheets: pushed {n_ideas} ideas, {n_pos} positions, 1 macro row → {url}",
        n_ideas=len(ideas_rows),
        n_pos=len(positions_rows),
        url=url,
    )
    return url


def _idea_to_row(as_of_date: object, idea: Idea) -> list[str]:
    """German-locale Idea-Zeile für `Ideas`-Tab.

    Spalten: Datum | Ticker | Strike | DTE | Delta | Mid-Prämie | Ann. Rendite |
             IVR | OTM-Abstand | Pflichtregeln | Gründe.
    """
    pflicht = "OK" if idea.pflichtregeln_passed and not idea.bypassed_rules else "NICHT BESTANDEN"
    reasons_or_bypass = idea.reasons + idea.bypassed_rules
    return [
        format_date_de(idea.as_of),
        idea.ticker,
        format_usd(idea.strike),
        str(idea.dte),
        f"{idea.delta:.2f}".replace(".", ","),
        format_usd(idea.mid_premium, decimals=4),
        format_pct(idea.annualized_yield_pct, decimals=1),
        format_pct(idea.iv_rank_1y_pct, decimals=0),
        format_pct(idea.otm_pct, decimals=1),
        pflicht,
        " | ".join(reasons_or_bypass),
    ]


def _trade_to_row(trade: Trade) -> list[str]:
    """German-locale Trade-Zeile für `Positions`-Tab.

    Spalten: Trade-ID | Ticker | Strike | Status | Kontrakte | Öffnung |
             Eröffnungsprämie | Cash-Bedarf | Notizen.
    """
    strike = trade.cash_secured / Decimal(trade.contracts) / Decimal(100)
    return [
        trade.trade_id,
        trade.ticker,
        format_usd(strike),
        trade.status.value,
        str(trade.contracts),
        format_date_de(trade.open_date),
        format_usd(trade.open_premium, decimals=4),
        format_usd(trade.cash_secured, decimals=0),
        trade.notes or "",
    ]


def _append(sid: str, tab: str, rows: list[list[str]]) -> None:
    """Append-Aufruf gegen das `gws sheets`-CLI.

    Nutzt `subprocess.run` direkt — kein neuer Python-Dep. `valueInputOption=
    USER_ENTERED` lässt Sheets formatierte Strings parsen (z. B. Datum
    `27.04.2026` als Datum, nicht als String — falls Sheets-Locale `de_DE` ist).
    Bei non-zero Exit Code wird `RuntimeError` mit gekürztem stderr geworfen.
    """
    params = json.dumps(
        {
            "spreadsheetId": sid,
            "range": f"{tab}!A:Z",
            "valueInputOption": "USER_ENTERED",
            "insertDataOption": "INSERT_ROWS",
        }
    )
    body = json.dumps({"values": rows})
    result = subprocess.run(
        ["gws", "sheets", "spreadsheets", "values", "append", "--params", params, "--json", body],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        # stderr kann Token-Echos enthalten; auf 500 Zeichen kürzen, redaction
        # läuft via loguru-Sink ohnehin auf Schreibseite.
        raise RuntimeError(
            f"gws sheets append (tab={tab}) fehlgeschlagen "
            f"(rc={result.returncode}): {result.stderr[:500]}"
        )

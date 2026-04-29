"""Tests für `csp.export_to_sheets` (Slice 10).

Strategie: `subprocess.run` per `monkeypatch` ersetzen — kein echter `gws`-CLI-
Aufruf, kein Network. Pinne (a) korrekte Aufruf-Argumente (params + JSON-Body),
(b) deutsche Locale-Werte in den Zeilen, (c) Fehler-Pfade (Config + non-zero
return code).
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import SecretStr

import csp
from csp import config as csp_config
from csp.config import Settings
from csp.exceptions import ConfigError
from csp.lifecycle.state_machine import TradeStatus
from csp.models.core import MacroSnapshot
from csp.models.daily_brief import DailyBrief
from csp.models.idea import Idea
from csp.models.trade import Trade

FAKE_SHEET_ID = "FAKE-SPREADSHEET-ID-12345"


@pytest.fixture
def stub_settings(
    monkeypatch: pytest.MonkeyPatch, default_settings: Settings
) -> Iterator[Settings]:
    patched = default_settings.model_copy(
        update={
            "orats_token": SecretStr("orats-fake"),
            "google_sheet_id": FAKE_SHEET_ID,
        }
    )
    monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
    yield patched


def _idea(*, ticker: str = "NOW", as_of: date = date(2026, 4, 29)) -> Idea:
    return Idea(
        ticker=ticker,
        strike=Decimal("88.00"),
        dte=45,
        delta=-0.20,
        put_bid=Decimal("1.50"),
        put_ask=Decimal("1.52"),
        mid_premium=Decimal("1.5100"),
        annualized_yield_pct=13.92,
        otm_pct=12.0,
        earnings_distance_days=30,
        sector="Technology",
        under_price=100.0,
        iv_rank_1y_pct=80.0,
        current_sector_share_pct=0.0,
        pflichtregeln_passed=True,
        reasons=[],
        bypassed_rules=[],
        as_of=as_of,
        data_freshness="live",
        region="US",
    )


def _trade() -> Trade:
    now = datetime.now(UTC)
    return Trade(
        trade_id="t-uuid-1234",
        idea_id="i-uuid-5678",
        ticker="NOW",
        status=TradeStatus.OPEN,
        contracts=2,
        open_date=date(2026, 4, 28),
        open_premium=Decimal("1.5100"),
        cash_secured=Decimal("17600.0000"),
        notes="initial",
        inserted_at=now,
        updated_at=now,
    )


@pytest.fixture
def captured_runs(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    """Sammelt jeden subprocess.run-Aufruf statt ihn zu starten."""
    calls: list[dict[str, object]] = []

    def fake_run(
        args: list[str], *, capture_output: bool, text: bool, check: bool
    ) -> subprocess.CompletedProcess[str]:
        del capture_output, text, check
        # args = [gws, sheets, spreadsheets, values, append, --params, <json>, --json, <json>]
        calls.append(
            {
                "args": args,
                "params": json.loads(args[args.index("--params") + 1]),
                "body": json.loads(args[args.index("--json") + 1]),
            }
        )
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="{}", stderr="")

    monkeypatch.setattr("csp.export.subprocess.run", fake_run)
    return calls


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


class TestPublicExport:
    def test_exports_with_idea_and_trade(
        self, stub_settings: Settings, captured_runs: list[dict[str, object]]
    ) -> None:
        brief = DailyBrief(
            as_of=date(2026, 4, 29),
            macro=MacroSnapshot(vix_close=18.7),
            open_positions=[_trade()],
            ranked_ideas=[_idea()],
        )
        url = csp.export_to_sheets(brief)
        assert url == f"https://docs.google.com/spreadsheets/d/{FAKE_SHEET_ID}/edit"
        # 3 Append-Calls (Ideas + Positions + Macro).
        assert len(captured_runs) == 3
        # Tabs in der Reihenfolge.
        ranges = [c["params"]["range"] for c in captured_runs]
        assert ranges == ["Ideas!A:Z", "Positions!A:Z", "Macro!A:Z"]

    def test_skips_empty_ideas_and_positions(
        self, stub_settings: Settings, captured_runs: list[dict[str, object]]
    ) -> None:
        """Leere Listen → keine Append-Calls für die jeweiligen Tabs;
        Macro wird IMMER geschrieben (das Datum ist allein schon nützlich)."""
        brief = DailyBrief(
            as_of=date(2026, 4, 29),
            macro=MacroSnapshot(vix_close=18.7),
        )
        csp.export_to_sheets(brief)
        ranges = [c["params"]["range"] for c in captured_runs]
        assert ranges == ["Macro!A:Z"]

    def test_explicit_spreadsheet_id_overrides_settings(
        self, stub_settings: Settings, captured_runs: list[dict[str, object]]
    ) -> None:
        brief = DailyBrief(as_of=date(2026, 4, 29), macro=MacroSnapshot(vix_close=18.7))
        custom_sid = "custom-sheet-id"
        url = csp.export_to_sheets(brief, spreadsheet_id=custom_sid)
        assert custom_sid in url
        # Macro-Append muss die override-ID benutzen.
        assert captured_runs[0]["params"]["spreadsheetId"] == custom_sid

    def test_empty_sheet_id_raises_config_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        default_settings: Settings,
    ) -> None:
        patched = default_settings.model_copy(
            update={"orats_token": SecretStr("x"), "google_sheet_id": ""}
        )
        monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
        brief = DailyBrief(as_of=date(2026, 4, 29), macro=MacroSnapshot(vix_close=18.7))
        with pytest.raises(ConfigError, match="GOOGLE_SHEET_ID"):
            csp.export_to_sheets(brief)

    def test_whitespace_sheet_id_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
        default_settings: Settings,
    ) -> None:
        patched = default_settings.model_copy(
            update={"orats_token": SecretStr("x"), "google_sheet_id": "   "}
        )
        monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
        brief = DailyBrief(as_of=date(2026, 4, 29), macro=MacroSnapshot(vix_close=18.7))
        with pytest.raises(ConfigError, match="GOOGLE_SHEET_ID"):
            csp.export_to_sheets(brief)

    def test_subprocess_failure_raises_runtime(
        self, stub_settings: Settings, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_run(
            args: list[str], *, capture_output: bool, text: bool, check: bool
        ) -> subprocess.CompletedProcess[str]:
            del args, capture_output, text, check
            return subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="auth expired"
            )

        monkeypatch.setattr("csp.export.subprocess.run", fake_run)
        brief = DailyBrief(as_of=date(2026, 4, 29), macro=MacroSnapshot(vix_close=18.7))
        with pytest.raises(RuntimeError, match="gws sheets append"):
            csp.export_to_sheets(brief)


# ---------------------------------------------------------------------------
# Row formatting (German locale)
# ---------------------------------------------------------------------------


class TestRowFormatting:
    def test_idea_row_german_locale(
        self, stub_settings: Settings, captured_runs: list[dict[str, object]]
    ) -> None:
        brief = DailyBrief(
            as_of=date(2026, 4, 29),
            macro=MacroSnapshot(vix_close=18.7),
            ranked_ideas=[_idea(as_of=date(2026, 4, 27))],
        )
        csp.export_to_sheets(brief)
        ideas_call = next(c for c in captured_runs if c["params"]["range"] == "Ideas!A:Z")
        row = ideas_call["body"]["values"][0]
        # Cols: Datum, Ticker, Strike, DTE, Delta, Mid-Prämie, Ann.Rendite,
        # IVR, OTM, Pflichtregeln, Gründe.
        assert row[0] == "27.04.2026"
        assert row[1] == "NOW"
        assert row[2] == "88,00 USD"
        assert row[3] == "45"
        assert row[4] == "-0,20"
        assert row[5] == "1,5100 USD"
        assert row[6] == "13,9 %"
        assert row[7] == "80 %"
        assert row[8] == "12,0 %"
        assert row[9] == "OK"
        assert row[10] == ""

    def test_idea_row_override_marks_bypass(
        self, stub_settings: Settings, captured_runs: list[dict[str, object]]
    ) -> None:
        idea = _idea().model_copy(update={"bypassed_rules": ["Pflichtregel 5", "Pflichtregel 6"]})
        brief = DailyBrief(
            as_of=date(2026, 4, 29),
            macro=MacroSnapshot(vix_close=18.7),
            ranked_ideas=[idea],
        )
        csp.export_to_sheets(brief)
        ideas_call = next(c for c in captured_runs if c["params"]["range"] == "Ideas!A:Z")
        row = ideas_call["body"]["values"][0]
        assert row[9] == "NICHT BESTANDEN"
        assert row[10] == "Pflichtregel 5 | Pflichtregel 6"

    def test_trade_row_german_locale(
        self, stub_settings: Settings, captured_runs: list[dict[str, object]]
    ) -> None:
        brief = DailyBrief(
            as_of=date(2026, 4, 29),
            macro=MacroSnapshot(vix_close=18.7),
            open_positions=[_trade()],
        )
        csp.export_to_sheets(brief)
        positions_call = next(c for c in captured_runs if c["params"]["range"] == "Positions!A:Z")
        row = positions_call["body"]["values"][0]
        # Cols: Trade-ID, Ticker, Strike, Status, Kontrakte, Öffnung,
        # Eröffnungsprämie, Cash-Bedarf, Notizen.
        assert row[0] == "t-uuid-1234"
        assert row[1] == "NOW"
        # Strike = cash_secured / contracts / 100 = 17600 / 2 / 100 = 88
        assert row[2] == "88,00 USD"
        assert row[3] == "open"
        assert row[4] == "2"
        assert row[5] == "28.04.2026"
        assert row[6] == "1,5100 USD"
        assert row[7] == "17.600 USD"
        assert row[8] == "initial"

    def test_macro_row(
        self, stub_settings: Settings, captured_runs: list[dict[str, object]]
    ) -> None:
        brief = DailyBrief(
            as_of=date(2026, 4, 29),
            macro=MacroSnapshot(vix_close=18.7),
        )
        csp.export_to_sheets(brief)
        macro_call = next(c for c in captured_runs if c["params"]["range"] == "Macro!A:Z")
        row = macro_call["body"]["values"][0]
        assert row[0] == "29.04.2026"
        assert row[1] == "18,70 %"

    def test_value_input_option_user_entered(
        self, stub_settings: Settings, captured_runs: list[dict[str, object]]
    ) -> None:
        brief = DailyBrief(
            as_of=date(2026, 4, 29),
            macro=MacroSnapshot(vix_close=18.7),
        )
        csp.export_to_sheets(brief)
        # USER_ENTERED damit Sheets unsere German-locale Strings als Datum / Zahlen parst.
        for c in captured_runs:
            assert c["params"]["valueInputOption"] == "USER_ENTERED"
            assert c["params"]["insertDataOption"] == "INSERT_ROWS"


# ---------------------------------------------------------------------------
# Public re-export
# ---------------------------------------------------------------------------


class TestPublicSurface:
    def test_export_to_sheets_in_csp_namespace(self) -> None:
        from csp.export import export_to_sheets as direct

        assert csp.export_to_sheets is direct
        assert "export_to_sheets" in csp.__all__

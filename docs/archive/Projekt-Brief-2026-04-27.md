# Projekt-Brief: Options-Trading-Terminal mit Claude Code

**Projektname (Vorschlag):** `csp-flywheel-terminal` oder `options-cockpit`
**Auftraggeber:** Familie Rehse (Family Office, Hamburg, DE)
**Sprache:** Deutsch (Code-Kommentare und CLI-Output)
**Adressat:** Claude Code (lokale AusfÃ¼hrung, terminal-basiert)
**Stand:** 27. April 2026

---

## 0. Zweck dieses Briefs

Dieses Dokument ist die **vollstÃ¤ndige Spezifikation** fÃ¼r den Aufbau eines lokalen, terminal-basierten Options-Trading-Cockpits mit **Claude Code als Hauptinterface**. Das Tool soll tÃ¤glich genutzt werden, um:

1. **Konkrete CSP-Ideen zu generieren** auf Basis tagesaktueller ORATS-Daten
2. **Bestehendes Portfolio zu berÃ¼cksichtigen** (Sektor-Caps, Konzentrations-Checks)
3. **Makro-Kontext einflieÃŸen zu lassen** (VIX-Regime, Earnings-Kalender, Treasury-Kurve)
4. **Optionsstrategien systematisch zu screenen** (nicht nur CSPs, auch Wheel, Spreads, Strangles)
5. **Trade-Lebenszyklus zu tracken** (Open â†’ 50%-Take â†’ 21-DTE â†’ Assignment â†’ Wheel)
6. **Reporting** in Google Sheets + lokale Logs fÃ¼r Steuer-Doku

Das Tool **automatisiert keine Order-AusfÃ¼hrung**. Es bereitet Trade-Ideen vor; die Order-Eingabe erfolgt **manuell** beim gewÃ¤hlten Broker (broker-agnostisch â€” der konkrete Broker ist fÃ¼r dieses Projekt **irrelevant**).

---

## 1. Kontext: Wer ist der User, was sind die Anforderungen?

### 1.1 Investor-Profil

- **Familie Rehse**, Hamburg
- Liquides Portfolio: ~16 Mio. EUR (operativ verwaltet)
- + 5,2 Mio. EUR Anleihenportfolio extern verwaltet bei FBG (Frankfurter Bankgesellschaft)
- + 3 Mio. EUR Sparkassenbriefe gebunden bis 2034
- **GesamtvermÃ¶gen konsolidiert: ~21,2 Mio. EUR**
- Geplante Trading GmbH (fÃ¼r Â§8b KStG-Optimierung)
- Technisches Profil: Advanced (Python, PowerShell, Linux/WSL2, VPS-Deployment)

### 1.2 Bestehende Optionsstrategie

Cash-Secured Puts (CSPs) als Kerneinkommens-Strategie. VollstÃ¤ndiges Regelwerk in Datei `CSP-Regelwerk-April-2026.md`. Kernregeln:

- **VIX â‰¥ 20 ODER IVR â‰¥ 40%** als Eintrittsfilter
- **Delta -0,18 bis -0,25** (~20-Delta)
- **DTE 30-55 Tage** (bevorzugt 35-45)
- **Strike â‰¥ 8% OTM**
- **Earnings-Abstand â‰¥ 8 Tage**
- Assignment willkommen
- 50%-Profit-Take ODER 21-DTE-Exit
- Stop-Loss bei 200% der ursprÃ¼nglichen PrÃ¤mie
- Sektor-Cap: 55%
- LiquiditÃ¤tspflicht: Optionsvolumen â‰¥ 50.000 Kontrakte/Tag, Bid-Ask-Spread â‰¤ 0,05 USD

### 1.3 Was das Tool **nicht** sein soll

- **Keine** automatische Order-AusfÃ¼hrung
- **Kein** komplexes UI (Web-App, Dashboard mit React/Vue)
- **Keine** Broker-Integration (broker-agnostisch)
- **Kein** Backtest-Framework von Grund auf (wir nutzen ORATS Backtest API spÃ¤ter optional)
- **Keine** Krypto-Options (Portfolio enthÃ¤lt Krypto-ETPs ohne Optionen)

### 1.4 Was das Tool sein soll

- **CLI-first**: Alles Ã¼ber Terminal, Claude Code als Co-Pilot
- **Reproduzierbar**: Jede CSP-Idee als JSON/CSV gespeichert mit Datenquellen-Snapshot
- **Persistent**: SQLite oder Parquet fÃ¼r Trade-History
- **Google Sheets als Read-Only-Dashboard** (Schreib-Zugriff via Connector)
- **Modular**: Jede Strategie ist ein Plugin (csp.py, wheel.py, iron_condor.py)
- **Schnell**: Tagesroutine soll < 10 Minuten dauern

---

## 2. Technologie-Stack (Empfehlung)

### 2.1 Pflicht-Stack

| Komponente | Wahl | BegrÃ¼ndung |
|---|---|---|
| **Sprache** | Python 3.12+ | User ist Python-affin, Ã–kosystem fÃ¼r Finanzdaten erstklassig |
| **Paket-Management** | `uv` (oder `poetry`) | Modern, schnell, lockfile-basiert |
| **CLI-Framework** | `typer` + `rich` | Typed CLI mit schÃ¶ner Tabellen-Ausgabe |
| **HTTP** | `httpx` (async-fÃ¤hig) | Moderner als `requests`, parallele API-Calls |
| **Datenmodellierung** | `pydantic v2` | Validierung + Typen-Sicherheit fÃ¼r API-Responses |
| **Tabellenoperationen** | `polars` (primÃ¤r) + `pandas` (KompatibilitÃ¤t) | Performance + Ã–kosystem |
| **Persistenz** | `duckdb` + Parquet | User kennt das, ideal fÃ¼r Time-Series |
| **Konfiguration** | `pydantic-settings` + `.env` + TOML | User-PrÃ¤ferenz fÃ¼r TOML |
| **Logging** | `loguru` | Strukturiert, einfach |
| **Testing** | `pytest` + `pytest-vcr` (fÃ¼r API-Replay) | Standard |
| **Linting/Formatting** | `ruff` (all-in-one) | Schnellster Stack |
| **Type-Checking** | `mypy` --strict oder `pyright` | Pflicht |
| **Datums-Handling** | `pendulum` oder `whenever` | Bessere TZ-UnterstÃ¼tzung |
| **Plotting (optional)** | `plotly` (HTML-Export) | FÃ¼r Vola-Surface, Skew-Plots |

### 2.2 Google Sheets Integration

| Komponente | Wahl |
|---|---|
| **Library** | `gspread` + `google-auth` |
| **Service Account** | OAuth2 Service Account JSON (lokal) |
| **Schreibrate** | Batch-Updates (1 pro Tag, nicht pro Trade) |

### 2.3 Optional (spÃ¤ter)

- **Telegram-Bot** fÃ¼r Push-Notifications bei Earnings-Warnings (User hat bereits `telegram_bot_api`-Connector)
- **Cron / systemd-Timer** fÃ¼r tÃ¤gliches Pre-Market-Update um 14:30 CEST (Pre-Market US)

---

## 3. Datenquellen â€” Verbindlich

### 3.1 ORATS (Optionsdaten â€” Hauptquelle)

- **API-Token:** `82326868-e296-44a2-bc03-901e110da9ef`
- **Base URL:** `https://api.orats.io/datav2`
- **Docs:** https://docs.orats.io/
- **Plan:** Subscription 99 USD/Monat (15-min delayed Data API)
- **Rate-Limit:** 1.000 Requests/Minute
- **Format:** JSON oder CSV (`?format=csv` oder `.csv`-Suffix)

#### Verifizierte Endpoints (mit User-Token getestet)

| Endpoint | Pfad | Zweck |
|---|---|---|
| Tickers | `/tickers` | Universum aller verfÃ¼gbaren Ticker mit min/max-Datum |
| Cores | `/cores?ticker=NOW` | **Wichtigster Endpoint**: Komplette TagesÃ¼bersicht eines Tickers (IV, IVR, HV, Beta, Earnings, Skew, Greeks-ATM) |
| Summaries | `/summaries?ticker=NOW` | Vola-Surface-Zusammenfassung pro Expiration (Skew, Term-Struktur, Earnings-Effekt, Forward-Vol) |
| IV-Rank (live) | `/ivrank?ticker=NOW` | Aktuelle IV + IVR/IVPct 1m + 1y |
| IV-Rank (hist) | `/hist/ivrank?ticker=NOW` | Historische IV-Reihe (fÃ¼r Backtest und Validierung) |
| Strikes (live) | `/strikes?ticker=NOW` | Komplette Optionskette (alle Strikes Ã— Expirations) â€” mit Greeks, Bid/Ask, IV |
| Strikes by Expiry | `/strikes/monthly?ticker=NOW&expiry=2026-06-19` | Eingegrenzt auf Expiration |
| Strikes by Options | `/strikes/options?ticker=NOW260619P00078000` | Einzelne Option per OCC-Symbol |
| Hist Strikes | `/hist/strikes?ticker=NOW&tradeDate=2026-04-24` | EOD-Snapshot fÃ¼r historisches Datum |
| Monies (Implied) | `/monies/implied?ticker=NOW` | Vola-Surface implied (vol100â€¦vol0 Skew-Curve pro Expiry) |
| Monies (Forecast) | `/monies/forecast?ticker=NOW` | ORATS-proprietÃ¤re Vol-Prognose pro Expiry |

#### Wichtige Datenfelder fÃ¼r CSP-Logik

Aus `/cores`-Response (Beispiel NOW, 27.04.2026):
- `ivPctile1y`: 96 â€” **IV-Perzentil 1-Jahr (= IVR)** â€” primÃ¤rer Filter
- `ivPctile1m`: 59 â€” kurzfristiges IV-Perzentil
- `atmIvM2`: 55.7 â€” ATM IV des 2. Verfallsmonats (~55-DTE)
- `daysToNextErn`: 0/89 â€” Tage bis nÃ¤chstem Earnings â†’ Pflicht-Check
- `lastErn`: 2026-04-22 â€” letztes Earnings-Datum (fÃ¼r Post-Earnings-IV-Crush-Plays)
- `nextErn`: 2026-07-22 â€” nÃ¤chstes Earnings (PflichtprÃ¼fung)
- `absAvgErnMv`: 7.62% â€” historisch durchschnittliche Earnings-Bewegung
- `impliedIee`: 3.76% â€” implizierte Earnings-Bewegung (Markt-Erwartung)
- `sector`: "Application Software"
- `sectorName`: "Technology"
- `bestEtf`: "XLK" â€” passendes Sektor-ETF
- `mktCap`: 96.524 Mio. USD (Mindestanforderung 50 Mrd.)
- `avgOptVolu20d`: 116.894 (Mindestanforderung 50.000)
- `correlSpy1y`: 0.49 â€” Diversifikations-Indikator
- `beta1y`: 0.85
- `straPxM2`: 8.90 â€” ATM-Straddle-Preis 2. Monat (Pricing-Sanity-Check)

Aus `/strikes`-Response (pro Strike):
- `delta` â€” Pflicht-Filter (-0.18 bis -0.25 fÃ¼r Puts)
- `theta`, `vega`, `gamma` â€” Risk-Management
- `putBidPrice`, `putAskPrice`, `putValue` (theoretischer Wert)
- `putBidIv`, `putMidIv`, `putAskIv`, `smvVol` (smoothed Vola)
- `dte`, `expirDate`, `strike`
- `putVolume`, `putOpenInterest`, `putBidSize`, `putAskSize`

#### Limitierungen mit aktuellem Plan

Folgende Endpoints liefern "User is not authorized to access" â€” nicht im Plan enthalten:
- `/datav2/hist/hv` (historische HV-Reihe)
- `/datav2/history/dailyPrice`
- `/datav2/volatility` (Vola-Surface raw)

â†’ **Workaround**: HV via FMP-Historie selbst berechnen, falls nÃ¶tig. FÃ¼r Tages-Workflow nicht kritisch.

### 3.2 Financial Modeling Prep (FMP â€” Kontext, Macro, Earnings, Fundamentals)

- **API-Key:** `A4I6B9uEEEk8ZHWydjYEmeRPX3TlWu8v`
- **Plan:** Ultimate Annual
- **Base URLs:**
  - Stable namespace (neu): `https://financialmodelingprep.com/stable/`
  - Legacy v3/v4 (teils deprecated seit 31.08.2025): `https://financialmodelingprep.com/api/v3/`
- **Docs:** https://site.financialmodelingprep.com/developer/docs

#### Verifizierte Endpoints

| Endpoint | Pfad | Zweck |
|---|---|---|
| Quote | `/stable/quote?symbol=NOW` | Kurs, Tagesperformance, 50d/200d-Avg, Marktkapitalisierung |
| Profile | `/stable/profile?symbol=NOW` | ISIN, Industry, Description, Sektor, Beta, Range |
| Historical Price | `/stable/historical-price-eod/full?symbol=NOW&from=...&to=...` | Tageskerzen mit OHLCV + VWAP |
| **VIX-Historie** | `/stable/historical-price-eod/full?symbol=^VIX` | VIX-Spot, EOD-Reihe |
| **Earnings (per Symbol)** | `/stable/earnings?symbol=NOW` | Vergangene + zukÃ¼nftige Earnings-Termine mit EPS-Estimates |
| Earnings-Calendar | `/stable/earnings-calendar?from=...&to=...` | Globaler Earnings-Kalender (Filter: US-Symbole) |
| **Treasury Rates** | `/stable/treasury-rates` | Komplette Zinskurve (1M-30Y) |
| Sector Performance | `/stable/sector-performance-snapshot?date=2026-04-24` | Tages-Performance pro Sektor pro Exchange |
| Industry Performance | `/stable/industry-performance-snapshot?date=...` | Industrie-Performance |
| Sector P/E | `/stable/sector-pe-snapshot?date=...` | Sektor-Bewertungsmultiplikatoren |
| Economic Calendar | `/stable/economic-calendar?from=...&to=...` | Macro-Events (CPI, Fed, NFP, etc.) |
| Economic Indicators | `/stable/economic-indicators?name=GDP` | Spezifische Makro-Reihen |
| Insider Trading | `/stable/insider-trading/search?symbol=NOW` | Insider-KÃ¤ufe/VerkÃ¤ufe (Conviction-Signal) |
| Income Statement | `/stable/income-statement?symbol=NOW` | Fundamentals (Q + FY) |
| Balance Sheet | `/stable/balance-sheet-statement?symbol=NOW` | Bilanz |
| Ratios TTM | `/stable/ratios-ttm?symbol=NOW` | Aktuelle Kennzahlen |
| Ratings Snapshot | `/stable/ratings-snapshot?symbol=NOW` | Analyst-Ratings |
| Price Target Consensus | `/stable/price-target-consensus?symbol=NOW` | Konsens-Kursziel |
| ETF Holdings | `/stable/etf/holdings?symbol=SPY` | Index-Komposition |

#### Was FMP **nicht** liefert (und ORATS deshalb Pflicht ist)

- **Optionsketten / Strikes / Greeks / IV** â€” die alten v3/v4-Optionschain-Endpoints sind seit 31.08.2025 **deprecated** und liefern "Legacy Endpoint" Errors. FMP ist hier ungeeignet.

### 3.3 Datenquellen-Verteilung in der Architektur

```
                â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                â”‚   ORATS     â”‚  â† Optionen, IV, Greeks, IVR, Earnings-IV
                â”‚  (15min)    â”‚
                â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
                       â–¼
                â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                â”‚  Strategy Engine   â”‚
                â”‚  (CSP, Wheel, ...) â”‚
                â””â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”˜
                  â”‚                 â”‚
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â–¼                                         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   FMP        â”‚  â† VIX, Treasuries,     â”‚  Local      â”‚
â”‚   (Macro)    â”‚     Earnings-Cal,        â”‚  Portfolio  â”‚
â”‚              â”‚     Sector-Perf,         â”‚  (CSV/SQL)  â”‚
â”‚              â”‚     Insider, Funda       â”‚             â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## 4. Funktionale Anforderungen â€” Was das Tool kann

### 4.1 Daily Workflow Commands

```bash
# Morgens (vor US-Markt-ErÃ¶ffnung, 14:30 CEST)
$ csp daily-brief
# â†’ Druckt: VIX-Level, VIX-Future, Top-IVR-Liste, Earnings-Heute, 21-DTE-Liste, 50%-Take-Liste

$ csp scan --strategy=csp --max-results=10
# â†’ Top 10 CSP-Kandidaten gemÃ¤ÃŸ Pflichtregeln, sortiert nach annualisierter Rendite

$ csp idea NOW --dte=45 --target-delta=0.20
# â†’ VollstÃ¤ndige CSP-Idee fÃ¼r NOW im April-Format

$ csp positions
# â†’ Aktuelle offene Positionen mit DTE, P/L, Aktion-Empfehlung

$ csp portfolio --check-sector-caps
# â†’ Sektor-Verteilung im aktiven CSP-Kapital, Warnung wenn >55%
```

### 4.2 Strategie-Befehle

```bash
$ csp wheel-status TICKER     # Phase im Flywheel?
$ csp scan --strategy=strangle --vix-min=22
$ csp scan --strategy=iron-condor --width=10
$ csp earnings-plays --post-earnings --max-days=3
$ csp roll PUT_ID --net-credit-only
```

### 4.3 Datenexport

```bash
$ csp export sheets        # Pushed alles zu Google Sheets
$ csp export csv --period=ytd
$ csp tax-report --period=2026
```

---

## 5. Architektur und Datenmodell

### 5.1 Modul-Struktur

```
csp-flywheel-terminal/
â”œâ”€â”€ pyproject.toml                  # uv-managed
â”œâ”€â”€ README.md
â”œâ”€â”€ .env.example                    # ORATS_TOKEN, FMP_KEY, GOOGLE_SHEET_ID, ...
â”œâ”€â”€ config/
â”‚   â”œâ”€â”€ settings.toml               # Sektor-Caps, DTE-Range, Delta-Range
â”‚   â”œâ”€â”€ universe.csv                # Erlaubte Ticker (Haupt + Erweitert)
â”‚   â””â”€â”€ portfolio.csv               # Aktuelle Holdings (mit ISIN, Wert)
â”œâ”€â”€ src/csp/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ cli.py                      # typer-App-Entrypoint
â”‚   â”œâ”€â”€ config.py                   # pydantic-settings
â”‚   â”œâ”€â”€ clients/
â”‚   â”‚   â”œâ”€â”€ orats.py                # async ORATS-Client mit Pydantic-Models
â”‚   â”‚   â”œâ”€â”€ fmp.py                  # async FMP-Client
â”‚   â”‚   â””â”€â”€ sheets.py               # gspread-Wrapper
â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â”œâ”€â”€ option.py               # OptionStrike, OptionChain
â”‚   â”‚   â”œâ”€â”€ core.py                 # OratsCore (Pydantic-Model des /cores Response)
â”‚   â”‚   â”œâ”€â”€ summary.py              # OratsSummary
â”‚   â”‚   â”œâ”€â”€ trade.py                # CSPTrade, CoveredCall, IronCondor, ...
â”‚   â”‚   â”œâ”€â”€ portfolio.py            # Position, PortfolioSnapshot
â”‚   â”‚   â””â”€â”€ macro.py                # MacroSnapshot (VIX, Treasuries, Sector-Perf)
â”‚   â”œâ”€â”€ strategies/
â”‚   â”‚   â”œâ”€â”€ base.py                 # AbstractStrategy
â”‚   â”‚   â”œâ”€â”€ csp.py                  # CashSecuredPut
â”‚   â”‚   â”œâ”€â”€ covered_call.py
â”‚   â”‚   â”œâ”€â”€ wheel.py                # State-Machine Phasen 1-4
â”‚   â”‚   â”œâ”€â”€ iron_condor.py
â”‚   â”‚   â”œâ”€â”€ strangle.py
â”‚   â”‚   â””â”€â”€ put_credit_spread.py
â”‚   â”œâ”€â”€ filters/
â”‚   â”‚   â”œâ”€â”€ pflichtregeln.py        # VIX/IVR/Delta/DTE/Strike/Earnings
â”‚   â”‚   â”œâ”€â”€ liquidity.py            # Volumen, Spread, OI
â”‚   â”‚   â””â”€â”€ sector_caps.py
â”‚   â”œâ”€â”€ ranking/
â”‚   â”‚   â”œâ”€â”€ annualized_yield.py     # Premium/Strike Ã— 365/DTE
â”‚   â”‚   â”œâ”€â”€ kelly.py                # Kelly-basierte Sizing
â”‚   â”‚   â””â”€â”€ score.py                # Composite-Score
â”‚   â”œâ”€â”€ lifecycle/
â”‚   â”‚   â”œâ”€â”€ state_machine.py        # Open â†’ 50%-Take â†’ 21-DTE â†’ Assignment
â”‚   â”‚   â”œâ”€â”€ alerts.py
â”‚   â”‚   â””â”€â”€ roll_engine.py
â”‚   â”œâ”€â”€ persistence/
â”‚   â”‚   â”œâ”€â”€ db.py                   # DuckDB-Init
â”‚   â”‚   â”œâ”€â”€ snapshots.py            # TÃ¤gliche Snapshots â†’ Parquet
â”‚   â”‚   â””â”€â”€ trades.py               # Trade-Lebenszyklus
â”‚   â”œâ”€â”€ reporting/
â”‚   â”‚   â”œâ”€â”€ sheets.py               # Push zu Google Sheets
â”‚   â”‚   â”œâ”€â”€ md_export.py            # Markdown-Brief
â”‚   â”‚   â””â”€â”€ tax.py                  # Trade-Doku fÃ¼r Anlage KAP / GmbH-Buchhaltung
â”‚   â””â”€â”€ ui/
â”‚       â”œâ”€â”€ tables.py               # rich.Table-Helper
â”‚       â””â”€â”€ formatters.py           # Zahlen, Datum, USD
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ snapshots/                  # Parquet pro Tag
â”‚   â”œâ”€â”€ trades.duckdb
â”‚   â””â”€â”€ tax_log/
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ conftest.py
â”‚   â”œâ”€â”€ cassettes/                  # vcr.py-Recordings (kein Live-API in Tests)
â”‚   â”œâ”€â”€ test_csp_filter.py
â”‚   â”œâ”€â”€ test_orats_client.py
â”‚   â””â”€â”€ test_lifecycle.py
â””â”€â”€ scripts/
    â”œâ”€â”€ daily_cron.sh               # fÃ¼r systemd-Timer
    â””â”€â”€ seed_universe.py
```

### 5.2 Wichtigste Datenmodelle (Pydantic)

```python
# src/csp/models/core.py
from pydantic import BaseModel, Field
from datetime import date

class OratsCore(BaseModel):
    """Mapping des /datav2/cores Response."""
    ticker: str
    trade_date: date = Field(alias="tradeDate")
    px_atm_iv: float = Field(alias="pxAtmIv")
    iv_pctile_1y: float = Field(alias="ivPctile1y")        # IVR
    iv_pctile_1m: float = Field(alias="ivPctile1m")
    atm_iv_m2: float = Field(alias="atmIvM2")
    days_to_next_ern: int = Field(alias="daysToNextErn")
    next_ern: str = Field(alias="nextErn")
    last_ern: str = Field(alias="lastErn")
    abs_avg_ern_mv: float = Field(alias="absAvgErnMv")
    sector: str
    sector_name: str = Field(alias="sectorName")
    best_etf: str = Field(alias="bestEtf")
    mkt_cap: int = Field(alias="mktCap")                   # in Tausend USD
    avg_opt_volu_20d: float = Field(alias="avgOptVolu20d")
    correl_spy_1y: float = Field(alias="correlSpy1y")
    beta_1y: float = Field(alias="beta1y")
    cls_px: float = Field(alias="pxCls")

# src/csp/models/option.py
class OptionStrike(BaseModel):
    ticker: str
    expir_date: date = Field(alias="expirDate")
    dte: int
    strike: float
    delta: float
    theta: float
    vega: float
    put_bid: float = Field(alias="putBidPrice")
    put_ask: float = Field(alias="putAskPrice")
    put_mid_iv: float = Field(alias="putMidIv")
    put_open_interest: int = Field(alias="putOpenInterest")

# src/csp/models/trade.py
from enum import StrEnum

class TradeStatus(StrEnum):
    OPEN = "open"
    PROFIT_TAKE_PENDING = "take_pending"
    DTE_21_PENDING = "dte21_pending"
    CLOSED_PROFIT = "closed_profit"
    CLOSED_LOSS = "closed_loss"
    ASSIGNED = "assigned"
    ROLLED = "rolled"

class CSPTrade(BaseModel):
    trade_id: str
    ticker: str
    strike: float
    dte_at_open: int
    expir_date: date
    delta_at_open: float
    premium_received: float
    cash_secured: float                # = strike Ã— 100
    open_date: date
    annualized_yield: float
    status: TradeStatus
    earnings_check_passed: bool
    sector: str
```

### 5.3 SQLite/DuckDB Schema

```sql
CREATE TABLE trades (
    trade_id TEXT PRIMARY KEY,
    strategy TEXT NOT NULL,            -- 'csp', 'wheel', 'iron_condor', ...
    ticker TEXT NOT NULL,
    sector TEXT,
    open_date DATE NOT NULL,
    close_date DATE,
    expir_date DATE NOT NULL,
    dte_at_open INTEGER,
    strike DOUBLE,
    delta_at_open DOUBLE,
    iv_at_open DOUBLE,
    ivr_at_open DOUBLE,
    premium_received DOUBLE,
    premium_close DOUBLE,
    pnl_realized DOUBLE,
    cash_secured DOUBLE,
    status TEXT,                       -- siehe TradeStatus enum
    earnings_check_passed BOOLEAN,
    rationale TEXT,                    -- "Post-Earnings IV-Crush, IVR 94"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE snapshots (
    ticker TEXT,
    snapshot_date DATE,
    iv_pctile_1y DOUBLE,
    atm_iv_m2 DOUBLE,
    days_to_next_ern INTEGER,
    sector TEXT,
    raw_json TEXT,                     -- ORATS-Response gepickelt
    PRIMARY KEY (ticker, snapshot_date)
);

CREATE TABLE macro_snapshots (
    snapshot_date DATE PRIMARY KEY,
    vix_close DOUBLE,
    vix_future_m1 DOUBLE,
    treasury_10y DOUBLE,
    sp500_close DOUBLE,
    sector_performance JSONB,
    economic_events JSONB
);
```

---

## 6. Pflichtregeln-Engine (Kern-Logik)

### 6.1 CSP-Filter-Pipeline

Pseudocode fÃ¼r `filters/pflichtregeln.py`:

```python
def passes_csp_filters(
    core: OratsCore,
    strike: OptionStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    config: Settings,
) -> tuple[bool, list[str]]:
    """Return (passed, reasons_failed)."""
    reasons = []

    # Regel 1: VIX â‰¥ 20 ODER IVR â‰¥ 40
    if not (macro.vix_close >= 20 or core.iv_pctile_1y >= 40):
        reasons.append(f"VIX {macro.vix_close:.1f} < 20 UND IVR {core.iv_pctile_1y} < 40")

    # Regel 2: Delta -0.18 bis -0.25
    if not (-0.25 <= strike.delta <= -0.18):
        reasons.append(f"Delta {strike.delta} auÃŸerhalb [-0.25, -0.18]")

    # Regel 3: DTE 30-55
    if not (30 <= strike.dte <= 55):
        reasons.append(f"DTE {strike.dte} auÃŸerhalb [30, 55]")

    # Regel 4: Strike â‰¥ 8% OTM
    otm_pct = (core.cls_px - strike.strike) / core.cls_px * 100
    if otm_pct < 8.0:
        reasons.append(f"OTM nur {otm_pct:.1f}% (< 8%)")

    # Regel 5: Earnings â‰¥ 8 Tage
    if 0 <= core.days_to_next_ern < 8:
        reasons.append(f"Earnings in {core.days_to_next_ern} Tagen (< 8)")

    # Regel 6: LiquiditÃ¤t
    if core.avg_opt_volu_20d < 50_000:
        reasons.append(f"Optionsvol. {core.avg_opt_volu_20d:.0f} < 50.000")
    spread = strike.put_ask - strike.put_bid
    if spread > 0.05:
        reasons.append(f"Spread {spread:.2f} > 0.05")

    # Regel 7: Market Cap â‰¥ 50 Mrd. USD
    if core.mkt_cap < 50_000_000:  # in Tsd. USD = 50 Mrd.
        reasons.append(f"MarketCap {core.mkt_cap/1000:.0f} Mrd. < 50 Mrd.")

    # Regel 8: Sektor-Cap (â‰¤ 55% des aktiven CSP-Kapitals)
    sector_exposure = portfolio.sector_csp_exposure(core.sector)
    new_exposure = sector_exposure + strike.cash_required()
    if new_exposure / portfolio.csp_total_capital > 0.55:
        reasons.append(f"Sektor-Cap Ã¼berschritten: {core.sector} wÃ¼rde {new_exposure/portfolio.csp_total_capital*100:.0f}% erreichen")

    # Regel 9: Universum-Check
    if core.ticker not in config.universe.allowed_tickers:
        reasons.append(f"Ticker nicht im Universum")

    return (len(reasons) == 0, reasons)
```

### 6.2 Annualisierte Rendite

```python
def annualized_yield(premium: float, strike: float, dte: int) -> float:
    """Premium / Strike Ã— 365/DTE Ã— 100"""
    return premium / strike * 365 / dte * 100
```

### 6.3 Lifecycle State-Machine (lifecycle/state_machine.py)

```
[open] â”€â”€50%-Take?â”€â”€â–¶ [closed_profit]
   â”‚
   â”œâ”€â”€21-DTE & Premium > 50%?â”€â”€â–¶ [closed_neutral]
   â”‚
   â”œâ”€â”€Stop-Loss (200%)?â”€â”€â–¶ [closed_loss]
   â”‚
   â”œâ”€â”€Earnings < 8d & DTE â‰¥ 8?â”€â”€â–¶ [emergency_close]
   â”‚
   â””â”€â”€Verfallâ”€â”€â–¶ Strike > Spot? â”€â”€Jaâ”€â”€â–¶ [assigned] â”€â”€â–¶ [wheel.cc_open]
                                  â””â”€Neinâ”€â–¶ [expired_otm]
```

---

## 7. Output-Formate

### 7.1 CSP-Idee (Standardformat)

Identisch zum bestehenden Format aus `CSP-Space-Prompt.md`:

```
---
CSP-IDEE | NOW | 27.04.2026
---
Kurs:              91,84 USD (Quelle: ORATS /summaries, 27.04.2026 15:54 ET)
Strike:            78,00 USD
Abstand OTM:       15,1 %
Delta:             -0,21
Verfall:           18. Juni 2026 (52 DTE)
IV aktuell:        56,1 % | IV-Rang 1y: 96 % (Quelle: ORATS /ivrank)
PrÃ¤mie Bid/Ask:    1,42 / 1,52 USD
Empf. Limit:       1,47 USD (Mid-Point)
Cash-Bedarf:       7.800 USD (1 Kontrakt)
Ann. Rendite:      13,3 % p.a.
NÃ¤chste Earnings:  22. Juli 2026 (86 Tage Abstand) âœ…
Assignment-Check:  Ja â€” NOW ist Kerntitel, langfristige Halte-Bereitschaft bei 78 USD
BegrÃ¼ndung:        IVR 96% nach Post-Earnings-Crash 24.04. attraktiv;
                   Strike 15% OTM bietet groÃŸen Sicherheitspuffer;
                   52 DTE optimal fÃ¼r Theta-Beschleunigung im 21-DTE-Fenster.
---
```

### 7.2 Daily Brief (CLI-Ausgabe via `rich`)

Beispiel:

```
â•­â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•®
â”‚  CSP DAILY BRIEF â€” 2026-04-27 (Mo)                   â”‚
â•°â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•¯

MAKRO
  VIX:           18,71 (-0,18)         Regime: Normal selektiv
  VIX Mai-Fut.:  20,50                 Markt erwartet Vola-Persistenz
  10Y Treasury:  4,31%                 Stabil
  S&P 500:       -0,2%                 Range-bound

OFFENE POSITIONEN (3)
  â”Œâ”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚ Tickerâ”‚Strikeâ”‚ DTE â”‚Delta â”‚P/L (Premie)â”‚ Aktion     â”‚
  â”œâ”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
  â”‚ MSFT â”‚ 380  â”‚ 18  â”‚-0,12 â”‚  +52%      â”‚ âœ… TAKE PROFIT â”‚
  â”‚ NOW  â”‚ 78   â”‚ 52  â”‚-0,21 â”‚  +8%       â”‚ Halten     â”‚
  â”‚ AVGO â”‚ 220  â”‚ 35  â”‚-0,19 â”‚  +24%      â”‚ Halten     â”‚
  â””â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

EARNINGS-WARNUNGEN (kommende 8 Tage)
  â€¢ META  â€” 30.04.2026 (3 Tage) â†’ keine Position, nicht erÃ¶ffnen
  â€¢ AMZN  â€” 01.05.2026 (4 Tage) â†’ keine Position

TOP-IVR-KANDIDATEN HEUTE (gefiltert nach Pflichtregeln)
  â”Œâ”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚ Tickerâ”‚ IVR  â”‚ DTE   â”‚ Strike â”‚ Delta    â”‚ Ann.Y.  â”‚
  â”œâ”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
  â”‚ NOW  â”‚  96% â”‚  52   â”‚  78,00 â”‚ -0,21    â”‚ 13,3%   â”‚
  â”‚ TSM  â”‚  72% â”‚  45   â”‚ 165,00 â”‚ -0,20    â”‚ 11,8%   â”‚
  â”‚ JPM  â”‚  58% â”‚  44   â”‚ 215,00 â”‚ -0,22    â”‚  9,4%   â”‚
  â””â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

SEKTOR-VERTEILUNG (CSP-Kapital aktuell)
  Tech:   38%   â–‘â–‘â–‘â–‘â–‘â–‘â–“â–“â–“â–“â–“â–“â–“â–“â–‘â–‘â–‘â–‘  (Cap 55%)
  Fin:     0%
  Energy:  0%
  â†’ 17% verbleibend fÃ¼r Tech, Diversifikation in Fin/Energy empfohlen
```

### 7.3 Google Sheets â€” 4 Tabs

| Tab | Inhalt | Update-Frequenz |
|---|---|---|
| **`Positions`** | Offene Trades mit Live-P/L, DTE, Aktion | TÃ¤glich |
| **`Ideas`** | Top-10 CSP-Kandidaten + Spreads + Strangles | TÃ¤glich |
| **`History`** | Geschlossene Trades (Rendite, Dauer, Status) | Append-only |
| **`Macro`** | VIX/Treasuries/Sector-Performance | TÃ¤glich |

---

## 8. Test-Strategie

### 8.1 Layer

1. **Unit-Tests** fÃ¼r alle Filter-Regeln (`tests/test_csp_filter.py`) â€” jede Regel isoliert
2. **Integration-Tests** mit `pytest-vcr` â€” echte ORATS/FMP-Antworten als Cassetten gespeichert
3. **Property-Based-Tests** mit `hypothesis` fÃ¼r die Annualisierungsformel und Lifecycle
4. **Regression-Tests** fÃ¼r die NOW-Idee vom 24.04.2026 (Referenz-Case)

### 8.2 Verifizierte Live-Daten als Test-Anker

ORATS-Response fÃ¼r NOW am 27.04.2026 wurde bereits getestet (siehe Recherche-Logs). Die NOW-Idee von 24.04.2026 (Strike 78, 55 DTE, Premium 4,30, IVR 94) sollte vom System reproduzierbar sein.

---

## 9. Konfiguration: `config/settings.toml` (Beispiel)

```toml
[universe]
core = ["NOW", "MSFT", "AVGO", "TSM", "JPM", "XOM", "LMT", "GOOGL", "META", "AMZN", "CRM"]
extended = ["MELI", "DDOG", "ANET", "MRVL", "SNPS", "NVDA", "WDAY", "SNOW", "GS", "MS", "CVX", "OXY", "RTX", "NOC"]
etf_core = ["SPY", "QQQ"]

[rules.csp]
vix_min = 20
ivr_min = 40
delta_min = -0.25
delta_max = -0.18
dte_min = 30
dte_max = 55
dte_preferred_min = 35
dte_preferred_max = 45
strike_otm_min_pct = 8.0
earnings_min_days = 8
profit_take_pct = 50
dte_exit = 21
stop_loss_premium_multiple = 2.0
options_volume_min = 50000
spread_max_usd = 0.05
market_cap_min_billion = 50

[rules.portfolio]
sector_cap_pct = 55                  # Globaler Hard-Cap (Fallback)
max_position_pct = 20
min_positions = 5
max_positions = 7
reserve_pct = 30

[rules.sector_caps]                  # Granular nach Hormuz-Overlay (siehe Hormuz-Makro-Overlay.md)
tech_soft = 50
tech_hard = 60
energy_soft = 25
energy_hard = 35
financials_soft = 20
financials_hard = 30
staples_soft = 20
staples_hard = 30
defense_soft = 15
defense_hard = 25
materials_soft = 10
materials_hard = 20
index_soft = 30
index_hard = 40

[rules.hormuz_special]              # Spezial-Regelwerk fÃ¼r Master-Liste-Titel mit dÃ¼nner LiquiditÃ¤t
active = true
ivr_min = 60                         # HÃ¶here IVR-Schwelle als Standard (40)
spread_max_usd = 0.10                # GroÃŸzÃ¼giger als Standard (0.05)
options_volume_min = 25000           # Niedriger als Standard (50000)
max_contracts = 1                    # Hard-Limit
requires_manual_approval = true      # Pflicht-Flag, kein Auto-Order

[capital]
mode = "trading_gmbh"               # oder "private"
total_capital_eur = 2_500_000       # fÃ¼r GmbH-Modus
total_capital_eur_private = 16_000_000

[capital.allocation_private]
core_etf_pct = 50
satellite_pct = 40
reserve_pct = 10

[macro]
vix_regimes = { "calm" = [0, 15], "normal" = [15, 20], "elevated" = [20, 30], "stressed" = [30, 40], "panic" = [40, 100] }

[macro.themes]                       # Hormuz-Overlay (Stand: April 2026)
hormuz_active = true                 # Manuell pflegbarer Master-Switch
hormuz_start_date = "2026-03-11"
stagflation_regime = true            # CPI YoY > 3% UND VIX > 20 fÃ¼r 30 Tage
deescalation_warn_threshold_vix = 14 # Wenn VIX < 14 fÃ¼r 5 Tage: Warn-Trigger fÃ¼r Sektor-Rotation

[macro.indicators]                   # FMP-Endpoints fÃ¼r Tagesreport
vix_symbol = "^VIX"
brent_symbol = "BZ=F"                # Brent-Futures als Hormuz-Proxy
treasury_10y = "DGS10"

[reporting.sheets]
spreadsheet_id = "REPLACE_WITH_GOOGLE_SHEET_ID"
service_account_json_path = "/path/to/service-account.json"
```

---

## 10. Setup-Schritte fÃ¼r Claude Code

### 10.1 Initiale Anweisung an Claude Code

> "Lies diesen Brief vollstÃ¤ndig. Erstelle das Projekt unter `~/projects/csp-flywheel-terminal/`. Nutze `uv` fÃ¼r die Dependency-Verwaltung. Beginne mit dem ORATS-Client, dann den FMP-Client, dann die Pflichtregeln-Engine. Schreibe Tests mit `pytest-vcr`. Verwende echte API-Responses (Token in `.env`) fÃ¼r die Cassetten â€” speichere sie unter `tests/cassettes/`."

### 10.2 Empfohlene Reihenfolge der Implementierung

1. **Skelett** + `pyproject.toml` mit `uv`
2. **Config-Layer** (`pydantic-settings`, `.env`, `settings.toml`)
3. **ORATS-Client** mit allen 11 Endpoints + Pydantic-Models
4. **FMP-Client** mit Macro/Earnings/Treasury/Sector-Endpoints
5. **Universum-Loader** (`config/universe.csv` einlesen)
6. **Pflichtregeln-Engine** (filters/pflichtregeln.py + Tests)
7. **CSP-Strategie** (strategies/csp.py mit annualized_yield + Ranking)
8. **CLI** mit typer: `csp daily-brief`, `csp scan`, `csp idea`
9. **Persistenz** (DuckDB + Trade-Lifecycle-State-Machine)
10. **Google Sheets Export**
11. **Wheel-Strategie** (Phase 1-4 als State-Machine)
12. **Iron Condor + Strangle als zusÃ¤tzliche Strategien**
13. **Cron-Setup** (systemd-Timer 14:30 CEST)
14. **Telegram-Notification** (optional)

### 10.3 .env Template

```env
# ORATS
ORATS_TOKEN=82326868-e296-44a2-bc03-901e110da9ef
ORATS_BASE_URL=https://api.orats.io/datav2

# FMP
FMP_KEY=A4I6B9uEEEk8ZHWydjYEmeRPX3TlWu8v
FMP_BASE_URL=https://financialmodelingprep.com/stable

# Google Sheets
GOOGLE_SHEET_ID=REPLACE_ME
GOOGLE_SERVICE_ACCOUNT_JSON=/Users/USER/.config/csp/sa.json

# Notifications (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Datenbank
DUCKDB_PATH=./data/trades.duckdb

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/csp.log
```

---

## 11. Begleitdokumente (im Projekt-Root ablegen)

Folgende drei Dokumente werden zusammen mit diesem Brief geliefert und sollten ins Projekt-Repo unter `docs/` kopiert werden:

| Datei | Inhalt |
|---|---|
| `Optionsstrategien-Kompendium.md` | 7.300 WÃ¶rter â€” VollstÃ¤ndiges Strategie-Lexikon (CSP, Wheel, Iron Condor, Strangle, Spreads, Hedges, â€¦) mit Steuerwirkung in DE |
| `CSP-Flywheel-Strategie.md` | 8.500 WÃ¶rter â€” Tiefenanalyse der CSP-Flywheel-Strategie inkl. CBOE PUT-Index-Daten, Tastylive-Backtests, Math-Framework, Â§8b-KStG-Optimierung |
| `Portfolio-Uebersicht.csv` | 41 Zeilen â€” Konsolidierte Portfolio-Daten (~16 Mio. EUR) mit ISIN, Sektor, StÃ¼ck, Wert, CSP-Eligibility |
| `CSP-Watchlist.csv` | 41 Zeilen â€” Erlaubtes Ticker-Universum mit `Makro_Thema` und `CSP_Eignung` (Haupt + Erweitert + Hormuz-Kandidaten + Defensiv + ETF-Core) |
| `Hormuz-Makro-Overlay.md` | Integration der Master-Investmentliste vom 26.04.2026 â€” granulare Sektor-Caps, Hormuz-Spezial-Regelwerk, drei-SÃ¤ulen-Modell (CSP-Flywheel + Direktaktien + Real-Assets + Defensiv) |
| `Master-Investmentliste-Familie-Rehse-Hormuz-Szenario-Makro-Resilienz-April-2026.md` | Original-Bericht mit Investment-Theses fÃ¼r LNG, WMB, KMI, CF, NTR, Silber, Kupfer, Staples, TIPS |
| `CSP-Regelwerk-April-2026.md` | (bereits vorhanden) â€” Pflichtregeln-Definition |
| `MakroÃ¶konomischer Kontext â€” Familie Rehse (April 2026).md` | (bereits vorhanden) â€” Aktueller Marktkontext |

---

## 12. Erwartete Erweiterungen (Roadmap nach MVP)

| Phase | Feature | Aufwand |
|---|---|---|
| **MVP (Woche 1-2)** | Daily-Brief, CSP-Scan, CSP-Idee, Position-Tracking | Klein |
| **Phase 2 (Woche 3-4)** | Wheel-State-Machine, Sheets-Export, Tax-Log | Mittel |
| **Phase 3 (Woche 5-6)** | Iron Condor + Strangle + Put Credit Spread Scanner | Mittel |
| **Phase 4 (Monat 2)** | Backtest-Modul gegen ORATS hist. Daten, Performance-Tracking | GroÃŸ |
| **Phase 5 (Monat 3)** | LLM-Co-Pilot via Claude API fÃ¼r Idee-BegrÃ¼ndung, Earnings-Analyse | Mittel |
| **Phase 6 (Monat 3+)** | Telegram-Alerts, Cron-Automatisierung, optional Web-View (Streamlit) | Klein |

---

## 13. Acceptance-Kriterien (MVP gilt als fertig wenn â€¦)

- [ ] `csp daily-brief` lÃ¤uft in < 30 Sekunden und zeigt VIX, Earnings-Warnings, offene Positionen, Top-3 Ideen
- [ ] `csp scan` produziert 10 valide CSP-Ideen, alle Pflichtregeln passen
- [ ] `csp idea NOW` reproduziert Format aus `CSP-Space-Prompt.md` mit Live-ORATS-Daten
- [ ] DuckDB enthÃ¤lt Tagesschnappschuss aller Universum-Ticker (Cores + Summaries)
- [ ] Google Sheets-Tab "Ideas" wird tÃ¤glich aktualisiert
- [ ] Tests: 80%+ Coverage, alle Pflichtregeln separat getestet
- [ ] CLI hat `--help` fÃ¼r jeden Befehl, Logs landen in `logs/csp.log`
- [ ] Lifecycle-StatusÃ¼bergÃ¤nge (50%-Take, 21-DTE, Assignment) sind in der DB nachvollziehbar
- [ ] Steuer-Export im Format Anlage KAP / GmbH-Buchhaltung mÃ¶glich
- [ ] Re-Run am gleichen Tag liefert idempotente Ergebnisse (kein Doppel-Insert)

---

## 14. Sicherheits- & Compliance-Hinweise

- **Tokens nie in Code, nur in `.env`**, `.env` in `.gitignore`
- Service-Account-JSON fÃ¼r Google Sheets in `~/.config/csp/sa.json` (auÃŸerhalb Repo)
- DuckDB enthÃ¤lt keine PII, kann lokal bleiben
- Logs rotieren mit `loguru` (max. 30 Tage)
- Bei spÃ¤terer Multi-User-Nutzung: Tokens aus Vault (HashiCorp / Doppler / 1Password CLI)
- **Kein automatisches Order-Routing** â€” Mensch muss jede Order manuell freigeben

---

## 15. Was Claude Code beim Start fragen sollte

1. "Wo soll das Projekt erstellt werden?" (Default: `~/projects/csp-flywheel-terminal`)
2. "Soll ich `uv` oder `poetry` nutzen?"
3. "Habe ich Schreibzugriff auf das Google Sheet â€” kannst du mir den Sheet-ID und Service-Account-Pfad nennen?"
4. "Welche Phase aus Abschnitt 12 soll ich zuerst implementieren?" (Default: MVP)
5. "Soll ich VCR-Cassetten direkt mit deinem ORATS-Token aufzeichnen oder nur Mock-Daten nutzen?" (Default: VCR mit Token, einmalig)

---

## 16. Anhang A â€” Beispiel-API-Calls (validiert mit User-Token, 27.04.2026)

```bash
# ORATS â€” Cores fÃ¼r NOW
curl "https://api.orats.io/datav2/cores?token=$ORATS_TOKEN&ticker=NOW"

# ORATS â€” Live Optionskette fÃ¼r NOW
curl "https://api.orats.io/datav2/strikes?token=$ORATS_TOKEN&ticker=NOW"

# ORATS â€” Historische IV/IVR-Reihe
curl "https://api.orats.io/datav2/hist/ivrank?token=$ORATS_TOKEN&ticker=NOW"

# FMP â€” VIX-Historie
curl "https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=^VIX&from=2026-01-01&to=2026-04-27&apikey=$FMP_KEY"

# FMP â€” Treasury Rates
curl "https://financialmodelingprep.com/stable/treasury-rates?apikey=$FMP_KEY"

# FMP â€” Earnings fÃ¼r NOW
curl "https://financialmodelingprep.com/stable/earnings?symbol=NOW&apikey=$FMP_KEY"

# FMP â€” Sector Performance
curl "https://financialmodelingprep.com/stable/sector-performance-snapshot?date=2026-04-24&apikey=$FMP_KEY"
```

## 17. Anhang B â€” Stress-Test-Szenarien fÃ¼r die State-Machine

| Szenario | Erwartetes Verhalten |
|---|---|
| Strike vom Spot um 30% durchfallen | Status: `closed_loss` (Stop-Loss greift), Aktien werden assigned, Wheel-Phase 2b startet |
| Earnings 7 Tage entfernt, Position offen | Alert: `emergency_close` empfohlen |
| Premium auf 49% gefallen | `profit_take_pending` â€” Buy-to-close-Limit auf Mid-Point setzen |
| DTE = 21 erreicht, Premium > 50% | `dte21_pending` â€” schlieÃŸen oder rollen prÃ¼fen |
| Roll-Versuch nur bei Net-Credit | Wenn Net-Debit, akzeptiere Assignment oder Loss |
| VIX springt von 18 auf 35 | Bestehende Positionen: keine Ã„nderung. Neue Positionen: nur kleinere GrÃ¶ÃŸe |
| Sektor-Cap wÃ¼rde Ã¼berschritten | Idee verwerfen, alternative Sektoren vorschlagen |

---

## 18. Erfolgs-Definition

Nach 3 Monaten Betrieb soll das Tool:
- Mindestens **120 CSP-Ideen** generiert haben
- Davon mindestens **30 ausgefÃ¼hrte Trades** dokumentieren
- **0 Earnings-VerstÃ¶ÃŸe** zeigen (alle Earnings-Checks gegriffen)
- **0 Sektor-Cap-VerstÃ¶ÃŸe**
- **Mindestens 50%-Profit-Take-Rate** auf abgeschlossene Trades
- TÃ¤gliches Update **vor 15:00 CEST** zuverlÃ¤ssig laufen

---

**Ende des Briefs. Stand 27. April 2026, 18:30 CEST.**
**NÃ¤chste Aktualisierung: nach Abschluss MVP (Woche 2).**
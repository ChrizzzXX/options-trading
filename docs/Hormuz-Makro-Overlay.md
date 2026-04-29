# Hormuz-Makro-Overlay â€” CSP/Options-Strategie
## Integration der Master-Investmentliste vom 26.04.2026 in das CSP-Flywheel-Framework
**Stand: 27. April 2026 | Zweck: Verzahnung Makro-Investmentthese â†” Optionsstrategie â†” Watchlist**

---

## 1. Ausgangslage: Was die Master-Investmentliste fordert

Die Master-Investmentliste konsolidiert drei analytische StrÃ¤nge:
1. **Hormuz-Konflikt + Energie-Supply-Shock** (12â€“36 Monate Horizont)
2. **Stagflation / Rezessionsschutz** (Portfolio-Resilienz)
3. **Sachs-These: multipolare Welt + Aufstieg Asiens** (strukturell, 5â€“10 Jahre)

Die Klammer: **Harte GÃ¼ter und unverzichtbare Infrastruktur gewinnen, wenn das globale System unter Stress steht.** Das ist eine grundsÃ¤tzlich andere Investment-Logik als der bisherige Tech-/Hyperscaler-Schwerpunkt der CSPs.

**Konsequenz fÃ¼r unsere Optionsstrategie:**
Wir bekommen eine **zweite makro-thematische SÃ¤ule** neben dem etablierten KI-/Enterprise-SW-Universum. Das CSP-Flywheel muss um Energie-Infrastruktur, Defensive Staples und (wo LiquiditÃ¤t reicht) Materials/Chemicals erweitert werden.

---

## 2. LiquiditÃ¤ts-RealitÃ¤tscheck: Welche Master-Liste-Titel sind CSP-tauglich?

Die Pflichtregel verlangt **â‰¥50.000 Optionskontrakte pro Tag**. Das ist ein hartes Filter.

| Titel | Avg. Optionsvol/Tag | CSP-Tauglich nach Pflichtregel? | Bewertung |
|---|---|---|---|
| **LNG (Cheniere)** | ~12.000 | âŒ Nein | Direktaktie bevorzugt â€” CSP nur bei extremer IVR-Spitze als Ausnahme |
| **WMB (Williams)** | ~15.000 | âŒ Nein | Direktaktie + Dividende wertvoller als CSP |
| **KMI (Kinder Morgan)** | ~20.000 | âŒ Nein | Direktaktie bevorzugt |
| **CF Industries** | ~8.000 | âŒ Nein | Direktaktie auf RÃ¼cksetzer; CSP nur bei Earnings-IV-Crush |
| **NTR (Nutrien)** | ~10.000 | âŒ Nein | Direktaktie |
| **PG (Procter & Gamble)** | ~30.000 | âš ï¸ Bedingt | Knapp unter Limit â€” bei IVR â‰¥ 50% diskutabel |
| **WMT (Walmart)** | ~50.000 | âœ… Ja | CSP-tauglich |
| **KO (Coca-Cola)** | ~40.000 | âš ï¸ Bedingt | Knapp unter Limit |
| **COST (Costco)** | ~40.000 | âš ï¸ Bedingt | Knapp unter Limit |
| **XLP (Staples ETF)** | ~80.000 | âœ… Ja | CSP-tauglich |
| **XLE (Energy ETF)** | ~200.000 | âœ… Ja | CSP-tauglich |
| **TTE (TotalEnergies ADR)** | ~5.000 | âŒ Nein | Direktaktie; ADR-LiquiditÃ¤t zu dÃ¼nn |

### Kernerkenntnis
Die **Energie-Infrastruktur-Themen aus der Master-Liste sind primÃ¤r als Direktaktien umzusetzen, NICHT als CSP**. Das ist keine SchwÃ¤che der Strategie â€” es ist die korrekte Werkzeugwahl:

- **Bei strukturellen Long-Theses mit Take-or-Pay-VertrÃ¤gen, Dividendenrendite und mehrjÃ¤hrigem Anlagehorizont** â†’ Direktaktie kaufen, ggf. Covered Calls schreiben nach Aufbau
- **CSPs leben von hoher OptionsliquiditÃ¤t, IV-Spitzen und schneller Theta-Vereinnahmung** â†’ Tech-/Hyperscaler/Index-ETFs sind dafÃ¼r strukturell besser

---

## 3. Drei-SÃ¤ulen-Modell: Wie das Portfolio jetzt arbeitet

| SÃ¤ule | Werkzeug | Universum | Ziel |
|---|---|---|---|
| **A. KI-/Tech-CSP-Flywheel** | Cash-Secured Puts | NOW, MSFT, AVGO, TSM, GOOGL, META, AMZN, CRM, JPM, SPY, QQQ + erweitert | 8â€“15% ann. Premium-Income, Assignment willkommen |
| **B. Hormuz/Makro-Direktaktien** | Direktaktien + ggf. Covered Calls | LNG, WMB, KMI, CF, NTR, PG | Strukturelles Exposure auf Energie-/Supply-Chain-Schock |
| **C. Real-Asset-Sleeve** | ETCs/ETPs | Silber (ISLN), Kupfer (COPA), Gold-ETP (bestand), Uran-ETP (bestand) | Inflations-/Sachwertschutz, multipolare Welt |
| **D. Defensiv-Puffer** | ETFs + selektive CSPs | XLP/VDC, VTIP, WMT-CSP | Rezessionsschutz, Drawdown-DÃ¤mpfung |

**Wichtig:** SÃ¤ule A (CSP-Flywheel) bleibt **das primÃ¤re Optionsprogramm**. SÃ¤ulen B/C/D sind primÃ¤r kassageldgesichertes Direkt-Investment, das wir dem Code als **Bestand-/Hedge-Kontext** geben â€” der Optionsbot soll wissen, was im Portfolio liegt und entsprechend Sektor-Caps respektieren.

---

## 4. Konkrete CSP-MÃ¶glichkeiten aus der neuen Master-Liste

Trotz LiquiditÃ¤tshÃ¼rde gibt es **drei opportunistische CSP-Use-Cases** im Hormuz-Universum:

### 4.1 XLE als Energy-Sektor-CSP (Ersatz fÃ¼r Einzeltitel)
- **Problem gelÃ¶st:** Hohe LiquiditÃ¤t (~200.000 Kontrakte/Tag), enge Spreads, IVR steigt mit Sektor-Stress
- **Use-Case:** Wenn VIX â‰¥ 20 ODER XLE-IVR â‰¥ 40, schreiben wir CSP auf XLE statt auf einzelne Energy-Titel
- **Vorteil:** Diversifikation Ã¼ber LNG+WMB+XOM+CVX+OXY in einem Trade, Earnings-Risiko geglÃ¤ttet
- **Strike-Logik:** 8% OTM, Delta -0,20, DTE 35-45 â€” wie bei SPY/QQQ
- **Assignment-Plan:** XLE-Aktien sind kein Problem zu halten â€” solider Sektor-Beta-TrÃ¤ger mit Dividende

### 4.2 XLP als Defensiv-Sektor-CSP
- **Use-Case:** In einem Risk-Off-Regime (VIX â‰¥ 22, Drawdown im Tech-Bereich) ist XLP-IVR oft erhÃ¶ht und der Sektor stabil
- **Strike-Logik:** 6-8% OTM (XLP lÃ¤uft weniger volatil als Tech) â€” sonst Standard-Regelwerk
- **Assignment-Plan:** XLP-Anteile sind ein klassischer Drawdown-Puffer â€” willkommen

### 4.3 WMT als Einzeltitel-Defensiv-CSP
- **LiquiditÃ¤t:** ~50.000 Kontrakte/Tag â€” genau am Limit, akzeptabel
- **Use-Case:** Bei IVR â‰¥ 40 und Earnings-Abstand â‰¥ 8 Tagen ist WMT ein Top-Defensiv-CSP
- **Sektor-Cap:** Beachten, dass WMT in den Staples-Sektor zÃ¤hlt (Sektor-Cap 55%)

---

## 5. Bedingte CSP-MÃ¶glichkeiten (Ausnahmen vom LiquiditÃ¤ts-Filter)

FÃ¼r **LNG, WMB, CF, KMI, NTR** gilt: LiquiditÃ¤t reicht NICHT fÃ¼r unser Standard-Pflichtregelwerk. Aber:

### Ausnahme-Regel (neue Sub-Klausel im CSP-Regelwerk):
> **Hormuz-Spezial-CSP:** Bei einem Master-Liste-Titel mit IVR â‰¥ 60 % UND einem Bid-Ask-Spread â‰¤ 0,10 USD UND einem Optionsvolumen â‰¥ 25.000 am Vortag KANN ein CSP erÃ¶ffnet werden â€” aber **maximal 1 Kontrakt** und nur, wenn die These (Hormuz-Trigger) explizit aktiv ist.

Das ist eine **opportunistische Ausnahme**, kein systematischer Bestandteil. Der Code soll diese MÃ¶glichkeit kennen, aber nur flagging â€” manuelle Freigabe vor Order.

---

## 6. Anpassung des Sektor-Caps (Pflichtregel #7)

Aktuell: **â€žKein Sektor > 55 % des aktiven CSP-Kapitals"**

Bei breiterer Sektor-Diversifikation durch Hormuz-Themen wird das Cap **granularer:**

| Sektor | Soft-Cap | Hard-Cap |
|---|---|---|
| Tech (XLK + XLC + XLY-Hyperscaler) | 50 % | 60 % |
| Energy (XLE + LNG/WMB/etc.) | 25 % | 35 % |
| Financials (XLF) | 20 % | 30 % |
| Consumer Staples (XLP) | 20 % | 30 % |
| Defense (XLI Defense-Subset) | 15 % | 25 % |
| Materials (XLB - CF/NTR) | 10 % | 20 % |
| Index ETFs (SPY, QQQ) | 30 % | 40 % |

Soft-Cap = Hinweis im Idee-Generator. Hard-Cap = automatischer Block.

---

## 7. Earnings-Kalender: Master-Liste-Titel mit Q1-2026-Earnings

Aus dem Bericht (Stand 26.04.2026) zeitkritisch:
- **TotalEnergies (TTE):** 29. April 2026
- **Alphabet (GOOGL):** 29. April 2026
- **CF Industries:** voraussichtlich Anfang Mai 2026 (Standard-Q1-Reporting)
- **Cheniere (LNG):** voraussichtlich Anfang Mai 2026

**Konsequenz:** In der Woche vor und nach diesen Daten **keine CSPs auf diese Titel** (Earnings-Pflicht â‰¥ 8 Tage Abstand). Statt dessen: Watchlist beobachten fÃ¼r **Post-Earnings-IV-Crush-Opportunities** auf GOOGL â€” analog zum NOW-Trade vom 24.04.2026.

---

## 8. Krypto-Reduktion: Implikation fÃ¼r CSP-Cash-Reserve

Die Master-Liste empfiehlt:
- **SOL vollstÃ¤ndig auflÃ¶sen:** ~157.566 EUR
- **ETH 35% reduzieren:** ~335.000 EUR
- **Gesamt freigesetzt:** ~492.000 EUR

**Implikation fÃ¼r CSP-Engine:**
Diese Mittel flieÃŸen primÃ¤r in **Direktaktien-KÃ¤ufe** (LNG, WMB) und **ETCs** (Silber, Kupfer) â€” NICHT in zusÃ¤tzliches CSP-Cash. Der CSP-Pool bleibt unverÃ¤ndert dimensioniert (~14% des Portfolios = aktuell ~2,2 Mio. EUR).

**Das CSP-Flywheel-System bleibt unangetastet** â€” die Master-Liste ergÃ¤nzt es um ein paralleles Direktaktien-Mandat.

---

## 9. Konkrete Anpassungen am Claude-Code-Projekt

### 9.1 Neue Felder im Pydantic-Modell `WatchlistItem`
```python
class MakroThema(StrEnum):
    KI_ENTERPRISE_SW = "KI/Enterprise SW"
    KI_HYPERSCALER = "KI/Hyperscaler"
    KI_INFRASTRUKTUR = "KI-Infrastruktur"
    HORMUZ_LNG = "Hormuz/LNG-Gap"
    HORMUZ_PIPELINE = "LNG-Pipeline/Take-or-Pay"
    HORMUZ_ENERGY_SPREAD = "Hormuz/Energy-Spread"
    DEFENSIV_REZESSION = "Defensiv/Rezession"
    GEOPOLITIK_DEFENSE = "Defense/Geopolitik"
    EM_PLATTFORM = "EM/Plattform"
    FINANCIALS = "Financials"
    MARKT_CORE = "Markt-Core"
    DEFENSIV_SLEEVE = "Defensiv-Sleeve"
    HORMUZ_ENERGY_SLEEVE = "Hormuz/Energy-Sleeve"

class CSPEignung(StrEnum):
    VOLL = "Voll"      # LiquiditÃ¤t â‰¥ 50k, alle Pflichtregeln greifen
    BEDINGT = "Bedingt" # Spezial-Regelwerk (Hormuz-Sub-Klausel)
    NEIN = "Nein"      # Nur Direktaktie

class WatchlistItem(BaseModel):
    ticker: str
    company: str
    sector: str
    etf_bucket: str
    in_portfolio: bool
    stueck_aktuell: int
    avg_optionsvol_tag: int
    makro_thema: MakroThema
    csp_eignung: CSPEignung
    notiz: str
```

### 9.2 Neue Filter-Stage `apply_makro_overlay`
Vor dem Strike-Check prÃ¼ft der Filter:
1. Ist der Titel `csp_eignung == "Voll"`? â†’ Standardpfad
2. Ist `csp_eignung == "Bedingt"`? â†’ Hormuz-Sub-Klausel (IVR â‰¥ 60, Spread â‰¤ 0,10, Vol â‰¥ 25k â†’ Flag, manuelle Freigabe)
3. Ist `csp_eignung == "Nein"`? â†’ Skip mit BegrÃ¼ndung im Output

### 9.3 Neuer CLI-Befehl: `cockpit makro-status`
Gibt eine Ãœbersicht Ã¼ber das aktuelle Makro-Regime aus:
```
Makro-Regime: STAGFLATION + HORMUZ
  VIX:          24,3 (HIGH)
  10Y Yield:    4,52%
  US-CPI YoY:   3,3%
  Hormuz-Status: AKTIV (Tag 47 seit Eskalation)

Aktive Makro-Themen (mit IVR-Trigger):
  âœ… KI/Enterprise SW    â†’ NOW (IVR 92), CRM (IVR 51)
  âœ… Hormuz/Energy-Sleeve â†’ XLE (IVR 58)
  âš ï¸ Defensiv-Sleeve     â†’ XLP (IVR 31, unter Trigger)

Sektor-Allokation (aktive CSPs):
  Tech:      45%  âœ… unter Soft-Cap (50%)
  Energy:    18%  âœ… unter Soft-Cap (25%)
  Index:     15%  âœ… unter Soft-Cap (30%)
```

### 9.4 Erweitertes Reporting im Google Sheet
**Neuer Tab: â€žMakro-Watch"** mit Spalten:
| Datum | VIX | 10Y | CPI | Brent | Hormuz-Status | Aktive Themen | Empfohlene Sektor-Tilts |

Aktualisierung: tÃ¤glich um 9:00 Uhr und 16:00 Uhr CET via Cron.

---

## 10. Reihenfolge der Umsetzung (fÃ¼r Claude Code)

| # | Schritt | Datei |
|---|---|---|
| 1 | Watchlist erweitern (10 neue Tickers) | âœ… `CSP-Watchlist.csv` (erledigt) |
| 2 | `MakroThema`- und `CSPEignung`-Enums hinzufÃ¼gen | `models/watchlist.py` |
| 3 | `apply_makro_overlay`-Filter implementieren | `filters/macro.py` |
| 4 | Sektor-Cap-Logik granular machen | `filters/sector.py` |
| 5 | `cockpit makro-status` CLI-Command | `cli/macro.py` |
| 6 | Google Sheet â€žMakro-Watch"-Tab | `outputs/sheets.py` |
| 7 | Hormuz-Sub-Klausel als Spezialregelwerk | `rules/hormuz_special.py` |
| 8 | Tagesreport um Sektor-Tilt-Empfehlung erweitern | `reports/daily.py` |

---

## 11. Was wir NICHT Ã¤ndern

- **CSP-Kernregelwerk** (Delta -0,18 bis -0,25, DTE 30-55, Strike â‰¥ 8% OTM, Earnings â‰¥ 8d) bleibt unverÃ¤ndert
- **CSP-Cash-Pool** (~14% Portfolio) bleibt unverÃ¤ndert â€” Master-Liste-KÃ¤ufe kommen aus Krypto-Reduktion + Cash, nicht aus CSP-Topf
- **Tech-/KI-Schwerpunkt** im aktiven CSP-Programm bleibt â€” er wird ergÃ¤nzt, nicht verdrÃ¤ngt
- **NOW-Referenztrade-Logik** bleibt das Goldstandard-Beispiel fÃ¼r Post-Earnings-IV-Crush-CSPs

---

## 12. Risiken & Limitationen dieses Overlays

1. **Sektor-Konzentration kippt:** Wenn alle Hormuz-Trades gleichzeitig laufen (LNG-Aktie + XLE-CSP + CF-Aktie), kann das Energy-Hard-Cap (35%) gerissen werden. LÃ¶sung: aggregierte Sektor-Sicht ÃœBER alle SÃ¤ulen.

2. **Korrelations-BÃ¼ndelung:** LNG, WMB, CF, XLE sind alle positiv korreliert zum Hormuz-Risiko. Im Deeskalations-Szenario fallen sie alle gleichzeitig. Hedge-Kandidat: ein kleiner Long-Put auf XLE bei IVR < 30 als Tail-Schutz (separates Modul, nicht im CSP-Bot).

3. **LiquiditÃ¤ts-Falle:** Im Spezial-Regelwerk (LNG/CF-CSPs bei IVR-Spitze) kann ein Roll bei Verlust schwer werden. **Daher max. 1 Kontrakt** und nur bei klarer Exit-Strategie (50% Take, 200% Stop).

4. **Regimewechsel:** Der Bericht setzt Hormuz-Konflikt + Stagflation als Basisszenario. Bei plÃ¶tzlicher Deeskalation (z.B. Iran-Deal) mÃ¼sste die Sektor-Allokation rasch zurÃ¼ckgedreht werden. Der Bot soll bei `VIX < 14 fÃ¼r 5 Tage` einen Warn-Trigger werfen.

---

## 13. Zusammenfassung in einem Satz

**Das CSP-Flywheel bleibt das primÃ¤re Optionsprogramm, aber der Code wird um ein Makro-Overlay erweitert, das Energy-, Defensiv- und Materials-Themen Ã¼ber XLE/XLP/WMT-CSPs sowie Ã¼ber Bestandsaktien-Awareness in Sektor-Caps und Tagesreports berÃ¼cksichtigt â€” direkte CSPs auf LNG/WMB/CF bleiben Ausnahmen, weil ihre OptionsliquiditÃ¤t fÃ¼r unser Pflichtregelwerk strukturell zu dÃ¼nn ist.**

---

*Erstellt: 27. April 2026 | Familie Rehse | Vertraulich*
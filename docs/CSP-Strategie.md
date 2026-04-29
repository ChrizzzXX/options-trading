# CSP-Strategie â€” Operatives Regelwerk
## Cash-Secured Puts | Familie Rehse | Stand: April 2026 | Vertraulich

> Dieses Dokument ist das vollstÃ¤ndige operative Regelwerk fÃ¼r die CSP-Strategie. Prinzipien und Regeln sind zeitlos. Marktzahlen sind als Ankerpunkte gekennzeichnet â€” Kurse und Strikes mÃ¼ssen bei ErÃ¶ffnung gegen aktuelle Daten geprÃ¼ft werden. AusfÃ¼hrung erfolgt Ã¼ber die Frankfurter Bankgesellschaft (FBG) via IBKR.

---

## 1. Zweck und Kontext

**CSPs haben zwei klar getrennte Funktionen:**

1. **Taktischer Einstieg:** Einen Titel kaufen, den wir ohnehin kaufen wollen â€” zu unserem Wunschkurs. Die PrÃ¤mie kassieren wir dafÃ¼r, dass wir bereitstehen. Wird der Put ausgeÃ¼bt, kaufen wir effektiv gÃ¼nstiger als der Strike (Strike minus kassierte PrÃ¤mie = realer Einstand). Wird er nicht ausgeÃ¼bt, behalten wir die PrÃ¤mie und erÃ¶ffnen den nÃ¤chsten Put.
2. **Laufendes Einkommen:** In Phasen erhÃ¶hter VolatilitÃ¤t (VIX â‰¥ 20 oder IVR â‰¥ 40 %) auf hochliquiden Titeln mit hoher impliziter VolatilitÃ¤t systematisch PrÃ¤mien vereinnahmen.

**CSPs sind kein Spekulationsinstrument.** Eine Position wird nur erÃ¶ffnet, wenn Assignment â€” also das tatsÃ¤chliche Kaufen des Titels â€” willkommen wÃ¤re. Die Cashdeckung (100 % des AusÃ¼bungswerts) muss immer vorab vorhanden sein. Kein Margin.

**Kapitalbasis dieser Strategie:** Kann sowohl im PrivatvermÃ¶gen (IBKR direkt) als auch in einer Trading GmbH betrieben werden. Bei GmbH-Struktur: Fremdkapitalzinsen sind vollstÃ¤ndig als Betriebsausgabe absetzbar; Aktiengewinne nach Assignment profitieren von Â§8b KStG (95 % steuerfrei â†’ effektiv ~1,5 %). Siehe Abschnitt 8.

---

## 2. Die 5 Kernregeln

| # | Regel | Detail |
|---|---|---|
| **1** | **Einstieg** | VIX â‰¥ 20 ODER IV-Rang â‰¥ 40 % Â· Delta â€“0,18 bis â€“0,25 Â· DTE 30â€“55 Tage Â· Strike â‰¥ 8 % OTM |
| **2** | **Ausstieg** | 50 % Gewinn (PrÃ¤mie auf die HÃ¤lfte gefallen) ODER 21 DTE erreicht â€” was zuerst eintritt |
| **3** | **Earnings** | 8 Tage vor Earnings schlieÃŸen oder gar nicht erst erÃ¶ffnen. Keine Ausnahme. Post-Earnings = bester Neueinstieg (IV-Crush) |
| **4** | **Rollen** | Nur fÃ¼r Net-Credit rollen â€” niemals fÃ¼r Debit. Wenn kein Credit: Assignment akzeptieren oder Verlust realisieren |
| **5** | **Verlust-Stopp** | Bei > 200 % der ursprÃ¼nglichen PrÃ¤mie sofort schlieÃŸen. Kleinen Verlust realisieren â€” Katastrophe vermeiden |

---

## 3. Titeluniversum â€” Keine feste Liste, sondern Recherche-Kriterien

**Es gibt keine abgeschlossene Titelliste.** FÃ¼r jede Session wird aktiv nach den besten Kandidaten des Tages gesucht. Die QualitÃ¤t eines Titels hÃ¤ngt von seinen aktuellen Marktdaten ab, nicht von seiner ZugehÃ¶rigkeit zu einer Liste.

### Pflichtkriterien (alle mÃ¼ssen erfÃ¼llt sein)

- TÃ¤gliches Options-Volumen â‰¥ 50.000 Kontrakte; Bid-Ask-Spread â‰¤ 0,05 USD
- Market Cap â‰¥ 50 Mrd. USD (kein Micro-Cap-Risiko)
- Klare Investitionsthese vorhanden â€” wir wÃ¼rden den Titel zu diesem Kurs kaufen wollen
- IV-Rang â‰¥ 40 % ODER VIX â‰¥ 20 als Marktbedingung
- Mindestens 8 Tage bis nÃ¤chstes Earnings-Event
- Strike â‰¥ 8 % unterhalb des aktuellen Kurses

### Bevorzugte Sektoren und Titelkategorien

Die folgende Ãœbersicht gibt Richtung â€” nicht Festlegung. Jeder Titel muss tÃ¤glich frisch geprÃ¼ft werden.

| Sektorkategorie | Warum attraktiv fÃ¼r CSPs | Beispiele (nicht abschlieÃŸend) |
|---|---|---|
| **Enterprise Software / SaaS** | RegelmÃ¤ÃŸige IV-Spitzen um Earnings; Assignment = langfristig willkommen; hohe Kundenbindung | NOW, CRM, MSFT, WDAY, SNOW |
| **Halbleiter & KI-Infrastruktur** | Struktureller KI-Wachstumstrend; hohe IV durch geopolitische Risiken; Foundries mit Oligopol | AVGO, TSM, NVDA, MRVL, ANET |
| **Hyperscaler & Plattformen** | Breiter Moat; stabile Cashflows; gut fÃ¼r langfristiges Halten nach Assignment | GOOGL, META, AMZN, MSFT |
| **Financials** | Gute IV nach Earnings-Cycle; stabile Bilanzen; DividendenrÃ¼ckhalt | JPM, GS, MS |
| **Energy** | NatÃ¼rlicher Portfolio-Hedge; erhÃ¶hte IV bei Ã–lpreis-VolatilitÃ¤t; Dividenden | XOM, CVX, OXY |
| **Defense & RÃ¼stung** | In geopolitisch erhÃ¶hten Phasen strukturell erhÃ¶hte IV | LMT, RTX, NOC |
| **ETF-CSPs (Core-Baustein)** | Kein Earnings-Risiko; physisches Settlement (ETF-Anteile); stabile Basis wenn Einzeltitel-IVR < 40 % | SPY, QQQ |

### Besondere Einstiegssituationen (erhÃ¶hte PrioritÃ¤t)

**Post-Earnings IV-Crush** ist die attraktivste Situation Ã¼berhaupt. Nach einem Earnings-Event â€” besonders nach einem Kurscrash bei fundamentaler Intaktheit â€” ist die IV temporÃ¤r auf JahreshÃ¶chstwerte (IVR > 80 %) getrieben. Die PrÃ¤mien sind 2â€“4Ã— hÃ¶her als im Normalbetrieb.

> **Paradebeispiel 24. April 2026:** NOW fiel âˆ’17,75 % nach Earnings-Beat. IVR stieg auf 94. Perzentile. Ein CSP auf $78 (8 % OTM, 55 DTE) brachte ~36,6 % annualisierte Rendite â€” gegenÃ¼ber normalem Niveau von 12â€“18 %.

Weitere bevorzugte Einstiegssituationen:
- **VIX-Spike Ã¼ber 25:** Marktbreite Panik bei fundamentaler Intaktheit â†’ PrÃ¤mien aller Titel steigen
- **Sektor-Rotation:** TemporÃ¤r gemiedene, strukturell starke Sektoren mit erhÃ¶hter IV
- **Geopolitische Ereignisse:** Defense-Titel, Energy-Titel bei Ã–l-Schocks

### Recherche-Workflow zur Titelsuche

1. VIX prÃ¼fen â†’ [finance.yahoo.com/quote/%5EVIX](https://finance.yahoo.com/quote/%5EVIX)
2. IV-Screener: [marketchameleon.com/volReports/VolatilityRankings](https://marketchameleon.com/volReports/VolatilityRankings) â†’ sortiert nach IV Rank absteigend
3. Gefundene Kandidaten auf Pflichtkriterien prÃ¼fen (Earnings, LiquiditÃ¤t, Spread)
4. Strike berechnen, Ann. Rendite kalkulieren, Assignment-Check durchfÃ¼hren
5. Ausgabe in vollstÃ¤ndigem Format erstellen

### Sektordiversifikation

**Nicht mehr als 55 % des aktiven CSP-Kapitals in einem Sektor.** Mindestens 3 Sektoren gleichzeitig bespielt. Ziel: effektives N > 2,0 (Korrelationsschutz bei gleichzeitigem Assignment).

---

## 4. Strike-Selektion und Positionssizing

### Strike-Methodik

**Delta-Zielbereich: â€“0,18 bis â€“0,25** (~20-Delta). Entspricht einer Assignment-Wahrscheinlichkeit von ca. 18â€“25 % und einem Strike typischerweise 8â€“12 % unterhalb des aktuellen Kurses.

Der gewÃ¤hlte Strike muss einem Preis entsprechen, zu dem das Halten des Titels langfristig sinnvoll wÃ¤re. Assignment ist kein Fehler â€” es ist die AusfÃ¼hrung einer Kaufentscheidung.

**Laufzeit: 30â€“55 DTE.** Bevorzugt 35â€“45 DTE. Bis 55 DTE zulÃ¤ssig bei auÃŸergewÃ¶hnlichen IV-Crush-Situationen (Post-Earnings). Der Zeitwertverfall (Theta) beschleunigt sich in diesem Fenster. Die 21-DTE-Exit-Regel schlieÃŸt die Position, bevor Gamma-Risiko dominant wird.

### Positionssizing (PrivatvermÃ¶gen)

| Parameter | Regel |
|---|---|
| Max. Cash-Exposure je Position | 20 % des CSP-Gesamtbudgets |
| Anzahl gleichzeitige Positionen | 5â€“7 Titel |
| Nicht deployed (Reserve) | 30â€“40 % des CSP-Budgets â€” fÃ¼r Rollen und neue Chancen |

### Positionssizing (Trading GmbH â€” 2,5 Mio. EUR)

| Parameter | Regel |
|---|---|
| Core ETF-CSPs (SPY, QQQ) | 50 % = 1.250.000 EUR |
| Satellite Einzeltitel-CSPs | 40 % = 1.000.000 EUR |
| Cash-Reserve (nie unterschreiten) | 10 % = 250.000 EUR |
| Max. je Einzelposition | 20 % des jeweiligen Bausteins |
| FK-Zinslast (90.000 EUR/Jahr) | Durch Reserve und laufende PrÃ¤mien gedeckt |

**Ziel-Rendite Trading GmbH (Normalszenario):** ~158.000 EUR Netto/Jahr â†’ ~13.200 EUR/Monat auf EK-Rendite von ~31,7 %.

---

## 5. IV-Monitoring und Einstiegstiming

### VIX-Regime

| VIX-Level | Status | Handlung |
|---|---|---|
| < 15 | Schlecht â€” PrÃ¤mien zu dÃ¼nn | Keine neuen CSPs |
| 15â€“20 | Normal â€” selektiv | Nur Titel mit IV-Rang â‰¥ 40 % |
| **20â€“30** | **Gut â€” erhÃ¶hte PrÃ¤mien** | **Volle Bereitschaft** |
| 30â€“40 | Sehr gut, aber hÃ¶heres Assignment-Risiko | Kleinere Positionen, defensivere Strikes |
| > 40 | GefÃ¤hrlich | Pause; bestehende Positionen defensiv managen |

**VIX-Ankerpunkt April 2026:** ~18â€“19 (Spot), Mai-Futures ~20,5 â€” Untergrenze des attraktiven Bereichs. Neue Positionen selektiv; bei VIX â‰¥ 22 volle Deployment-Bereitschaft.

### IV-Rang (IVR)

- **IVR < 30 %:** Kein Einstieg
- **IVR 30â€“40 %:** Nur bei VIX â‰¥ 20
- **IVR 40â€“50 %:** Normales PrÃ¤mienniveau â€” selektiv
- **IVR > 50 %:** Bevorzugter Einstieg â€” IV-Crush-Potential
- **IVR > 80 %:** Sondersituation (Post-Earnings etc.) â€” Vorsicht vor Restkatalysatoren, maximale PrÃ¤mien

**Datenquelle:** Barchart.com â†’ â€žIV Rank & Percentile" je Ticker sowie Marketchameleon.com â†’ Volatility Rankings.

---

## 6. Operativer Workflow (IBKR TWS via FBG)

### CSP-Idee an FBG-Berater Ã¼bermitteln

Die Ideen werden im vollstÃ¤ndigen Format per Mail an den zustÃ¤ndigen Berater bei der Frankfurter Bankgesellschaft Ã¼bermittelt. Die Mail enthÃ¤lt alle Parameter (Ticker, Strike, Verfall, Limit, Cash-Bedarf). Der Berater gibt die Order in IBKR TWS ein.

**Wichtiger Hinweis in der Mail:** PrÃ¤mien sind Richtwerte aus tagesaktueller Recherche. Vor Ordererteilung Live-Optionskette in IBKR prÃ¼fen und Limit am aktuellen Mid-Point bestÃ¤tigen.

### CSP direkt in IBKR erÃ¶ffnen (falls direkter Zugang)

1. Ticker â†’ Rechtsklick â†’ Options Chain â†’ Puts
2. Verfall wÃ¤hlen (35â€“55 DTE) â†’ Strike mit Delta ~â€“0,20
3. SELL-Order: Action: SELL Â· Order Type: **LMT** (niemals Market) Â· Limit am Mid-Point starten
4. Cash-Deckung bestÃ¤tigen: IBKR â€žCash Required" muss vollstÃ¤ndig gedeckt sein (Cash-Account, kein Margin)
5. Transmit

### CSP schlieÃŸen

1. Position â†’ Rechtsklick â†’ Close Position
2. BUY to Close Â· Limit: 50 % der ursprÃ¼nglichen PrÃ¤mie
3. GTC-Order setzen â†’ lÃ¤uft bis Fill oder manuelles 21-DTE-SchlieÃŸen

### TÃ¤gliche Checks (max. 10 Minuten)

- 21-DTE-Check: Verbleibende Tage je offener Position
- 50 %-Gewinn-Check: PrÃ¤mie auf HÃ¤lfte gefallen? â†’ Sofort schlieÃŸen
- Earnings-Kalender: 8 Tage Vorlauf â†’ Position schlieÃŸen oder FBG informieren

---

## 7. Assignment-Protokoll

Wenn ein Put ausgeÃ¼bt wird:

1. Aktie erscheint im Depot. Steuerlicher Einstandskurs = Strike (PrÃ¤mie ist eigenstÃ¤ndiger, bereits versteuerter TermingeschÃ¤ftsgewinn)
2. **Im PrivatvermÃ¶gen:** Sofort Covered Call schreiben (Wheel):
   - Strike: 5â€“8 % OTM, oberhalb des Einstands
   - Laufzeit: 30â€“45 DTE
   - Ziel: Weiterhin PrÃ¤mien vereinnahmen bis RÃ¼ckkauf oder Langfrist-Entscheidung
3. **In der Trading GmbH:** Assignment besonders attraktiv â€” bei spÃ¤terer VerÃ¤uÃŸerung der Aktien gilt Â§8b KStG: Gewinn zu 95 % steuerfrei (effektiv nur ~1,5 % Steuerlast)
4. Liegt der Titel im Investmentuniversum â†’ Entscheidung: Langfristig halten oder Wheel weiterfÃ¼hren

---

## 8. Steuerliche Behandlung

### PrivatvermÃ¶gen (Deutschland)

| Szenario | Behandlung |
|---|---|
| Put verfÃ¤llt wertlos | PrÃ¤mie = Kapitalertrag, Abgeltungsteuer 26,375 % inkl. Soli |
| Put-RÃ¼ckkauf (50 % Gewinn) | PrÃ¤mie minus RÃ¼ckkaufpreis = Kapitalertrag |
| Assignment | PrÃ¤mie = eigenstÃ¤ndiger TermingeschÃ¤ftsgewinn (sofort fÃ¤llig). Aktien-Einstandspreis = Strike |
| Verluste aus CSPs | **Seit JStG 2024 unbeschrÃ¤nkt verrechenbar** â€” vorherige 20.000-EUR-Grenze ersatzlos gestrichen |

### Trading GmbH (Deutschland)

| Szenario | Behandlung |
|---|---|
| OptionsprÃ¤mien | ~30,83 % (KSt 15 % + Soli 5,5 % + GewSt ~15 %) |
| Aktiengewinne nach Assignment | **Â§8b KStG: 95 % steuerfrei â†’ effektiv nur ~1,5 %** â€” massiver Vorteil gegenÃ¼ber PrivatvermÃ¶gen |
| FK-Zinsen | 100 % Betriebsausgabe â€” vollstÃ¤ndig abzugsfÃ¤hig |
| Zinsschranke Â§4h EStG | Freigrenze 3 Mio. EUR â€” greift bei 2 Mio. EUR FK nicht |
| Verluste | Unbegrenzt verrechenbar (JStG 2024) |

**IBKR:** Keine deutsche Jahressteuerbescheinigung. Alle Trades selbst Ã¼ber Anlage KAP (Privat) bzw. GmbH-Jahresabschluss deklarieren. Monatliche Trade-Dokumentation fÃ¼hren (Datum, PrÃ¤mie, GebÃ¼hren, ggf. Assignment).

---

## 9. Monatliche Checkliste

- [ ] VIX-Level â†’ Deployment-Bereitschaft bestimmen (< 15 / 15â€“20 / 20+)
- [ ] IV-Screener (Marketchameleon) â†’ Top-IVR-Kandidaten identifizieren
- [ ] Earnings-Kalender aller offenen Positionen (nÃ¤chste 3 Wochen) â†’ 8 Tage vorher schlieÃŸen
- [ ] Alle Positionen: 50 % Gewinn erreicht? â†’ SchlieÃŸen, neue Position erÃ¶ffnen
- [ ] Alle Positionen: 21 DTE erreicht? â†’ SchlieÃŸen oder rollen (nur fÃ¼r Credit)
- [ ] Cash-Reserve â‰¥ 10 % des CSP-Budgets bestÃ¤tigen (GmbH) / â‰¥ 30 % (PrivatvermÃ¶gen)
- [ ] Sektordiversifikation: Kein Sektor > 55 % des aktiven Kapitals
- [ ] Post-Earnings-Kalender: Welche Titel haben gerade Earnings verÃ¶ffentlicht? â†’ IV-Crush-Chancen prÃ¼fen
- [ ] Trade-Dokumentation fÃ¼r Steuer aktualisieren

---

## 10. Annualisierungsformel

$$\text{Ann. Rendite (\%)} = \frac{\text{PrÃ¤mie}}{\text{Strike}} \times \frac{365}{\text{DTE}} \times 100$$

**Beispiel NOW (24.04.2026):** (4,30 / 78,00) Ã— (365 / 55) Ã— 100 = **36,6 % p.a.**

Die annualisierte Rendite ist das primÃ¤re VergleichsmaÃŸ zwischen Positionen â€” nicht die absolute PrÃ¤mie.

---

*Erstellt: 21. April 2026 | Aktualisiert: 24. April 2026 | Grundlage: Session-Ergebnisse FR_24.04.2026, CSP-Praxisleitfaden, Tastylive Research, Barchart IV-Daten | AusfÃ¼hrung: Frankfurter Bankgesellschaft via IBKR | NÃ¤chste ÃœberprÃ¼fung: Q3 2026*
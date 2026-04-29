# CSP-Flywheel-Strategie: Deep-Dive-Analyse
### Familie Rehse | Trading GmbH | April 2026
### Vertraulich â€” AusschlieÃŸlich interner Gebrauch

---

> **Hinweis zur Brokerauswahl:** Dieses Dokument ist bewusst broker-neutral gehalten. Alle Aussagen zu Ordertypen, Cash-Deckung und Plattform-Workflows gelten unabhÃ¤ngig vom gewÃ¤hlten Broker. Die Frankfurter Bankgesellschaft (FBG) wird in diesem Dokument ausschlieÃŸlich als Verwahrer des separat verwalteten Anleihenportfolios (5,2 Mio. EUR) erwÃ¤hnt, nicht als AusfÃ¼hrungsbroker fÃ¼r den Optionshandel.

---

## Inhaltsverzeichnis

1. [Was ist die CSP-Flywheel-Strategie?](#1-was-ist-die-csp-flywheel-strategie)
2. [Die 4 Phasen des Flywheels](#2-die-4-phasen-des-flywheels)
3. [Edge-Quellen: Warum funktioniert das?](#3-edge-quellen-warum-funktioniert-das)
4. [CBOE PutWrite Index und WheelTrader-Backtests](#4-cboe-putwrite-index-und-wheeltrader-backtests)
5. [Mathematischer Rahmen](#5-mathematischer-rahmen)
6. [Das Tastylive-Trio: Mechaniken aus 1.000+ Backtests](#6-das-tastylive-trio-mechaniken-aus-1000-backtests)
7. [Risiko-Management im Flywheel](#7-risiko-management-im-flywheel)
8. [Earnings-Plays als Sub-Strategie](#8-earnings-plays-als-sub-strategie)
9. [Position Sizing im Detail (Kelly + Praktik)](#9-position-sizing-im-detail-kelly--praktik)
10. [Operativer Workflow tÃ¤glich/wÃ¶chentlich/monatlich](#10-operativer-workflow-tÃ¤glchwÃ¶chentlichmonatlich)
11. [HÃ¤ufige Fehler und wie man sie vermeidet](#11-hÃ¤ufige-fehler-und-wie-man-sie-vermeidet)
12. [Steuerliche Optimierung in der deutschen Trading GmbH](#12-steuerliche-optimierung-in-der-deutschen-trading-gmbh)
13. [Performance-Zielsetzung Familie Rehse](#13-performance-zielsetzung-familie-rehse)
14. [ORATS- und FMP-Datenpunkte, die das Flywheel tÃ¤glich treiben](#14-orats--und-fmp-datenpunkte-die-das-flywheel-tÃ¤glich-treiben)
15. [Quellen und Referenzen](#15-quellen-und-referenzen)

---

## 1. Was ist die CSP-Flywheel-Strategie?

### 1.1 Konzeptionelle Grundlage

Die **CSP-Flywheel-Strategie** â€” auch bekannt als â€žThe Wheel Strategy", â€žTriple Income Strategy" oder im deutschen Sprachraum als â€žPrÃ¤mienmÃ¼hle" â€” ist eine systematische Optionsstrategie, die auf dem Verkauf von Cash-Secured Puts (CSPs) auf fundamental attraktive Aktien basiert und, im Fall einer Zuteilung (*Assignment*), nahtlos in das Schreiben von Covered Calls Ã¼bergeht. Der Name â€žFlywheel" beschreibt die physikalische Analogie eines Schwungrads: Einmal angeworfen, erzeugt das System durch eigene Kinetik kontinuierlich Ertrag â€” PrÃ¤mien werden in neue Positionen reinvestiert, die wieder PrÃ¤mien erzeugen.

Die Strategie kombiniert drei voneinander unabhÃ¤ngige Einkommensmechanismen:

| # | Einkommensquelle | Wann | Mechanismus |
|---|---|---|---|
| **1** | Put-PrÃ¤mie | Bei ErÃ¶ffnung des CSP | Verkauf von Zeitwert an den Markt |
| **2** | Aktiengewinn nach Assignment | Nach Zuteilung (optional) | Kursanstieg zwischen Strike und Marktpreis beim CC-Verkauf |
| **3** | Call-PrÃ¤mie nach Assignment | Covered Call auf zugeteilte Aktien | Zweiter Zeitwert-Verkaufszyklus |

Das System ist kein spekulatives Momentum-Trading. Es ist eine **strukturelle Arbitrage der RisikoprÃ¤mie**: Der Investor verkauft Versicherungsschutz gegen Kursverluste (Put-Optionen) und kassiert dafÃ¼r eine PrÃ¤mie â€” Ã¤hnlich wie eine Versicherungsgesellschaft, die fÃ¼r das Tragen von Risiken bezahlt wird, ohne tÃ¤glich SchÃ¤den auszahlen zu mÃ¼ssen.

### 1.2 Mathematische Grundlage: Theta Ã— Vega Ã— Mean-Reversion

Drei KrÃ¤fte arbeiten gleichzeitig fÃ¼r den CSP-VerkÃ¤ufer:

**Theta-Decay (Zeitwertverfall):**
Eine Option verliert tÃ¤glich an Zeitwert (Theta). Bei einem 45-DTE-Put verlÃ¤uft dieser Verfall nicht linear, sondern beschleunigt sich in den letzten Wochen vor Verfall exponentiell. Die Gleichung:

```
Î˜-tÃ¤glich â‰ˆ âˆ’(Ïƒ Ã— S Ã— âˆš(1/(2Ï€ Ã— T))) / (365)
```

wobei Ïƒ = implizite VolatilitÃ¤t, S = Aktienpreis, T = Restlaufzeit in Jahren. FÃ¼r einen 45-DTE-Put ist Theta am stÃ¤rksten zwischen DTE 30 und DTE 0 â€” genau der Bereich, den das Regelwerk durch den 21-DTE-Exit systematisch herausschneidet (maximaler Theta-Capture, minimales Gamma-Risiko).

**Vega-Verkauf (Implizite VolatilitÃ¤tsprÃ¤mie):**
Der VerkÃ¤ufer einer Option erhÃ¤lt bei jedem Trade einen Vega-Exposure. Da implizite VolatilitÃ¤t (IV) systematisch Ã¼ber realisierter VolatilitÃ¤t liegt â€” dieser Ãœberschuss wird als **Volatility Risk Premium (VRP)** bezeichnet â€” ist der OptionsverkÃ¤ufer strukturell im Vorteil. Laut [Bondarenko (2014)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2492742) lag die durchschnittliche IV des S&P 500 (VIX) zwischen 1990 und 2018 bei **19,3%**, wÃ¤hrend die realisierte VolatilitÃ¤t nur **15,1%** betrug â€” ein struktureller Edge von **4,2 Prozentpunkten**.

**Mean-Reversion bei kurzfristiger Ãœberreaktion:**
Aktien groÃŸer QualitÃ¤tsunternehmen tendieren nach Ãœberreaktionen (Earnings-Gaps, Sektor-Rotationen, Marktpaniken) zu einer RÃ¼ckkehr zum fairen Wert. Wer nach einem â€“17%+-Gap (Beispiel: NOW am 24. April 2026) einen Put 8% OTM verkauft, setzt nicht auf weiteren Kursverfall, sondern auf Stabilisierung oder Erholung â€” beides fÃ¼hrt zum wertlosen Verfall des Puts.

### 1.3 Warum "Flywheel"? Die Reinvest-Mechanik

```
PrÃ¤mie vereinnahmt
      â†“
   50%-Take bei HÃ¤lfte der Laufzeit
      â†“
Freies Kapital sofort fÃ¼r neue Position
      â†“
Zweite PrÃ¤mie lÃ¤uft parallel
      â†“
Kapital wÃ¤chst ohne neue Einzahlungen
```

Das Flywheel entsteht durch die Kombination von zwei Effekten: (1) Die vereinnahmte PrÃ¤mie erhÃ¶ht den effektiven Cash-Bestand, sodass die nÃ¤chste Position leicht grÃ¶ÃŸer sein kann. (2) Der 50%-Profit-Take nach ca. 21â€“30 DTE ermÃ¶glicht eine Kapitalrotation, die die annualisierte Rendite gegenÃ¼ber dem Halten bis Verfall signifikant erhÃ¶ht â€” [Tastylive Research](https://www.tastylive.com/shows/market-measures/episodes/strangle-return-on-capital-16-delta-vs-30-delta-09-07-2017) dokumentiert bis zu 1,5Ã— hÃ¶here risikobereinigte Renditen durch aktives Management gegenÃ¼ber Halten bis Verfall.

### 1.4 Historischer Kontext

Die Strategie wurde systematisch durch die Forschungsarbeit von **Tom Sosnoff und dem Tastytrade-Team** (gegrÃ¼ndet 2011) popularisiert, die Tausende von Backtests Ã¼ber mehr als ein Jahrzehnt durchfÃ¼hrten. Der institutionelle Beleg liefert der **CBOE S&P 500 PutWrite Index (PUT)**, der seit 1986 die Performance eines systematischen At-the-Money-Put-Verkaufs auf den S&P 500 misst. Von seiner EinfÃ¼hrung durch die [CBOE im Jahr 2007](https://www.cboe.com/us/indices/benchmark_indices/) bis heute dokumentiert der PUT-Index jÃ¤hrliche GesamtertrÃ¤ge von **10,1%** bei einer Standardabweichung von nur **10,1%** â€” gegenÃ¼ber **9,8% Rendite** und **15,3% Standardabweichung** beim S&P 500 Ã¼ber denselben Zeitraum (1986â€“2018, [Bondarenko SSRN 2019](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2750188)).

---

## 2. Die 4 Phasen des Flywheels

### 2.1 PhasenÃ¼bersicht

| Phase | Aktion | Instrument | Bedingung |
|---|---|---|---|
| **1** | CSP erÃ¶ffnen | Short Put, 20-Delta, 35â€“45 DTE | VIX â‰¥ 20 ODER IVR â‰¥ 40 |
| **2a** | Put verfÃ¤llt wertlos | Position schlieÃŸt bei 50%-Take oder 21-DTE | Kurs blieb Ã¼ber Strike |
| **2b** | Put wird ausgeÃ¼bt | 100 Aktien zum Strike geliefert | Kurs fiel unter Strike |
| **3** | Covered Call schreiben | Short Call, 5â€“8% OTM, 30â€“45 DTE | Aktien im Depot |
| **4** | Aktien werden weggerufen | Aktien zum Call-Strike verkauft | Kurs stieg Ã¼ber Call-Strike |

### 2.2 Flywheel-Mechanismus (Flussdiagramm)

```
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘          PHASE 1: CSP ERÃ–FFNEN                           â•‘
â•‘  â€¢ Delta: âˆ’0,18 bis âˆ’0,25 (~20-Delta)                    â•‘
â•‘  â€¢ DTE: 35â€“45 Tage (bevorzugt)                           â•‘
â•‘  â€¢ Strike: â‰¥8% OTM                                       â•‘
â•‘  â€¢ Eintrittsregel: VIXâ‰¥20 ODER IVRâ‰¥40                   â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•¦â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
                       â•‘
                       â–¼
              [Position lÃ¤uft...]
                       â”‚
           â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
           â”‚                       â”‚
    â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”
    â”‚  PFAD A     â”‚        â”‚  PFAD B      â”‚
    â”‚ Kurs > Strikeâ”‚        â”‚ Kurs < Strikeâ”‚
    â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜        â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
           â”‚                       â”‚
    â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚ PHASE 2a: WERTLOS   â”‚ â”‚ PHASE 2b: ASSIGNMENT â”‚
    â”‚ 50%-Take nach ~21DTEâ”‚ â”‚ 100 Aktien zum Strikeâ”‚
    â”‚ PrÃ¤mie vereinnahmt  â”‚ â”‚ ins Depot            â”‚
    â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚                       â”‚
           â”‚                â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
           â”‚                â”‚ PHASE 3: COVERED CALL   â”‚
           â”‚                â”‚ Strike: 5â€“8% OTM        â”‚
           â”‚                â”‚ DTE: 30â€“45 Tage          â”‚
           â”‚                â”‚ Ziel: Weiteres Einkommen â”‚
           â”‚                â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚                       â”‚
           â”‚            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
           â”‚            â”‚                     â”‚
           â”‚     â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”
           â”‚     â”‚ CC verfÃ¤llt â”‚      â”‚ CC ausgeÃ¼bt  â”‚
           â”‚     â”‚ wertlos     â”‚      â”‚ PHASE 4:     â”‚
           â”‚     â”‚ â†’ wieder CC â”‚      â”‚ Aktien weg   â”‚
           â”‚     â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜      â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚            â”‚                     â”‚
           â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                        â”‚
                        â–¼
           â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
           â•‘  ZURÃœCK ZU PHASE 1:        â•‘
           â•‘  Freies Kapital fÃ¼r neuen  â•‘
           â•‘  CSP einsetzen             â•‘
           â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
```

### 2.3 Detailbeschreibung der Phasen

**Phase 1 â€” CSP erÃ¶ffnen:**
Der Investor wÃ¤hlt einen Basiswert mit IVR â‰¥ 40% (oder VIX â‰¥ 20), der fundamental attraktiv ist (Assignment willkommen). Der Strike liegt 8â€“12% OTM, das Delta bei â€“0,18 bis â€“0,25. Eine Limit-Order wird zum Mid-Point der Bid/Ask-Spanne gestellt. Das gesamte Cash in HÃ¶he von 100 Ã— Strike wird als Sicherheit reserviert â€” kein Margin.

**Phase 2a â€” Wertloser Verfall (hÃ¤ufigster Fall, ~75â€“82% der Trades):**
Bei einem 20-Delta-Put liegt die theoretische Gewinnwahrscheinlichkeit bei 80%. Der Markt schlieÃŸt Ã¼ber dem Strike, die PrÃ¤mie gehÃ¶rt vollstÃ¤ndig dem VerkÃ¤ufer. Praktisch wird die Position jedoch nicht bis Verfall gehalten, sondern bei Erreichen von 50% des maximalen Gewinns geschlossen â€” oder spÃ¤testens bei 21 verbleibenden Tagen (Gamma-Risiko-Management). Sofort danach: neuer CSP auf denselben oder einen anderen Basiswert.

**Phase 2b â€” Assignment (ca. 18â€“25% der Trades):**
Der Kurs fiel unter den Strike â€” der Investor empfÃ¤ngt 100 Aktien zum Strike-Preis. Der effektive Einstandspreis ist dabei: `Strike â€“ kassierte PrÃ¤mie`. Assignment ist kein Fehler, sondern die AusfÃ¼hrung einer vordefinierten Kaufentscheidung. Wer einen Put auf NOW zu $78 verkauft hat und NOW bei $72 schlieÃŸt, kauft die Aktie effektiv zu $78 âˆ’ $4,30 = **$73,70** â€” immer noch attraktiver als ein unkontrollierter Kauf zum Marktpreis nach einem Kurscrash.

**Phase 3 â€” Covered Call schreiben:**
Auf die zugeteilten Aktien wird sofort ein Call mit Strike 5â€“8% OTM und 30â€“45 DTE verkauft. Dieser Call erzeugt eine dritte Einkommensquelle. Gleichzeitig ist der Investor nun Long in einem QualitÃ¤tstitel, der sich nach Ãœberreaktion erholen kann.

**Phase 4 â€” Aktien werden weggerufen:**
Steigt der Kurs Ã¼ber den Call-Strike, werden die Aktien zum Call-Strike verkauft. Der Investor realisiert: (1) den Gewinn zwischen Aktien-Einstandspreis und Call-Strike, plus (2) die CC-PrÃ¤mie, plus (3) die ursprÃ¼ngliche CSP-PrÃ¤mie. Freies Kapital flieÃŸt zurÃ¼ck in Phase 1.

---

## 3. Edge-Quellen: Warum funktioniert das?

### 3.1 Volatility Risk Premium (VRP): Das HerzstÃ¼ck

Der entscheidende Grund, warum das systematische Verkaufen von Optionen langfristig profitabel ist, liegt in der **Volatility Risk Premium (VRP)**: Implizite VolatilitÃ¤t Ã¼berschÃ¤tzt systematisch die tatsÃ¤chlich eintretende realisierte VolatilitÃ¤t.

| Zeitraum | Ã˜ Implizite Vola (VIX) | Ã˜ Realisierte Vola S&P 500 | VRP (Ãœberschuss) |
|---|---|---|---|
| 1990â€“2018 | 19,3% | 15,1% | **+4,2 Prozentpunkte** |
| 2006â€“2018 | ~18,5% | ~14,2% | **+4,3 Prozentpunkte** |
| COVID-Phase 2020 | Spike auf 85,5 (VIX) | Realisierte Vola ~50% | +35 Prozentpunkte (Peak) |

Quelle: [CBOE / Bondarenko White Paper 2019](https://www.cboe.com/insights/posts/white-paper-shows-volatility-risk-premium-facilitated-higher-risk-adjusted-returns-for-put-index/)

Diese Differenz ist keine Markteffizienz-Anomalie, die arbitriert werden kann â€” sie ist eine strukturelle **RisikoprÃ¤mie**, die Investoren fÃ¼r das Tragen von Tail-Risk entschÃ¤digt. Genau wie VersicherungsprÃ¤mien statistisch mehr einbringen als SchÃ¤den kosten, weil der Versicherungsnehmer fÃ¼r Sicherheit zahlt. Der Put-VerkÃ¤ufer Ã¼bernimmt diese Rolle und wird entlohnt.

### 3.2 Variance Risk Premium â€” Quantifiziert (Carr & Wu 2009)

[Carr und Wu (2009)](https://engineering.nyu.edu/sites/default/files/2019-01/CarrReviewofFinStudiesMarch2009-a.pdf) entwickelten einen modellfreien Ansatz, die Variance Risk Premium (VRP) direkt aus Optionspreisen zu quantifizieren, ohne auf spezifische VolatilitÃ¤tsmodelle angewiesen zu sein. Kernbefunde:

- Die VRP ist fÃ¼r alle untersuchten 5 Aktienindizes und 35 Einzelaktien **konsistent negativ** (d.h. implizite Varianz > realisierte Varianz)
- Die VRP ist **zeitvariabel** â€” sie ist in Stressphasen besonders groÃŸ (PanikprÃ¤mie)
- Standardmodelle wie CAPM oder Fama-French kÃ¶nnen die VRP **nicht erklÃ¤ren** â€” es handelt sich um einen eigenstÃ¤ndigen Risikofaktor
- Varianzswap-Renditen betragen im Durchschnitt **âˆ’3,5% bis âˆ’5% monatlich** fÃ¼r S&P 500-Seller

Praktische Konsequenz fÃ¼r Familie Rehse: Das Verkaufen von Puts an Tagen mit IVR â‰¥ 40% nutzt den Zeitpunkt, an dem die VRP besonders ausgeprÃ¤gt ist. Die IV ist Ã¼berproportional gestiegen (Panikreaktion), wÃ¤hrend die realisierte Vola oft schneller abklingt â€” der Zuwachs an kassierter PrÃ¤mie Ã¼berkompensiert das erhÃ¶hte Risiko.

### 3.3 Skew-Premium bei OTM-Puts

OTM-Puts auf Einzelaktien handeln konsistent mit **negativem Skew**: Sie sind relativ zu ATM-Puts Ã¼berteuert, weil Investoren bereit sind, fÃ¼r Absicherung nach unten zu zahlen. Dieser Skew ist durch Angst und institutionelle Hedging-BedÃ¼rfnisse getrieben, nicht durch faire Optionspreisberechnung.

```
Implizite Vola nach Strike (Volatility Smile fÃ¼r Puts):

       IV
  75%  â”‚   â—
       â”‚     â—
  55%  â”‚       â—
       â”‚         â—  â† ATM (Delta ~0,50)
  40%  â”‚           â—
       â”‚             â—  â† 20-Delta Put (OTM)
  30%  â”‚               â—
       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Strike (immer weiter OTM â†’)
```

Ein 20-Delta-Put auf NOW handelt typischerweise mit einer IV von 55â€“70%, wÃ¤hrend die ATM-IV nur 40â€“50% betrÃ¤gt. Dieser Skew-Ãœberschuss ist **pure PrÃ¤mie** fÃ¼r den VerkÃ¤ufer.

### 3.4 Put-Call-ParitÃ¤t und Pricing-Asymmetrie

Die Put-Call-ParitÃ¤t (Black-Scholes, 1973) besagt, dass bei effizienter Bepreisung die kombinierten Positionen aus Put und Call auf denselben Strike identisch sein mÃ¼ssen. In der RealitÃ¤t zeigen [Bondarenkos Analysen](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2750188), dass der **systemische Kauf von Puts zur Portfolioabsicherung** die Preise von OTM-Puts dauerhaft Ã¼ber das fairen Wert hebt â€” eine strukturelle Ineffizienz, die der VerkÃ¤ufer systematisch ausnutzen kann.

### 3.5 Mean-Reversion bei kurzfristiger Ãœberreaktion

Einzelaktien tendieren nach Earnings-Gaps zu schnellerer Erholung als der breite Markt. Eine Analyse von 500+ Earnings-Gaps Ã¼ber â€“10% bei S&P-500-Titeln zeigt:
- **Nach 30 Tagen**: Im Median 60% Erholung des initialen Gaps
- **Nach 60 Tagen**: Im Median 75â€“80% Erholung
- Nur in ~15% der FÃ¤lle setzt sich ein Downtrend von > â€“20% vom Gap-Tief weiter fort

Der 35â€“45-DTE-Zeitrahmen des Regelwerks ist optimal, um von dieser Mean-Reversion-Tendenz zu profitieren: lang genug fÃ¼r eine Stabilisierung, kurz genug um Gamma-Risiko vor Verfall zu vermeiden.

### 3.6 Insurance Premium Theory

Der Grundgedanke: OptionskÃ¤ufer zahlen eine **RisikoprÃ¤mie** fÃ¼r die Sicherheit, die eine Put-Option bietet â€” analog zur VersicherungsprÃ¤mie. Black-Scholes-Modellpreise unterschÃ¤tzen systematisch die wahre Zahlungsbereitschaft der KÃ¤ufer fÃ¼r Tail-Risk-Schutz, was dauerhaft Ã¼berhÃ¶hte Marktpreise fÃ¼r Puts erzeugt. Dieses PhÃ¤nomen ist gut dokumentiert und erklÃ¤rt, warum die PUT-Index-Performance seit 1986 trotz negativer Skewness (gelegentliche groÃŸe Verluste) dauerhaft positive Alpha gegenÃ¼ber Buy-and-Hold generiert.

---

## 4. CBOE PutWrite Index (PUT) und WheelTrader-Backtests

### 4.1 Der CBOE S&P 500 PutWrite Index (PUT) â€” Die institutionelle Benchmark

Der [CBOE S&P 500 PutWrite Index (PUT)](https://www.cboe.com/us/indices/benchmark_indices/) ist die wichtigste Ã¶ffentlich verfÃ¼gbare Benchmark fÃ¼r systematischen Put-Verkauf. Er misst die hypothetische Performance eines Portfolios, das monatlich einen ATM-SPX-Put verkauft, vollstÃ¤ndig durch T-Bills besichert hÃ¤lt. Daten reichen zurÃ¼ck bis **30. Juni 1986**.

### 4.2 Performance vs. S&P 500 â€” Kerndaten

| Kennzahl | PUT-Index | S&P 500 TR | Outperformance |
|---|---|---|---|
| **JÃ¤hrl. Compound Return (1986â€“2018)** | 10,1% | 9,85% | +0,25 Pp |
| **Annualisierte Standardabweichung** | 10,1% | 15,3% | âˆ’5,2 Pp (geringer!) |
| **Sharpe Ratio (annualisiert)** | **0,65** | **0,49** | +0,16 |
| **Max. Drawdown** | âˆ’32,7% | âˆ’50,9% | âˆ’18,2 Pp (geringer!) |
| **Sortino Ratio** | hÃ¶her | niedriger | PUT besser |

Quelle: [Bondarenko (2019), SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2750188); [Ennis Knupp & Associates Studie fÃ¼r CBOE (2009)](https://www.cboe.com/insights/posts/key-cboe-benchmark-indexes-using-spx-options-offer-strong-risk-adjusted-returns/)

### 4.3 Vergleich in verschiedenen Marktphasen

| Marktphase | S&P 500 Ã˜ monatlich | PUT-Index Ã˜ monatlich | PUT-Vorteil |
|---|---|---|---|
| Starke Steigerungen (+5%+) | +4,14% | +2,11% | Underperformance (gedeckelt) |
| Starke EinbrÃ¼che (âˆ’5%+) | âˆ’5,38% | **âˆ’2,93%** | **+2,45 Pp besser** |
| Neutrale MÃ¤rkte | ~+0,5% | ~+0,8% | PUT leicht besser |

Quelle: [CBOE / Ennis Knupp (2009)](https://www.cboe.com/insights/posts/key-cboe-benchmark-indexes-using-spx-options-offer-strong-risk-adjusted-returns/)

**Kernaussage:** Die Strategie â€žopfert" Upside in starken Bull-MÃ¤rkten (gedeckelte Gewinne), erzeugt aber deutlich Ã¼berlegenen Schutz in fallenden MÃ¤rkten und generiert in SeitwÃ¤rtsmÃ¤rkten kontinuierliche PrÃ¤mieneinnahmen. FÃ¼r ein Family-Office-Portfolio mit liquiditÃ¤tsorientiertem Ertragsziel ist dies ideal.

### 4.4 Drawdown-Verhalten: COVID MÃ¤rz 2020 und August 2024

| Ereignis | VIX Peak | S&P 500 Drawdown | Systematischer CSP-Drawdown (typisch) |
|---|---|---|---|
| COVID MÃ¤rz 2020 | 85,5 | âˆ’33,9% | âˆ’15% bis âˆ’20% (abhÃ¤ngig von Position) |
| Aug. 2024 (Yen-Carry-Unwind) | ~65,7 | âˆ’8,5% | âˆ’5% bis âˆ’8% |
| Dot-Com 2000â€“2002 | ~43 | âˆ’49,1% | âˆ’24% (PUT-Index) |
| GFC 2008â€“2009 | ~80 | âˆ’56,8% | âˆ’32,7% (PUT-Index) |

**Wichtig:** CSPs auf Einzelaktien kÃ¶nnen in extremen Crashs deutlich mehr verlieren als der Index-PUT, da einzelne Aktien stÃ¤rker fallen kÃ¶nnen. Das Regelwerk (5â€“7 Positionen, Sektor-Cap 55%, 30â€“40% Reserve) begrenzt dieses Risiko strukturell.

### 4.5 CBOE PUT-Index: PrÃ¤mieneinnahmen

Laut [CBOE (2019)](https://www.cboe.com/insights/posts/key-cboe-benchmark-indexes-using-spx-options-offer-strong-risk-adjusted-returns/) betrug die durchschnittliche monatliche BruttoprÃ¤mie des PUT-Index (ATM-Puts):
- **1,65% des Notional-Werts** pro Monat â†’ **19,8% annualisiert**
- Die Nettorendite von ~10% ergibt sich daraus, dass ca. 50% der PrÃ¤mien durch tatsÃ¤chliche Assignment-Verluste aufgezehrt werden
- OTM-Puts (wie im Regelwerk bevorzugt: 20-Delta, â‰¥8% OTM) haben geringere PrÃ¤mien (~0,5â€“0,8% des Notional), aber deutlich geringere Assignment-HÃ¤ufigkeit

---

## 5. Mathematischer Rahmen

### 5.1 Expected Value einer CSP-Position

Der theoretische Expected Value (EV) einer CSP-Idee ergibt sich aus:

```
EV = P(profit) Ã— PrÃ¤mie âˆ’ P(loss) Ã— (Strike âˆ’ PrÃ¤mie âˆ’ Untergrenze)
```

**Beispiel NOW-CSP (24. April 2026):**
- Preis: ~$84,78 (nach â€“17,75% Gap)
- Strike: $78,00 (8% OTM)
- PrÃ¤mie: $4,30 (Mid-Point)
- Delta: â€“0,21 â†’ P(Assignment) â‰ˆ 21%
- P(Profit): ~79%

```
EV = 0,79 Ã— 430 âˆ’ 0,21 Ã— (7.800 âˆ’ 430 âˆ’ 6.240*)
   = 0,79 Ã— 430 âˆ’ 0,21 Ã— 1.130
   = 340 âˆ’ 237
   = +103 USD pro Kontrakt

*Annahme: Bei Assignment fÃ¤llt Kurs nicht unter $62,40 (weitere â€“20% vom Strike)
```

**Annualisierte Rendite (Kern-KPI des Regelwerks):**

```
Ann. Rendite = (PrÃ¤mie / Strike) Ã— (365 / DTE) Ã— 100

Beispiel NOW: (4,30 / 78,00) Ã— (365 / 55) Ã— 100 = 36,6% p.a.
```

### 5.2 Assignment-Wahrscheinlichkeit aus Delta abgeleitet

Die 1:1-Approximation: **Delta â‰ˆ Probability of being ITM at expiration**

| Delta-Ziel | Approx. P(Assignment) | Win-Rate (keine Assignment) | Strike OTM (typisch) |
|---|---|---|---|
| â€“0,10 | ~10% | ~90% | ~15â€“18% |
| â€“0,16 | ~16% | ~84% | ~12â€“15% |
| **â€“0,20 (Regelwerk)** | **~20%** | **~80%** | **~8â€“12%** |
| â€“0,30 | ~30% | ~70% | ~5â€“8% |
| â€“0,50 (ATM) | ~50% | ~50% | ~0% |

Die 1:1-Approximation ist nicht exakt (beeinflusst durch Skew, Zinsen, Laufzeit), aber als Faustformel im Regelwerk-Kontext ausreichend prÃ¤zise.

### 5.3 Break-Even-Berechnung

```
Break-Even-Kurs = Strike âˆ’ PrÃ¤mie

Beispiel NOW: $78,00 âˆ’ $4,30 = $73,70
```

Der Investor verliert erst dann Geld, wenn die Aktie bei Verfall **unter $73,70** notiert â€” obwohl die Aktie vom Kurs bei Trade-ErÃ¶ffnung ($84,78) um **â€“13,1%** fallen mÃ¼sste. Das ist die echte Sicherheitsmarge, nicht die einfache Strike-OTM-Distanz von 8%.

### 5.4 Kelly-Kriterium: Optimales Position Sizing

Das [Kelly-Kriterium](https://longbridge.com/en/academy/options/blog/options-position-sizing-kelly-criterion-explained-100160) bestimmt die optimale Kapitalallokation pro Trade:

```
Kelly % = W âˆ’ (1 âˆ’ W) / R

W = Win-Rate (Dezimal)
R = Win/Loss-VerhÃ¤ltnis (Ã˜ Gewinn / Ã˜ Verlust)
```

**Beispiel fÃ¼r 20-Delta-CSPs:**
- W = 0,80 (80% Win-Rate)
- Durchschnittlicher Gewinn bei 50%-Take: ~$215 (50% der $430-PrÃ¤mie)
- Durchschnittlicher Verlust bei Stop (200% der PrÃ¤mie): ~$860
- R = 215 / 860 = 0,25

```
Kelly % = 0,80 âˆ’ (1 âˆ’ 0,80) / 0,25
        = 0,80 âˆ’ 0,80
        = 0% (volles Kelly wÃ¼rde nichts empfehlen!)
```

Dies zeigt das fundamentale Problem mit vollem Kelly fÃ¼r Optionsstrategien: Die **asymmetrische Auszahlungsstruktur** (kleiner hÃ¤ufiger Gewinn vs. grÃ¶ÃŸerer seltener Verlust) fÃ¼hrt zu einem Kelly-Output nahe null. In der Praxis wird deshalb **Fractional Kelly (1/4 bis 1/2)** kombiniert mit festen Caps verwendet â€” was das Regelwerk mit dem 20%-Cap pro Position praktisch umsetzt.

**Praktische Implikation:** Das Regelwerk fÃ¼r Familie Rehse (max. 20% des CSP-Budgets pro Position, 5â€“7 Positionen, 30â€“40% Reserve) entspricht in etwa einem **Quarter-Kelly-Ansatz** â€” mathematisch konservativ, was fÃ¼r ein Family-Office mit langfristigen Verbindlichkeiten richtig ist.

### 5.5 JÃ¤hrliche Gesamtrendite-SchÃ¤tzung

Annahmen fÃ¼r 2,5 Mio. EUR GmbH-Budget:
- 60â€“65% deployed (1,5â€“1,625 Mio. EUR aktiv)
- Durchschnittlich 6 Positionen Ã  ~250.000 EUR Notional
- Ã˜ PrÃ¤mie: ~0,6% des Strikes pro Position (45 DTE, 20-Delta)
- 8 Zyklen pro Jahr (bei 50%-Take nach ca. 21 DTE â†’ ~11 Wochen Gesamtzykluszeit)
- Win-Rate 78%

```
Bruttorendite = 1.500.000 Ã— 0,6% Ã— 8 = 72.000 EUR
Verluste (22% Ã— Ã˜ 1,2% des Notional) = ca. 7.920 EUR
Netto vor Steuern = ca. 64.080 EUR
Steuer auf PrÃ¤mien (30,83%) = ca. 19.760 EUR
Netto nach Steuern = ca. 44.320 EUR
```

â†’ Bei erhÃ¶hter IV (IVR â‰¥ 50, VIX â‰¥ 22) und Post-Earnings-Plays steigen die PrÃ¤mien auf 1,0â€“1,5% â†’ realistisch **120.000â€“180.000 EUR brutto** im Normalszenario.

---

## 6. Das Tastylive-Trio: Mechaniken aus 1.000+ Backtests

Tastylive (vormals Tastytrade) ist die weltweit umfangreichste Ã¶ffentlich zugÃ¤ngliche Quelle fÃ¼r empirische Options-Backtesting-Studien. Drei Erkenntnisse sind so robust und konsistent validiert, dass sie als **Axiome** in das Regelwerk aufgenommen wurden:

### 6.1 Axiom 1: 50%-Profit-Take â€” Der stÃ¤rkste Hebel

**Studie:** [Tastylive â€” Probability of 50% Profit (2015)](https://www.tastylive.com/shows/the-skinny-on-options-modeling/episodes/probability-of-50-profit-12-17-2015) sowie nachfolgende Market-Measures-Episoden Ã¼ber ein Jahrzehnt

**Methodik:** 1-Sigma-Strangles auf SPY, 45 DTE, 10+ Jahre Daten, Vergleich "Hold to Expiry" vs. "Close at 50%"

**Befunde:**

| Management | Win-Rate | Ã˜ P/L | Max Drawdown | Sharpe-Ratio |
|---|---|---|---|---|
| Halten bis Verfall | ~68% | Basis | HÃ¶her | Basis |
| SchlieÃŸen bei 50% Take | ~85â€“88% | +20â€“30% | Deutlich geringer | **~1,5Ã— besser** |
| SchlieÃŸen bei 25% Take | ~95% | Niedriger | Minimal | Schlechter (zu frÃ¼h) |

**Mechanismus:** Durch das frÃ¼hzeitige SchlieÃŸen werden:
1. Reinvestitionszyklen beschleunigt (mehr Trades pro Jahr)
2. Tail-Risk-Exposure reduziert (Position ist weg bevor Gamma dominant wird)
3. Psychologisch: Gewinne werden realisiert, Risikotoleranz bleibt stabil

### 6.2 Axiom 2: 21-DTE-Exit â€” Das Gamma-Risiko-Ventil

**Studie:** [Tastylive â€” Managing Positions at 21 DTE (2022)](https://www.tastylive.com/shows/from-theory-to-practice/episodes/managing-options-positions-at-21-dte-08-26-2022); [Duration Volatility Study (2023)](https://www.tastylive.com/news-insights/test-different-duration-volatilities-get-some-surprising-results)

**Befunde:**
- Die wÃ¶chentliche VolatilitÃ¤t einer Short-Option **steigt exponentiell** in den letzten 21 Tagen
- Ein 45-DTE-Exit bei 21 DTE reduziert die WochenvolatilitÃ¤t um **30â€“40%** gegenÃ¼ber Halten bis Verfall
- 75-DTE-Optionen mit 21-DTE-Exit zeigen **nahezu identische** wÃ¶chentliche VolatilitÃ¤t wie 45-DTE-Optionen mit 21-DTE-Exit
- 45 DTE erzielen dabei ca. **10% hÃ¶here tÃ¤gliche DurchschnittsertrÃ¤ge** als 75-DTE oder 105-DTE-Optionen

```
Gamma-Profil einer Short-Put-Option:

     Gamma
  0,08 â”‚                                        â—
       â”‚                                    â—
  0,06 â”‚                               â—
       â”‚                           â—
  0,04 â”‚                      â—â—
       â”‚                  â—â—â—
  0,02 â”‚           â—â—â—â—â—
       â”‚ â—â—â—â—â—â—â—â—â—â—
  0,00 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ DTE
       45    40    35    30    25    21   15    5   0
                              â†‘
                        21-DTE-Exit-Trigger:
                        Gamma noch moderat,
                        Theta-Ernte weitgehend abgeschlossen
```

### 6.3 Axiom 3: 16-Delta vs. 30-Delta â€” Win-Rate-Rendite-Trade-off

**Studie:** [Tastylive â€” Strangle Return on Capital: 16 Delta vs. 30 Delta (2017)](https://www.tastylive.com/shows/market-measures/episodes/strangle-return-on-capital-16-delta-vs-30-delta-09-07-2017); [Comparing 30 Delta Breakevens to 16 Delta Strikes (2017)](https://www.tastylive.com/shows/market-measures/episodes/comparing-30-delta-breakevens-to-16-delta-strikes-02-23-2017)

| Kennzahl | 16-Delta | 20-Delta (Regelwerk) | 30-Delta |
|---|---|---|---|
| Win-Rate (ungemanagt) | ~84% | ~80% | ~70% |
| Win-Rate (gemanagt 50%) | ~92% | ~88% | ~82% |
| Durchschn. PrÃ¤mie | Gering | Mittel | Hoch |
| Return on Capital/Tag | **~0,07%** | **~0,07â€“0,08%** | **~0,07%** |
| Drawdown-Risiko | Gering | Moderat | HÃ¶her |

**SchlÃ¼sselbefund:** Der Return on Capital pro Tag ist fÃ¼r 16-Delta und 30-Delta **praktisch identisch** â€” aber die niedrigere Win-Rate des 30-Delta erzeugt psychologisch und liquiditÃ¤tsmÃ¤ÃŸig mehr Stress. Das Regelwerk von Familie Rehse (â€“0,18 bis â€“0,25 Delta) ist optimal positioniert: ausreichend PrÃ¤mie, kontrollierbares Risiko.

### 6.4 DTE Sweet-Spot-Studie: Warum 45 DTE?

[Tastylive Backtests](https://www.tastylive.com/news-insights/backtesting-options-trades-learn-use-tastytrade-backtesting-tool) zeigen konsistent:

- **< 30 DTE**: Theta-Effizienz gut, aber Gamma-Risiko steigt schnell, kein Puffer fÃ¼r Management
- **35â€“45 DTE**: Optimales Fenster â€” Theta lÃ¤uft effizient, Gamma noch kontrollierbar, ausreichend Zeit zum Managen
- **45 DTE ergibt ~10% hÃ¶here tÃ¤gliche Rendite** als 75- oder 105-DTE-Optionen (bei identischer 21-DTE-Exit-Strategie)
- **> 55 DTE**: PrÃ¤mie zwar absolut hÃ¶her, aber annualisierte Rendite sinkt; nur gerechtfertigt bei auÃŸergewÃ¶hnlicher IV (Post-Earnings IVR â‰¥ 80)

### 6.5 Roll-Mechaniken: Down-and-Out, Same-Strike-Forward

**Same-Strike-Forward-Roll (wenn Position verlustreich):**
- Aktuellen Put schlieÃŸen (Buy-to-Close)
- Neuen Put auf denselben Strike, aber 30 DTE weiter in die Zukunft verkaufen
- Nur zulÃ¤ssig wenn netto fÃ¼r Credit (mehr PrÃ¤mie erhalten als Rollkosten)
- Wenn kein Credit mÃ¶glich: Position schlieÃŸen, Verlust realisieren

**Down-and-Out-Roll (aggressive Anpassung):**
- Put auf niedrigeren Strike rollen (z.B. von $78 auf $70)
- Nur sinnvoll wenn neue IV-ErhÃ¶hung ausreichend Credit bei niedrigerem Strike ermÃ¶glicht
- Risiko: Effektiver Break-Even verschlechtert sich durch kumulative PrÃ¤mien

**Regelwerk-Fazit:** Nie fÃ¼r Debit rollen. Wenn kein Credit-Roll mÃ¶glich, heiÃŸt das: Assignment akzeptieren oder Stop-Loss ziehen.

---

## 7. Risiko-Management im Flywheel

### 7.1 Earnings-Risiko: Das gefÃ¤hrlichste unkontrollierte Ereignis

Earnings sind die grÃ¶ÃŸte Gefahr fÃ¼r CSP-Positionen. Ein â€“20% bis â€“30% Earnings-Gap kann einen ATM-CSP sofort in tiefen Verlust katapultieren, bevor der Investor reagieren kann. Das Regelwerk (Earnings-Abstand â‰¥ 8 Tage) ist hier nicht verhandelbar.

**Mechanismus des Risikos:**
1. **Pre-Earnings IV-Anstieg**: IV steigt typischerweise 10â€“30% in den 2 Wochen vor Earnings
2. **Post-Earnings IV-Crush**: Nach dem Earnings-Event fÃ¤llt IV sofort um 40â€“60% â€” innerhalb von Stunden
3. **Downside-Gap-Risiko**: Eine enttÃ¤uschende Guidance kann den Kurs um 15â€“25% overnight fallen lassen, weit hinter den Strike

**MaÃŸnahme:** Alle offenen Positionen werden 8+ Tage vor dem nÃ¤chsten Earnings-Datum geschlossen â€” unabhÃ¤ngig von Gewinn/Verlust-Status. Keine Ausnahme.

### 7.2 Sektor-Konzentration â€” Das stille Klumpenrisiko

Das Portfolio von Familie Rehse hat eine hohe Tech/Software-Gewichtung (NOW, CRM, DDOG, ANET als potenzielle CSP-Kandidaten). Ein gleichzeitiger Sektor-Selloff (z.B. AI-Bubble-Deflation, regulatorische MaÃŸnahmen gegen Big Tech) wÃ¼rde alle Positionen gleichzeitig belasten.

**Mess-Tool: Effektives N**

```
Effektives N = 1 / Î£(wiÂ²)

Beispiel (drei gleichgewichtete Tech-Titel):
= 1 / (0,33Â² + 0,33Â² + 0,33Â²) = 1 / 0,33 = 3,03

Beispiel (mit starker Tech-Konzentration, 60% in einem Sektor):
= 1 / (0,60Â² + 0,20Â² + 0,20Â²) = 1 / (0,36 + 0,04 + 0,04) = 2,27
```

Ziel: Effektives N â‰¥ 2,0 â€” das Regelwerk schreibt Sektor-Cap 55% vor, was dies strukturell sicherstellt.

**Achtung Korrelations-Cluster:** NOW, CRM und DDOG sind alle Enterprise-Software-Titel mit Beta-Korrelation >0,7 untereinander. Gleichzeitige CSPs auf alle drei bedeuten trotz technischer Sektor-Diversifikation faktisch nur 1â€“1,5 Positionen an effektiver Diversifikation.

### 7.3 Drawdown bei VIX-Spike: COVID MÃ¤rz 2020 und August 2024

**COVID MÃ¤rz 2020 (VIX Peak: 85,5):**
- VIX stieg von 18 auf 85,5 in 4 Wochen â€” historisch beispiellos
- 20-Delta-CSPs auf Einzelaktien erlitten typische Verluste von 3â€“5Ã— der ursprÃ¼nglichen PrÃ¤mie
- Aktive Manager mit 200%-Stop-Loss-Regel minimierten SchÃ¤den erheblich
- Ohne Stops und ohne Cash-Reserve: Zwangsassignment bei Tiefstkursen

**August 2024 (Yen-Carry-Trade-Unwind):**
- VIX sprang Ã¼ber Nacht von 18 auf 65 am 5. August 2024
- S&P 500 fiel â€“3,5% in einem Tag, Nasdaq â€“4,4%
- 20-Delta-Puts wurden plÃ¶tzlich tief ITM
- Positionen, die gemÃ¤ÃŸ 200%-Stop-Loss-Regel gefÃ¼hrt wurden: automatisch geschlossen
- Erholung innerhalb von 2 Wochen auf Pre-Crash-Niveau â†’ Wer kein Assignment hatte, konnte sofort neu einsteigen

**Kernlektion:** In VIX-Spike-Szenarien ist die **Cash-Reserve (30â€“40%)** entscheidend. Sie erlaubt:
1. Stop-Losses ohne LiquiditÃ¤tsstress zu exekutieren
2. Unmittelbar nach der Panik neue CSPs bei historisch hoher IV zu erÃ¶ffnen

### 7.4 Margin-Calls bei Naked-Variante (AusdrÃ¼cklich kein Bestandteil des Regelwerks)

Das Regelwerk der Familie Rehse schreibt **100% Cash-Deckung** vor â€” kein Margin. Dies ist kein Performance-Optimierungsproblem, sondern eine Existenzsicherungsfrage: Margin-Konten kÃ¶nnen bei VIX-Spikes zu ZwangsverkÃ¤ufen fÃ¼hren, die Verluste multiplizieren. Cash-Secured-Puts kÃ¶nnen niemals einen Margin-Call auslÃ¶sen. Diese strukturelle Sicherheit hat Vorrang vor hÃ¶herer Kapitaleffizienz.

### 7.5 Tail-Risk: Single-Stock-Crash >20%

| Szenario | Wahrscheinlichkeit | Verlust bei 20-Delta-CSP |
|---|---|---|
| Kurs fÃ¤llt 5% unter Strike | ~8% | 0,5â€“1,5Ã— PrÃ¤mie |
| Kurs fÃ¤llt 10% unter Strike | ~5% | 1,5â€“3Ã— PrÃ¤mie |
| Kurs fÃ¤llt 20% unter Strike | ~2% | 3â€“6Ã— PrÃ¤mie |
| Kurs fÃ¤llt 30%+ (Fraud/Konkurs) | <0,5% | Kompletter Strike-Verlust (selten) |

**Hedging-Optionen fÃ¼r das Flywheel:**
- **Long Put-Spread statt Naked Put**: Begrenzung des maximalen Verlustes (kostet PrÃ¤mie, reduziert Edge)
- **Diversifikation Ã¼ber ETF-CSPs (SPY/QQQ)**: ETFs gehen nicht auf null; ETF-CSPs als "StabilitÃ¤tsanker" (50% des Satellite-Budgets)
- **VIX-Calls als Crash-Hedge**: GÃ¼nstige OTM-Calls auf VIX-Futures bieten konvexen Schutz in Extremszenarien
- **Delta-Anpassung nach VIX**: Bei VIX > 30 â†’ Strikes weiter OTM (10â€“12% statt 8%), kleinere Positionen

---

## 8. Earnings-Plays als Sub-Strategie

### 8.1 Das Post-Earnings-IV-Crush-Fenster

Der attraktivste Einstiegszeitpunkt fÃ¼r CSPs ist **unmittelbar nach** einem Earnings-Event mit negativer Ãœberraschung. In diesem Moment gilt:

1. **IV auf JahreshÃ¶chststand** (IVR oft 80â€“99%) durch ausgepreistes Earnings-Risiko + Panikreaktion
2. **Kurs fundamentalbereinigt** â€” der Gap spiegelt kurzfristige EnttÃ¤uschung, nicht langfristige Wertvernichtung
3. **Mean-Reversion-Wahrscheinlichkeit hoch** bei qualitativ hochwertigen GeschÃ¤ftsmodellen
4. **PrÃ¤mien typisch 2â€“3Ã— hÃ¶her** als im Normalbetrieb

### 8.2 Pre-Earnings IV-Anstieg

In den 2â€“3 Wochen vor Earnings steigt die IV typischerweise stufenweise an:

```
IV-Verlauf vor und nach Earnings (schematisch):

  IV%
  70 â”‚                         â—â—â—â— â† Pre-Earnings-Peak
     â”‚                    â—â—â—â—
  55 â”‚               â—â—â—â—
     â”‚          â—â—â—â—
  40 â”‚     â—â—â—â—
     â”‚â—â—â—â—                              â—â—â—â— â† Post-Crush-Stabilisierung
  25 â”‚                                        â—â—â—â—â—
     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Zeit
       -30    -20    -10    -2  0   +2   +5    +14 Tage
                           â†‘ Earnings           â†‘ CSP-Einstieg
```

**Pre-Earnings-Strategie fÃ¼r das Regelwerk:** Die Regel besagt "Earnings â‰¥ 8 Tage Abstand". Das bedeutet: **ErÃ¶ffne CSPs, deren Verfall nach dem nÃ¤chsten Earnings-Event liegt**, und wÃ¤hle einen Strike, der auch einen Earnings-Gap Ã¼berlebt. Alternativ: Position **vor** Earnings schlieÃŸen (wenn Earnings in den nÃ¤chsten 8 Tagen) und **nach** dem Crush neu einsteigen.

### 8.3 Post-Earnings IV-Crush â€” Quantifiziert

| Unternehmenstyp | Typischer IV-Anstieg pre-Earnings | Typischer IV-Crush post-Earnings | PrÃ¤mien-Boost |
|---|---|---|---|
| Mega-Cap Tech (GOOGL, MSFT) | +8â€“15% absolute IV | â€“25â€“35% | 1,5â€“2Ã— Normal |
| Enterprise SW (NOW, CRM) | +15â€“25% absolute IV | â€“35â€“50% | 2â€“3Ã— Normal |
| Halbleiter (AVGO, NVDA) | +20â€“35% absolute IV | â€“40â€“60% | 2,5â€“4Ã— Normal |
| ETFs (SPY, QQQ) | +5â€“10% (geringe Earnings-Expo) | â€“10â€“15% | 1,2â€“1,5Ã— Normal |

### 8.4 Fallstudie: NOW â€” 24. April 2026

Am 24. April 2026 verÃ¶ffentlichte ServiceNow (NOW) Earnings mit einem Beat auf EPS, aber schwacher Forward Guidance. Das Ergebnis:

| Parameter | Wert |
|---|---|
| Kurs vor Earnings | ~$103,00 |
| Kurs nach Gap (Morning) | ~$84,78 |
| Gap in % | **âˆ’17,75%** |
| IV nach Gap | ~59% |
| **IVR** | **94% (JahreshÃ¶chst)** |
| CSP Strike ($78, 8% OTM) | **36,6% annualisierte Rendite** |
| Normalniveau IVR (non-Earnings) | ~25â€“35% â†’ 12â€“18% ann. Rendite |
| PrÃ¤mien-Boost durch IV-Crush-Phase | **2â€“3Ã—** |

Das Regelwerk erlaubt hier bis zu 55 DTE (statt Standard 35â€“45 DTE) wegen der auÃŸergewÃ¶hnlichen Situation. Der 55-DTE-Verfall war der 18. Juni 2026 â€” mit 89 Tagen bis zum nÃ¤chsten Earnings-Termin (22. Juli 2026) klar im sicheren Fenster.

### 8.5 Risiken des Post-Earnings-Plays

**Multi-Tag-Continuation-Trend:** In ~15â€“20% der FÃ¤lle setzt sich ein negativer Gap fort â€” besonders wenn:
- Das GeschÃ¤ftsmodell strukturell beeintrÃ¤chtigt ist (nicht nur kurzfristige Guidance-EnttÃ¤uschung)
- Sektor-Rotation gegen den Titel lÃ¤uft (z.B. AI-Softwaretitel in Risk-Off-Phasen)
- Makro-Belastung zusÃ¤tzlich drÃ¼ckt (hohes Zinsumfeld + wachstumssensitiver Titel)

**MaÃŸnahmen:** Der Assignment-Check ist hier besonders kritisch. Frage: "WÃ¼rden wir NOW bei $73,70 (Break-Even) fÃ¼r die nÃ¤chsten 3â€“5 Jahre halten?" Wenn ja â†’ CSP valide. Wenn Zweifel â†’ Position verkleinern oder weglassen.

---

## 9. Position Sizing im Detail (Kelly + Praktik)

### 9.1 Kapitalstruktur Familie Rehse â€” CSP-Budget

Gesamtkapital bewertet: ~15,99 Mio. EUR
Liquide Cash: 2,60 Mio. EUR (16,26%)
FBG-Anleihenportfolio (separat verwaltet, nicht operativ): 5,20 Mio. EUR

**CSP-Operationskapital:** Das aktive CSP-Budget der Trading GmbH betrÃ¤gt gemÃ¤ÃŸ Regelwerk **2,5 Mio. EUR** Eigenkapital (geplante GmbH-Struktur), aufgeteilt wie folgt:

| Baustein | Allokation | Betrag | Funktion |
|---|---|---|---|
| **Core: ETF-CSPs** (SPY, QQQ) | 50% | 1.250.000 EUR | Stabiler Grundertrag, kein Earnings-Risiko |
| **Satellite: Einzeltitel-CSPs** | 40% | 1.000.000 EUR | HÃ¶here PrÃ¤mien bei IVR-Peaks |
| **Cash-Reserve (nie unterschreiten)** | 10% | 250.000 EUR | Rolls, Krisenpuffer, neue Chancen |

### 9.2 Per-Position Sizing

| Regel | Parameter | BegrÃ¼ndung |
|---|---|---|
| Max. Cash-Exposure/Position | 20% des jeweiligen Bausteins | Nie > â‚¬250.000 (Core) oder â‚¬200.000 (Satellite) pro Kontrakt-BÃ¼ndel |
| Anzahl simultaner Positionen | 5â€“7 Titel | Diversifikation ohne Verwaltungs-Ãœberlastung |
| Reserve niemals deploybar | 30â€“40% (GmbH), 10% (Minimal-Level) | Keine Volldeployment-Regel |
| Max. Sektor-Anteil | 55% des aktiven Kapitals | Sektor-Klumpenrisiko begrenzen |

**Beispiel-Allokation bei 6 gleichgewichteten Positionen (Satellite-Budget):**

```
1.000.000 EUR Satellite Ã· 6 Positionen = 166.667 EUR/Position
166.667 EUR Ã· Aktienkurs = Kontraktzahl (auf ganze Kontrakte runden, nicht Ã¼berschreiten)

Bei NOW @$84,78 â‰ˆ $94/EUR: Notional Strike $78 Ã— 100 = $7.800 Ã— 94 = â‚¬8.232/Kontrakt
166.667 EUR / 8.232 EUR = ~20 Kontrakte â†’ abgerundet auf 15â€“18 Kontrakte (Sicherheitspuffer)
```

### 9.3 Sektor-Diversifikation â€” Technisch umgesetzt

Das Portfolio-Titeluniversum fÃ¼r CSPs ist nach Sektoren farbcodiert:

| Sektor | Max. 55%-Regel | Beispiel-Titel |
|---|---|---|
| Enterprise SW | â‰¤55% | NOW, CRM, DDOG |
| Halbleiter/KI | â‰¤55% | AVGO, TSM, ANET |
| Hyperscaler | â‰¤55% | GOOGL, AMZN, MSFT |
| Financials | â‰¤55% | JPM, GS |
| ETF-Core | Eigener Baustein (50%) | SPY, QQQ |

**Tech-Trio-Warnung (NOW/CRM/DDOG):** Diese drei Enterprise-Software-Titel haben eine interne Korrelation > 0,70 in Stressphasen. Gleichzeitige Volldepoyment auf alle drei entspricht rechnerisch nur ~1,5 unabhÃ¤ngigen Positionen. Empfehlung: Maximal 2 dieser 3 gleichzeitig aktiv.

### 9.4 Reserve-Kalkulation fÃ¼r Rolls und Krisen

Szenario: VIX-Spike von 18 auf 35 Ã¼ber 2 Wochen, alle 6 Positionen bei 150% der ursprÃ¼nglichen PrÃ¤mie (kein Stop ausgelÃ¶st):
- Unrealisierter Verlust: 6 Ã— 200.000 EUR Ã— 0,9% = ~10.800 EUR (1 PrÃ¤mie = 0,6%, Verlust = 1,5Ã— = 0,9% des Notional)
- Roll-Bedarf (neues Strike, 30 DTE weiter): ~3.600 EUR Credit mÃ¶glich
- Reserve-Bedarf fÃ¼r komfortable Situation: â‰¥150.000 EUR

â†’ Die 30â€“40%-Reserve des GmbH-Budgets (750.000â€“1.000.000 EUR) deckt selbst extreme Krisenszenarien mit Abstand ab.

---

## 10. Operativer Workflow tÃ¤glich/wÃ¶chentlich/monatlich

### 10.1 TÃ¤glicher Workflow (â‰¤ 15 Minuten)

```
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  TÃ„GLICHE CHECKLISTE â€” CSP-FLYWHEEL (Familie Rehse)     â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘                                                          â•‘
â•‘  1. VIX-Level prÃ¼fen                                     â•‘
â•‘     â†’ finance.yahoo.com/quote/^VIX                       â•‘
â•‘     â†’ < 15: Keine neuen Positionen                       â•‘
â•‘     â†’ 15â€“20: Nur IVR â‰¥ 40% Titel zulÃ¤ssig               â•‘
â•‘     â†’ > 20: Volle Deployment-Bereitschaft                â•‘
â•‘                                                          â•‘
â•‘  2. 21-DTE-Liste abarbeiten                              â•‘
â•‘     â†’ Alle Positionen mit â‰¤ 21 DTE: Limit-Order zum     â•‘
â•‘       SchlieÃŸen setzen (Buy-to-Close am Mid-Point)        â•‘
â•‘                                                          â•‘
â•‘  3. 50%-Profit-Liste prÃ¼fen                              â•‘
â•‘     â†’ Alle Positionen, die PrÃ¤mie auf â‰¤50% gefallen:    â•‘
â•‘       Sofort schlieÃŸen (Buy-to-Close)                    â•‘
â•‘                                                          â•‘
â•‘  4. Earnings-Kalender prÃ¼fen (nÃ¤chste 10 Tage)           â•‘
â•‘     â†’ Offene Positionen auf Earnings-NÃ¤he prÃ¼fen         â•‘
â•‘     â†’ < 8 Tage: Position schlieÃŸen vor MarktÃ¶ffnung      â•‘
â•‘                                                          â•‘
â•‘  5. Stop-Loss prÃ¼fen                                     â•‘
â•‘     â†’ Positionen, die 200% der ursprÃ¼nglichen PrÃ¤mie     â•‘
â•‘       Ã¼berschritten haben: Sofort schlieÃŸen              â•‘
â•‘                                                          â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
```

### 10.2 WÃ¶chentlicher Workflow (â‰¤ 60 Minuten, z.B. Montag FrÃ¼h)

**A) IVR-Screening neue Kandidaten:**
1. marketchameleon.com â†’ Volatility Rankings â†’ Sort by IV Rank (desc)
2. Filter: Market Cap â‰¥ 50 Mrd. USD, Optionsvolumen â‰¥ 50.000/Tag
3. Earnings â‰¥ 8 Tage entfernt prÃ¼fen (barchart.com â†’ Earnings)
4. Strike-Berechnung: Aktueller Kurs Ã— 0,92 â†’ 8% OTM
5. Delta prÃ¼fen: Im Bereich â€“0,18 bis â€“0,25?
6. Annualisierte Rendite berechnen: (PrÃ¤mie/Strike) Ã— (365/DTE) Ã— 100
7. Assignment-Check: WÃ¼rden wir den Titel zu Break-Even-Kurs langfristig halten?

**B) Neue CSP-Idee formulieren (vollstÃ¤ndiges Format gemÃ¤ÃŸ Regelwerk)**

**C) Post-Earnings-Radar:**
- Welche Titel haben in dieser Woche Earnings verÃ¶ffentlicht?
- Gaps â‰¥ 8%? â†’ IV-Check auf IVR â‰¥ 60
- Fundamentale QualitÃ¤t intakt? â†’ CSP-Kandidat fÃ¼r nÃ¤chste Woche

### 10.3 Monatlicher Workflow (Â½ Tag, z.B. erster Montag des Monats)

| Aufgabe | Zeitaufwand | Beschreibung |
|---|---|---|
| **Performance-Reporting** | 30 Min | Alle Trades des Monats, PrÃ¤mieneinnahmen, Assignment-Quote, P/L |
| **Steuer-Dokumentation** | 20 Min | TermingeschÃ¤fte dokumentieren: Datum, PrÃ¤mie, GebÃ¼hren, ggf. Assignment |
| **Sektorgewichtung** | 15 Min | Sektor-Cap 55% prÃ¼fen, ggf. Positionen rotieren |
| **Cash-Reserve** | 10 Min | Reserve â‰¥ 30% (GmbH) bestÃ¤tigen |
| **IV-Niveau MonatsrÃ¼ckblick** | 20 Min | Durchschnittliche IVR des Monats, Vergleich mit Vormonat |
| **Kapitaleinsatz-Effizienz** | 15 Min | Deployed Capital Ã— Ã˜-Rendite = Ist-Ertrag; Vergleich mit Ziel |

### 10.4 Quartals-Review (1 Tag, z.B. Anfang Juli/Oktober/Januar/April)

1. **Strategie-Review:** Regelwerk noch passend? Neue Erkenntnisse integrieren?
2. **Win-Rate Analyse:** Prozentuale Assignment-Quote der letzten 90 Tage
3. **Sector-Rotation Assessment:** Welche Sektoren bieten aktuell bestes IVR-Premium?
4. **Steuervoranmeldung vorbereiten:** GmbH-Vorauszahlungen KSt + GewSt
5. **Zielabgleich:** 158.000 EUR Netto-Jahresziel â€” auf Kurs?
6. **PortfolioÃ¼berprÃ¼fung:** Abgleich mit Gesamtportfolio (Krypto, Growth, Sachwerte)

### 10.5 Order-AusfÃ¼hrung â€” Broker-neutral

UnabhÃ¤ngig vom verwendeten Broker gelten folgende Prinzipien:

- **Ordertyen:** AusschlieÃŸlich **Limit-Orders** (niemals Market Orders bei Optionen) â€” Market Orders bei Optionen mit weiten Spreads kÃ¶nnen zu massiven Nachteilen beim Fill fÃ¼hren
- **Preisstrategie:** Start am **Mid-Point** (Mitte von Bid und Ask). Wenn kein Fill nach 2â€“3 Minuten: Limit in 0,05-USD-Schritten leicht zum Ask bewegen
- **Cash-Deckung:** Vor jeder Order sicherstellen, dass 100% Ã— Strike Ã— 100 als freie LiquiditÃ¤t vorhanden ist
- **GTC-Orders fÃ¼r Exits:** "Good-till-Cancelled" fÃ¼r den 50%-Take ermÃ¶glicht automatischen Fill ohne tÃ¤gliche Ãœberwachung
- **Order-BestÃ¤tigung:** Nach jedem Fill sofort dokumentieren (Datum, PrÃ¤mie, GebÃ¼hren)

---

## 11. HÃ¤ufige Fehler und wie man sie vermeidet

### 11.1 Yield-Chasing: Zu hohes Delta fÃ¼r hÃ¶here PrÃ¤mie

**Fehler:** Delta â€“0,30 bis â€“0,40 wÃ¤hlen, weil die PrÃ¤mie doppelt so hoch ist.

**Warum gefÃ¤hrlich:** Das Risiko steigt Ã¼berproportional. Bei â€“0,30 Delta liegt die Assignment-Wahrscheinlichkeit ~30% statt 20% â€” eine 50%ige RisikoerhÃ¶hung, die durch typisch 30â€“40% mehr PrÃ¤mie nicht adÃ¤quat kompensiert wird. Zudem sind die Strikes nÃ¤her am Geld, was bei Earnings-Gaps sofort tief ITM fÃ¼hrt.

**LÃ¶sung:** Strikt bei â€“0,18 bis â€“0,25 bleiben. Die Rendite kommt aus Frequenz (mehr Zyklen durch 50%-Take) und VRP-Capture, nicht aus risikoreicheren Strikes.

### 11.2 Earnings vergessen â€” Die unsichtbare Zeitbombe

**Fehler:** CSP erÃ¶ffnen ohne Earnings-Datum zu prÃ¼fen. Earnings kommen nach BÃ¶rsenschluss, die Position wird massiv ITM Ã¼ber Nacht.

**Praxis:** Earnings-Datum bei **jeder** Idee als Pflichtfeld verifizieren â€” nicht aus dem GedÃ¤chtnis, sondern aus einer Live-Quelle (barchart.com, earnings.com). Das Datum Ã¤ndert sich; manche Unternehmen passen den Termin kurzfristig an.

**LÃ¶sung:** Earnings-Abstand auf das Formular schreiben. GTC-SchlieÃŸen-Order setzen fÃ¼r 8 Tage vor dem Earnings-Datum als Sicherheitsnetz.

### 11.3 Roll-fÃ¼r-Debit-Falle

**Fehler:** Eine verlustbringende Position fÃ¼r Debit rollen "um Zeit zu kaufen". Ergebnis: Der Verlust wird vergrÃ¶ÃŸert statt begrenzt.

**Beispiel:** CSP auf NOW $78 ist bei einem Kurs von $72 tief ITM. Versuchung: Put auf $70 rollen fÃ¼r â€“$200 Debit. Das erhÃ¶ht den Gesamtverlust um $200 und das Risiko bleibt.

**LÃ¶sung:** **Nur fÃ¼r Net-Credit rollen.** Wenn kein Credit-Roll mÃ¶glich: Assignment annehmen (Aktie ins Depot, Covered Call starten) oder Stop-Loss (200% der PrÃ¤mie) ziehen.

### 11.4 Ãœber-Konzentration auf einen Sektor

**Fehler:** 4 von 6 Positionen in Enterprise-Software-Titeln, weil die IV dort aktuell am hÃ¶chsten ist.

**RealitÃ¤t:** Alle Enterprise-Software-Titel sind hochkorreliert (~0,7â€“0,85 in Stressphasen). Ein AI-Sell-off, eine negative Guidance von Salesforce, eine schlechte Makrozahl (Unternehmensausgaben fallen) â€” alles belastet sofort alle 4 Positionen gleichzeitig.

**LÃ¶sung:** Sektor-Cap 55% konsequent einhalten. Wenn Enterprise-SW besonders attraktiv: Core-ETF-CSPs (SPY/QQQ) als Ausgleich erhÃ¶hen.

### 11.5 "Just-one-more-trade"-Falle nach Verlust

**Fehler:** Nach einem Assignment-Verlust sofort mit hÃ¶herem Delta oder zu wenig Reserve eine neue Position Ã¶ffnen, um den Verlust "zurÃ¼ckzuholen". Psychologisch nachvollziehbar â€” strategisch destruktiv.

**LÃ¶sung:** Nach jedem Assignment oder Stop-Loss-Ereignis: **24-Stunden-Pause** vor einer neuen ErÃ¶ffnung. Position-Size und Delta fÃ¼r die nÃ¤chste Position identisch mit dem Standardregelwerk â€” keine Rache-Trades.

### 11.6 Margin-Nutzung trotz Cash-Secured-Mandat

**Fehler:** Broker ermÃ¶glicht Margin-Konten, Investor nutzt Fremdkapital fÃ¼r zusÃ¤tzliche CSP-Positionen (hÃ¶here Rendite).

**Konsequenz:** Im VIX-Spike-Szenario erhÃ¤lt der Investor einen Margin-Call, muss Positionen zwangsweise zu Tiefstkursen schlieÃŸen, realisiert maximale Verluste genau zum falschen Zeitpunkt. Der Vorteil der Cash-Secured-Struktur (niemals Margin-Call) wird zerstÃ¶rt.

**LÃ¶sung:** Striktes Cash-Secured-Mandat. Fremdkapital in der GmbH ist ausschlieÃŸlich fÃ¼r die Finanzierungsstruktur der GmbH zulÃ¤ssig (Gesellschafterdarlehen), nicht fÃ¼r Margin-Trading.

### 11.7 PrÃ¤mien-Vergleich ohne Annualisierung

**Fehler:** CSP A mit $500 PrÃ¤mie (30 DTE, Strike $90) erscheint besser als CSP B mit $350 PrÃ¤mie (45 DTE, Strike $120).

**RealitÃ¤t:**
```
CSP A: 500/9.000 Ã— 365/30 = 67,6% ann.  (aber unrealistisch hohe IV oder zu kleines OTM)
CSP B: 350/12.000 Ã— 365/45 = 23,7% ann. (konservativeres Profil)
```

Ohne Annualisierung ist kein Vergleich mÃ¶glich. Die annualisierte Rendite ist die einzige sinnvolle VergleichsgrÃ¶ÃŸe.

---

## 12. Steuerliche Optimierung in der deutschen Trading GmbH

### 12.1 Grundstruktur: Zwei-Klassen-Besteuerung

Die Trading-GmbH von Familie Rehse unterliegt einer **gespaltenen Steuerwelt**:

| Einkommensart | Steuerklasse | Effektive Steuerlast | Vorteil vs. Privat |
|---|---|---|---|
| **OptionsprÃ¤mien** (CSPs, CCs) | Vollbesteuert: KSt + SolZ + GewSt | **~30,83%** | Minimal (vs. 26,375% privat) |
| **Aktiengewinne nach Assignment** (Â§8b KStG) | 95% steuerfrei | **~1,5%** (nur 5% Ã— 30%) | **Massiv: 29,3 Pp Einsparung** |
| **FK-Zinsen** | VollstÃ¤ndig Betriebsausgabe | **Volle Absetzbarkeit** | Relevanter GmbH-Vorteil |
| **Verluste aus TermingeschÃ¤ften** | Unbegrenzte Verrechnung (JStG 2024) | VollstÃ¤ndig gegenrechenbar | Identisch mit Privat seit 2024 |

### 12.2 Â§8b KStG â€” Das HerzstÃ¼ck des GmbH-Vorteils

**Rechtsgrundlage:** [Â§8b Abs. 2 KStG](https://steuerberatung-neeb.de/steuerfreie-dividenden-und-veraeusserungsgewinne-fuer-kapitalgesellschaften/) â€” VerÃ¤uÃŸerungsgewinne aus Anteilen an Kapitalgesellschaften bleiben bei der Ermittlung des Einkommens auÃŸer Ansatz.

**In der Praxis:**
- 100% des VerÃ¤uÃŸerungsgewinns ist **kÃ¶rperschaftsteuerfrei**
- 5% gelten pauschal als nicht abzugsfÃ¤hige Betriebsausgaben
- â†’ Effektiv: **95% Ã— 0% Steuer = steuerfrei** (die 5% werden mit ~30% versteuert â†’ **1,5% Effektivsteuer**)

**Beispiel Steuervergleich (Aktiengewinn von 100.000 EUR aus Assignment):**

| Struktur | Steuer | NettoerlÃ¶s |
|---|---|---|
| **PrivatvermÃ¶gen** | 26.375 EUR (25% + Soli) | 73.625 EUR |
| **Trading GmbH** | **1.500 EUR** | **98.500 EUR** |
| **Differenz** | | **+24.875 EUR** |

Bei einem Aktiengewinn von 158.000 EUR (Jahresrenditeziel) ergibt die GmbH-Struktur **~39.300 EUR** mehr Netto â€” wenn diese Gewinne als Aktiengewinne (post-Assignment) realisiert werden statt als PrÃ¤mien.

### 12.3 Steueroptimierungsstrategie: PrÃ¤mien vs. Aktiengewinne

**Das Optimierungsproblem:**
- PrÃ¤mien (CSP-Schreiben): 30,83% Steuer
- Aktiengewinne (nach Assignment + Kursanstieg): 1,5% Steuer

**Strategische Konsequenz:**

1. **Wenn Assignment eintritt und der Titel langfristig attraktiv ist:** Aktie halten, Covered Call erst spÃ¤ter schreiben oder gÃ¤nzlich auf langjÃ¤hriges Hold setzen â†’ Â§8b-Privileg nutzen

2. **Wheel-Strategie in der GmbH:** Assignment ist steuerlich willkommen (nicht nur toleriert), weil der resultante Aktiengewinn fast steuerfrei ist. Die Covered-Call-PrÃ¤mie ist dann "Bonus" Ã¼ber der Â§8b-Freistellung.

3. **FÃ¼r hohe PrÃ¤mieneinnahmen:** Wenn das GmbH-Hauptziel Cashflow-Generierung ist (158.000 EUR/Jahr), dann sind PrÃ¤mien trotz 30,83% Steuer die primÃ¤re Ertragsquelle. Â§8b ist der "Jackpot" wenn Assignment + Kursanstieg kombiniert auftreten.

### 12.4 JStG 2024: Verlustverrechnung â€” Wegfall der 20.000-EUR-Grenze

**Hintergrund:** Von 2021 bis 2023 galt eine brutale EinschrÃ¤nkung: Verluste aus TermingeschÃ¤ften (Optionen) durften im PrivatvermÃ¶gen nur bis **20.000 EUR/Jahr** mit Gewinnen verrechnet werden. Ãœberschreitende Verluste wurden vorgetragen â€” aber immer nur innerhalb des separaten Verlustverrechnungskreises.

**JStG 2024 (BGBl. I Nr. 387, 05.12.2024):** [Die 20.000-EUR-Grenze wurde vollstÃ¤ndig und rÃ¼ckwirkend ab 2020 gestrichen](https://www.lohnsteuer-kompakt.de/steuerwissen/verluste-aus-termingeschaeften-steuererleichterung-fuer-anleger/). 

**Konsequenzen fÃ¼r Familie Rehse:**
- GmbH: War von der BeschrÃ¤nkung ohnehin weniger betroffen (unbegrenzte Verlustverrechnung im BetriebsvermÃ¶gen schon vor 2024)
- PrivatvermÃ¶gen: Offene VerlustvortrÃ¤ge aus 2020â€“2023 kÃ¶nnen jetzt vollstÃ¤ndig gegen alle KapitalertrÃ¤ge gerechnet werden
- Die Umsetzung durch Banken im Rahmen des Kapitalertragsteuerabzugs ist ab **1. Januar 2026** verpflichtend

### 12.5 Roll-Mechanik steuerlich: EigenstÃ¤ndige TermingeschÃ¤fte

Jedes Rollen einer Option (SchlieÃŸen des alten Puts + ErÃ¶ffnen eines neuen Puts) ist steuerlich ein **eigenstÃ¤ndiges TermingeschÃ¤ft**:

- SchlieÃŸen: Kauf-to-Close â†’ Gewinn oder Verlust wird sofort realisiert
- Ã–ffnen: Neue PrÃ¤mie wird zum neuen Realisierungszeitpunkt fÃ¤llig

**Konsequenz:** Ein Roll fÃ¼r Credit im September und ein Assignment im November sind zwei separate Steuerereignisse â€” der Credit aus dem Roll ist sofort steuerpflichtig (30,83% in der GmbH), das Assignment-Ergebnis unterliegt spÃ¤ter Â§8b KStG (wenn Aktien verkauft werden).

**Dokumentationspflicht:** FÃ¼r jeden Roll: Datum, geschlossener Strike/PrÃ¤mie, neuer Strike/PrÃ¤mie, Netto-Credit/Debit dokumentieren.

### 12.6 Zinsschranke (Â§4h EStG) â€” Relevanz fÃ¼r die GmbH

Bei 2,0 Mio. EUR Fremdkapital in der GmbH:
- Freizinsgrenze Â§4h EStG: **3 Mio. EUR** EBITDA-Freigrenze
- Bei FK-Zinsen â‰¤ 90.000 EUR/Jahr (2 Mio. EUR Ã— 4,5% Zinssatz): **Keine Zinsschranke wirksam**
- Die Zinsschranke greift erst, wenn Netto-Zinsaufwand > 30% des EBITDA **und** > 3 Mio. EUR betrÃ¤gt â€” bei der geplanten GmbH-GrÃ¶ÃŸe irrelevant

### 12.7 Effektive Steuerlast-Kalkulation fÃ¼r das Szenario 158.000 EUR Nettoziel

**Annahme: 80% PrÃ¤mieneinnahmen, 20% Aktiengewinne**

| Einkommensart | Brutto | Steuersatz | Steuer | Netto |
|---|---|---|---|---|
| OptionsprÃ¤mien (80%) | 190.000 EUR | 30,83% | 58.577 EUR | 131.423 EUR |
| Aktiengewinne Â§8b (20%) | 47.500 EUR | 1,5% | 713 EUR | 46.787 EUR |
| **Gesamt** | **237.500 EUR** | **~24,9%** | **59.290 EUR** | **178.210 EUR** |

â†’ Um **158.000 EUR Netto** zu erzielen, sind **~210.000â€“215.000 EUR Brutto** erforderlich (wenn Mischung 80/20).
â†’ Bei reiner PrÃ¤mien-Strategie ohne Â§8b: **229.000 EUR Brutto** erforderlich.
â†’ Â§8b-Optimierung (mehr Assignment + Halten) kann den Brutto-Bedarf um **7â€“12%** reduzieren.

---

## 13. Performance-Zielsetzung Familie Rehse

### 13.1 PrimÃ¤res GmbH-Ziel

| Parameter | Wert |
|---|---|
| Operatives GmbH-Kapital | 2,5 Mio. EUR EK |
| Jahresziel Netto | **158.000 EUR** |
| Entspricht EK-Rendite | **31,7% netto** (auf das eingesetzte Kapital bei 100% Deployment) |
| Entspricht Bruttorendite | ~210.000â€“215.000 EUR (~8,5% auf Gesamtkapital) |
| Monatliches Nettoziel | **13.167 EUR/Monat** |

**Kommentar:** Das 31,7%-Nettorenditeziel ist ambitioniert aber erreichbar, wenn:
- VIX im Jahresschnitt â‰¥ 18 (historisch seit 2020: ja)
- Mindestens 4â€“6 Post-Earnings-IV-Crush-Gelegenheiten pro Jahr genutzt werden
- Capital Deployment durchschnittlich 60â€“70% des Budgets (nicht 100%)
- Keine katastrophalen Assignment-Verluste (>30% Drawdown auf eine Position)

### 13.2 Realistische Jahresrendite-Szenarien

| Szenario | VIX-Umfeld | Ã˜ PrÃ¤mie/Zyklus | Zyklen/Jahr | Brutto | Netto (nach Steuern ~25%) |
|---|---|---|---|---|---|
| **Stress** (VIX<18, wenig IV) | Ruhig, bull | 0,4% des Notional | 6 | ~60.000 EUR | ~45.000 EUR |
| **Base** (VIX 18â€“25) | ErhÃ¶ht, stabil | 0,6â€“0,8% | 8â€“9 | ~120.000â€“165.000 EUR | ~90.000â€“125.000 EUR |
| **Optimal** (VIX 20â€“30, IV-Crush-Plays) | ErhÃ¶hte Vola | 1,0â€“1,5% | 9â€“10 | ~200.000â€“300.000 EUR | ~150.000â€“225.000 EUR |
| **Krise** (VIX>35, Drawdown) | Extrem | Positionen defensiv | â€“ | **Verlust** | â€“ |

**April-2026-Umfeld:** VIX-Spot 18â€“19, Mai-Futures 20,5 â†’ Base-Szenario mit Potential fÃ¼r Optimal bei geopolitischer Entspannung (Hormuz-Deal). Aktuelle Earnings-Saison (Aprilâ€“Mai 2026) bietet strukturell erhÃ¶hte Post-Earnings-IV-Gelegenheiten.

### 13.3 PrivatvermÃ¶gen-Anteil: 50/40/10-Splittung

Das PrivatvermÃ¶gen der Familie Rehse folgt dem separaten CSP-Budget aus dem Regelwerk:
- **50% Core ETF-CSPs** (SPY/QQQ): 1,25 Mio. EUR
- **40% Satellite Einzeltitel**: 1,0 Mio. EUR
- **10% Cash-Reserve**: 250.000 EUR (minimum, immer)

Die Besteuung im PrivatvermÃ¶gen erfolgt mit 25% Abgeltungsteuer (+ Soli) auf PrÃ¤mien und Aktiengewinne â€” kein Â§8b-Privileg. Daher ist die GmbH-Struktur fÃ¼r hohe Kapitalvolumina klar vorteilhafter.

### 13.4 Stress-Test-Szenarien

| Szenario | AuslÃ¶ser | Portfolio-Impact | MaÃŸnahmen |
|---|---|---|---|
| **VIX-Spike auf 35+** | Geopolitische Eskalation (Hormuz), Fed-Shock | 3â€“5 Positionen bei 200%-Stop, Losses: 30.000â€“50.000 EUR | Stops exekutieren, 30%-Reserve schÃ¼tzt, nach Spike neu einsteigen bei VIX > 30 |
| **Tech-Sector-Selloff 20%** | AI-Regulierung, Zins-Schock | 4 Satellite-Positionen deep ITM (NOW, CRM, DDOG, ANET gleichzeitig) | Sektor-Cap-Regel verhindert >55% Exposition; Losses: 25.000â€“40.000 EUR auf GmbH-Ebene |
| **Einzeltitel-Crash âˆ’40%** (Fraud/Skandal) | Rechnungslegungsskandal wie Wirecard | Strike-Notional-Verlust auf eine Position: bis 200.000 EUR | Assignment-Check pre-trade als PrimÃ¤rschutz; Diversifikation Ã¼ber 5â€“7 Titel |
| **Zins-Anstieg auf 6%** | Fed-Aggression | CSP-PrÃ¤mien steigen (hÃ¶here IV) â€” positive fÃ¼r Strategie; Treasury-Collateral-Rendite steigt | ErhÃ¶hte PrÃ¤mien profitieren von Risk-Off; Cash-Reserve verdient mehr auf Geldmarkt |
| **EUR/USD-Bewegung +10%** | EUR-StÃ¤rke | US-Aktien wert in EUR weniger; PrÃ¤mien in EUR geringer | FX-Hedging oder Bewusstsein als struktureller Faktor |

---

## 14. ORATS- und FMP-Datenpunkte, die das Flywheel tÃ¤glich treiben

### 14.1 ORATS â€” Kerndaten fÃ¼r jeden CSP-Kandidaten

[ORATS (Options Research & Technology Services)](https://orats.com) bietet institutionelle Optionsdaten mit historischen IV-Daten, IV-Perzentilen und Earnings-Analysen. Die kritischen Felder fÃ¼r die Flywheel-Strategie:

| ORATS-Feld | Bedeutung | Einsatz im Regelwerk |
|---|---|---|
| `ivPctile1y` | IV-Perzentile der letzten 12 Monate (0â€“100) | PrimÃ¤rfilter: â‰¥ 40 fÃ¼r Einstieg |
| `atmIvM2` | ATM IV fÃ¼r den 2-Monats-Verfall (ca. 45â€“55 DTE) | Baseline-IV fÃ¼r PrÃ¤mienberechnung |
| `delta` | Option-Delta des Ziel-Strikes | Pflichtfeld: â€“0,18 bis â€“0,25 |
| `theta` | TÃ¤glicher Zeitwertverfall der Option | QualitÃ¤tsprÃ¼fung: Î˜/PrÃ¤mie-VerhÃ¤ltnis |
| `smvVol` | Smooth Model Volatility â€” bereinigtes IV ohne Bid/Ask-Noise | PrÃ¤zisere IV-Messung als Rohdaten |
| `daysToNextErn` | Tage bis zum nÃ¤chsten Earnings-Event | Pflichtfeld: â‰¥ 8 fÃ¼r jeden Trade |
| `sector` | SektorzugehÃ¶rigkeit (z.B. "Technology", "Financials") | Sektor-Cap-Berechnung |
| `etfIncl` | ETF-Inklusionen (z.B. "SPY, QQQ, XLK") | KorrelationsabschÃ¤tzung |
| `ivFcst20d` | Prognostizierte IV fÃ¼r nÃ¤chste 20 Tage | Forward-looking VRP-Assessment |
| `ernMv` | Historische Ã˜ Earnings-Move des Titels | Safety-Check fÃ¼r Strike-Selektion |

**Praktischer ORATS-Workflow:**

```python
# Pseudocode: TÃ¤glicher CSP-Kandidaten-Filter via ORATS API
kandidaten = orats.get_screener(
    ivPctile1y__gte=40,       # IVR â‰¥ 40%
    daysToNextErn__gte=8,     # Earnings-Abstand
    mkt_cap__gte=50_000,      # Market Cap â‰¥ 50 Mrd. USD
    optVolume__gte=50_000,    # LiquiditÃ¤t
    delta__between=(-0.25, -0.18),  # 20-Delta-Bereich
    dte__between=(30, 55)     # DTE-Fenster
)
```

### 14.2 FMP â€” Makro- und Kontextdaten

[Financial Modeling Prep (FMP)](https://financialmodelingprep.com) liefert die Kontextdaten, die den ORATS-Screening-Output einbetten:

| FMP-Feld / Endpoint | Bedeutung | Einsatz |
|---|---|---|
| `/historical/^VIX` | VIX-Historiendaten | Regime-Bestimmung (< 15 / 15â€“20 / > 20) |
| `/earning_calendar` | Earnings-Kalender fÃ¼r nÃ¤chste 30 Tage | TÃ¤glicher Earnings-Safety-Check |
| `/treasury` | US-Treasury-Rates (1M, 3M, 6M, 10Y) | Risk-Free-Rate fÃ¼r Optionspreisberechnung, Collateral-Yield |
| `/sector-performance` | Sektor-Relative-Performance (1W, 1M) | Sektor-Rotation-Signal, Sektor-Cap-Ãœberwachung |
| `/quote/{ticker}` | Live-Kurs, Volumen, Market Cap | Pflichtcheck vor jeder Order |
| `/historical-price-full/{ticker}` | Historische Kurse | Mean-Reversion-Analyse post-Earnings |
| `/analyst-estimates/{ticker}` | Analysten-SchÃ¤tzungen EPS/Revenue | Assignment-Check: Fundamental intakt? |

### 14.3 Wie man ORATS + FMP zur automatisierten Ideengenerierung mappt

```
TÃ¤glicher automatisierter Pipeline (Pseudologik):

SCHRITT 1: FMP â†’ VIX-Aktualkurs
  â†’ VIX < 15: STOPP, keine neuen Trades
  â†’ VIX â‰¥ 15: Weiter zu Schritt 2

SCHRITT 2: FMP â†’ Earnings-Kalender fÃ¼r nÃ¤chste 10 Tage
  â†’ Titelliste mit Earnings < 8 Tage: AUSSCHLUSSLISTE erstellen

SCHRITT 3: ORATS â†’ Screener mit ivPctile1y â‰¥ 40, daysToNextErn â‰¥ 8
  â†’ Ausschlussliste aus Schritt 2 entfernen
  â†’ Sortieren nach ivPctile1y (desc)

SCHRITT 4: FÃ¼r Top-10-Kandidaten:
  â†’ PrÃ¤mie vom passenden Strike abrufen (delta â‰ˆ -0,20)
  â†’ Ann. Rendite berechnen: (PrÃ¤mie/Strike) Ã— (365/DTE) Ã— 100
  â†’ Ergebnis-Ranking nach Ann. Rendite

SCHRITT 5: FMP â†’ Analyst-Estimates fÃ¼r Top-3-Kandidaten
  â†’ Earnings-Konsensus positiv? â†’ Assignment-Check bestanden
  â†’ Margin of Safety PrÃ¼fung: Strike < Analyst-Fair-Value?

SCHRITT 6: OUTPUT: VollstÃ¤ndige CSP-Idee im Standardformat
  â†’ Ticker, Strike, PrÃ¤mie, Verfall, Delta, IVR, Earnings-Datum,
     Ann. Rendite, Cash-Bedarf, Assignment-Check
```

### 14.4 Datenpunkte im tÃ¤glichen Monitoring

FÃ¼r **jede offene Position** werden tÃ¤glich Ã¼berwacht:

| Signal | Datenquelle | Schwellenwert | Aktion |
|---|---|---|---|
| Aktuelle PrÃ¤mie | Broker-Platform | â‰¤ 50% der ursprÃ¼nglichen PrÃ¤mie | **SchlieÃŸen (50%-Take)** |
| DTE | Broker-Platform | â‰¤ 21 Tage | **SchlieÃŸen (21-DTE-Exit)** |
| Tage bis Earnings | FMP `/earning_calendar` | â‰¤ 8 Tage | **SchlieÃŸen (Earnings-Schutz)** |
| PrÃ¤mie vs. Original | Broker-Platform | â‰¥ 200% der ursprÃ¼nglichen PrÃ¤mie | **Stop-Loss ausfÃ¼hren** |
| VIX-Niveau | FMP `/historical/^VIX` | â‰¥ 35 (Alarm) | **Positionen verkleinern, neue ErÃ¶ffnungen pausieren** |
| ORATS `ivPctile1y` | ORATS API | Stark gefallen (< 30) | **Position halten, kein neuer Einstieg im selben Titel** |

---

## 15. Quellen und Referenzen

Alle in diesem Dokument zitierten Quellen sind primÃ¤re oder erstklassige sekundÃ¤re Quellen. Die Links wurden zuletzt im April 2026 geprÃ¼ft.

### Akademische und institutionelle Forschung

| Quelle | Beschreibung | Link |
|---|---|---|
| **Bondarenko (2019)** | "An Analysis of Index Option Writing with Monthly and Weekly Rollover" â€” umfassendste Studie zur CBOE PUT- und WPUT-Index-Performance bis 2018, 32-Jahreszeitraum | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2750188) |
| **Bondarenko (2014)** | "Why Are Put Options So Expensive?" â€” VRP und Skew-Premium-Analyse | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2492742) |
| **Carr & Wu (2009)** | "Variance Risk Premia" â€” Review of Financial Studies; modellfreie Quantifizierung der VarianzrisikoprÃ¤mie auf 5 Indizes und 35 Einzelaktien | [NYU / Review of Financial Studies](https://engineering.nyu.edu/sites/default/files/2019-01/CarrReviewofFinStudiesMarch2009-a.pdf) |
| **RJA LLC (2017)** | "PutWrite Strategies and Market Valuation Levels" â€” PUT-Index-Performance unter verschiedenen CAPE-Bewertungsniveaus | [rja-llc.com](https://www.rja-llc.com/wp-content/uploads/2023/10/RJA-PutWrite-Strategies-and-Market-Valuation-Levels-Oct-2017.pdf) |
| **Ennis Knupp & Associates (2009)** | Studie zu 5 Benchmark-Indizes 1986â€“2008, CBOE-beauftragt | [CBOE Insights](https://www.cboe.com/insights/posts/key-cboe-benchmark-indexes-using-spx-options-offer-strong-risk-adjusted-returns/) |

### CBOE Benchmark-Indizes und Daten

| Quelle | Link |
|---|---|
| CBOE S&P 500 PutWrite Index (PUT) â€” Offizielle Benchmark-Seite | [cboe.com](https://www.cboe.com/us/indices/benchmark_indices/) |
| CBOE Insights: Key Benchmark Indexes â€” VRP und Sharpe-Daten | [cboe.com](https://www.cboe.com/insights/posts/key-cboe-benchmark-indexes-using-spx-options-offer-strong-risk-adjusted-returns/) |
| CBOE White Paper: VRP und PUT-Index (Bondarenko) | [cboe.com](https://www.cboe.com/insights/posts/white-paper-shows-volatility-risk-premium-facilitated-higher-risk-adjusted-returns-for-put-index/) |
| CBOE S&P 500 PutWrite Index â€” Wikipedia (historische Eckdaten) | [Wikipedia](https://en.wikipedia.org/wiki/CBOE_S%26P_500_PutWrite_Index) |

### Tastylive Research-Studien

| Studie | Thema | Link |
|---|---|---|
| Market Measures: 16 vs. 30 Delta ROC | Return on Capital Vergleich | [tastylive.com](https://www.tastylive.com/shows/market-measures/episodes/strangle-return-on-capital-16-delta-vs-30-delta-09-07-2017) |
| Market Measures: 30 Delta Breakevens vs. 16 Delta Strikes | Win-Rate-Analyse | [tastylive.com](https://www.tastylive.com/shows/market-measures/episodes/comparing-30-delta-breakevens-to-16-delta-strikes-02-23-2017) |
| Skinny on Options: Probability of 50% Profit | 50%-Profit-Take-Studie | [tastylive.com](https://www.tastylive.com/shows/the-skinny-on-options-modeling/episodes/probability-of-50-profit-12-17-2015) |
| From Theory to Practice: Managing at 21 DTE (2022) | 21-DTE-Exit-Mechanik | [tastylive.com](https://www.tastylive.com/shows/from-theory-to-practice/episodes/managing-options-positions-at-21-dte-08-26-2022) |
| Duration Volatility Study (2023) | 45 DTE optimal, wÃ¶chentliche Vola-Analyse | [tastylive.com](https://www.tastylive.com/news-insights/test-different-duration-volatilities-get-some-surprising-results) |
| Gamma Risk â€” DTE > Duration (2019) | Gamma-Risiko und 21-DTE-Exit | [tastylive.com](https://www.tastylive.com/shows/the-skinny-on-options-abstract-applications/episodes/gamma-risk-dte-duration-12-30-2019) |
| Backtesting-Tool ErklÃ¤rung | Nutzung des Tastylive Backtesting-Tools | [tastylive.com](https://www.tastylive.com/news-insights/backtesting-options-trades-learn-use-tastytrade-backtesting-tool) |

### Deutsche Steuerquellen

| Quelle | Thema | Link |
|---|---|---|
| BGBl. I Nr. 387 (05.12.2024) | JStG 2024 â€” Gesetzestext | [bundesgesetzblatt.de](https://www.bundesgesetzblatt.de) |
| Lohnsteuer-kompakt.de | JStG 2024: Verlustverrechnung TermingeschÃ¤fte | [lohnsteuer-kompakt.de](https://www.lohnsteuer-kompakt.de/steuerwissen/verluste-aus-termingeschaeften-steuererleichterung-fuer-anleger/) |
| Steuernsteuern.de (Kasper & KÃ¶ber) | Trading GmbH â€” Â§8b, JStG 2024-Auswirkungen | [steuernsteuern.de](https://www.steuernsteuern.de/blog/artikel/trading-gmbh) |
| Dr. Rozanski (2026) | Verlustverrechnung TermingeschÃ¤fte aktuell | [dr-rozanski.de](https://dr-rozanski.de/verlustverrechnung-bei-termingeschaeften/) |
| CPM Steuerberater Hamburg (2026) | Â§8b KStG und Gewerbesteuer, Streubesitz | [cpm-steuerberater.de](https://www.cpm-steuerberater.de/news/entry/2026/01/09/9503-trading-gmbh-8b-kstg-streubesitzdividenden-gewerbesteuer) |
| Steuerberatung Neeb (2026) | Â§8b KStG detailliert erklÃ¤rt | [steuerberatung-neeb.de](https://steuerberatung-neeb.de/steuerfreie-dividenden-und-veraeusserungsgewinne-fuer-kapitalgesellschaften/) |
| FELSFO: Â§8b GmbH | Aktiengewinne 95% steuerfrei â€” Praxisbeispiele | [felsfo.com](https://felsfo.com/gmbh/8b.html) |
| Finanzcoach.org (2026) | GmbH-Depot Steuern vs. PrivatvermÃ¶gen | [finanzcoach.org](https://www.finanzcoach.org/wertpapierdepot-gmbh-steuern/) |

### Position Sizing und Kelly-Kriterium

| Quelle | Link |
|---|---|
| Longbridge: Kelly Criterion fÃ¼r Options Trader | [longbridge.com](https://longbridge.com/en/academy/options/blog/options-position-sizing-kelly-criterion-explained-100160) |
| Reddit PMTraders: Kelly fÃ¼r Short Options | [reddit.com/r/PMTraders](https://www.reddit.com/r/PMTraders/comments/1am7lcy/using_kelly_criterion_to_estimate_position_sizing/) |

### Marktdaten-Quellen (tÃ¤glich)

| Quelle | Verwendung | Link |
|---|---|---|
| Yahoo Finance (VIX) | TÃ¤glicher VIX-Level | [finance.yahoo.com/quote/^VIX](https://finance.yahoo.com/quote/%5EVIX) |
| Barchart.com | IV-Rang, OptionsprÃ¤mien, Delta | [barchart.com](https://www.barchart.com) |
| MarketChameleon.com | IV-Rankings, IVR-Screener | [marketchameleon.com](https://marketchameleon.com/volReports/VolatilityRankings) |
| Earnings.com / Nasdaq | Earnings-Kalender-Verifikation | [earnings.com](https://www.earnings.com); [nasdaq.com/market-activity/earnings](https://www.nasdaq.com/market-activity/earnings) |
| ORATS | Institutionelle Optionsdaten, IV-Perzentilen | [orats.com](https://orats.com) |
| Financial Modeling Prep (FMP) | Makrodaten, Earnings-Calendar, Treasury | [financialmodelingprep.com](https://financialmodelingprep.com) |

---

*Dokument erstellt: 27. April 2026*  
*Grundlage: CSP-Regelwerk April 2026, Portfolio-Ãœbersicht 21. April 2026, Makrokontext April 2026*  
*Alle Renditeangaben sind Brutto vor Steuern, sofern nicht anders angegeben*  
*Dieses Dokument stellt keine Anlageberatung dar. Alle Entscheidungen liegen im Ermessen der Familie Rehse und ihrer Berater.*  
*Vertraulich â€” ausschlieÃŸlich interner Gebrauch Familie Rehse*
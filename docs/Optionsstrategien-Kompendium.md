# Optionsstrategien-Kompendium
## Familie Rehse â€” Sophistizierter Privatinvestor (Family Office)
**Stand: April 2026 | Vertraulich | Nur fÃ¼r internen Gebrauch**

---

> **Scope dieses Dokuments:** Dieses Kompendium beschreibt das vollstÃ¤ndige Spektrum an Optionsstrategien, die fÃ¼r ein liquides Portfolio von ~16 Mio. EUR relevant sind. Die Cash-Secured Put (CSP)-Strategie dient als Referenz und Kern. Alle anderen Strategien werden danach bewertet, ob sie den CSP ergÃ¤nzen, ersetzen oder absichern. Broker-Implementierungsdetails in Abschnitt 9 sind bewusst broker-agnostisch gehalten.

---

## Inhaltsverzeichnis

1. [Mentaler Rahmen: Wie man systematisch Optionsstrategien einordnet](#1-mentaler-rahmen)
2. [Premium-Selling-Strategien (Income-Generierung)](#2-premium-selling-strategien)
3. [Premium-Buying / Direktionale Strategien](#3-premium-buying--direktionale-strategien)
4. [Hedging-Strategien fÃ¼r ein bestehendes Portfolio](#4-hedging-strategien)
5. [VolatilitÃ¤ts-Strategien](#5-volatilitÃ¤ts-strategien)
6. [Strategien-Auswahlmatrix](#6-strategien-auswahlmatrix)
7. [Greeks-Management auf Portfolioebene](#7-greeks-management-auf-portfolioebene)
8. [Backtest-Erkenntnisse / Quantitative Evidenz](#8-backtest-erkenntnisse--quantitative-evidenz)
9. [Praktische Order-AusfÃ¼hrung (Broker-agnostisch)](#9-praktische-order-ausfÃ¼hrung-broker-agnostisch)
10. [Deutsche Steuerwirkung pro Strategie](#10-deutsche-steuerwirkung-pro-strategie)
11. [Quellen und Referenzen](#11-quellen-und-referenzen)

---

## 1. Mentaler Rahmen: Wie man systematisch Optionsstrategien einordnet

### 1.1 Risk-Defined vs. Risk-Undefined

Jede Optionsstrategie lÃ¤sst sich entlang einer grundlegenden Achse einordnen: Ist das maximale Verlustrisiko bei PositionserÃ¶ffnung bekannt (risk-defined) oder theoretisch unbegrenzt (risk-undefined)?

| Kategorie | Charakteristik | Beispiele |
|---|---|---|
| **Risk-Defined** | Max. Verlust bekannt und begrenzt | Iron Condor, Vertical Spreads, Long Options |
| **Risk-Undefined** | Max. Verlust theoretisch unbegrenzt | Naked Put/Call, Short Strangle, Short Straddle |
| **Hybrid** | Auf einer Seite defined, auf der anderen undefined | Jade Lizard (upside defined), CSP (downside bis Null) |

FÃ¼r ein Family-Office-Portfolio mit Compliance-Anforderungen und Reputationsrisiken gilt als Faustregel: Risk-defined-Strategien sind bevorzugt, sobald die Kapitalbasis kein Instrument zur vollstÃ¤ndigen Absicherung mehr erfordert. Der CSP ist eine Sonderform: technisch â€žrisk-undefined nach unten", faktisch jedoch durch die vollstÃ¤ndige Cash-Deckung und die Willkommens-Haltung bei Assignment als **risikoÃ¤quivalent zu einer Kaufentscheidung** zu bewerten.

### 1.2 Direktional vs. Neutral vs. VolatilitÃ¤tsbasiert

| Ausrichtung | Profitiert von | Beispiel-Strategien |
|---|---|---|
| **Direktional Bullish** | Kursanstieg des Underlyings | Long Call, Bull Call Spread, CSP, Wheel |
| **Direktional Bearish** | KursrÃ¼ckgang | Long Put, Bear Put Spread, Bear Call Spread |
| **Neutral/Range-Bound** | SeitwÃ¤rtsbewegung, IV-RÃ¼ckgang | Iron Condor, Short Strangle, Iron Butterfly |
| **VolatilitÃ¤tsbasiert Long** | Anstieg der impliziten VolatilitÃ¤t (IV) | Long Calendar Spread, Long Diagonal, Long Straddle |
| **VolatilitÃ¤tsbasiert Short** | RÃ¼ckgang der IV (IV-Crush) | Short Straddle, Short Strangle, CSP post-Earnings |

### 1.3 Premium-Selling (Theta-positiv) vs. Premium-Buying

**Theta-positive Strategien** (Premium-Seller):
- Verdienen Geld mit dem Zeitwertverfall
- Profitieren von ruhigen MÃ¤rkten und IV-RÃ¼ckgang
- Haben typischerweise hohe Gewinnwahrscheinlichkeit, aber negatives Auszahlungsprofil (viele kleine Gewinne, seltene groÃŸe Verluste)
- [Tastylive Research](https://www.tastylive.com/news-insights/backtesting-duration-in-credit-spreads) zeigt: Credit Put Spreads mit 45 DTE und Management bei 50% erzielen Win-Rates â‰¥ 88%

**Theta-negative Strategien** (Premium-Buyer):
- Zahlen fÃ¼r das Recht auf Bewegung oder IV-Anstieg
- Verlieren tÃ¤glich durch Zeitwertverfall (Theta-Decay)
- Sinnvoll bei strukturellen Katalysatoren, extrem niedriger IV, oder als Hedge
- Erfordern eine hÃ¶here trefferquote, um profitabel zu sein

**Kernprinzip fÃ¼r Family Office:**  
Premium-Selling ist das strukturell Ã¼berlegene Modell fÃ¼r kontinuierliche Einkommensgenerierung. Premium-Buying ist selektiv einzusetzen: als Hedge, fÃ¼r spezifische direktionale Trades oder bei extrem niedriger IV (VIX < 15), wenn Long-Vega gÃ¼nstig ist.

### 1.4 Kapitaleffizienz: Cash-Secured vs. Margin

| Methode | Kapitalbindung | Renditewirkung | Risiko |
|---|---|---|---|
| **Cash-Secured (100%)** | Volle NominalhÃ¶he des Strikes | Niedrigere annualisierte Rendite | Kein Margin-Call-Risiko |
| **Portfolio-Margin** | ~15â€“25% des NominalhÃ¶he | 3â€“5Ã— hÃ¶here Kapitaleffizienz | Margin-Call bei VolatilitÃ¤t mÃ¶glich |
| **Reg-T-Margin** | ~20% + Optionspreis | 2â€“3Ã— Kapitaleffizienz | Mittleres Margin-Call-Risiko |

**Empfehlung fÃ¼r Familie Rehse:** Cash-Secured ist die korrekte Grundstruktur fÃ¼r das Kern-CSP-Portfolio. Bei einer Trading-GmbH kÃ¶nnen margin-effizientere Strukturen (Iron Condors, Spreads) eingesetzt werden, ohne Eigenkapital-IlliquiditÃ¤t zu riskieren. Das CSP-Regelwerk sieht 100% Cash-Deckung explizit vor â€” dies eliminiert Margin-Calls und ermÃ¶glicht das Assignment ohne Zwangsliquidation.

### 1.5 Position Greeks als SteuerungsgrÃ¶ÃŸen

Die fÃ¼nf Griechen bilden das Steuerungsinstrumentarium jeder Optionsstrategie:

| Greek | Definition | Bedeutung fÃ¼r Premium-Seller |
|---|---|---|
| **Delta (Î”)** | KursverÃ¤nderung der Option bei $1 Bewegung des Underlyings | Assignment-Wahrscheinlichkeit â‰ˆ absoluter Delta-Wert. Zielbereich CSP: â€“0,18 bis â€“0,25 |
| **Theta (Î˜)** | Zeitwertverfall pro Tag | Hauptrenditetreiber beim Premium-Selling. Beschleunigt sich ab 30 DTE stark |
| **Vega (Î½)** | OptionspreisÃ¤nderung bei 1% IV-VerÃ¤nderung | Short-Premium-Positionen haben negatives Vega â€” steigt IV, steigen Verluste |
| **Gamma (Î“)** | VerÃ¤nderungsrate des Delta | Negatives Gamma bei Short-Positionen: hohes Risiko bei schnellen Kursbewegungen. Wird ab 21 DTE dominant |
| **Rho (Ï)** | Zinsempfindlichkeit | Bei kurzlaufenden Optionen vernachlÃ¤ssigbar. Relevant nur bei LEAPS |

**Praxisregel:** Ein Short-Premium-Portfolio ist typischerweise: Positives Theta, negatives Vega, negatives Gamma. Das Theta/Vega-VerhÃ¤ltnis ist die wichtigste Kennzahl fÃ¼r die QualitÃ¤t einer Short-Premium-Position. Hohes Theta bei niedrigem negativen Vega-Risiko ist optimal.

---

## 2. Premium-Selling-Strategien (Income-Generierung)

### 2.1 Cash-Secured Put (CSP) â€” Referenzstrategie

**Setup:**
- SELL 1 Put, Strike â‰¥ 8% OTM, DTE 30â€“55, Delta â€“0,18 bis â€“0,25
- 100% Cash-Deckung in HÃ¶he des Strike-Werts Ã— 100

**P/L-Profil:**

```
Gewinn
  â”‚     â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ
  â”‚   â–ˆâ–ˆ
  â”‚  â–ˆ
Max-Verlust â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Strike    Kurs
  (Strike â€“ PrÃ¤mie)
```

- Max. Gewinn: Vereinnahmte PrÃ¤mie (bei Verfall OTM)
- Max. Verlust: Strike â€“ kassierte PrÃ¤mie (bei Kurs = 0, theoretisch)
- Break-Even: Strike â€“ PrÃ¤mie

**Greeks:** Î” +0,18â€“0,25 (Ã¤quivalent Long-Position), Î˜ positiv, Î½ negativ, Î“ negativ

**Ideale Marktbedingungen:**
- VIX â‰¥ 20 ODER IV-Rang â‰¥ 40%
- Leicht bullisher oder neutraler Markt
- Fundamental intaktes Underlying mit klarer Kaufabsicht

**Management-Regeln (aus CSP-Regelwerk April 2026):**
- SchlieÃŸen bei 50% Gewinn (PrÃ¤mie auf HÃ¤lfte gefallen)
- SchlieÃŸen bei 21 DTE (Gamma-Risiko steigt)
- Verlust-Stopp bei 200% der ursprÃ¼nglichen PrÃ¤mie
- Rollen nur fÃ¼r Net-Credit; sonst: Assignment akzeptieren

**Steuer DE:**
- PrivatvermÃ¶gen: StillhalterprÃ¤mie = Kapitalertrag, sofort fÃ¤llig bei Vereinnahmung, 26,375% Abgeltungssteuer
- Trading GmbH: PrÃ¤mien = laufende Betriebseinnahmen, KSt + GewSt ca. 30,83%; aber Assignment â†’ Aktie â†’ Â§8b KStG bei VerÃ¤uÃŸerung

---

### 2.2 Covered Call (CC)

**Setup:**
- SELL 1 Call, Strike 5â€“8% OTM, DTE 30â€“45, Delta +0,20â€“0,30
- Voraussetzung: 100 Aktien im Depot

**P/L-Profil:**
- Max. Gewinn: PrÃ¤mie + (Strike â€“ Einstiegskurs) wenn Kurs â‰¥ Strike
- Max. Verlust: Einstiegskurs â€“ PrÃ¤mie (Aktie fÃ¤llt auf null)
- Break-Even: Einstiegskurs â€“ PrÃ¤mie

**Greeks:** Î” positiv (< 1,0 durch Short Call), Î˜ positiv, Î½ negativ

**Ideale Bedingungen:** Post-Assignment nach CSP (Wheel Phase 2). Leicht bullisher bis neutraler Markt. IVR 30â€“60%.

**Management-Regeln:**
- SchlieÃŸen bei 50% Gewinn oder 21 DTE
- Bei Kursanstieg Ã¼ber Strike: Rollen nach oben und zeitlich aus (nur fÃ¼r Credit)
- Strike mindestens oberhalb des Einstiegskurses setzen (kein Verlust bei Assignment)

**Vorteile:** Kostenbasisreduktion. Theta-Ertrag auf existierende Aktienposition. NatÃ¼rliche ErgÃ¤nzung nach CSP-Assignment.

**Nachteile:** Cap auf Kursgewinne. Bei starkem Kursanstieg entgangener Gewinn.

**Steuer DE:**
- StillhalterprÃ¤mie = Kapitalertrag sofort
- Bei AusÃ¼bung: VerÃ¤uÃŸerungserlÃ¶s = Strike + gezahlte PrÃ¤mie des KÃ¤ufers (nicht fÃ¼r Seller relevant) â€” fÃ¼r Seller gilt: Aktienverkauf zum Strike-Preis, der Gewinn/Verlust aus dem Aktienkauf zuzÃ¼glich Call-PrÃ¤mie ergibt das Gesamtergebnis

---

### 2.3 The Wheel (CSP + Covered Call)

**Setup:**
Phase 1: CSP verkaufen (8â€“12% OTM, Delta â€“0,20, DTE 30â€“55)
â†’ Bei Assignment: Aktie wird zugeteilt (Phase 2 beginnt)
Phase 2: Covered Call verkaufen (5â€“8% OTM, Delta +0,20â€“0,30, DTE 30â€“45)
â†’ Bei Assignment: Aktie verkauft â†’ zurÃ¼ck zu Phase 1
â†’ Kein Assignment: nÃ¤chsten CC verkaufen; Kostenbasis sinkt weiter

**P/L-Profil:** 
Laufendes Einkommen durch PrÃ¤mieneinnahmen. Effektiver Einstandskurs sinkt mit jeder Runde. In echten BullenmÃ¤rkten: Underperformance gegenÃ¼ber Buy-and-Hold durch Call-Cap.

**Greeks (Phase 1):** identisch CSP. **Phase 2:** identisch Covered Call.

**Ideale Bedingungen:** 
- IVR 40â€“80%, VIX â‰¥ 20
- Titel, die das Portfolio langfristig halten mÃ¶chte
- Volatiler, aber fundamental intakter Markt

**Quantitative Evidenz:** [QuantConnect-Backtest](https://www.quantconnect.com/research/17871/automating-the-wheel-strategy/) der Wheel-Strategie auf SPY ergibt Sharpe-Ratio 1,083 vs. 0,70 fÃ¼r Buy-and-Hold Ã¼ber denselben Zeitraum.

**Vorteil fÃ¼r Familie Rehse:** Die Wheel-Strategie ist das natÃ¼rliche Protokoll nach Assignment (CSP â†’ CC â†’ optional RÃ¼ckkehr). Das CSP-Regelwerk sieht exakt diesen Ablauf vor.

**Nachteile:** Erfordert aktive Verwaltung nach Assignment. In starken BullenmÃ¤rkten entgehen Kursgewinne.

**Steuer DE:**
- Jede Phase steuerlich getrennt: CSP-PrÃ¤mie, CC-PrÃ¤mie, Aktiengewinn/-verlust beim Verkauf
- Trading GmbH: Aktienverkauf nach Assignment = Â§8b KStG, 95% steuerfrei â€” massiver Vorteil

---

### 2.4 Naked Put (Referenz mit Warnung)

**Setup:** SELL 1 Put ohne 100% Cash-Deckung, nur Margin-Anforderung (~20% des Nominals)

**Warnung:** Rechtlich und regulatorisch im PrivatvermÃ¶gen hÃ¤ufig eingeschrÃ¤nkt. Margin-Call-Risiko bei VIX-Spike. Nicht kompatibel mit dem CSP-Regelwerk der Familie Rehse. Hier nur zur vollstÃ¤ndigen Darstellung â€” keine Empfehlung.

**Vorteil:** 3â€“5Ã— hÃ¶here Kapitaleffizienz als CSP. **Nachteil:** Bei erzwungener SchlieÃŸung durch Margin-Call entstehen realisierte Verluste ohne WahlmÃ¶glichkeit.

---

### 2.5 Short Strangle

**Setup:**
- SELL 1 Call (Delta +0,16 bis +0,25, OTM) + SELL 1 Put (Delta â€“0,16 bis â€“0,25, OTM)
- Gleicher Verfall, DTE 30â€“45

**P/L-Profil:**
- Max. Gewinn: GesamtprÃ¤mie beider Legs (Underlying bleibt zwischen Strikes)
- Max. Verlust: Unbegrenzt auf der Call-Seite; bis Null auf der Put-Seite
- Zwei Break-Even-Punkte: Short-Put-Strike â€“ GesamtprÃ¤mie und Short-Call-Strike + GesamtprÃ¤mie

**Greeks:** Î” nahe null (leicht bearish durch Put-Skew), Î˜ stark positiv, Î½ stark negativ, Î“ negativ

**Ideale Bedingungen:**
- IVR â‰¥ 50%, VIX â‰¥ 20
- SeitwÃ¤rts- oder leicht bullisher/bearisher Markt
- Keine bekannten Earnings-Katalysatoren innerhalb des Verfallzeitraums
- Hochliquide Underlyings (SPY, QQQ, groÃŸe Einzeltitel)

**Management nach [Tastylive-Studie](https://www.tastylive.com/shows/market-measures/episodes/profit-expectations-and-strategy-06-08-2022):**
- SchlieÃŸen bei 50% Gewinn oder bei 21 DTE
- Getestete Seite Ã¼ber 2Ã— PrÃ¤mie: SchlieÃŸen oder Rollen
- "Rolling the untested side" (OTM-Seite nÃ¤her an Kurs) bei Breach, um Gesamtguthaben zu verbessern

**Quantitative Evidenz:**  
[Tastylive 10-Jahres-Studie](https://www.youtube.com/watch?v=Wt90xWeRuMQ): Short Strangles erzielen 10â€“15% hÃ¶here Win-Rates als Iron Condors Ã¼ber verschiedene Marktbedingungen. Bei hoher IV (VIX > 18) verdoppelt sich die durchschnittliche Return on Capital bei gleichbleibender Win-Rate von 76â€“78%.

**Vorteil:** HÃ¶heres Theta als CSP bei gleichem Kapital. Flexibler Profit-Bereich.  
**Nachteil:** Unbegrenztes Risiko auf beiden Seiten. Erfordert hÃ¶here Margin-Freigabe.

**Steuer DE:** Beide PrÃ¤mien einzeln als StillhalterprÃ¤mie steuerlich erfasst.

---

### 2.6 Short Straddle

**Setup:**
- SELL 1 Call ATM + SELL 1 Put ATM, gleicher Strike, gleicher Verfall (DTE 30â€“45)
- Maximum-Theta-Strategie, da ATM-Optionen hÃ¶chsten Zeitwert haben

**P/L-Profil:**
- Max. Gewinn: GesamtprÃ¤mie (nur wenn Kurs exakt bei Strike liegt)
- Schmalster Profit-Korridor aller Strangle/Condor-Varianten
- Break-Even: Strike Â± GesamtprÃ¤mie

**Greeks:** Î” â‰ˆ 0 (ATM), Î˜ maximal positiv, Î½ stark negativ, Î“ stark negativ (hÃ¶chstes Gamma-Risiko)

**Ideale Bedingungen:** IVR â‰¥ 60â€“70%. AusgeprÃ¤gter SeitwÃ¤rtsmarkt erwartet. Nur nach extremem IV-Spike sinnvoll (z.B. post-Earnings, wenn noch ATM).

**Risiko:** Das hÃ¶chste Gamma-Risiko aller Short-Strategien. Kleine Kursbewegungen verÃ¤ndern das Delta stark. Nur fÃ¼r erfahrene HÃ¤ndler.

---

### 2.7 Iron Condor

**Setup:**
- SELL 1 Put (Delta â€“0,20 bis â€“0,30), BUY 1 Put (weitere OTM)
- SELL 1 Call (Delta +0,20 bis +0,30), BUY 1 Call (weitere OTM)
- Gleicher Verfall, typisch DTE 30â€“45; FlÃ¼gelbreite 1/10 des Aktienkurses

**P/L-Profil:**
- Max. Gewinn: Nettokreditsumme (alle vier Legs) bei Underlying zwischen Short-Strikes
- Max. Verlust: FlÃ¼gelbreite â€“ Nettokredit (auf jeder Seite)
- Risk-Defined: klares max. Verlustpotenzial bekannt

**Greeks:** Î” nahe null, Î˜ positiv, Î½ negativ, Î“ negativ

**Ideale Bedingungen:**
- IVR 40â€“70%, VIX 18â€“30
- SeitwÃ¤rtsbewegung erwartet
- Ausreichend liquide Optionskette (SPY, QQQ ideal)

**Management-Regeln nach [Tastylive Iron Condor-Studie](https://www.tastylive.com/news-insights/maximizing-profits-the-art-of-the-iron-condor-wingspan):**
- Optimale FlÃ¼gelbreite: $10â€“$20 fÃ¼r SPY (â‰ˆ 1/10 des Aktienkurses)
- SchlieÃŸen bei 50% Gewinn oder bei 21 DTE
- Bei Breach eines Short-Strikes: entweder gesamte Position schlieÃŸen oder Spread auf Gegenseite eng stellen

**Quantitative Evidenz:**  
[Tastylive 15-Jahres-Studie](https://www.tastylive.com/news-insights/maximizing-profits-the-art-of-the-iron-condor-wingspan): FlÃ¼gel $15â€“$20 auf SPY liefern optimale Return-on-Capital. Breitere FlÃ¼gel erhÃ¶hen Win-Rate und beschleunigen das Erreichen des 50%-Gewinnziels.

**Vorteil gegenÃ¼ber Short Strangle:** Risk-defined. Niedrigere Margin-Anforderung. Geeignet fÃ¼r Cash-Konten mit Margin-Freigabe Level 3+.

**Nachteil:** Niedrigeres Theta als Short Strangle. Mehr Beinarbeit (4 Legs). Schwieriger zu rollen.

**Steuer DE:** 4 separate Optionspositionen, aber als Combination Order steuerlich kohÃ¤rent behandelbar.

---

### 2.8 Iron Butterfly

**Setup:**
- SELL 1 Call ATM + SELL 1 Put ATM (gleicher Strike) + BUY 1 Call weiter OTM + BUY 1 Put weiter OTM
- Wie Short Straddle, aber mit FlÃ¼geln zur Risikobegrenzung

**P/L-Profil:**
- Hoher maximaler Gewinn (ATM-PrÃ¤mien sind groÃŸ), aber enger Profit-Korridor
- Risk-defined: Max. Verlust = FlÃ¼gelbreite â€“ Nettokredit

**Ideale Bedingungen:** Sehr niedrige Bewegungserwartung. Post-Earnings mit noch-ATM-Situation. IVR â‰¥ 60%.

**Nachteile:** Kaum Toleranz fÃ¼r Kursbewegungen. Praktisch nur auf Indizes (SPX, SPY) sinnvoll.

---

### 2.9 Calendar Spread (Short-Variante / Sell Calendar)

**Setup:**
- BUY 1 Put (lÃ¤ngere Laufzeit, z.B. 60 DTE) + SELL 1 Put (kÃ¼rzere Laufzeit, z.B. 30 DTE) â€” gleicher Strike
- Nettokosten: Debit (der Kauf der lÃ¤ngerlaufenden Option kostet mehr)

**Hinweis:** Der "Sell Calendar" (Short Calendar) bedeutet das Umgekehrte â€” Short der langen, Long der kurzen. Dies ist komplex und nicht fÃ¼r Standard-Income-Strategien geeignet. Der Long Calendar (Kauf lang, Verkauf kurz) ist das gebrÃ¤uchlichere Instrument und wird in Abschnitt 3 und 5 behandelt.

---

### 2.10 Diagonal Spread (Sell-Variante)

**Setup:**
- BUY 1 Option (lÃ¤ngere Laufzeit, tieferer Strike) + SELL 1 Option (kÃ¼rzere Laufzeit, hÃ¶herer Strike)
- Asymmetrie in Strike UND Zeit

**Praxiseinsatz:** Der Diagonal Spread ist die Basis des Poor Man's Covered Call (PMCC), der in Abschnitt 3.4 ausfÃ¼hrlich behandelt wird.

**Direkter Anwendungsfall:** SELL 1 Call (30â€“45 DTE, Delta +0,20â€“0,30) gegen bestehende LEAPS Long Calls. Dies reduziert das Theta-Decay-Risiko der LEAPS und generiert laufendes Einkommen.

---

### 2.11 Put Credit Spread (Bull Put Spread)

**Setup:**
- SELL 1 Put (Delta â€“0,25â€“0,30, OTM) + BUY 1 Put (weiter OTM, gleicher Verfall)
- Nettokredit wird vereinnahmt

**P/L-Profil:**
- Max. Gewinn: Nettokredit (Underlying bleibt Ã¼ber Short-Strike)
- Max. Verlust: Spread-Breite â€“ Nettokredit
- Break-Even: Short-Strike â€“ Nettokredit

**Greeks:** Î” leicht positiv, Î˜ positiv, Î½ negativ, Î“ negativ

**Vorteil gegenÃ¼ber CSP:** Definiertes Risiko. Niedrigere Kapitalbindung. 
**Nachteil gegenÃ¼ber CSP:** Kein Assignment mÃ¶glich (kein Aktienerwerb). Niedrigere absolute PrÃ¤mie. Weniger steuerlich attraktiv in GmbH (kein Â§8b-Effekt mÃ¶glich).

[Tastylive Credit-Spread-Studie](https://www.tastylive.com/news-insights/backtesting-duration-in-credit-spreads): Win-Rate bei 45 DTE Bull Put Spreads â‰¥ 88% bei Management auf 50%.

**Wann nutzen:** Wenn keine Aktien gewÃ¼nscht sind (z.B. zu teures Underlying), aber bullisher Ausblick und erhÃ¶hte IV. Oder zur ErgÃ¤nzung eines CSP-Portfolios bei begrenztem Cash.

---

### 2.12 Call Credit Spread (Bear Call Spread)

**Setup:**
- SELL 1 Call (Delta +0,20â€“0,30, OTM) + BUY 1 Call (weiter OTM, gleicher Verfall)
- Nettokredit vereinnahmt; Profit bei stagnierendem oder fallendem Kurs

**P/L-Profil:**
- Max. Gewinn: Nettokredit (Underlying bleibt unter Short-Call-Strike)
- Max. Verlust: Spread-Breite â€“ Nettokredit

**Anwendungsfall:** Als zweite Seite eines Iron Condors oder als direktionaler bearisher Trade. In Kombination mit einem CSP entsteht ein synthetischer Iron Condor (wenn CSP = Bull Put Spread).

**FÃ¼r Familie Rehse relevant als:** ErgÃ¤nzung zu bestehenden Aktienpositionen. Wenn ein Titel stark gestiegen ist und temporÃ¤re Rallye-Absicherung gewÃ¼nscht wird, ohne die Aktie zu verkaufen.

---

### 2.13 Jade Lizard

**Setup:**
- SELL 1 Put (Delta â€“0,20â€“0,30, OTM)
- SELL 1 Call (Delta +0,20â€“0,30, OTM)  
- BUY 1 Call (weiterer Strike OTM, gleiche Laufzeit)
- Kernregel: Nettokredit > Breite des Call-Spreads â†’ kein Upside-Risiko

**P/L-Profil:**
- Max. Gewinn: GesamtprÃ¤mie (alle drei Legs) bei Underlying zwischen Put-Strike und Short-Call-Strike
- Upside-Risiko: Null (wenn Kreditbedingung erfÃ¼llt)
- Downside-Risiko: Unbegrenzt auf Put-Seite (wie CSP)

**Beispiel (aus [Tastylive Jade Lizard Guide](https://www.tastylive.com/concepts-strategies/jade-lizard)):**
- Underlying: $50
- SELL Put $45 fÃ¼r $2,00 â†’ $200 Kredit
- SELL Call $55 fÃ¼r $1,00 â†’ $100 Kredit
- BUY Call $57 fÃ¼r $0,50 â†’ â€“$50 Kosten
- Nettokredit: $250. Call-Spread-Breite: $200. Nettokredit > Spread-Breite â†’ kein Upside-Risiko.

**Greeks:** Î” leicht positiv (bullish bias), Î˜ positiv, Î½ negativ

**Ideale Bedingungen:**
- Stark negativer Skew (Puts deutlich teurer als Calls)
- Titel hat kÃ¼rzlich verkauft, IVR 50â€“80%
- Bullisher Grundausblick

**Tastylive-Empfehlung:** Mindestens 70% des Gesamtkredits sollte vom Put-Leg kommen, 30% vom Call-Spread. Dies maximiert das Upside-Puffer-VerhÃ¤ltnis.

**FÃ¼r Familie Rehse:** Ideal fÃ¼r Post-Crash-Situationen (z.B. NOW nach â€“17,75%-RÃ¼ckgang am 24. April 2026), bei denen der Skew extrem ist und ein leicht bullishes Exposure gewÃ¼nscht wird. Der Jade Lizard ist eine natÃ¼rliche Erweiterung des CSP mit optionalem Credit-Call-Spread.

---

### 2.14 Ratio Put Spread (1Ã—2 Put Spread)

**Setup:**
- BUY 1 Put (hÃ¶herer Strike, z.B. ATM oder leicht OTM)
- SELL 2 Puts (niedrigerer Strike, weiter OTM)
- Ziel: Net Credit oder minimales Debit

**P/L-Profil:**
- Max. Gewinn: Bei Verfall des Underlyings nahe dem unteren Strike (beide Short Puts wertlos, Long Put maximal)
- Risk-Zone: Kurs fÃ¤llt tief unter untere Short-Puts â†’ unbegrenzte Verluste auf Unterseite
- Upside: Kleiner Kredit bleibt (alle Puts verfallen wertlos)

**Beispiel ([Fidelity](https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/1x2-ratio-volatility-spread-puts)):**
- Buy 1 XYZ 100 Put @ $3,50; Sell 2 XYZ 95 Puts @ $1,50 each
- Nettokredit: $0,50. Max. Gewinn bei Kurs = $95: $4,50. Break-Even Unterseite: $89,50.

**Wann nutzen:** Ausnahme-Situation mit sehr spezifischer These: "Aktie fÃ¤llt etwas, aber nicht viel." Post-Earnings mit erwartetem moderaten RÃ¼ckgang. Bei extremem Skew (Puts teuer) zur kostengÃ¼nstigen Absicherung.

**Warnung:** Unbegrenztes Verlustrisiko unterhalb der Short-Strike-Zone. Nur fÃ¼r fortgeschrittene HÃ¤ndler mit klarer Verlustbegrenzungsstrategie (Stop-Loss bei 2Ã— maximales Kredit).

**Steuer DE:** Drei separate Positionen; komplexes Rollieren schwierig zu dokumentieren.

---

## 3. Premium-Buying / Direktionale Strategien

### 3.1 Long Call / Long Put

**Long Call:**
- BUY 1 Call, Strike ATM oder leicht OTM, DTE 45â€“90
- Profitiert von: Kursanstieg des Underlyings
- Max. Verlust: Gezahlte PrÃ¤mie (100%)
- Max. Gewinn: Theoretisch unbegrenzt
- Wann sinnvoll: Erwartete starke AufwÃ¤rtsbewegung, IV extrem niedrig (VIX < 15)

**Long Put:**
- BUY 1 Put, Strike ATM oder leicht OTM, DTE 45â€“90
- Profitiert von: KursrÃ¼ckgang
- Wann sinnvoll: Direktionaler bearisher Trade; oder als Absicherung bestehender Positionen (Protective Put, siehe Abschnitt 4)

**Lottoschein vs. echter Trade:**  
Deep-OTM-Optionen (Delta < 0,10) = "Lottoscheine" â€” hohe Win-Rate gegen null, sehr gÃ¼nstig, kÃ¶nnen bei Black-Swan-Events massiv aufwerten. Echte direktionale Trades: Delta 0,30â€“0,50, hÃ¶herer Kapitaleinsatz, klares Kursziel und Zeitfenster.

**Empfehlung:** Long Calls/Puts sind fÃ¼r Familie Rehse selektiv einsetzbar bei strukturellen Katalysatoren (z.B. bekannter Zulassung, Fed-Entscheidung) oder als Tail-Hedge-ErgÃ¤nzung (Deep OTM Puts auf SPY/QQQ als Absicherung).

---

### 3.2 Bull Call Spread / Bear Put Spread (Debit Spreads)

**Bull Call Spread:**
- BUY 1 Call (Strike A, ATM) + SELL 1 Call (Strike B, OTM)
- Nettodebit vereinnahmt; profitiert von Kursanstieg bis Strike B
- Max. Gewinn: Breite â€“ Nettodebit. Max. Verlust: Nettodebit.
- Vorteil: GÃ¼nstiger als Long Call; Risk-defined.

**Bear Put Spread:**
- BUY 1 Put (Strike A, ATM) + SELL 1 Put (Strike B, OTM, tiefer)
- Profitiert von KursrÃ¼ckgang
- Sinnvoll als definiertes bearishes Exposure, z.B. auf Indizes als Teil eines Hedges

**FÃ¼r Familie Rehse:** Bull Call Spreads kÃ¶nnen eingesetzt werden, wenn eine AufwÃ¤rtsbewegung erwartet wird, IV aber zu hoch fÃ¼r einen Long Call ist (Short-Leg reduziert Vega-Kosten).

---

### 3.3 Long Calendar / Long Diagonal

**Long Calendar:**
- SELL 1 Option (kurze Laufzeit, z.B. 30 DTE) + BUY 1 Option (lÃ¤ngere Laufzeit, z.B. 60 DTE)
- Gleicher Strike; profitiert von Zeitwertverfall des kurzlaufenden Legs und/oder IV-Anstieg

**Greeks:** Î” â‰ˆ 0, Î˜ leicht positiv, **Î½ positiv** (Long Vega) â€” dies ist der Hauptunterschied zu Short-Premium-Strategien

**Wann sinnvoll:**
- IV extrem niedrig (VIX < 15, IVR < 20): Long Vega gÃ¼nstig einkaufen
- Anstieg der IV erwartet (z.B. vor bekannten Ereignissen, aber auÃŸerhalb des kurzlaufenden Verfalls)
- Term-Structure-Plays: wenn kurzlaufende IV Ã¼berproportional teuer ist

**FÃ¼r Familie Rehse:** Im aktuellen Marktregime (VIX 18â€“19, Mai-Futures 20,5) sind Long Calendars als Vega-Diversifikation im Short-Premium-Portfolio sinnvoll â€” sie hedgen das negative Vega-Exposure von CSPs und Iron Condors.

---

### 3.4 LEAPS und Poor Man's Covered Call (PMCC)

**LEAPS (Long-Term Equity Anticipation Securities):**
Optionen mit Laufzeit â‰¥ 1 Jahr. Dienen als kostengÃ¼nstige Aktiensubstitute (Delta 0,70â€“0,85 = 70â€“85 Aktien-Ã¤quivalent bei Bruchteil des Kapitals).

**Poor Man's Covered Call (PMCC) â€” Diagonal Spread:**
- BUY 1 LEAPS Call (DTE 12â€“24 Monate, Delta 0,70â€“0,85, tief ITM)
- SELL 1 Short Call (DTE 30â€“45, Delta 0,20â€“0,35, OTM)

**Parameter nach [Pro Trader Dashboard](https://protraderdashboard.com/blog/what-is-poor-mans-covered-call/):**
- LEAPS: â‰¥ 6 Monate, idealerweise 12â€“18 Monate, Delta â‰¥ 0,70
- Short Call: 25â€“35 Delta, 30â€“45 DTE
- Delta-Differenz zwischen Long und Short: mindestens 0,30â€“0,40 (Schutz vor "Blowout")
- Short-Strike oberhalb des LEAPS Break-Even (LEAPS-Strike + gezahlte PrÃ¤mie)

**Kapitaleffizienz:** LEAPS-Kosten ca. 30â€“40% des Aktienwertes vs. 100% fÃ¼r echte Aktie. Laufende Short-Call-Einnahmen reduzieren den LEAPS-Einstand kontinuierlich.

**FÃ¼r Familie Rehse:** Attraktiv fÃ¼r Titel, die man nicht als Aktie kaufen mÃ¶chte (z.B. zu teuer: AVGO, NVDA, AMZN), aber an deren Kursanstieg man partizipieren mÃ¶chte. Das PMCC kombiniert die Einkommensgenerierung des Covered Call mit niedrigerem Kapitaleinsatz.

**Wann LEAPS rollen:** Wenn noch 4â€“6 Monate bis Verfall â€” auf neues 12-Monatsziel rollen, um Theta-Decay-Beschleunigung zu vermeiden.

---

### 3.5 Synthetic Long Stock

**Setup:**
- BUY 1 Call (Delta +0,50, ATM) + SELL 1 Put (Delta â€“0,50, ATM, gleicher Strike)
- Nettodebit oder -kredit je nach Zinsniveau

**Eigenschaften:** Delta â‰ˆ +1,0; verhÃ¤lt sich wie eine Aktienposition. Kein Kapitaleinsatz fÃ¼r Aktie notwendig. Risiko: identisch Long-Aktie auf der Unterseite.

**Anwendungsfall:** Sehr begrenzt fÃ¼r Familie Rehse â€” wenn hohe Ãœberzeugung und keine Aktie gewÃ¼nscht wird. In der Regel Ã¼berlegen der CSP bei hÃ¶herer IV.

---

## 4. Hedging-Strategien fÃ¼r ein bestehendes Portfolio

### 4.1 Protective Put

**Setup:**
- BUY 1 Put auf bestehende Aktienposition
- Strike: 5â€“10% OTM (AbwÃ¤rtsschutz beginnt bei Strike), DTE 60â€“180 Tage

**Kosten:** Laufende PrÃ¤mie (Theta-Decay). Typisch 1â€“3% des Portfoliowerts pro Jahr fÃ¼r 10%-OTM-Schutz.

**Wann nutzen:**
- Vor bekannten Risiko-Ereignissen (Earnings trotz Haltens, geopolitische Eskalation)
- VIX-Tief-Phase (Schutz gÃ¼nstig): VIX < 15, IV-Perzentile < 30% â†’ Long-Optionen gÃ¼nstig
- Konzentrierte Positionen (Einzeltitel > 10% des Portfolios)

**FÃ¼r Familie Rehse:** Post-Assignment-Positionen aus Wheel-Strategie kÃ¶nnen temporÃ¤r mit Protective Puts gesichert werden, wenn Earnings oder makro-geopolitische Risiken (Iran-Konflikt, Zollpolitik) akut sind.

---

### 4.2 Collar (Zero-Cost Collar)

**Setup:**
- SELL 1 Call (5â€“10% OTM) + BUY 1 Put (5â€“10% OTM) auf bestehende Aktienposition
- Ziel: PrÃ¤mieneinnahmen des Calls finanzieren den Put-Kauf vollstÃ¤ndig (Net Cost = 0)

**P/L-Profil:**
- Upside gedeckelt auf Call-Strike
- Downside gesichert ab Put-Strike
- Zwischen den Strikes: normale Aktien-Performance

**Praktische Asymmetrie:** Um kostenlose Struktur zu erreichen, muss der Call-Strike typischerweise nÃ¤her am Kurs sein als der Put-Strike (5% OTM-Call vs. 10% OTM-Put). Daraus ergibt sich ein asymmetrisches Profil: mehr Upside-Verzicht als Downside-Schutz.

**Hinweis ([Savant Wealth Management](https://savantwealth.com/savant-views-news/article/the-zero-cost-collar-a-strategy-to-limit-your-lossesand-gains/)):** In einer langfristigen Studie wurde der Call-Strike mehr als 50% der Zeit ausgeÃ¼bt, mit einem durchschnittlichen entgangenen Gewinn von 7,3% pro Zyklus.

**FÃ¼r Familie Rehse:** Zero-Cost Collar ist besonders geeignet fÃ¼r:
1. Konzentrierte Positionen in stark gestiegenen Titeln (z.B. NVDA, MSFT nach groÃŸen Kursgewinnen)
2. Portfolioabsicherung vor strategischen Ereignissen ohne Verkauf der Position
3. Als Â§8b-KStG-Strategie: Aktie wird gehalten, kein Verkaufsgewinn ausgelÃ¶st

**Steuer:** Collar auf Aktie = Short Call (StillhalterprÃ¤mie) + Long Put (TermingeschÃ¤ft). Wird Put ausgeÃ¼bt: Aktienverkauf zum Strike-Preis realisiert Aktiengewinn/-verlust.

---

### 4.3 Put Spread Hedge

**Setup:**
- BUY 1 Put (5â€“8% OTM) + SELL 1 Put (15â€“20% OTM) als Finanzierung
- Nettodebit reduziert sich durch Short-Put-PrÃ¤mie (Schutz bis zur unteren Short-Put-Strike)

**Vorteil gegenÃ¼ber Protective Put:** Deutlich gÃ¼nstiger. Bei VIX 20â€“25 kann der Short-Put die Kosten um 50â€“70% reduzieren.
**Nachteil:** Schutz endet beim Short-Put-Strike â€” bei massivem Crash (â€“20%+) kein weiterer Schutz.

**FÃ¼r Familie Rehse:** Effizienter Hedge auf SPY/QQQ-Ebene fÃ¼r das Gesamtportfolio. Beispiel: Bei SPY bei $530 â†’ BUY 490 Put (8% OTM) + SELL 460 Put (13% OTM) = Schutz fÃ¼r 8â€“13% KursrÃ¼ckgang bei reduziertem Nettodebit.

---

### 4.4 VIX-Calls als Tail-Hedge

**Konzept:**  
VIX und Aktienmarkt sind stark negativ korreliert (historisch â€“0,75 bis â€“0,85). Bei einem Markteinbruch steigt VIX Ã¼berproportional. VIX-Call-Optionen profitieren also von Marktstress.

**Setup nach [Option Alpha](https://optionalpha.com/blog/vix-portfolio-hedging-strategy):**
**Komponente 1 (Short-term Spike-Schutz):** Short-Call-Ladder auf VIX â€” SELL 1 VIX Call (ATM/leicht OTM) + BUY 2 VIX Calls (weiter OTM). Positioniert fÃ¼r Netto-Kredit oder Break-Even. SchÃ¼tzt bei moderatem VIX-Anstieg.

**Komponente 2 ("Doomsday"-Calls):** BUY VIX Calls mit Delta 0,05â€“0,10 (weit OTM, z.B. Strike $35â€“$40 bei VIX = 18). Laufzeit 90â€“120 DTE. Kosten: $0,30â€“$0,60 je Kontrakt. SchÃ¼tzen bei Black-Swan-Events (VIX > 40).

**GrÃ¶ÃŸenordnung:**
- Total-Hedge-Kosten: < 0,50% des Portfoliowerts pro Jahr
- FÃ¼r 16 Mio. EUR Portfolio: ca. $60.000â€“$80.000 jÃ¤hrliche Hedge-Kosten

**Vorteil gegenÃ¼ber SPY-Puts:** 
- VIX-Optionen sind bei niedrigem VIX (< 20) deutlich gÃ¼nstiger als Ã¤quivalenter SPY-Schutz
- VIX steigt bei Markteinbruch, bevor SPY-Put-Werte entsprechend steigen
- Physischer VIX-Settlment-Basis (VIX-Futures), nicht direktes Aktienexposure

**Wichtig:** VIX-Optionen verfallen gegen VIX-Futures (nicht Spot-VIX). Die Termstruktur kann Kosten erhÃ¶hen (Contango) oder reduzieren (Backwardation). Aktuell bei VIX Spot 18â€“19 vs. Mai-Futures 20,5 = leichtes Contango.

---

### 4.5 SPY/QQQ Index-Puts als Portfolio-Insurance

**Setup:**
- BUY SPY/QQQ Put (Delta â€“0,10 bis â€“0,20, DTE 60â€“120)
- Proportional zur Portfolio-Beta-Exposition

**Kostenberechnung:**
Bei SPY-Portfolio-Beta â‰ˆ 1,0 und 16 Mio. EUR Aktienexposure:
- SPY-Notionalwert pro Kontrakt: ca. $53.000 (100 Aktien Ã— $530)
- Absicherung von 10% des Portfolios (1,6 Mio. EUR â‰ˆ $1,75 Mio.) = ca. 33 Kontrakte
- Kosten 10%-OTM-Put, 90 DTE: ca. $4â€“$6 pro Aktie â†’ $13.000â€“$20.000 fÃ¼r 33 Kontrakte

**Effizienz:** Portfolio-Insurance ist in HochvolatilitÃ¤tsphasen (VIX > 25) teuer. Idealer Kauf bei VIX < 15â€“18 (niedrige IV = gÃ¼nstige Long-PrÃ¤mien).

---

## 5. VolatilitÃ¤ts-Strategien

### 5.1 IV-Rang als Filter: Skew, Term Structure, Surface

**IV-Rang (IVR):**  
Misst die aktuelle IV relativ zum 52-Wochen-Hoch/Tief. IVR = (aktuell â€“ 52W-Tief) / (52W-Hoch â€“ 52W-Tief) Ã— 100.

| IVR | Interpretation | Strategie-Implikation |
|---|---|---|
| < 20% | IV extrem niedrig | Premium-Buying (Long Vega) bevorzugen; Calendars, Long Strangles |
| 20â€“40% | IV normal | CSP selektiv; Credit Spreads, Iron Condors |
| 40â€“60% | IV erhÃ¶ht | CSP, Strangles, Iron Condors â€” idealer Einstiegsbereich |
| 60â€“80% | IV hoch | Maximale Premium-Selling-AktivitÃ¤t; Post-Earnings-Situationen |
| > 80% | IV extrem (Ausnahme) | Selektiv arbeiten; Vorsicht vor Restkatalysatoren; maximale PrÃ¤mien |

**VolatilitÃ¤ts-Skew:**  
OTM-Puts sind typischerweise teurer als Ã¤quivalente OTM-Calls (negatives Skew bei Aktien). Grund: Portfolio-Absicherungsnachfrage. Der Skew ist die Grundlage fÃ¼r den Jade-Lizard-Vorteil (gÃ¼nstigere Call-Seite, teurere Put-Seite).

**Termstruktur:**  
Normalzustand = Contango (lÃ¤nger = teurer). Stress = Backwardation (kurzlaufend > langlaufend IV). Calendar Sells profitieren von Backwardation; Calendar Buys von Contango.

---

### 5.2 Vega-Plays bei tiefer IV (Long Vega via Calendars)

**Situation:** VIX < 15, IVR < 20% â€” IV ist historisch gÃ¼nstig zu kaufen.

**Strategie: Long Calendar Spread**
- BUY 1 Option (60â€“90 DTE) + SELL 1 Option (30 DTE, gleicher Strike)
- Net: Debit, aber positives Vega â€” Anstieg der IV profitiert die Position

**Ziel:** Kassieren der IV-Expansion, wenn IV vom Tief steigt. Calendars sind "VolatilitÃ¤tswetten" ohne groÃŸes Direktionalrisiko.

**Risk-Management:** Calendars verlieren bei sehr starken Kursbewegungen (Underlying bewegt sich weit weg vom Strike). Daher: Strike nahe am Kurs wÃ¤hlen; Small Size.

**FÃ¼r Familie Rehse:** Im aktuellen Regime (VIX 18â€“19) sind Calendars als ErgÃ¤nzung zum Short-Premium-Core sinnvoll, um das Portfolio-Vega zu neutralisieren.

---

### 5.3 Earnings-Plays: Short Strangle vor Earnings vs. nach IV-Crush

**Short Strangle VOR Earnings:**  
Hohe PrÃ¤mien durch Earnings-Unsicherheit einsammeln, aber vor dem Event schlieÃŸen. EXTREM RISKANT: Eine Gap-Bewegung von Â±15â€“25% kann maximale Verluste generieren.

**âš ï¸ Nicht kompatibel mit CSP-Regelwerk der Familie Rehse** (Earnings-Abstand â‰¥ 8 Tage Pflicht).

**Post-Earnings IV-Crush-Strategie:**  
Nach dem Earnings-Event fÃ¤llt die IV schlagartig. Wer NACH Earnings in Short-Premium einsteigt, profitiert von:
1. Historisch hoher IVR (80â€“95% nach Crash/Miss)
2. Normalisierung der IV in den folgenden 2â€“4 Wochen
3. ErhÃ¶hte PrÃ¤mien ohne binÃ¤res Earnings-Risiko

**Paradebeispiel (CSP-Regelwerk April 2026):**  
NOW fiel am 24. April 2026 um â€“17,75% nach Earnings-Beat. IVR stieg auf 94. CSP auf $78 Strike (8% OTM bei $86 Kurs), 55 DTE â†’ 36,6% annualisierte Rendite vs. normalem Niveau von 12â€“18%.

**Win-Rate-Daten (Tastylive):**  
Short Strangles nach Earnings-IV-Crush: Win-Rate â‰¥ 75â€“80% in Zeitfenstern 30â€“45 DTE, da IV-Normalisierung statistisch zuverlÃ¤ssig ist.

---

### 5.4 Forward Volatility Trades (Calendar Sells)

**Konzept:**  
Calendar Sells (Short Calendar, Long kurzlaufend, Short langlaufend) profitieren, wenn kurzlaufende IV Ã¼berproportional teuer ist (Backwardation). Sie sind die umgekehrte Wette zu Long Calendars.

**Praktisch selten eingesetzt** â€” die meisten Premium-Seller bevorzugen Long Calendars fÃ¼r die Vega-Diversifikation. Short Calendars sind nur in extremem Backwardation (VIX-Spike, Krisenumfeld) relevant.

---

## 6. Strategien-Auswahlmatrix

### 6.1 Haupt-Matrix: Marktregime Ã— IVR

| Marktregime | IVR < 20% | IVR 20â€“40% | IVR 40â€“60% | IVR > 60% |
|---|---|---|---|---|
| **VIX < 15** | Long Calendar; Long Straddle; LEAPS kaufen | Nur Bull/Bear Spreads | CSP selektiv; IC mÃ¶glich | CSP, IC, Strangle aktiv |
| **VIX 15â€“20** | Long Calendar; PMCC | Bull Put Spread; IC auf SPY/QQQ | CSP (IVR-Pflicht erfÃ¼llt); IC; Jade Lizard | CSP + Jade Lizard; Short Strangle; IC |
| **VIX 20â€“30** | Long Calendar als Vega-Hedge | Short Strangle; Iron Condor; CSP | CSP; Wheel; Short Strangle; Jade Lizard | Alle Premium-Selling; Post-Earnings CSP |
| **VIX > 30** | Small-Size Calendars; Defensive | Defensive; Rollen bestehender Positionen | CSP (Klein-Size); Defined Risk Spreads | CSP (sehr hohe PrÃ¤mien); kleine Positionen; primÃ¤r Hedge |

### 6.2 Ampelsystem

| Ampel | Bedingung | Handlung |
|---|---|---|
| ðŸ”´ Rot | VIX > 40 ODER ungelÃ¶ster Marktschock | Alle neuen Positionen pausieren. Bestehende verteidigen. Tail-Hedges aktivieren. |
| ðŸŸ¡ Gelb | VIX 15â€“20 und IVR < 40% | Nur Titel mit IVR â‰¥ 40% zulÃ¤ssig. Kleinere PositionsgrÃ¶ÃŸen. Kein neues Kapital deployen. |
| ðŸŸ¢ GrÃ¼n (normal) | VIX 20â€“30, IVR 40â€“70% | Volle Deployment-Bereitschaft. CSP + Wheel + Jade Lizard aktiv. |
| ðŸŸ¢ðŸŸ¢ GrÃ¼n+ | VIX > 25, IVR > 70% (Post-Crash oder Post-Earnings) | Maximale Premium-Selling. Beste Einstiegsgelegenheiten. Priorisierung post-Earnings-CSPs. |

### 6.3 Strategie-Schnellauswahl nach Marktsituation

| Situation (April 2026-analog) | Empfohlene Strategie(n) |
|---|---|
| Einzeltitel nach â€“15% Earnings-Crash, IVR 90% | CSP (55 DTE, 8% OTM) â†’ spÃ¤ter CC (Wheel) |
| VIX 20, breiter Markt stabil | Iron Condor auf SPY/QQQ; CSPs auf Einzeltiteln |
| Geopolitisches Risiko (Iran), VIX steigt | VIX-Calls als Tail-Hedge; Put Spread auf SPY |
| Bestehende Aktienposition stark gestiegen | Zero-Cost Collar; oder Covered Call |
| VIX < 15, IV extrem gÃ¼nstig | Long Calendar Spreads; LEAPS kaufen fÃ¼r PMCC |
| Post-Assignment, Aktie im Depot | Covered Call (Wheel Phase 2) |
| Starke bullische Meinung, kein Aktie gewÃ¼nscht | PMCC (LEAPS + Short Call Diagonal) |

---

## 7. Greeks-Management auf Portfolioebene

### 7.1 Net Delta, Net Theta, Net Vega Steuerung

Auf Portfolioebene addieren sich alle Einzel-Greeks zu einem **Netto-Greek-Profil**. Das Ziel ist nicht perfekte NeutralitÃ¤t, sondern ein kontrollierbares und gewÃ¼nschtes Profil.

**TÃ¤gliche Ãœberwachungsroutine:**

| Greek | Zielbereich (Short-Premium-Portfolio) | Alarm-Signal |
|---|---|---|
| **Net Delta** | Leicht positiv (+$500 bis +$2.000 je $1 Marktbewegung) | Delta > +$5.000 = unbeabsichtigtes bullisches Klumpenrisiko |
| **Net Theta** | Stark positiv (â‚¬500â€“â‚¬2.000/Tag bei 16 Mio. EUR Portfolio) | Theta < $200/Tag = zu wenig Theta-Income fÃ¼r Strategie |
| **Net Vega** | Negativ, aber begrenzt (â€“$3.000 bis â€“$8.000 je 1% IV-Anstieg) | Vega < â€“$15.000 = gefÃ¤hrliches Vega-Exposure bei VIX-Spike |
| **Net Gamma** | Negativ (kurz vor 21 DTE: kritisch Ã¼berwachen) | Konzentrierte Gamma vor Earnings/Marktereignissen |

**Quelle fÃ¼r Methodik:** [WealthBee Portfolio Greeks Analysis](https://wealthbee.io/learn/options-portfolio-greeks-analysis/) und [Options Trading IQ](https://optionstradingiq.com/how-to-hedge-vega-risk/)

---

### 7.2 Beispiel fÃ¼r Delta-Neutral-Aufbau

**Ausgangsposition:** Short 10 CSPs auf MSFT (Delta je â€“0,22) = Portfolio-Delta +22,0 (bullish)

**Schritt 1:** Analyse: Ist +22 Delta gewÃ¼nscht? Bei bullischer Marktmeinung: Ja. Bei neutraler Sicht: Ã¼bersteuert.

**Schritt 2 (Hedging):** Zur Neutralisierung:
- Option A: BUY 22 MSFT-Aktien ($530/Aktie Ã— 22 = $11.660 Kapitaleinsatz)
- Option B: BUY 1 MSFT Bear Call Spread (Delta â€“0,20 je Spread) = gÃ¼nstigere LÃ¶sung
- Option C: SELL 1 MSFT Covered Call auf bestehende Aktien (aus frÃ¼heren Assignments)

**Praxishinweis:** FÃ¼r ein reines Einkommensportfolio ist leicht positives Delta (bullish bias) erwÃ¼nscht und korrekt â€” es spiegelt die Investment-Grundannahme (MÃ¤rkte steigen langfristig) wider. Delta-Hedging ist nur notwendig, wenn die Richtungsrisiken das Portfolio-Risikobudget Ã¼bersteigen.

---

### 7.3 Vega-Risiko bei Short-Premium-Portfolios in VIX-Spikes

**Das Problem:**  
Ein Portfolio aus 7â€“10 CSPs auf hochvolatile Tech-Titel (NOW, AVGO, MSFT, DDOG) trÃ¤gt stark negatives Vega. Bei einem VIX-Spike von 18 auf 30 (+12 Punkte):

**Beispielrechnung:**
- 10 CSP-Positionen mit Vega je â€“$500 = Portfolio-Vega â€“$5.000
- VIX-Anstieg +12 IV-Punkte Ã— â€“$5.000 = â€“$60.000 unrealisierter Verlust
- (Nicht-realisiert, solange nicht vorzeitig geschlossen)

**GegenmaÃŸnahmen:**

| Methode | Mechanismus | Kosten |
|---|---|---|
| **VIX-Calls (OTM)** | Positives Vega, uncorrelated mit Einzel-Aktien | $200â€“$500/Monat fÃ¼r sinnvollen Schutz |
| **Long Calendar Spreads** | Positives Netto-Vega | Debit $500â€“$1.500 je Spread |
| **KÃ¼rzere DTE bei neuen Positions** | Weniger Vega-Exposure je Position | Weniger Theta, aber weniger Vega-Risiko |
| **Defined-Risk-Spreads (Iron Condors)** | Limitiertes Vega durch gekaufte FlÃ¼gel | Niedrigere PrÃ¤mie als Naked-Struktur |

**SchlÃ¼sselprinzip (nach [Options Trading IQ](https://optionstradingiq.com/how-to-hedge-vega-risk/)):**  
Das Ziel ist nicht Vega-NeutralitÃ¤t, sondern **balancierte Vega-Exposition**. 10â€“20% des Portfolios in Long-Vega-Strukturen (Calendars, LEAPS) kompensiert das negative Vega aus dem Short-Premium-Kern.

---

## 8. Backtest-Erkenntnisse / Quantitative Evidenz

### 8.1 CBOE-Studien zu Index-Optionsstrategien

**CBOE S&P 500 PutWrite Index (PUT) â€” 30 Jahre Daten:**

| Kennzahl | PUT Index | S&P 500 Total Return |
|---|---|---|
| Annualisierte Rendite | 10,13% (1986â€“2015) | 9,80% |
| VolatilitÃ¤t (Standardabweichung) | 9,91% | 15,39% |
| Sharpe Ratio | **0,67** | 0,47 |
| Max. Drawdown | â€“33% | â€“51% |

**Quelle:** [CBOE PutWrite Index Wikipedia](https://en.wikipedia.org/wiki/CBOE_S%26P_500_PutWrite_Index); [CBOE Strategy Benchmark Indexes](https://www.cboe.com/insights/posts/key-cboe-benchmark-indexes-using-spx-options-offer-strong-risk-adjusted-returns/)

**Interpretation:**  
Der PUT-Index Ã¼bertrifft den S&P 500 auf risikoadjustierter Basis um 43% im Sharpe-VerhÃ¤ltnis, bei 36% niedrigerer VolatilitÃ¤t und 35% niedrigerem Max. Drawdown. Dies ist die stÃ¤rkste quantitative Rechtfertigung fÃ¼r systematisches CSP/Put-Selling.

**CBOE BuyWrite Index (BXM) â€” Covered Call:**

| Kennzahl | BXM | S&P 500 |
|---|---|---|
| Annualisierte Rendite (1988â€“2004) | 12,39% | 12,20% |
| VolatilitÃ¤t | ~10% | ~15% |
| Sharpe | HÃ¶her | Niedriger |

**Quelle:** [Ibbotson BXM Study](https://www.borntosell.com/covered-call-blog/buy-write-options-strategy); [CBOE Q4 2018 Bericht](https://www.cboe.com/insights/posts/key-cboe-benchmark-indexes-using-spx-options-offer-strong-risk-adjusted-returns/)

**Wichtiger Befund:** Bei Ã¼berbewerteten MÃ¤rkten (Shiller-CAPE im obersten Quartil) Ã¼bertrifft der PUT-Index den S&P 500 sogar auf absoluter Basis: +10,84% vs. Marktrendite, bei Sharpe 0,965 vs. 0,672. ([RJA Whitepaper](https://www.rja-llc.com/wp-content/uploads/2023/10/RJA-PutWrite-Strategies-and-Market-Valuation-Levels-Oct-2017.pdf))

---

### 8.2 Tastylive-Studien zu Short-Premium-Strategien

**Credit Spreads nach DTE:**  
[Tastylive Backtest-Studie](https://www.tastylive.com/news-insights/backtesting-duration-in-credit-spreads): Win-Rate fÃ¼r Credit Put Spreads bei 15, 45 und 75 DTE: alle â‰¥ 88% (Management auf 50%). Average P/L steigt mit DTE â€” 75 DTE hat hÃ¶chste absolute Rendite.

**Iron Condor Wing-Effizienz:**  
[Tastylive Iron Condor-Studie](https://www.tastylive.com/news-insights/maximizing-profits-the-art-of-the-iron-condor-wingspan) auf 15 Jahren SPY-Daten:
- Optimale FlÃ¼gelbreite: $10â€“$20 (â‰ˆ 1/10 des Aktienkurses)
- Breitere FlÃ¼gel â†’ hÃ¶here Win-Rate, schnelleres Erreichen des 50%-Gewinnziels
- Management bei 21 DTE: beste Risikominimierung

**Strangles vs. Iron Condors ([10-Jahres-Studie](https://www.youtube.com/watch?v=Wt90xWeRuMQ)):**
- Short Strangles: 10â€“15% hÃ¶here Win-Rate als Iron Condors
- Bei IVR > 40%: Return on Capital fÃ¼r Strangles fast doppelt so hoch wie bei Iron Condors
- 20â€“30-Delta-Strangles optimal (nicht zu nah am Kurs, nicht zu weit OTM)
- Management bei 21 DTE: hÃ¶chste Gesamtrendite

**Wheel-Strategie ([QuantConnect Backtest](https://www.quantconnect.com/research/17871/automating-the-wheel-strategy/)):**
- Sharpe-Ratio Wheel auf SPY: **1,083**
- Sharpe-Ratio Buy-and-Hold SPY: **0,700**
- Wheel Ã¼bertrifft Buy-and-Hold auf risikoadjustierter Basis um 55%

---

### 8.3 Earnings-Trade Win-Rates

**Datenlage aus Tastylive-Forschung:**
- Short Strangles NACH Earnings-IV-Crush (30â€“45 DTE): Win-Rate **75â€“80%**
- IV-Normalisierung nach Earnings: statistisch zuverlÃ¤ssig innerhalb von 2â€“4 Wochen
- Beste Gelegenheiten: Titel, die trotz Earnings-Beat fallen (idiosynkratischer KursrÃ¼ckgang bei fundamentaler Intaktheit = extremes IVR-Spike-Szenario)

**Beispiel-Kalibrierung (April 2026):**
- NOW nach â€“17,75% KursrÃ¼ckgang: IVR 94% â†’ annualisierte CSP-Rendite 36,6%
- Normales NOW-Niveau: IVR 25â€“40% â†’ 12â€“18% annualisierte Rendite
- Premium-Uplift durch Sondersituation: +100â€“200%

---

## 9. Praktische Order-AusfÃ¼hrung (Broker-agnostisch)

Dieser Abschnitt beschreibt allgemein gÃ¼ltige AusfÃ¼hrungsprinzipien fÃ¼r Optionsstrategien. Die konkreten MenÃ¼pfade und SystemoberflÃ¤chen variieren je nach Broker.

### 9.1 Order-Typen fÃ¼r Optionen

| Order-Typ | Beschreibung | Empfehlung fÃ¼r Optionen |
|---|---|---|
| **Limit Order** | AusfÃ¼hrung nur zu spezifiziertem Preis oder besser | **Standard fÃ¼r alle OptionserÃ¶ffnungen.** Niemals Market Orders bei Optionen. |
| **Market Order** | AusfÃ¼hrung zum aktuellen Marktpreis | Strikt vermeiden â€” hohe Slippage bei Optionen, besonders bei weitem Bid-Ask-Spread |
| **Stop-Limit** | Stop triggert Limit Order | FÃ¼r Verlust-Stop-Loss auf offene Positionen (z.B. 200% der ursprÃ¼nglichen PrÃ¤mie) |
| **GTC (Good Till Cancelled)** | Order bleibt aktiv bis manuell storniert | FÃ¼r Gewinnmitnahme-Orders (50% Gewinn) und Verlust-Stops |
| **Combo/Multi-Leg** | Gleichzeitige AusfÃ¼hrung mehrerer Legs | FÃ¼r Iron Condors, Strangles, Calendars â€” reduziert Legging-Risiko |

### 9.2 Mid-Point-Routing und Slippage-Minimierung

**Bid-Ask-Spread bei Optionen:**  
Der wichtigste Kostenfaktor bei Optionshandel ist der Bid-Ask-Spread (nicht die Kommission). Bei einem Spread von $0,10 kostet jeder Trade $5 je Kontrakt versteckten "Spread-Tax".

**Strategie:**
1. **Mid-Point als Startpunkt:** Limit-Order immer am Mittelpunkt zwischen Bid und Ask platzieren
2. **Schrittweise Anpassung:** Bei Non-Fill nach 2â€“5 Minuten: Limit in 1-Cent-Schritten Richtung natÃ¼rlicher Preis verschieben
3. **Nie Market Order:** Market Orders bei Optionen werden fast immer zum Ask (beim Kauf) oder zum Bid (beim Verkauf) ausgefÃ¼hrt = maximale Slippage

**FÃ¼r Combo-Orders (Iron Condor, Strangle):**  
Multi-Leg-Orders als garantierte Kombination platzieren, um Legging-Risiko zu eliminieren. Nachteil: hÃ¶here Slippage-Wahrscheinlichkeit als bei sequentiellem Legging. Empfehlung: Kombinations-Order bevorzugen, wenn Bid-Ask-Spreads beider Legs < $0,05 sind.

**LiquiditÃ¤tsprÃ¼fung vor Orderaufgabe:**
- Optionsvolumen > 50.000 Kontrakte/Tag (Pflichtkriterium CSP-Regelwerk)
- Open Interest > 1.000 Kontrakte am gewÃ¼nschten Strike/Verfall
- Bid-Ask-Spread â‰¤ $0,05 fÃ¼r Einzeltitel; â‰¤ $0,02â€“$0,03 fÃ¼r ETFs (SPY, QQQ)

### 9.3 Margin- vs. Cash-Secured-Anforderungen

**Cash-Secured Put (100% Deckung):**
- Kapitalbindung: Strike Ã— 100 Aktien Ã— Anzahl Kontrakte
- Beispiel: CSP $78 Strike Ã— 100 = $7.800 je Kontrakt
- Voraussetzung: Entsprechende Cash-Reserve vor Orderaufgabe bestÃ¤tigen
- Kein Margin-Call-Risiko. Volle AusÃ¼bungsbereitschaft.

**Margin-Anforderungen (Referenz, variiert je Broker):**
- Naked Put (Reg-T-Margin): ca. 20% des Nominalwerts + Optionspreis
- Naked Put (Portfolio-Margin): ca. 15â€“25% je nach VolatilitÃ¤t
- Iron Condor: Breite des breiteren Spreads Ã— 100 â€“ Nettokredit
- CSP vs. Naked Put: Gleiche Strategie, aber CSP = 100% Cash vs. Margin = 20â€“30% â†’ 3â€“5Ã— Kapitaleffizienz bei Margin

**Empfehlung fÃ¼r Familie Rehse:**  
FÃ¼r den Core-CSP-Betrieb bleibt 100% Cash-Deckung das Pflichtprinzip (CSP-Regelwerk). FÃ¼r Erweiterungsstrategien (Iron Condors, Strangles) in der Trading-GmbH-Struktur kÃ¶nnen margin-basierte Anforderungen genutzt werden, da dort kein PrivatvermÃ¶gen gefÃ¤hrdet ist.

### 9.4 Roll-Execution (praktisch)

**Roll = SchlieÃŸen der alten + ErÃ¶ffnen der neuen Position als Kombination:**
1. BUY TO CLOSE alte Short-Option (Debit)
2. SELL TO OPEN neue Short-Option (Credit)
3. Als Spread-Order mit Limit = Nettokredit â‰¥ $0,05 platzieren

**Regel:** Rollen nur fÃ¼r Net-Credit (d.h. mehr vereinnahmen als ausgegeben). Bei Net-Debit: Assignment akzeptieren oder Verlust realisieren.

**Roll-Timing:**
- Bei 21 DTE (mechanisches Rollen nach Regelwerk)
- Oder wenn 50% Gewinn noch nicht erreicht und DTE noch > 21

---

## 10. Deutsche Steuerwirkung pro Strategie

### 10.1 PrivatvermÃ¶gen: Ãœberblick

**Grundsatz:**  
Alle ErtrÃ¤ge aus Optionshandel im PrivatvermÃ¶gen unterliegen der **Abgeltungssteuer von 25% + 5,5% SolidaritÃ¤tszuschlag = 26,375%** (ohne Kirchensteuer). Freistellungsauftrag: â‚¬1.000 je Person (â‚¬2.000 bei Verheirateten).

**Auslandsbroker-Besonderheit:**  
Bei Auslandsbroker-Konten (ohne deutsches Institut als Depotbank) erfolgt kein automatischer Quellensteuerabzug. Alle ErtrÃ¤ge sind selbst in der **Anlage KAP** der EinkommensteuererklÃ¤rung zu deklarieren. Monatliche Trade-Dokumentation (Datum, PrÃ¤mie, GebÃ¼hren, ggf. Assignment) ist Pflicht.

**JStG 2024 â€” VerlustverrechnungsbeschrÃ¤nkung aufgehoben:**  
Die vormalige BeschrÃ¤nkung der Verlustverrechnung bei TermingeschÃ¤ften auf â‚¬20.000/Jahr wurde durch das [Jahressteuergesetz 2024](https://www.lohnsteuer-kompakt.de/steuerwissen/verluste-aus-termingeschaeften-steuererleichterung-fuer-anleger/) **ersatzlos gestrichen**. Zustimmung Bundesrat: 22. November 2024. RÃ¼ckwirkend ab 2020 fÃ¼r alle offenen FÃ¤lle.

Quelle: [DeltaValue Besteuerung Optionen 2025](https://www.deltavalue.de/besteuerung-von-optionen/), [Lohnsteuer-Kompakt JStG 2024](https://www.lohnsteuer-kompakt.de/steuerwissen/verluste-aus-termingeschaeften-steuererleichterung-fuer-anleger/)

---

### 10.2 Strategie-spezifische Steuerbehandlung (PrivatvermÃ¶gen)

| Strategie | Steuerlicher Vorgang | Zeitpunkt | Steuersatz |
|---|---|---|---|
| **CSP: PrÃ¤mie vereinnahmt** | Kapitalertrag aus StillhaltergeschÃ¤ft | Bei Vereinnahmung (ErÃ¶ffnung) | 26,375% |
| **CSP: VerfÃ¤llt wertlos** | Kein weiterer Vorgang (PrÃ¤mie bereits versteuert) | Verfall = kein neues Ereignis | â€” |
| **CSP: RÃ¼ckkauf (50%-Gewinn)** | Ausgabe (RÃ¼ckkaufpreis) mindert bereits versteuerte PrÃ¤mie nicht â€” neuer Verlust als TermingeschÃ¤ftsverlust | SchlieÃŸen der Position | Verrechenbar mit anderen KapErtr. |
| **CSP: Assignment** | PrÃ¤mie = eigener TermingeschÃ¤ftsgewinn (bereits versteuert). Aktien-Einstandskurs = Strike-Preis. | AusÃ¼bung | PrÃ¤mie schon versteuert; Aktien-KK = Strike |
| **Covered Call: PrÃ¤mie** | Kapitalertrag Stillhalter | Bei Vereinnahmung | 26,375% |
| **Covered Call: Assignment** | Aktienverkauf zum Strike-Preis; Gewinn/Verlust auf Aktie als Kapitalertrag | AusÃ¼bung | 26,375% auf Aktiengewinn |
| **Iron Condor / Spreads** | Alle vier Legs einzeln erfasst | ErÃ¶ffnung (Kredit) + SchlieÃŸung | 26,375% |
| **Long Put (Hedge)** | Kauf = Anschaffungskosten; Verkauf/Verfall = Kapitalertrag oder -verlust | SchlieÃŸen/Verfall | 26,375%; Verlust verrechenbar (JStG 2024) |
| **Rollen** | SchlieÃŸen (Verlust oder Gewinn) + NeuerÃ¶ffnung (neuer PrÃ¤mienertrag) â€” zwei separate steuerliche VorgÃ¤nge | Rollzeitpunkt | Beide Legs einzeln |

**Wichtige Praxishinweise:**
- Rollen = zwei separate steuerliche VorgÃ¤nge (SchlieÃŸung + NeuerÃ¶ffnung). Dokumentation beider Beine ist Pflicht.
- Einstandskurs nach Assignment = Strike (nicht Strike minus PrÃ¤mie). Die PrÃ¤mie ist ein **eigenstÃ¤ndiger, separat versteuerter TermingeschÃ¤ftsgewinn**.
- Verluste aus CSP-RÃ¼ckkÃ¤ufen (z.B. bei 200%-Verlust-Stop) sind seit JStG 2024 unbeschrÃ¤nkt mit allen KapitalertrÃ¤gen verrechenbar.

---

### 10.3 Trading GmbH: Â§8b KStG und Steuerstruktur

**Kernvorteil:**  
In einer deutschen GmbH, die als Trading-Gesellschaft fungiert, profitiert der Aktienverkauf nach Assignment von **Â§8b Abs. 2 KStG**: VerÃ¤uÃŸerungsgewinne aus Aktien sind zu **95% steuerfrei**. Lediglich 5% gelten als nicht-abzugsfÃ¤hige Betriebsausgaben ("Schachtelstrafe").

**Effektive Steuerbelastung auf Aktiengewinne:**
- KSt 15% + 5,5% Soli + GewSt ~15% = ~30,83% auf 5% des Gewinns = **ca. 1,5% effektiv**
- PrivatvermÃ¶gen: 26,375% auf 100% = 26,375% effektiv
- **Vorteil Trading GmbH: 24,9 Prozentpunkte Steuerersparnis auf Aktiengewinne**

Quellen: [Steuerberatung Neeb Â§8b KStG](https://steuerberatung-neeb.de/steuerfreie-dividenden-und-veraeusserungsgewinne-fuer-kapitalgesellschaften/), [CPM Steuerberater Trading GmbH](https://www.cpm-steuerberater.de/news/entry/2026/01/09/9503-trading-gmbh-8b-kstg-streubesitzdividenden-gewerbesteuer), [KASPER & KÃ–BER Â§8b](https://www.steuernsteuern.de/blog/artikel/aktien-steuerfrei-verkaufen)

---

### 10.4 Steuervergleich Trading GmbH vs. PrivatvermÃ¶gen

| Ertragsart | PrivatvermÃ¶gen | Trading GmbH |
|---|---|---|
| **OptionsprÃ¤mien (Stillhalter)** | 26,375% | ~30,83% (KSt + GewSt) |
| **Aktiengewinne nach Assignment** | 26,375% | **~1,5%** (Â§8b KStG) |
| **Dividenden (< 10% Beteiligung)** | 26,375% | Voll kÃ¶rperschaft- und gewsteuerpflichtig (Â§8b Abs. 4) |
| **Fremdkapitalzinsen** | Nicht abzugsfÃ¤hig (privat) | 100% Betriebsausgabe (Zinsschranke bei 3 Mio. Freigrenze unproblematisch) |
| **Verluste aus TermingeschÃ¤ften** | UnbeschrÃ¤nkt verrechenbar (JStG 2024) | UnbeschrÃ¤nkt verrechenbar als Betriebsausgaben |

**Schlussfolgerung:**  
Die Trading GmbH ist besonders attraktiv, wenn:
1. HÃ¤ufige Assignments erwartet werden (Wheel-Strategie)
2. AktienbestÃ¤nde langfristig gehalten und spÃ¤ter mit erheblichem Gewinn verÃ¤uÃŸert werden
3. Fremdfinanzierung genutzt wird (FK-Zinsen vollstÃ¤ndig absetzbar)

Die OptionsprÃ¤mien selbst werden in der GmbH steuerlich nicht besser behandelt als privat (sogar leicht schlechter durch GewSt). Der Â§8b-Effekt wirkt ausschlieÃŸlich auf den spÃ¤teren Aktienverkaufsgewinn.

---

### 10.5 Roll-VorgÃ¤nge steuerlich (beide Strukturen)

**Steuerlicher Grundsatz:**  
Jedes Rollen ist eine SchlieÃŸung + eine NeuerÃ¶ffnung. Zwei eigenstÃ¤ndige steuerliche Ereignisse:

1. **SchlieÃŸung (BUY TO CLOSE):** Differenz zwischen ursprÃ¼nglich erhaltener PrÃ¤mie und RÃ¼ckkaufpreis = Gewinn oder Verlust. Dieser ist unmittelbar verrechenbar.
2. **NeuerÃ¶ffnung (SELL TO OPEN):** Neue PrÃ¤mie = neuer steuerpflichtiger Ertrag bei Vereinnahmung (PrivatvermÃ¶gen: sofort bei Eingang; GmbH: Betriebsertrag im Wirtschaftsjahr).

**Nettokredit-Rollen:**  
Das Net-Credit-Prinzip hat auch steuerliche Logik: der Kredit sichert, dass trotz Verlust beim SchlieÃŸen (Debit) insgesamt ein positiver Cashflow entsteht.

**Dokumentationspflicht:**  
FÃ¼r jeden Roll: Datum, Ticker, Original-PrÃ¤mie, RÃ¼ckkaufpreis, Verlust, neue PrÃ¤mie, neuer Strike, neuer Verfall. Bei Auslandsbrokern ohne deutschen Quellensteuerabzug: monatliche Eigenerfassung obligatorisch, da keine deutsche Jahressteuerbescheinigung ausgestellt wird.

---

## 11. Quellen und Referenzen

### PrimÃ¤re Datenquellen

| Quelle | Inhalt | URL |
|---|---|---|
| **Tastylive (Tastytrade)** | Backtests, Market Measures, Strategy Guides | [tastylive.com](https://www.tastylive.com) |
| **CBOE Strategy Benchmarks** | PutWrite (PUT), BuyWrite (BXM), VIX Tail Hedge | [cboe.com/us/indices/benchmark_indices](https://www.cboe.com/us/indices/benchmark_indices/) |
| **CBOE PutWrite Index (Wikipedia)** | 30-Jahre-Performancedaten | [en.wikipedia.org/wiki/CBOE_S%26P_500_PutWrite_Index](https://en.wikipedia.org/wiki/CBOE_S%26P_500_PutWrite_Index) |
| **CBOE Benchmark Insights** | Sharpe-Ratio Vergleich Ã¼ber 32,5 Jahre | [cboe.com/insights](https://www.cboe.com/insights/posts/key-cboe-benchmark-indexes-using-spx-options-offer-strong-risk-adjusted-returns/) |

### Strategiequellen

| Quelle | Inhalt | URL |
|---|---|---|
| **Tastylive: Iron Condor Wing Study** | Optimale FlÃ¼gelbreite, 15-Jahres-Analyse | [tastylive.com/news-insights/maximizing-profits](https://www.tastylive.com/news-insights/maximizing-profits-the-art-of-the-iron-condor-wingspan) |
| **Tastylive: Credit Spread DTE Study** | Win-Rates nach DTE, 45-DTE-Optimum | [tastylive.com/news-insights/backtesting-duration](https://www.tastylive.com/news-insights/backtesting-duration-in-credit-spreads) |
| **Tastylive: Strangle Sweet Spot** | 20-30-Delta-Strangles, hohes IV verdoppelt Returns | [tastylive.com/shows/market-measures](https://www.tastylive.com/shows/market-measures/episodes/profit-expectations-and-strategy-06-08-2022) |
| **Tastylive: Jade Lizard Guide** | Setup, Struktur, Tastylive-Methodik | [tastylive.com/concepts-strategies/jade-lizard](https://www.tastylive.com/concepts-strategies/jade-lizard) |
| **Tastylive: Wheel Strategy** | CSP â†’ Covered Call â†’ Wheel | [tastylive.com/shows/options-trading-concepts](https://www.tastylive.com/shows/options-trading-concepts-live/episodes/the-wheel-strategy-short-put-to-covered-call-07-27-2021) |
| **QuantConnect: Wheel Backtest** | Sharpe 1,083 vs. SPY 0,70 | [quantconnect.com/research/17871](https://www.quantconnect.com/research/17871/automating-the-wheel-strategy/) |
| **RJA Whitepaper: PutWrite vs. CAPE** | PUT-Index-Outperformance bei Ãœberbewertung | [rja-llc.com](https://www.rja-llc.com/wp-content/uploads/2023/10/RJA-PutWrite-Strategies-and-Market-Valuation-Levels-Oct-2017.pdf) |
| **Fidelity: Ratio Put Spread** | 1Ã—2 Ratio-Spread ErlÃ¤uterung | [fidelity.com/options-guide/1x2-ratio](https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/1x2-ratio-volatility-spread-puts) |

### Hedging-Quellen

| Quelle | Inhalt | URL |
|---|---|---|
| **Option Alpha: VIX Hedging Strategy** | Short Call Ladder + Doomsday Calls, Case Study | [optionalpha.com/blog/vix-portfolio-hedging](https://optionalpha.com/blog/vix-portfolio-hedging-strategy) |
| **iVolatility: VIX Tail Hedge** | VIX-Call-Backstrategy ErlÃ¤uterung | [ivolatility.com/news/3000](https://www.ivolatility.com/news/3000) |
| **Savant Wealth: Zero-Cost Collar** | Historische Performancedaten, Kosten-Analyse | [savantwealth.com](https://savantwealth.com/savant-views-news/article/the-zero-cost-collar-a-strategy-to-limit-your-lossesand-gains/) |
| **QuantPedia: VIXY Tail Hedge** | VIX-basiertes Sizing, dynamische Hedge-Modelle | [quantpedia.com](https://quantpedia.com/hedging-tail-risk-with-robust-vixy-models/) |

### Steuerquellen (Deutschland)

| Quelle | Inhalt | URL |
|---|---|---|
| **DeltaValue: Besteuerung von Optionen** | PrivatvermÃ¶gen, Abgeltungssteuer, JStG 2024 | [deltavalue.de/besteuerung-von-optionen](https://www.deltavalue.de/besteuerung-von-optionen/) |
| **Lohnsteuer-Kompakt: JStG 2024** | Aufhebung VerlustverrechnungsbeschrÃ¤nkung | [lohnsteuer-kompakt.de](https://www.lohnsteuer-kompakt.de/steuerwissen/verluste-aus-termingeschaeften-steuererleichterung-fuer-anleger/) |
| **CPM Steuerberater: Trading GmbH** | Â§8b KStG, Streubesitzdividenden, GewSt | [cpm-steuerberater.de](https://www.cpm-steuerberater.de/news/entry/2026/01/09/9503-trading-gmbh-8b-kstg-streubesitzdividenden-gewerbesteuer) |
| **Steuerberatung Neeb: Â§8b KStG** | Detaillierte Â§8b-ErlÃ¤uterung, Schachtelstrafe | [steuerberatung-neeb.de](https://steuerberatung-neeb.de/steuerfreie-dividenden-und-veraeusserungsgewinne-fuer-kapitalgesellschaften/) |
| **KASPER & KÃ–BER: Aktien steuerfrei** | Â§8b GmbH vs. PrivatvermÃ¶gen Vergleich | [steuernsteuern.de](https://www.steuernsteuern.de/blog/artikel/aktien-steuerfrei-verkaufen) |
| **Deutsche Bank: Steuertext Optionen** | Offizieller Banktext, Optionen im BV | [deutsche-bank.de/dam/steuertext-optionen](https://www.deutsche-bank.de/dam/deutschebank/de/shared/pdf/rechtliche-hinweise/steuertexte/250213_Steuertext-Optionen.pdf) |
| **Geldschnurrbart: Optionen Steuer 2026** | Praxisorientierte SteuerfÃ¼hrung | [geldschnurrbart.de](https://geldschnurrbart.de/geld-anlegen/optionen/optionen-steuer/) |

### Greeks & Portfolio-Management

| Quelle | Inhalt | URL |
|---|---|---|
| **Options Trading IQ: Vega Hedge** | Vega-Hedging Strategien, Routine | [optionstradingiq.com/how-to-hedge-vega-risk](https://optionstradingiq.com/how-to-hedge-vega-risk/) |
| **WealthBee: Portfolio Greeks** | WÃ¶chentlicher Greeks-Review-Prozess | [wealthbee.io/learn/options-portfolio-greeks](https://wealthbee.io/learn/options-portfolio-greeks-analysis/) |
| **Michael Brenndoerfer: Greeks & Risk** | Delta-Gamma-NeutralitÃ¤t, Formeln | [mbrenndoerfer.com/greeks-option-risk-management](https://mbrenndoerfer.com/writing/greeks-option-risk-management-delta-gamma-theta-vega) |

### Interne Quellen (Familie Rehse Space)

| Dokument | Inhalt |
|---|---|
| **CSP-Regelwerk April 2026** | VollstÃ¤ndige operationale Regeln, Titeluniversum, Workflow |
| **Portfolio-Ãœbersicht April 2026** | Aktuelles GesamtvermÃ¶gen, Positionen, Asset-Klassen |
| **MakroÃ¶konomischer Kontext April 2026** | VIX-Regime, Iran-Konflikt, Zollpolitik, Szenarien |

---

*Erstellt: April 2026 | Grundlage: Tastylive Research, CBOE-Studiendaten, Deutsche Steuerquellen, interne Portfoliodokumentation Familie Rehse | ÃœberprÃ¼fung empfohlen: Q3 2026 oder bei wesentlichen RegelÃ¤nderungen (Steuer, Marktregime)*

*Vertraulich â€” ausschlieÃŸlich interner Gebrauch Familie Rehse*
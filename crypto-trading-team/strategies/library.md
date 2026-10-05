# Strategy Library — 115 candidates for the Strategy Lab

> مكتبة أفكار، موش وصفات ربح. كل استراتيجية هنا حالتها **IDEA** لين ما تعدّي اختبارات المختبر (backtest 100+ صفقة، اختبار خارج العينة، أسبوعين Paper). ولا وحدة مضمونة.

**How the strategist uses this file**

- This is a pool of ideas with written rules. Nothing here is approved. Status lives in `reports/strategies.md` (IDEA → BACKTESTED → PAPER → APPROVED → RETIRED).
- Parameters are **starting defaults to test**, not optimised values. Tune only on in-sample data, then confirm out-of-sample.
- The team trades **spot only, long only, no leverage**. Column **Fit**: ✅ usable as-is · 🔶 usable as a filter / position-sizing overlay or long-only variant · ❌ needs shorting, leverage or derivatives — research only, do not paper-trade.
- **★ = test first** (simple, spot-long, documented, enough trades for a 100-trade backtest).
- Every backtest includes fees (CEX taker ~0.1%, DEX 0.3–1% + priority fees) and slippage (≥0.5% for memecoins, more for thin pools). A strategy that only works without costs is rejected.
- Abbreviations: EMA/SMA = moving averages, ATR = average true range, BB = Bollinger Bands, HH/HL = higher high / higher low, TP = take profit, SL = stop loss, TF = timeframe, mcap = market cap, LP = liquidity pool.

---

## A. Trend following (majors and large memecoins)

| ID | Name | Fit | TF | Entry (long) | Exit / stop | Notes & known weakness |
|---|---|---|---|---|---|---|
| L-001 ★ | Donchian breakout (lab S-01) | ✅ | 1D | Close > highest high of last 20 days | Close < lowest low of last 10 days; initial SL 2×ATR(20) | Turtle-style. Many small losses, few big wins. Whipsaws in ranges. |
| L-002 ★ | EMA 50/200 crossover | ✅ | 1D | EMA50 crosses above EMA200 | EMA50 crosses below EMA200 | Very few trades per coin → test across many coins to reach 100. Late entries. |
| L-003 | Triple EMA stack | ✅ | 4H | EMA10 > EMA20 > EMA50 and price > EMA10 | Close < EMA20 | Faster than L-002; more whipsaw. |
| L-004 ★ | Time-series momentum | ✅ | 1D | 30-day return > 0 (or > risk-free) | Re-check weekly; exit when 30-day return ≤ 0 | Moskowitz/Ooi/Pedersen (2012) TSMOM; documented in crypto. Long-only version = cash when negative. |
| L-005 | Supertrend | ✅ | 4H | Supertrend(10, 3) flips to up | Flips to down | Simple, popular → crowded. |
| L-006 | Ichimoku cloud breakout | ✅ | 1D | Close above cloud, Tenkan > Kijun, Chikou above price | Close back inside cloud | Lagging; needs strong trends. |
| L-007 | ADX trend filter + EMA | ✅ | 4H | ADX(14) > 25 and +DI > −DI and price > EMA50 | ADX < 20 or −DI > +DI | ADX as regime filter improves many trend systems; test as overlay too. |
| L-008 | Parabolic SAR trend | ✅ | 4H | SAR flips below price, price > EMA100 | SAR flips above price | Noisy alone; use EMA filter. |
| L-009 | Keltner channel breakout | ✅ | 4H | Close > EMA20 + 2×ATR(20) | Close < EMA20 | Volatility-adjusted breakout. |
| L-010 | Higher-high / higher-low structure | ✅ | 4H | New HH after a confirmed HL, entry on break of last swing high | Close below last HL | Discretion risk — swing points must be defined mechanically (fractals, 5 bars). |
| L-011 | Moving-average ribbon | ✅ | 1D | 8 EMAs (20…55) all rising and ordered | Ribbon order breaks | Smoothed version of L-003. |
| L-012 | 200-day SMA regime | 🔶 | 1D | Hold only when BTC close > SMA200 | BTC close < SMA200 | Best as **market regime filter** for all other long strategies. |
| L-013 | Dual momentum (absolute + relative) | ✅ | 1W | Among BTC/ETH/SOL pick the best 12-week return; hold only if its return > 0 | Re-check weekly | Antonacci-style, adapted. Low turnover. |
| L-014 | Linear-regression slope | ✅ | 1D | Slope of 30-day regression of log price > 0 and R² > 0.5 | Slope < 0 | Measures trend quality, not just direction. |
| L-015 | Hull MA trend | ✅ | 4H | Hull MA(55) turns up and price > HMA | HMA turns down | Less lag than EMA, more false turns. |

## B. Momentum, breakout & rotation

| ID | Name | Fit | TF | Entry (long) | Exit / stop | Notes & known weakness |
|---|---|---|---|---|---|---|
| L-016 ★ | Cross-sectional momentum, long-only (lab S-04 variant) | ✅ | 1W | Rank top-30 liquid coins by 3-week return; buy top 3, equal weight | Rebalance weekly; drop coins leaving top 3 | Liu, Tsyvinski & Wu (NBER 25882) found crypto momentum. Long-only removes the short leg. |
| L-017 | 52-week high proximity | ✅ | 1D | Price within 5% of 52-week high and volume > 20-day average | Close < EMA50 | George & Hwang (2004) effect in stocks; test in crypto. |
| L-018 | Volatility contraction breakout (VCP / squeeze) | ✅ | 4H | BB width at 6-month low, then close above upper BB | Close < middle BB; SL below range low | Few signals per coin. |
| L-019 | Opening-range breakout (UTC day) | ✅ | 15m | Price breaks high of first 2h after 00:00 UTC | End of day or SL at range low | Crypto has no real "open"; test 00:00 UTC and US open 13:30 UTC. |
| L-020 | Range breakout with volume | ✅ | 1H | Close above 48h range high with volume > 2× average | SL at range midpoint; TP 2R | Fake breakouts common in memecoins. |
| L-021 | Rate-of-change burst | ✅ | 1H | ROC(24) > +15% and price above VWAP | ROC turns negative or trailing 3×ATR | Chases moves; strict risk needed. |
| L-022 | Sector / narrative rotation | ✅ | 1D | Buy the strongest coin of the sector with the best 7-day sector return (AI, dogs, cats, political…) | Sector falls out of top 2 | Matches scout's narrative tracking; data from CoinGecko categories. |
| L-023 | Relative strength vs BTC | ✅ | 1D | Coin/BTC ratio makes new 30-day high while BTC > SMA50 | Ratio < its EMA20 | Picks outperformers. |
| L-024 | New-listing momentum (CEX) | ✅ | 1H | Coin listed on a top CEX in last 7 days, price above listing-day VWAP, volume rising | Close < listing-day VWAP | Listing pumps often reverse fast; test hold periods 1–72h. |
| L-025 | Weekly-close breakout | ✅ | 1W | Weekly close above prior 12-week high | Weekly close below 6-week low | Slow, few trades. |
| L-026 | Pocket-pivot volume | ✅ | 1D | Up day whose volume > highest down-day volume of last 10 days, price above SMA50 | Close < SMA50 | From equities; test. |
| L-027 | Gap-and-go (CEX) | ✅ | 1H | 1h candle opens > 3% above prior close and holds above for 2 candles | Close back below the gap | Rare on 24/7 markets except after outages/news. |
| L-028 | Momentum + low volatility | ✅ | 1W | Among top-20 by 4-week return, pick the 3 with lowest 30-day volatility | Weekly rebalance | Combines two documented factors. |
| L-029 | Breakout retest | ✅ | 4H | After breakout above resistance, buy first retest of that level that closes above it | Close below the level | Fewer but cleaner entries than L-020. |
| L-030 | Altcoin season gate | 🔶 | 1D | Hold alts only when BTC dominance falling 30d and >75% of top-50 alts beat BTC over 90d | Condition fails | Overlay for all altcoin/memecoin strategies. |

## C. Mean reversion

| ID | Name | Fit | TF | Entry (long) | Exit / stop | Notes & known weakness |
|---|---|---|---|---|---|---|
| L-031 ★ | RSI(2) pullback in uptrend | ✅ | 1D/4H | Price > SMA200 and RSI(2) < 10 | RSI(2) > 70 or close > SMA5; time stop 5 bars | Connors-style. Many trades → good for 100-trade backtest. |
| L-032 | Bollinger lower-band bounce | ✅ | 4H | Close below lower BB(20,2) then next close back inside, price > SMA200 | Middle band; SL 1.5×ATR | Fails badly in crashes — needs the trend filter. |
| L-033 | Z-score reversion | ✅ | 1H | 48h z-score of price < −2 and 1D trend up | z-score > 0 | Pure statistics; check regime. |
| L-034 | VWAP reversion | ✅ | 15m | Price ≥ 2 std below daily VWAP, 4H trend up | Back to VWAP | Intraday; fees matter a lot. |
| L-035 | Stochastic oversold in uptrend | ✅ | 4H | Price > EMA100, Stoch(14,3) crosses up from < 20 | Stoch > 80 | Close cousin of L-031; compare and keep the better. |
| L-036 | Three-down-days | ✅ | 1D | Three consecutive lower closes while price > SMA200 | First up close | Simple, documented in equities. |
| L-037 | Pullback to EMA20 (lab S-02) | ✅ | 4H | Daily trend up (HH/HL), price touches EMA20 and prints bullish close | Close below swing low; TP at prior high | Lab already flags weak evidence. |
| L-038 | Fibonacci 61.8% pullback | ✅ | 4H | In uptrend, buy at 50–61.8% retracement with bullish candle | Below 78.6%; TP prior high | Widely used → self-fulfilling or crowded. Mechanise swing selection. |
| L-039 | Capitulation volume reversal | ✅ | 1H | Drop > 15% in 24h, volume > 3× average, long lower wick | TP +8%; SL below wick low | Catching knives; strict size. |
| L-040 | Weekend-dip buy | ✅ | 1H | Buy BTC/ETH if Sunday 18:00 UTC price < Friday 21:00 UTC price by > 3% | Sell Tuesday 00:00 UTC | Calendar effect; test if it still exists. |
| L-041 | Pairs trade (cointegrated coins) | ❌ | 1H | Long the laggard, short the leader when spread z < −2 | Spread z → 0 | Needs a short leg. Research only. |
| L-042 | Grid trading in a range | 🔶 | 15m | Buy levels every 1% below mid, sell 1% above, only when ADX < 20 | Stop grid if price leaves range by 5% | Works in ranges, bleeds in trends. Spot grid (no leverage) only. |
| L-043 | Overnight / Asia session reversal | ✅ | 1H | Buy at 00:00 UTC if US session (13:30–21:00) dropped > 2% | Sell 08:00 UTC | Session effects documented in some crypto papers; verify. |
| L-044 | DCA on drawdown | 🔶 | 1D | Add fixed amount to BTC/ETH each time price is 10/20/30% below 90-day high | Hold; trim at new highs | Accumulation plan, not a trading signal. Separate from trading capital. |
| L-045 | RSI divergence | ✅ | 4H | Price lower low, RSI(14) higher low, RSI < 35, then close above prior candle high | SL below low; TP 2R | Subjective unless divergence is coded exactly. |

## D. Volatility & risk overlays

| ID | Name | Fit | TF | Entry (long) | Exit / stop | Notes & known weakness |
|---|---|---|---|---|---|---|
| L-046 ★ | Volatility targeting (overlay) | 🔶 | 1D | Position size = target vol (e.g. 40%/yr) ÷ realised 30-day vol | — | Not a signal. Apply to every approved strategy; documented to improve risk-adjusted returns. |
| L-047 | ATR trailing stop (overlay) | 🔶 | any | — | Trail stop at highest close − 3×ATR(14) | Compare against each strategy's native exit. |
| L-048 | Chandelier exit (overlay) | 🔶 | any | — | Highest high(22) − 3×ATR(22) | Same family as L-047. |
| L-049 | Low-volatility regime long | ✅ | 1D | 30-day vol in bottom third of 1-year range and price > SMA50 | Vol jumps to top third | Calm uptrends. |
| L-050 | Volatility breakout (Larry Williams) | ✅ | 1D | Price > open + 0.5 × prior day range | Exit at next day open | Classic; check costs. |
| L-051 | NR7 (narrowest range of 7) | ✅ | 1D | After NR7 day, buy break of its high | Break of its low or 3 days | Few trades per coin. |
| L-052 | Max-drawdown circuit breaker (overlay) | 🔶 | — | — | Halt a strategy after −10% equity drawdown until reviewed | Risk manager already has −15% kill switch; this is per-strategy. |
| L-053 | Correlation cap (overlay) | 🔶 | 1D | Reject a new position if 30-day correlation with an open one > 0.8 | — | Memecoins are highly correlated; avoids 3× the same bet. |
| L-054 | Kelly-fraction sizing (overlay) | 🔶 | — | Size = ¼ Kelly from backtest win rate and payoff | — | Only after 100+ trade backtest; full Kelly is far too aggressive. |
| L-055 | Stablecoin depeg pause (overlay) | 🔶 | 1m | — | Stop all buys if USDT/USDC < 0.995 (already in risk rules) | Already enforced; listed for completeness. |

## E. Volume & order flow

| ID | Name | Fit | TF | Entry (long) | Exit / stop | Notes & known weakness |
|---|---|---|---|---|---|---|
| L-056 | OBV trend confirmation | ✅ | 4H | OBV makes new 20-bar high while price above EMA50 | OBV below its EMA20 | Volume leads price (sometimes). |
| L-057 | Volume spike + breakout | ✅ | 1H | Volume > 3× 24h average and close at top 25% of candle range above resistance | Close below breakout candle low | Spoofed volume on DEX/small CEX. |
| L-058 | Anchored VWAP reclaim | ✅ | 1H | Price reclaims VWAP anchored at last major low/high with volume | Loses AVWAP | Anchor point must be mechanical. |
| L-059 | Volume-profile POC bounce | ✅ | 4H | Price returns to 30-day point of control in uptrend and holds 2 candles | Close 2% below POC | Needs volume-by-price data. |
| L-060 | CVD divergence (spot) | ✅ | 1H | Price flat/down, spot cumulative volume delta rising (absorption) | CVD turns down | Needs exchange trade data. |
| L-061 | Buy/sell ratio surge (DEX) | ✅ | 5m | On Dexscreener: buys/sells > 2 in last 5m and 1h, liquidity > $250k | Ratio < 1 or −10% | Bot-inflated counts are common — compare unique makers. |
| L-062 | Volume/liquidity ratio | 🔶 | 1H | 24h volume ÷ liquidity between 2 and 10 (active but not wash-traded) | — | Filter for memecoin entries; > 20 often means wash trading. |
| L-063 | Order-book imbalance (CEX) | ✅ | 1m | Bid depth within 1% > 2× ask depth for 5 min, price > VWAP | Imbalance flips | Spoofing risk; fast data needed. |

## F. On-chain & smart money

| ID | Name | Fit | TF | Entry (long) | Exit / stop | Notes & known weakness |
|---|---|---|---|---|---|---|
| L-064 ★ | Smart-money netflow follow | ✅ | 1D | Nansen smart-money 24h netflow into token > $250k and 7d netflow > 0, liquidity > $1M | Netflow turns negative 2 days in a row or −15% | Uses NANSEN_API_KEY. Test lag between smart-money buys and price. |
| L-065 | Smart-money holder count rising | ✅ | 1D | Nansen smart-money holders up ≥ 20% in 7d, price < +50% in same period (not yet chased) | Holders fall 10% | Avoid buying after the move is done. |
| L-066 | Whale accumulation (wallet tracking) | ✅ | 1H | ≥ 3 labeled whale/fund wallets buy the same token within 24h (Alchemy transfers + labels) | Any of them sends to an exchange | Labels from Nansen/Arkham site; verify labels. |
| L-067 | Exchange outflow | ✅ | 1D | Net outflow of the coin from CEXs > 1% of circulating supply over 7d | Net inflow returns | Outflows = withdrawal to hold (bullish-ish). Data quality varies. |
| L-068 | Exchange inflow avoid (overlay) | 🔶 | 1H | — | Block buys / exit if a whale sends > 0.5% supply to a CEX | Sniper rule; mainly a filter. |
| L-069 | Holder growth vs price | ✅ | 1D | Unique holders +10% in 7d while price flat (±10%) | Holder growth stops | Airdrop dust inflates holder counts — use holders with > $10. |
| L-070 | Top-10 concentration falling | 🔶 | 1D | Top-10 holder share falls ≥ 5 points in 14d (distribution to many) | — | Filter: healthier tokens. |
| L-071 | Stablecoin supply growth (macro) | 🔶 | 1W | Increase risk when USDT+USDC total supply grows > 2% in 30d | Supply shrinking | Liquidity regime signal for the whole market. |
| L-072 | MVRV / realised-price zone (BTC) | 🔶 | 1D | Accumulate BTC when MVRV < 1 | Trim when MVRV > 3.5 | Cycle indicator; very few signals. |
| L-073 | Dev-wallet hold check (overlay) | 🔶 | — | Only enter if dev wallet hasn't sold in 7d and holds < 5% | Exit if dev sells > 1% supply | Security auditor already checks; add as exit trigger. |
| L-074 | LP lock extension | ✅ | 1D | Team extends LP lock / burns LP and adds liquidity, price > 24h VWAP | −15% | Rare signal; mostly a quality filter. |
| L-075 | Fresh-wallet cluster avoid (overlay) | 🔶 | — | Reject token if > 15% of supply bought by wallets < 7 days old funded from the same source | — | Bubblemaps / GMGN; anti-rug filter. |

## G. Derivatives & sentiment (used as filters on spot)

| ID | Name | Fit | TF | Entry (long) | Exit / stop | Notes & known weakness |
|---|---|---|---|---|---|---|
| L-076 | Funding extreme filter (lab S-03) | 🔶 | 8H | Avoid new longs when perp funding > 0.05%/8h on the coin | — | BIS WP 1087: high carry predicts crashes. |
| L-077 | Negative-funding squeeze | ✅ | 8H | Funding < −0.03%/8h for 24h while price holds above 3-day low → buy spot | +10% or funding back to 0 | Shorts crowded → squeeze. |
| L-078 | Open-interest flush | ✅ | 1H | OI drops ≥ 15% in 24h with price −10% (leverage washed out), then green 4H close | TP 2R; SL below flush low | Needs Coinglass-type data. |
| L-079 | Liquidation cascade bounce | ✅ | 15m | > $100M long liquidations in 1h, then first 15m higher low | TP +5–8%; SL at low | Fast; manual approval latency may kill it. |
| L-080 | Fear & Greed contrarian | 🔶 | 1D | Increase BTC/ETH exposure when index < 20 for 3 days | Reduce when > 80 | Coarse; good as regime overlay. |
| L-081 | Social-volume spike fade (overlay) | 🔶 | 1H | Do **not** chase if social mentions > 5× 7-day average and price already +30% | — | Tops often coincide with peak attention. |
| L-082 | Basis/carry trade | ❌ | 1D | Long spot + short future when annualised basis > 15% | Basis < 5% | Needs a short future. Research only. |
| L-083 | Long/short ratio contrarian | 🔶 | 4H | Avoid longs when retail long/short ratio > 3 | — | Exchange ratios are noisy; filter only. |

## H. Memecoins & new launches

| ID | Name | Fit | TF | Entry (long) | Exit / stop | Notes & known weakness |
|---|---|---|---|---|---|---|
| L-084 ★ | Graduated-token second leg | ✅ | 5m | pump.fun / letsbonk token graduates to Raydium/PumpSwap, security PASS, holders > 500, first pullback ≥ 30% holds above graduation price | TP +50%/+100% in thirds; SL −25% or below graduation price | Most graduates still die. Strict size (≤ 0.5% of account). |
| L-085 | Established-memecoin narrative rotation | ✅ | 1D | Buy the large memecoin (mcap > $300M) leading its narrative's 7-day inflow (scout's rotation table) | Narrative drops out of top 2 | Builds on scout/memecoins.md. |
| L-086 | Dexscreener trending + filters | ✅ | 15m | Token in Dexscreener top-20 trending, age > 24h, liquidity > $500k, security PASS, buys > sells 1h | −20% or trend exit | Trending is paid/boosted — L-087 filter required. |
| L-087 | Paid-boost avoid (overlay) | 🔶 | — | Reject tokens whose only visibility is Dexscreener boosts / paid trending | — | Scout already found boosted rugs. |
| L-088 | CEX-listing rumour → listing | ✅ | 1H | Buy on confirmed official listing announcement (not rumour), on DEX, within 10 min | Sell 50% at +30%, rest on listing open or −15% | Speed matters; often "sell the news". |
| L-089 | Celebrity mention (verified) | ✅ | 5m | Verified post by a watchlist account names an existing token's ticker/contract; token security PASS; liquidity > $1M | Sell in thirds within 24h; SL −20% | Impersonation is #1 scam — sniper verifies the account first. |
| L-090 | Pullback after first pump | ✅ | 15m | Token +200% in < 48h, then pulls back 40–60% on falling volume and holds a level for 6h | TP retest of high; SL −20% | Many never recover; small size. |
| L-091 | Holder-milestone momentum | ✅ | 1H | Holders cross 5k / 10k / 25k with growth accelerating and top-10 < 25% | Growth stalls 12h | Milestones are crowded attention points. |
| L-092 | KOL-cluster avoid (overlay) | 🔶 | — | Reject if > 5 paid influencer posts within 1h of launch (coordinated shill) | — | Scout's organic check. |
| L-093 | Liquidity-add confirmation | ✅ | 1H | Team/large LP adds ≥ 30% more liquidity and price holds above pre-add level | −15% | Adding liquidity = commitment; can also precede a pull. Verify lock. |

## I. Events, calendar & news

| ID | Name | Fit | TF | Entry (long) | Exit / stop | Notes & known weakness |
|---|---|---|---|---|---|---|
| L-094 | Token-unlock avoid / post-unlock buy | ✅ | 1D | Avoid 7 days before unlocks > 2% of supply; buy 3–7 days after if price stabilised above unlock-day low | −12% | Sniper already tracks unlocks (ENA/ASTER). |
| L-095 | FOMC / CPI volatility pause (overlay) | 🔶 | — | No new entries 2h before to 1h after FOMC, CPI, NFP | — | Pure risk filter. |
| L-096 | Post-FOMC drift | ✅ | 1H | 1h after FOMC, buy BTC if 1h candle closes up > 1% | Sell after 24h | Event study; few trades/year → pool many macro events. |
| L-097 | ETF-flow follow | ✅ | 1D | Spot BTC/ETH ETF net inflows positive 3 days in a row and > $300M total | Two days of net outflows | Data from Farside / issuers; T+1 lag. |
| L-098 | Halving / supply-shock cycle | 🔶 | 1M | Bias long BTC in the 6–18 months after a halving | — | Only 4 halvings ever — not statistically testable; overlay only. |
| L-099 | Hack/exploit avoid & rebound | ✅ | 1H | Avoid affected tokens; buy majors (not the hacked token) after −5% market-wide hack dip once funds are traced/frozen | +5% or 48h | Event-driven; news feeds are the source. |
| L-100 | Month-end / turn-of-month | ✅ | 1D | Buy BTC at last day of month close | Sell 3rd trading day of new month | Documented in equities; mixed in crypto. Cheap to test. |

## J. From public research & open-source libraries (added 2026-10-04)

Top discretionary traders don't publish their systems. What *is* public: a professional's open-source framework (Rob Carver, ex-Man AHL), research papers replicated by Papers With Backtest, and the Freqtrade community library. Rules below are summarised in our own words from the source (no code copied — Freqtrade and pysystemtrade are GPL-3.0); read the linked source before backtesting. Reality check from Papers With Backtest's own replication of 4,843 published strategies: **median Sharpe 0.37, and only 48% were statistically significant** — half of published strategies don't survive re-testing.

| ID | Name | Fit | TF | Entry (long) | Exit / stop | Source & notes |
|---|---|---|---|---|---|---|
| L-101 ★ | BTC intraday seasonality | ✅ | 1H | Hold BTC only during the historically strongest hours of the day (paper: a 2-hour window around 22:00–00:00 UTC — **verify the exact hours in the paper first**) | Sell at end of window | Padysak & Vojtko (2022), "Seasonality, Trend-following, and Mean reversion in Bitcoin" (SSRN). Fees on 365 round trips/yr are the main risk. |
| L-102 | BTC N-day maximum (trend) | ✅ | 1D | Close = highest close of last N days (paper uses ~10 days — verify) | Close no longer at N-day max / fixed hold | Same paper. Close cousin of L-001; keep whichever tests better. |
| L-103 | BTC N-day minimum (reversion) | ✅ | 1D | Close = lowest close of last N days (verify N) | Fixed hold per paper | Same paper; reported to work alongside the MAX rule. |
| L-104 | Multi-timeframe trend on BTC | ✅ | 1D+1H | Daily trend up (our definition: close > EMA50 daily) **and** hourly trigger (hourly MACD crosses up) | Trailing stop (start 3×ATR hourly) | Vojtko & Mesíček (2025). The paper's exact parameters aren't public on the summary page; this is our mechanical version. PwB reports Sharpe 0.93, max DD 47% (their list shows a different number — treat as unverified). |
| L-105 | Crypto factor portfolio (long-only) | ✅ | 1W | Rank liquid coins on the paper's factors (momentum, size…), hold the best quintile | Weekly rebalance | "Know When to Hodl 'Em, Know When to Fodl 'Em" (factor investing in crypto). Read paper for exact factor definitions before coding. Overlaps L-016/L-028. |
| L-106 ★ | Carver EWMAC trend ensemble | ✅ | 1D | Forecast per speed = (EMA_fast − EMA_slow) ÷ daily price volatility, for pairs 8/32, 16/64, 32/128, 64/256; scale each to average |10|, cap ±20, average them. Long-only: position ∝ max(0, forecast) | Position shrinks to 0 as forecast falls | Rob Carver, *Systematic Trading* / *Leveraged Trading*; open-source in `pst-group/pysystemtrade` (GPL-3.0, futures). A real professional's method. Combine with L-046 vol targeting. |
| L-107 | Carver breakout rule | ✅ | 1D | Forecast = (close − midpoint of N-day range) ÷ (N-day range), smoothed (EMA N/4), scaled; N = 20, 40, 80, 160; long-only = max(0, ·) | Forecast ≤ 0 | Same source. Smoother than a pure Donchian breakout. |
| L-108 | BbandRsi (Freqtrade) | ✅ | 1H | RSI(14) < 30 **and** close < lower Bollinger band (20, 2, typical price) | RSI(14) > 70; source stop −25% | `freqtrade/freqtrade-strategies` berlinguyinca/BbandRsi. No trend filter → test with L-012. |
| L-109 | ClucMay72018 (Freqtrade) | ✅ | 5m | Close < EMA50 **and** close < 0.985 × lower BB(20, 2) **and** volume < 20× 30-bar average volume | Close > middle BB; stop −5% | berlinguyinca/ClucMay72018 (the code names it `ema100` but uses period 50). Dip-buyer; 5m → fees and slippage dominate. |
| L-110 | BinHV45 (Freqtrade) | ✅ | 1m/5m | BB(40, 2): (mid − lower) > 0.8% of close, |close − prev close| > 1.75% of close, lower wick < 25% of (mid − lower), close < previous lower band, close ≤ previous close | ROI table / stop −5% | berlinguyinca/BinHV45 + CombinedBinHAndCluc (= L-109 OR L-110). Very short-term; DEX fees likely kill it — CEX only. |
| L-111 | HLHB system (Freqtrade) | ✅ | 4H | RSI(10 of (open+close)/2) crosses above 50 **and** EMA5 crosses above EMA10 **and** ADX > 25 | RSI crosses below 50 **and** EMA5 crosses below EMA10 **and** ADX > 25; stop −32% | `user_data/strategies/hlhb.py`. Classic forex system ported to crypto. |
| L-112 | Triple Supertrend (Freqtrade) | ✅ | 1H | Three Supertrend indicators (different multiplier/period, hyperopted) all "up" | Three separate sell Supertrends all "down"; stop −26.5% | `Supertrend.py`. Parameters were hyperopted on past data → re-tune only in-sample. Overlaps L-005. |
| L-113 | ADX Momentum (Freqtrade) | ✅ | 1H | ADX(14) > 25, MOM(14) > 0, +DI > 25, +DI > −DI | ADX > 25, MOM < 0, −DI > 25, +DI < −DI; stop −25% | berlinguyinca/ADXMomentum. Overlaps L-007. |
| L-114 | MultiMa (Freqtrade) | ✅ | 4H | A ladder of TEMAs (count/gap hyperopted) all rising in order | Ladder all falling; stop −34.5% | `MultiMa.py`. Overlaps L-011. |
| L-115 | NostalgiaForInfinity (reference) | 🔶 | 5m | Very large multi-condition dip-buy system with many protections (`iterativv/NostalgiaForInfinity`, GPL-3.0, ~3.4k★, updated daily) | Many exit modes | Too complex to backtest as one rule; mine it for **protection ideas** (pump guards, BTC-crash guards, cooldowns) to add as overlays. |

---

## Suggested testing order

1. **Overlays first** (they change all results): L-012 regime, L-046 vol targeting, L-047 ATR trail, L-053 correlation cap, L-095 macro pause.
2. **★ core signals:** L-001, L-004, L-016, L-031, L-064, L-084, L-101, L-106 — different families, so if they pass they diversify each other.
3. **Then by family**, one candidate at a time, keeping the best of each near-duplicate group (e.g. L-031 vs L-035 vs L-036).
4. ❌ strategies stay research-only while the team is spot/long/no-leverage.

Sources mentioned (verify before relying on them): Moskowitz, Ooi & Pedersen (2012) "Time Series Momentum"; Liu, Tsyvinski & Wu, NBER w25882 "Common Risk Factors in Cryptocurrency"; George & Hwang (2004) "The 52-Week High and Momentum Investing"; BIS Working Paper 1087 "Crypto carry"; Concretum Group "Catching Crypto Trends". Everything else is common trading practice without peer-reviewed crypto evidence.

#!/usr/bin/env python3
"""Part B batch 2: L-001 (re-run BTC/ETH), L-106 (Carver EWMAC ensemble, daily), L-101 (BTC 1H seasonality 22:00-00:00 UTC).
Rules = strategies/library.md defaults, UNTUNED. Reuses backtest.py / backtest_L.py (loader, costs, windows, L-001 engine, stats).
Conventions (same as section 9): signal at close of bar i, fill at open of bar i+1, fee 0.10%/side + slippage 0.05%/side,
long-only spot, no leverage, last open position marked at last close with exit costs.

PRE-SPECIFIED CHOICES (fixed BEFORE looking at any result):
 L-106: forecast_k = (EMA_fast - EMA_slow) / (close * EWMvol_35d(daily pct returns))   [price-unit daily vol, Carver]
        scalars = Carver's PUBLISHED forecast scalars: 8/32:5.3  16/64:3.75  32/128:2.65  64/256:1.87 (not fitted)
        cap +-20 each, simple average (no forecast-diversification multiplier), long-only position = max(0,F)/20 in [0,1] of capital.
        No-trade buffer = 10% of capital (trade only if |target - current| > 0.10, or target = 0 while holding -> full exit).
        Unbuffered variant (buffer 0) and zero-cost (gross) variant = labelled sensitivities. Signals live from bar 256.
 L-101: paper (Padysak & Vojtko 2022, SSRN 4081000): open long at 22:00 UTC, hold 2 hours (quote via Quantpedia) ->
        enter at OPEN of the 22:00 candle, exit at CLOSE of the 23:00 candle (= 00:00 UTC).
        Secondary (labelled): best 2h start hour chosen on first 70% (by mean net trade) applied unchanged to last 30%.
Run: python3 backtest_L2.py
"""
import sys, os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv = sys.argv[:1]
import backtest as B, backtest_L as L

FEE = B.FEE; SLIP = 0.0005; ASSETS = ["BTC", "ETH"]; WARM = L.WARM; FIXED = L.FIXED
SPEEDS = [(8, 32, 5.3), (16, 64, 3.75), (32, 128, 2.65), (64, 256, 1.87)]; CAP = 20.0; BUF = 0.10; SIG_START = 256
PERIODS = ["IS70", "OOS30", "FULL", "IS_fixed", "OOS_fixed"]
TODAY = B.TODAY

def tst(r):
    """L.tstats with deterministic per-call bootstrap seed + t/normal-approx CI of the mean."""
    L.rng = np.random.default_rng(0); o = L.tstats(r); r = np.asarray(r, float)
    if len(r) >= 10:
        se = r.std(ddof=1)/np.sqrt(len(r)); o["t_lo"], o["t_hi"] = r.mean()-1.96*se, r.mean()+1.96*se
    return o

def pm(p):
    if len(p) < 30: return dict(days=len(p))
    e = (1+p).cumprod(); return dict(days=len(p), ret=e.iloc[-1]-1, maxdd=(e/e.cummax()-1).min(), sharpe=p.mean()/p.std()*np.sqrt(365) if p.std() > 0 else np.nan)

def windows(data):
    win = {}
    for a in ASSETS:
        ix = data[a].index; u0 = ix[WARM]; k = WARM+int(0.7*(len(ix)-WARM)); sp = ix[k]; end = ix[-1]+pd.Timedelta(days=1)
        win[a] = {"IS70": (u0, sp), "OOS30": (sp, end), "FULL": (u0, end), "IS_fixed": (u0, FIXED), "OOS_fixed": (FIXED, end)}
    return win

def agg(series, g, win, per):
    return pd.concat({x: series[x].pct_change().where((series[x].index >= win[x][per][0]) & (series[x].index < win[x][per][1])) for x in g}, axis=1).mean(axis=1, skipna=True).dropna()

# ---------------------------------------------------------------- L-106
def forecast(d):
    c = d.close; vol = c.pct_change().ewm(span=35, min_periods=35, adjust=False).std()*c
    fs = []
    for f, s, sc in SPEEDS:
        raw = (c.ewm(span=f, adjust=False).mean()-c.ewm(span=s, adjust=False).mean())/vol
        fs.append((raw*sc).clip(-CAP, CAP))
    F = pd.concat(fs, axis=1).mean(axis=1)
    out = d.copy(); out["F"] = F; out["target"] = (F.clip(lower=0)/CAP).clip(0, 1)
    out.loc[out.index[:SIG_START], "target"] = np.nan   # no signals before bar 256 (slow EMA warm-up)
    for k, (f, s, sc) in enumerate(SPEEDS): out[f"F{f}_{s}"] = fs[k]
    return out

def run106(a, d, buffer, costs=True):
    fee = FEE if costs else 0.0; s = SLIP if costs else 0.0
    n = len(d); o, c = d.open.values, d.close.values; T = d.target.values
    cash = 1.0; u = 0.0; curve = np.full(n, 1.0); frac = np.zeros(n); traded = np.zeros(n); cost = np.zeros(n); eps = []; ep = None; nreb = 0; fills = []
    for i in range(n):
        if i >= 1 and not np.isnan(T[i-1]):
            V = cash+u*o[i]; cur = u*o[i]/V; tg = T[i-1]; dl = tg-cur
            if abs(dl) > max(buffer, 1e-9) or (tg == 0 and u > 0):
                if dl > 0:
                    X = min(dl*V, cash); gain = X/(o[i]*(1+s)*(1+fee)); cost[i] = (X-gain*o[i])/V; traded[i] = X/V
                    cash -= X; u += gain
                    if ep is None: ep = dict(entry_date=d.index[i], entry_px=o[i]*(1+s), cin=0.0, cout=0.0)
                    ep["cin"] += X
                else:
                    q = u if tg == 0 else min(u, -dl*V/o[i]); pr = q*o[i]*(1-s)*(1-fee); cost[i] = (q*o[i]-pr)/V; traded[i] = q*o[i]/V
                    cash += pr; u -= q
                    if ep is not None: ep["cout"] += pr
                    if u < 1e-12: u = 0.0
                    if ep is not None and u == 0:
                        eps.append(dict(asset=a, strat="L106", entry_date=ep["entry_date"], exit_date=d.index[i], entry_px=ep["entry_px"], exit_px=o[i]*(1-s),
                                        exit_reason="signal_flat", bars=(i-d.index.get_loc(ep["entry_date"])), net_ret=ep["cout"]/ep["cin"]-1)); ep = None
                nreb += 1; fills.append((d.index[i], tg, cur, dl))
        curve[i] = cash+u*c[i]; frac[i] = u*c[i]/curve[i]
    if u > 0:
        pr = u*c[-1]*(1-s)*(1-fee); ep["cout"] += pr; cost[-1] += (u*c[-1]-pr)/curve[-1]; cash += pr; curve[-1] = cash
        eps.append(dict(asset=a, strat="L106", entry_date=ep["entry_date"], exit_date=d.index[-1], entry_px=ep["entry_px"], exit_px=c[-1]*(1-s), exit_reason="open_at_end",
                        bars=(n-1-d.index.get_loc(ep["entry_date"])), net_ret=ep["cout"]/ep["cin"]-1))
    return eps, pd.Series(curve, index=d.index), pd.Series(frac, index=d.index), pd.Series(traded, index=d.index), pd.Series(cost, index=d.index), nreb, fills

# ---------------------------------------------------------------- L-101
def load1h(a):
    d = pd.read_csv(f"{B.D}/{a}USDT_1h.csv", parse_dates=["time"]).set_index("time").astype(float)
    return d[d.index < TODAY]   # same cut-off as the daily lab: last complete UTC day = 2026-10-03

def trades101(d, h):
    """Long at OPEN of hour h, sell at CLOSE of hour h+1 (UTC). Returns DataFrame indexed by entry date (day of entry)."""
    full = d.reindex(pd.date_range(d.index[0], d.index[-1], freq="1h"))
    o = full.open; cn = full.close.shift(-1)
    sel = full.index.hour == h
    x = pd.DataFrame(dict(entry_open=o[sel], exit_close=cn[sel])).dropna()
    x["gross"] = x.exit_close/x.entry_open-1
    x["net"] = x.exit_close*(1-SLIP)*(1-FEE)/(x.entry_open*(1+SLIP)*(1+FEE))-1
    x["entry_time"] = x.index; x["exit_time"] = x.index+pd.Timedelta(hours=2)
    x.index = x.index.normalize(); x.index.name = "date"
    return x

def daily_series(x, col, start, end):
    ix = pd.date_range(start.normalize(), end.normalize()-pd.Timedelta(days=1), freq="D")
    return x[col].reindex(ix).fillna(0.0)

if __name__ == "__main__":
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 80); pd.set_option("display.max_rows", 500)
    daily = {a: B.load(a) for a in ASSETS}
    data = {a: L.prep(daily[a]) for a in ASSETS}; win = windows(data)
    rows = []
    # ======================= L-001 re-run (same script, same parameters, BTC+ETH only) =======================
    t_all, cur, curf = [], {}, {}
    for a in ASSETS:
        t, cur[a] = L.run(a, data[a], "L001"); tf, curf[a] = L.run(a, data[a], "L001", full=True); assert len(t) == len(tf); t_all += t
    tr1 = pd.DataFrame(t_all); tr1["entry_date"] = pd.to_datetime(tr1.entry_date)
    for per in PERIODS: tr1[per] = [(win[x][per][0] <= e < win[x][per][1]) for x, e in zip(tr1.asset, tr1.entry_date)]
    tr1.sort_values("entry_date").to_csv(f"{HERE}/trades_L001_rerun_BTC_ETH.csv", index=False)
    old_tr = pd.read_csv(f"{HERE}/trades_L001.csv", parse_dates=["entry_date", "exit_date"]); old_tr = old_tr[old_tr.asset.isin(ASSETS)].sort_values(["asset", "entry_date"]).reset_index(drop=True)
    new_tr = tr1.assign(exit_date=pd.to_datetime(tr1.exit_date)).sort_values(["asset", "entry_date"]).reset_index(drop=True)
    same_trades = len(old_tr) == len(new_tr) and (old_tr.entry_date == new_tr.entry_date).all() and (old_tr.exit_date == new_tr.exit_date).all() and np.allclose(old_tr.net_ret, new_tr.net_ret, rtol=0, atol=1e-12)
    old = pd.read_csv(f"{HERE}/results_L.csv"); old = old[(old.strat == "L001") & old.group.isin(ASSETS)]
    for grp in ASSETS + ["POOLED"]:
        g = ASSETS if grp == "POOLED" else [grp]
        for per in PERIODS:
            sub = tr1[tr1.asset.isin(g) & tr1[per]]; row = dict(strat="L001", group=grp, period=per, **tst(sub.net_ret.values))
            row["exit_mix"] = ";".join(f"{k}:{v}" for k, v in sub.exit_reason.value_counts().items())
            row.update({"port_"+k: v for k, v in pm(agg(cur, g, win, per)).items()}); row.update({"full_"+k: v for k, v in pm(agg(curf, g, win, per)).items()})
            row.update({"bh_"+k: v for k, v in pm(agg({x: data[x].close for x in g}, g, win, per)).items()}); rows.append(row)
    new_res = pd.DataFrame(rows); maxdiff = {}; ncmp = 0
    for _, orow in old.iterrows():
        nrow = new_res[(new_res.strat == "L001") & (new_res.group == orow.group) & (new_res.period == orow.period)].iloc[0]
        for col in old.columns:
            if col in ("strat", "group", "period", "exit_mix") or col not in nrow.index or pd.isna(orow[col]): continue
            diff = abs(float(orow[col])-float(nrow[col])) if np.isfinite(orow[col]) else (0 if orow[col] == nrow[col] else 1)
            maxdiff.setdefault(col, 0); maxdiff[col] = max(maxdiff[col], diff); ncmp += 1
    print("=== L-001 re-run verification vs results_L.csv / trades_L001.csv (BTC, ETH slices) ===")
    print("trade lists identical (dates + net_ret, 1e-12):", same_trades, "| n trades", len(new_tr))
    print("cells compared:", ncmp, "| max abs diff per column:", {k: float(f"{v:.3g}") for k, v in maxdiff.items()})
    # ======================= L-106 =======================
    d106 = {a: forecast(data[a]) for a in ASSETS}
    for a in ASSETS:
        x = d106[a].iloc[SIG_START:]
        print(f"L-106 diagnostics {a}: mean|F| per speed (diagnostic only, NOT used to rescale):", {c: round(float(x[c].abs().mean()), 2) for c in x.columns if c.startswith("F") and "_" in c},
              "| mean target", round(float(x.target.mean()), 3), "| share target>0", round(float((x.target > 0).mean()), 3))
    VAR = {"L106": (BUF, True), "L106_nobuf": (0.0, True), "L106_gross": (BUF, False)}
    all_eps = []
    for st, (buf, costs) in VAR.items():
        out = {a: run106(a, d106[a], buf, costs) for a in ASSETS}
        eps = pd.DataFrame([dict(e, strat=st) for a in ASSETS for e in out[a][0]]); eps["entry_date"] = pd.to_datetime(eps.entry_date)
        for per in PERIODS: eps[per] = [(win[x][per][0] <= e < win[x][per][1]) for x, e in zip(eps.asset, eps.entry_date)]
        all_eps.append(eps)
        curves = {a: out[a][1] for a in ASSETS}
        for grp in ASSETS + ["POOLED"]:
            g = ASSETS if grp == "POOLED" else [grp]
            for per in PERIODS:
                sub = eps[eps.asset.isin(g) & eps[per]]; row = dict(strat=st, group=grp, period=per, **tst(sub.net_ret.values))
                row.update({"port_"+k: v for k, v in pm(agg(curves, g, win, per)).items()})
                row.update({"bh_"+k: v for k, v in pm(agg({x: data[x].close for x in g}, g, win, per)).items()})
                tim, expo, turn, cst = [], [], [], []
                for x in g:
                    m = (curves[x].index >= win[x][per][0]) & (curves[x].index < win[x][per][1]); yrs = m.sum()/365
                    tim.append((out[x][2][m] > 0).mean()); expo.append(out[x][2][m].mean()); turn.append(out[x][3][m].sum()/yrs); cst.append(out[x][4][m].sum())
                row.update(time_in_mkt=np.mean(tim), avg_exposure=np.mean(expo), turnover_yr=np.mean(turn), cost_sum=np.mean(cst)); rows.append(row)
        if st == "L106":
            pd.concat([out[a][1].rename(a) for a in ASSETS], axis=1).join(pd.concat([out[a][2].rename(a+"_frac") for a in ASSETS], axis=1)).to_csv(f"{HERE}/curve_L106.csv")
            d106["BTC"][["open", "close", "F", "target"]].to_csv(f"{HERE}/signals_L106_BTC.csv")
            print("L-106 rebalances (FULL, buffered) BTC/ETH:", out["BTC"][5], out["ETH"][5])
        if st == "L106_nobuf": print("L-106 rebalances (FULL, unbuffered) BTC/ETH:", out["BTC"][5], out["ETH"][5])
    pd.concat(all_eps).sort_values(["strat", "entry_date"]).to_csv(f"{HERE}/trades_L106.csv", index=False)
    # ======================= L-101 =======================
    d1h = {a: load1h(a) for a in ASSETS}; yrs_rows = []; hour_rows = []
    for a in ASSETS:
        d = d1h[a]; ix = d.index; t0 = ix[0].normalize()+pd.Timedelta(days=1); end = pd.Timestamp("2026-10-04")
        sp = ix[int(0.7*len(ix))].normalize(); w1 = {"IS70": (t0, sp), "OOS30": (sp, end), "FULL": (t0, end), "IS_fixed": (t0, FIXED), "OOS_fixed": (FIXED, end)}
        print(f"L-101 {a}: hourly {ix[0]} -> {ix[-1]} ({len(d)} bars) | windows from {t0.date()} | 70/30 split {sp.date()}")
        prof = {h: trades101(d, h) for h in range(24)}   # entry hour h -> exit close of hour h+1
        for per in ["IS70", "OOS30"]:
            for h in range(24):
                x = prof[h]; x = x[(x.index >= w1[per][0]) & (x.index < w1[per][1])]
                hour_rows.append(dict(asset=a, period=per, start_hour=h, n=len(x), mean_gross=x.gross.mean(), mean_net=x.net.mean(), win_rate_net=(x.net > 0).mean()))
        hp = pd.DataFrame(hour_rows); best = int(hp[(hp.asset == a) & (hp.period == "IS70")].set_index("start_hour").mean_net.idxmax())
        print(f"L-101 {a}: in-sample best 2h start hour (first 70%, by mean net trade) = {best}:00 UTC")
        for st, h in [("L101", 22), ("L101_ISsel", best)]:
            x = prof[h].copy(); x.assign(asset=a, strat=st, start_hour=h).to_csv(f"{HERE}/trades_{st}_{a}.csv")
            for per in PERIODS:
                sub = x[(x.index >= w1[per][0]) & (x.index < w1[per][1])]
                row = dict(strat=st, group=a, period=per, start_hour=h, **tst(sub.net.values))
                row.update({"gross_"+k: v for k, v in tst(sub.gross.values).items() if k in ("avg_trade", "profit_factor", "win_rate", "median_trade")})
                pn = daily_series(x, "net", *w1[per]); pg = daily_series(x, "gross", *w1[per])
                row.update({"port_"+k: v for k, v in pm(pn).items()}); row.update({"gross_port_"+k: v for k, v in pm(pg).items() if k != "days"})
                m = (daily[a].index >= w1[per][0]) & (daily[a].index < w1[per][1]); bh = daily[a].close.pct_change()[m].dropna()
                row.update({"bh_"+k: v for k, v in pm(bh).items()}); row["time_in_mkt"] = 2/24; row["avg_cost_per_rt"] = (sub.gross-sub.net).mean()
                row["trades_per_yr"] = len(sub)/((w1[per][1]-w1[per][0]).days/365); rows.append(row)
            for y in range(x.index.min().year, 2027):
                sy = x[x.index.year == y]
                if len(sy) == 0: continue
                byr = daily[a].close.pct_change(); byr = byr[(byr.index.year == y) & (byr.index >= w1["FULL"][0])]
                yrs_rows.append(dict(strat=st, asset=a, start_hour=h, year=y, n=len(sy), win_rate_net=(sy.net > 0).mean(), avg_gross=sy.gross.mean(), avg_net=sy.net.mean(),
                                     cum_gross=(1+sy.gross).prod()-1, cum_net=(1+sy.net).prod()-1, bh_year=(1+byr).prod()-1))
    res = pd.DataFrame(rows); res.to_csv(f"{HERE}/results_L2.csv", index=False)
    pd.DataFrame(yrs_rows).to_csv(f"{HERE}/results_L2_L101_by_year.csv", index=False); pd.DataFrame(hour_rows).to_csv(f"{HERE}/results_L2_L101_hour_profile.csv", index=False)
    print(res.drop(columns=[c for c in ["exit_mix"] if c in res.columns]).round(3).to_string())
    print(pd.DataFrame(yrs_rows).round(4).to_string())

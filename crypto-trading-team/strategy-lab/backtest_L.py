#!/usr/bin/env python3
"""Library strategies L-001 (Donchian 20/10, SL 2xATR20), L-004 (TSMOM 30d, weekly re-check), L-031 (RSI(2) pullback)
on BTC/ETH/SOL daily. Rules = strategies/library.md defaults, UNTUNED (no parameter fitted on any data).
Reuses harness from backtest.py (data loader, costs, trade bookkeeping). Run: python3 backtest_L.py
Conventions (identical to S-01): signal on close of bar i, fill at open of i+1, fee 0.10%/side + slippage 0.05%/side,
long-only spot, one position per asset, sizing = min(100% notional, 1% risk / stop distance), last open trade marked at last close.
For L-004 / L-031 the library defines no stop: the reference distance 2xATR(20) is used for SIZING ONLY (no stop order).
Second variant 'full' = 100% notional per entry (portfolio-level comparison only; trade-level stats are identical).
"""
import sys, os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv = sys.argv[:1]
import backtest as B

ASSETS = ["BTC", "ETH", "SOL"]; WARM = 200; RISK = B.RISK; FEE = B.FEE
FIXED = pd.Timestamp("2023-06-01"); STRATS = {"L001": "L-001 Donchian 20/10", "L004": "L-004 TSMOM 30d", "L031": "L-031 RSI(2) pullback"}
rng = np.random.default_rng(0)

def prep(df):
    d = df.copy(); pc = d.close.shift(1)
    tr = pd.concat([d.high-d.low, (d.high-pc).abs(), (d.low-pc).abs()], axis=1).max(axis=1)
    d["atr20"] = tr.rolling(20).mean()
    d["dh20"] = d.high.shift(1).rolling(20).max(); d["dl10"] = d.low.shift(1).rolling(10).min()
    d["ret30"] = d.close/d.close.shift(30)-1
    d["sma200"] = d.close.rolling(200).mean(); d["sma5"] = d.close.rolling(5).mean()
    dl = d.close.diff(); up = dl.clip(lower=0); dn = (-dl).clip(lower=0)   # Wilder RSI, period 2
    au = up.ewm(alpha=0.5, adjust=False, min_periods=2).mean(); ad = dn.ewm(alpha=0.5, adjust=False, min_periods=2).mean()
    d["rsi2"] = np.where(ad == 0, 100.0, 100-100/(1+au/ad)); d.loc[au.isna(), "rsi2"] = np.nan
    d["sunday"] = d.index.dayofweek == 6   # weekly re-check on Sunday close -> Monday open
    return d

def run(a, d, strat, full=False):
    s = B.SLIP[a]; n = len(d); o, h, l, c = d.open.values, d.high.values, d.low.values, d.close.values
    cash = 1.0; sh = 0.0; pos = None; pend = None; curve = np.full(n, 1.0); trades = []
    for i in range(n):
        if pend:
            kind = pend; pend = None
            if kind[0] == "exit" and pos:
                px = o[i]*(1-s); cash += sh*px*(1-FEE); trades.append(B.close_trade(a, pos, d.index[i], px, pos["why"] if "why" in pos else "signal")); sh = 0; pos = None
            elif kind[0] == "enter" and not pos:
                dist = kind[1]; stop = o[i]-dist if strat == "L001" else -np.inf   # L-001 only has an actual stop
                px = o[i]*(1+s); rdist = (px-(o[i]-dist))/px
                notional = cash if full else min(1.0*cash, RISK*cash/rdist)
                if notional > 0:
                    sh = notional/(px*(1+FEE)); cash -= notional
                    pos = dict(asset=a, strat=strat, entry_date=d.index[i], entry_px=px, stop=stop, tgt=None, cost=notional, bars=0, risk_frac=rdist)
        if pos and pos["entry_date"] <= d.index[i]:
            pos["bars"] += 1
            if l[i] <= pos["stop"]:
                px = min(o[i], pos["stop"])*(1-s); cash += sh*px*(1-FEE); trades.append(B.close_trade(a, pos, d.index[i], px, "stop")); sh = 0; pos = None
        curve[i] = cash + sh*c[i]
        if i < WARM or i+1 >= n: continue
        if strat == "L001":
            if pos and c[i] < d.dl10.iat[i]: pend = ("exit",)
            elif not pos and c[i] > d.dh20.iat[i]: pend = ("enter", 2*d.atr20.iat[i])
        elif strat == "L004":
            if d.sunday.iat[i]:
                if pos and d.ret30.iat[i] <= 0: pend = ("exit",)
                elif not pos and d.ret30.iat[i] > 0: pend = ("enter", 2*d.atr20.iat[i])
        elif strat == "L031":
            if pos:
                if d.rsi2.iat[i] > 70 or c[i] > d.sma5.iat[i] or pos["bars"] >= 5: pend = ("exit",)
            elif c[i] > d.sma200.iat[i] and d.rsi2.iat[i] < 10: pend = ("enter", 2*d.atr20.iat[i])
    if pos:
        px = c[-1]*(1-s); trades.append(B.close_trade(a, pos, d.index[-1], px, "open_at_end")); cash += sh*px*(1-FEE); curve[-1] = cash
    return trades, pd.Series(curve, index=d.index)

def tstats(r, extra=True):
    r = np.asarray(r, float); n = len(r)
    if n == 0: return dict(n=0)
    w = r[r > 0]; ls = r[r <= 0]
    o = dict(n=n, win_rate=len(w)/n, avg_win=w.mean() if len(w) else np.nan, avg_loss=ls.mean() if len(ls) else np.nan,
             profit_factor=w.sum()/-ls.sum() if ls.sum() < 0 else np.inf, avg_trade=r.mean(), median_trade=np.median(r))
    if n >= 10:
        bs = rng.choice(r, (5000, n)).mean(axis=1); o["ci_lo"], o["ci_hi"] = np.percentile(bs, [2.5, 97.5])
        if n > 3:
            e = np.sort(r)[:-3]; wl = e[e > 0].sum(); ll = -e[e <= 0].sum(); o["pf_ex_top3"] = wl/ll if ll > 0 else np.inf
    return o

def pmetrics(p):
    if len(p) < 30: return dict(days=len(p))
    e = (1+p).cumprod(); return dict(days=len(p), ret=e.iloc[-1]-1, maxdd=(e/e.cummax()-1).min(), sharpe=p.mean()/p.std()*np.sqrt(365) if p.std() > 0 else np.nan)

if __name__ == "__main__":
    data = {a: prep(B.load(a)) for a in ASSETS}
    win = {}   # per asset: dict period -> (start, end) ; usable history starts after WARM bars
    for a in ASSETS:
        ix = data[a].index; u0 = ix[WARM]; k = WARM+int(0.7*(len(ix)-WARM)); sp = ix[k]; end = ix[-1]+pd.Timedelta(days=1)
        win[a] = {"IS70": (u0, sp), "OOS30": (sp, end), "FULL": (u0, end), "IS_fixed": (u0, FIXED), "OOS_fixed": (FIXED, end)}
        print(a, "data", ix[0].date(), "->", ix[-1].date(), len(ix), "bars | usable from", u0.date(), "| 70/30 split", sp.date())
    rows, alltr = [], []
    for st in STRATS:
        tr_all, cur, curf = [], {}, {}
        for a in ASSETS:
            t, cur[a] = run(a, data[a], st); tf, curf[a] = run(a, data[a], st, full=True)
            assert len(t) == len(tf)
            tr_all += t
        tr = pd.DataFrame(tr_all)
        tr["entry_date"] = pd.to_datetime(tr.entry_date)
        for per in win["BTC"]:
            tr[per] = [(win[x][per][0] <= e < win[x][per][1]) for x, e in zip(tr.asset, tr.entry_date)]
        tr.sort_values("entry_date").to_csv(f"{HERE}/trades_{st}.csv", index=False); alltr.append(tr)
        for grp in ASSETS + ["POOLED"]:
            g = ASSETS if grp == "POOLED" else [grp]
            for per in win["BTC"]:
                sub = tr[tr.asset.isin(g) & tr[per]]
                row = dict(strat=st, group=grp, period=per, **tstats(sub.net_ret.values))
                row["exit_mix"] = ";".join(f"{k}:{v}" for k, v in sub.exit_reason.value_counts().items())
                def agg(src):
                    return pd.concat({x: src[x].pct_change().where((src[x].index >= win[x][per][0]) & (src[x].index < win[x][per][1])) for x in g}, axis=1).mean(axis=1, skipna=True).dropna()
                row.update({"port_"+k: v for k, v in pmetrics(agg(cur)).items()})
                row.update({"full_"+k: v for k, v in pmetrics(agg(curf)).items()})
                bh = {x: data[x].close for x in g}
                row.update({"bh_"+k: v for k, v in pmetrics(agg(bh)).items()})
                rows.append(row)
    res = pd.DataFrame(rows); res.to_csv(f"{HERE}/results_L.csv", index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 60); pd.set_option("display.max_rows", 500)
    print(res.drop(columns=["exit_mix"]).round(3).to_string())
    full = pd.concat(alltr)
    print(full.groupby(["strat", "asset"]).net_ret.agg(["count", "mean", "median"]).round(4).to_string())
    print(full.groupby(["strat", "exit_reason"]).size().to_string())
    print("avg bars held:", full.groupby("strat").bars.mean().round(1).to_dict())

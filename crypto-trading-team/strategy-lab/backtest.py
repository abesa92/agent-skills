#!/usr/bin/env python3
"""Strategy lab backtest (S-01 Donchian 40/20, S-02 EMA20 pullback, S-03 funding filter on S-01).
Rules were fixed BEFORE testing; no parameter was tuned. Run: python3 backtest.py [DATA_DIR]
Data: Binance spot 1d klines (data-api.binance.vision), Hyperliquid funding history (api.hyperliquid.xyz). No keys.
Conventions: signal on bar close i, fill at open i+1. Fee 0.10%/side, slippage 0.05% (majors) / 0.30% (memes) per side.
"""
import sys, os, json, numpy as np, pandas as pd, requests
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(D, exist_ok=True)
MAJ = ["BTC", "ETH", "SOL"]; MEME = ["DOGE", "SHIB", "PEPE", "WIF", "BONK", "FLOKI"]
HL = {"BTC":"BTC","ETH":"ETH","SOL":"SOL","DOGE":"DOGE","SHIB":"kSHIB","PEPE":"kPEPE","WIF":"WIF","BONK":"kBONK","FLOKI":"kFLOKI"}
FEE = 0.001; SLIP = {**{a:0.0005 for a in MAJ}, **{a:0.003 for a in MEME}}
SPLIT = pd.Timestamp("2023-06-01")   # fixed in advance (~60% of BTC history); in-sample = entries before, OOS = on/after
RISK = 0.01; LEV_CAP = 1.0; ANN = 365
TODAY = pd.Timestamp("2026-10-04")   # last (partial) bar dropped

def download():
    for a in MAJ + MEME:
        f = f"{D}/{a}USDT_1d.csv"
        if not os.path.exists(f):
            rows, t = [], 0
            while True:
                d = requests.get("https://data-api.binance.vision/api/v3/klines", params=dict(symbol=a+"USDT", interval="1d", startTime=t, limit=1000), timeout=30).json()
                if not d: break
                rows += d; t = d[-1][0] + 86400000
                if len(d) < 1000: break
            df = pd.DataFrame(rows).iloc[:, :6]; df.columns = ["ts","open","high","low","close","volume"]
            df["date"] = pd.to_datetime(df.ts, unit="ms").dt.strftime("%Y-%m-%d")
            df[["date","open","high","low","close","volume"]].to_csv(f, index=False)
        f = f"{D}/{a}_hl_funding.csv"
        if not os.path.exists(f):
            rows, t = [], 1640000000000
            while True:
                d = requests.post("https://api.hyperliquid.xyz/info", json=dict(type="fundingHistory", coin=HL[a], startTime=t), timeout=30).json()
                if not d: break
                rows += d
                if len(d) < 500: break
                t = d[-1]["time"] + 1
            pd.DataFrame(rows).to_csv(f, index=False)

def load(a):
    df = pd.read_csv(f"{D}/{a}USDT_1d.csv", parse_dates=["date"]).set_index("date")
    return df[df.index < TODAY].astype(float)

def prep(df):
    d = df.copy(); pc = d.close.shift(1)
    tr = pd.concat([d.high-d.low, (d.high-pc).abs(), (d.low-pc).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14).mean()
    d["dh40"] = d.high.shift(1).rolling(40).max(); d["dl20"] = d.low.shift(1).rolling(20).min()
    d["ema20"] = d.close.ewm(span=20, adjust=False).mean(); d["ema50"] = d.close.ewm(span=50, adjust=False).mean()
    d["sma100"] = d.close.rolling(100).mean(); d["ll7"] = d.low.rolling(7).min()
    return d

def run(a, d, strat, block=None):
    """Long-only single-asset sleeve. Returns (trades list, daily equity series starting 1.0)."""
    s = SLIP[a]; n = len(d); o, h, l, c = d.open.values, d.high.values, d.low.values, d.close.values
    eq = 1.0; cash = 1.0; sh = 0.0; pos = None; pend = None; curve = np.full(n, np.nan); trades = []
    for i in range(n):
        # 1) execute pending order at this bar's open
        if pend:
            kind = pend; pend = None
            if kind[0] == "exit" and pos:
                px = o[i]*(1-s); cash += sh*px*(1-FEE); trades.append(close_trade(a, pos, d.index[i], px, "signal")); sh = 0; pos = None
            elif kind[0] == "enter" and not pos:
                stop, tgt = kind[1], kind[2]
                if isinstance(stop, tuple): stop = o[i] - stop[1]
                if o[i] > stop:
                    px = o[i]*(1+s); rdist = (px - stop)/px
                    notional = min(LEV_CAP*cash, RISK*cash/rdist) if rdist > 0 else 0
                    if notional > 0:
                        sh = notional/(px*(1+FEE)); cash -= notional
                        pos = dict(asset=a, strat=strat, entry_date=d.index[i], entry_px=px, stop=stop, tgt=tgt, cost=notional, bars=0, risk_frac=rdist)
        # 2) intrabar stop / target
        if pos and pos["entry_date"] <= d.index[i]:
            pos["bars"] += 1
            if l[i] <= pos["stop"]:
                px = min(o[i], pos["stop"])*(1-s); cash += sh*px*(1-FEE); trades.append(close_trade(a, pos, d.index[i], px, "stop")); sh = 0; pos = None
            elif pos["tgt"] and h[i] >= pos["tgt"]:
                px = max(o[i], pos["tgt"])*(1-s); cash += sh*px*(1-FEE); trades.append(close_trade(a, pos, d.index[i], px, "target")); sh = 0; pos = None
        curve[i] = cash + sh*c[i]
        # 3) signals on this bar's close -> order for next open
        if i+1 >= n or np.isnan(d.atr.iat[i]) or np.isnan(d.dh40.iat[i]) or np.isnan(d.sma100.iat[i]): continue
        if strat in ("S01", "S03"):
            if pos and c[i] < d.dl20.iat[i]: pend = ("exit",)
            elif not pos and c[i] > d.dh40.iat[i]:
                if strat == "S03" and block is not None and block(a, d.index[i]): continue
                pend = ("enter", ("off", 3*d.atr.iat[i]), None)   # stop = FILL price - 3*ATR14(signal bar)
        elif strat == "S02":
            if pos:
                if c[i] < d.ema50.iat[i] or pos["bars"] >= 20: pend = ("exit",)
            else:
                up = c[i] > d.sma100.iat[i] and d.ema20.iat[i] > d.ema50.iat[i]
                if up and l[i] <= d.ema20.iat[i] and c[i] > d.ema20.iat[i]:
                    stop = d.ll7.iat[i]; r = c[i] - stop
                    if r > 0: pend = ("enter", stop, c[i] + 2*r)
    if pos:  # close at last close (mark-to-market, flagged)
        px = c[-1]*(1-s); trades.append(close_trade(a, pos, d.index[-1], px, "open_at_end", shares=sh))
        cash += sh*px*(1-FEE); curve[-1] = cash
    return trades, pd.Series(curve, index=d.index)

def close_trade(a, pos, dt, px, why, shares=None):
    sh = pos["cost"]/(pos["entry_px"]*(1+FEE)); proceeds = sh*px*(1-FEE)
    ret = proceeds/pos["cost"] - 1
    return dict(asset=a, strat=pos["strat"], entry_date=pos["entry_date"].date(), exit_date=pd.Timestamp(dt).date(), entry_px=pos["entry_px"], exit_px=px, exit_reason=why,
                bars=pos["bars"], net_ret=ret, R=ret/pos["risk_frac"] if pos["risk_frac"] else np.nan, pnl_frac_of_equity=proceeds-pos["cost"], hold_pnl_dummy=0)

def stats(tr):
    if len(tr) == 0: return dict(n=0)
    r = tr.net_ret; w = r[r > 0]; ls = r[r <= 0]
    return dict(n=len(tr), win_rate=len(w)/len(r), avg_win=w.mean() if len(w) else np.nan, avg_loss=ls.mean() if len(ls) else np.nan,
                profit_factor=w.sum()/-ls.sum() if ls.sum() < 0 else np.inf, expectancy_pct=r.mean(), expectancy_R=tr.R.mean(), median_ret=r.median())

def port(curves, mask_start=None, mask_end=None):
    """Equal-weight, daily-rebalanced portfolio of sleeve daily returns (assets enter when they have data)."""
    rets = pd.concat({a: c.pct_change() for a, c in curves.items()}, axis=1)
    if mask_start is not None: rets = rets[(rets.index >= mask_start) & (rets.index < mask_end)]
    p = rets.mean(axis=1, skipna=True).fillna(0)
    return p

def pm(p):
    if len(p) < 30: return dict(days=len(p))
    e = (1+p).cumprod(); dd = (e/e.cummax()-1).min()
    return dict(days=len(p), total_return=e.iloc[-1]-1, max_dd=dd, sharpe=p.mean()/p.std()*np.sqrt(ANN) if p.std() > 0 else np.nan)

def bh(a_list, data, start, end):
    r = pd.concat({a: data[a].close.pct_change() for a in a_list}, axis=1)
    r = r[(r.index >= start) & (r.index < end)]
    return r.mean(axis=1, skipna=True).fillna(0)

def funding_block(thresh=0.20):
    fs = {}
    for a in MAJ+MEME:
        f = f"{D}/{a}_hl_funding.csv"
        if os.path.exists(f):
            x = pd.read_csv(f); x["t"] = pd.to_datetime(x.time, unit="ms").dt.floor("D")
            fs[a] = x.groupby("t").fundingRate.mean()*24*365   # annualised from hourly rate
    def blk(a, dt):
        if a not in fs: return False
        w = fs[a][(fs[a].index <= dt) & (fs[a].index > dt - pd.Timedelta(days=7))]
        return len(w) >= 5 and w.mean() > thresh
    first = {a: fs[a].index.min() for a in fs}
    return blk, first

if __name__ == "__main__":
    download()
    data = {a: prep(load(a)) for a in MAJ+MEME}
    blk, fstart = funding_block()
    res, alltr = [], []
    GROUPS = {"MAJORS": MAJ, "MEMES": MEME, "ALL": MAJ+MEME}
    for strat in ["S01", "S02", "S03"]:
        curves, trs = {}, []
        for a in MAJ+MEME:
            if strat == "S03":   # restrict to window with funding data (HL history starts 2023-05) for a like-for-like comparison
                d = data[a][data[a].index >= fstart[a]] if a in fstart else None
                if d is None: continue
                t, c = run(a, d, strat, blk)
            else:
                t, c = run(a, data[a], strat)
            trs += t; curves[a] = c
        tr = pd.DataFrame(trs); tr["period"] = np.where(pd.to_datetime(tr.entry_date) < SPLIT, "IS", "OOS")
        tr.sort_values("entry_date").to_csv(f"{OUT}/trades_{strat}.csv", index=False); alltr.append(tr)
        if strat == "S03":  # baseline = S01 on the identical window, no filter
            base = []
            for a in MAJ+MEME:
                t, _ = run(a, data[a][data[a].index >= fstart[a]], "S01"); base += t
            btr = pd.DataFrame(base); btr.to_csv(f"{OUT}/trades_S03_baseline_unfiltered.csv", index=False)
            res.append(dict(strat="S03_baseline(S01 no filter, funding window)", group="ALL", period="window", **stats(btr)))
            res.append(dict(strat="S03(S01 + funding filter)", group="ALL", period="window", **stats(tr)))
            continue
        for gname, g in GROUPS.items():
            for per, (s0, s1) in {"IS": (pd.Timestamp("2000-01-01"), SPLIT), "OOS": (SPLIT, pd.Timestamp("2100-01-01")), "FULL": (pd.Timestamp("2000-01-01"), pd.Timestamp("2100-01-01"))}.items():
                sub = tr[tr.asset.isin(g)]
                if per != "FULL": sub = sub[sub.period == per]
                row = dict(strat=strat, group=gname, period=per, **stats(sub))
                p = port({a: curves[a] for a in g}, s0, s1); row.update({"port_"+k: v for k, v in pm(p).items()})
                b = bh(g, data, s0, s1); row.update({"bh_"+k: v for k, v in pm(b).items()})
                res.append(row)
    pd.DataFrame(res).to_csv(f"{OUT}/results_summary.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(pd.DataFrame(res).round(3).to_string())
    full = pd.concat(alltr)
    print(full.groupby(["strat", "asset"]).net_ret.agg(["count", "mean"]).round(4).to_string())
    print("data:", {a: (str(data[a].index[0].date()), str(data[a].index[-1].date()), len(data[a])) for a in data})

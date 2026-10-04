"""Diagnostics + independent hand-check for backtest_L.py (reads raw candles with plain csv, recomputes signals without pandas)."""
import csv, pandas as pd, numpy as np, os
H = os.path.dirname(os.path.abspath(__file__))
FEE, SLIP = 0.001, 0.0005
def raw(a):
    rows = list(csv.DictReader(open(f"{H}/data/{a}USDT_1d.csv"))); rows = [r for r in rows if r["date"] < "2026-10-04"]
    return {k: [r[k] if k == "date" else float(r[k]) for r in rows] for k in ["date", "open", "high", "low", "close"]}
# ---- exposure & concentration
for st in ["L001", "L004", "L031"]:
    t = pd.read_csv(f"{H}/trades_{st}.csv"); t["entry_date"] = pd.to_datetime(t.entry_date)
    ex = {}
    for a in ["BTC", "ETH", "SOL"]:
        x = t[t.asset == a]; r = raw(a); n_days = len(r["date"]) - 200
        ex[a] = round(x.bars.sum()/n_days, 3)
    top3 = t.sort_values("net_ret").tail(3); gw = t.net_ret[t.net_ret > 0].sum()
    print(st, "exposure(share of usable days in position)", ex, "| top3 share of gross wins FULL: %.0f%%" % (100*top3.net_ret.sum()/gw),
          "| top3:", [(r.asset, str(r.entry_date.date()), round(r.net_ret, 3)) for r in top3.itertuples()])
    o = t[t.OOS30]; gwo = o.net_ret[o.net_ret > 0].sum()
    print("   OOS30 pooled n=%d top3 share of gross wins %.0f%%" % (len(o), 100*np.sort(o.net_ret.values)[-3:].sum()/gwo))
# ---- hand check
def rsi2(c):
    out = [None]*len(c); au = ad = None
    for i in range(1, len(c)):
        d = c[i]-c[i-1]; u, dn = max(d, 0), max(-d, 0)
        au = u if au is None else 0.5*au+0.5*u*1 if False else (0.5*u+0.5*au if au is not None else u)
        ad = dn if ad is None else 0.5*dn+0.5*ad
        if i >= 2: out[i] = 100.0 if ad == 0 else 100-100/(1+au/ad)
    return out
def check(st, a, k):
    t = pd.read_csv(f"{H}/trades_{st}.csv"); t = t[t.asset == a].sort_values("entry_date").iloc[k]
    r = raw(a); D = r["date"]; ie = D.index(t.entry_date); ix = D.index(t.exit_date)
    print(f"\n[{st} {a} trade#{k}] entry {t.entry_date} exit {t.exit_date} reason {t.exit_reason} net_ret {t.net_ret:.4f}")
    s = ie-1
    print(" signal bar", D[s], "close", r["close"][s], "| entry open (next bar)", r["open"][ie], "-> fill", round(r["open"][ie]*(1+SLIP), 4), "csv", round(t.entry_px, 4))
    if st == "L001":
        print(" max high prev 20:", max(r["high"][s-20:s]), "close>", r["close"][s] > max(r["high"][s-20:s]))
        tr = [max(r["high"][j]-r["low"][j], abs(r["high"][j]-r["close"][j-1]), abs(r["low"][j]-r["close"][j-1])) for j in range(s-19, s+1)]
        atr = sum(tr)/20; stop = r["open"][ie]-2*atr; print(" ATR20 %.2f stop %.2f" % (atr, stop), "| lows bars after entry min:", min(r["low"][ie:ix+1]))
    if st == "L004":
        print(" signal weekday (6=Sun):", pd.Timestamp(D[s]).dayofweek, "ret30 = %.4f" % (r["close"][s]/r["close"][s-30]-1))
    if st == "L031":
        rs = rsi2(r["close"]); print(" RSI2 at signal %.2f, close %.2f vs SMA200 %.2f" % (rs[s], r["close"][s], sum(r["close"][s-199:s+1])/200))
    sx = ix-1
    print(" exit signal bar", D[sx], "close", r["close"][sx], "| exit fill (open of", D[ix], ")", round(r["open"][ix]*(1-SLIP), 4), "csv", round(t.exit_px, 4))
    if st == "L001" and t.exit_reason == "signal": print(" min low prev 10 at exit signal:", min(r["low"][sx-10:sx]), "close<", r["close"][sx] < min(r["low"][sx-10:sx]))
    if st == "L004": print(" exit-signal weekday", pd.Timestamp(D[sx]).dayofweek, "ret30 %.4f" % (r["close"][sx]/r["close"][sx-30]-1))
    if st == "L031":
        rs = rsi2(r["close"]); print(" RSI2 at exit signal %.2f, close %.2f vs SMA5 %.2f, bars held %d" % (rs[sx], r["close"][sx], sum(r["close"][sx-4:sx+1])/5, t.bars))
    px_in = r["open"][ie]*(1+SLIP); px_out = r["open"][ix]*(1-SLIP) if t.exit_reason != "stop" else t.exit_px
    print(" recomputed net_ret %.4f" % (px_out*(1-FEE)/(px_in*(1+FEE))-1), "csv %.4f" % t.net_ret)
check("L001", "BTC", 2); check("L001", "ETH", 0); check("L004", "BTC", 5); check("L031", "BTC", 10)

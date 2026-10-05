#!/usr/bin/env python3
"""Independent hand-checks (plain python/csv, no pandas engine reuse) of L-001 / L-106 / L-101 against raw candles. Run: python3 diagnostics_L2.py > diagnostics_L2_output.txt"""
import csv, os, math, datetime as dt
H = os.path.dirname(os.path.abspath(__file__)); FEE = 0.001; S = 0.0005
def rd(f): return list(csv.DictReader(open(f)))
# ---------------- L-001 : first BTC trade in the re-run file, rebuilt from raw daily candles
d = [r for r in rd(f"{H}/data/BTCUSDT_1d.csv") if r["date"] < "2026-10-04"]
o = [float(r["open"]) for r in d]; h = [float(r["high"]) for r in d]; l = [float(r["low"]) for r in d]; c = [float(r["close"]) for r in d]; dd = [r["date"] for r in d]
tr = [r for r in rd(f"{H}/trades_L001_rerun_BTC_ETH.csv") if r["asset"] == "BTC"]; tr.sort(key=lambda r: r["entry_date"]); t = tr[0]
i = dd.index(t["entry_date"]); sig = i-1
hh = max(h[sig-20:sig]); print("L-001 BTC trade #1:", t["entry_date"], "->", t["exit_date"], t["exit_reason"])
print(f"  signal bar {dd[sig]} close {c[sig]:.2f} > highest high of prior 20 bars {hh:.2f}: {c[sig] > hh}")
tr_ = [max(h[k]-l[k], abs(h[k]-c[k-1]), abs(l[k]-c[k-1])) for k in range(sig-19, sig+1)]; atr = sum(tr_)/20
ent = o[i]*(1+S); print(f"  entry = open[{dd[i]}] {o[i]:.2f} x1.0005 = {ent:.4f} (file {float(t['entry_px']):.4f}); ATR20 {atr:.2f}; stop = open - 2xATR = {o[i]-2*atr:.2f}")
j = dd.index(t["exit_date"]); print(f"  exit bar {dd[j]} open {o[j]:.2f} low {l[j]:.2f}; prior close {c[j-1]:.2f} vs lowest low prior 10 bars (to bar j-2) {min(l[j-11:j-1]):.2f}")
if t["exit_reason"] == "signal":
    px = o[j]*(1-S); net = px*(1-FEE)/(ent*(1+FEE))-1; print(f"  exit px {px:.4f} (file {float(t['exit_px']):.4f}); net ret {net:.6f} (file {float(t['net_ret']):.6f})")
# ---------------- L-106 : independent forecast + simulation for BTC
def ema(x, span):
    a = 2/(span+1); e = x[0]; out = []
    for v in x: e = a*v+(1-a)*e; out.append(e)
    return out
def ewstd(x, span, k):   # exp-weighted std at k, reliability-weights bias correction (pandas ewm.std equivalent), x list with None for NaN
    a = 2/(span+1); ws = []; xs = []
    for m in range(1, k+1):
        if x[m] is None: continue
        ws.append((1-a)**(k-m)); xs.append(x[m])
    sw = sum(ws); mu = sum(w*v for w, v in zip(ws, xs))/sw; sw2 = sum(w*w for w in ws)
    var = sum(w*(v-mu)**2 for w, v in zip(ws, xs))/sw/(1-sw2/sw**2); return math.sqrt(var)
ret = [None]+[c[k]/c[k-1]-1 for k in range(1, len(c))]
E = {(f, s): (ema(c, f), ema(c, s)) for f, s in [(8, 32), (16, 64), (32, 128), (64, 256)]}; SC = {(8, 32): 5.3, (16, 64): 3.75, (32, 128): 2.65, (64, 256): 1.87}
def target(k):
    vol = ewstd(ret, 35, k)*c[k]; F = 0
    for key, (ef, es) in E.items(): F += max(-20, min(20, (ef[k]-es[k])/vol*SC[key]))/4
    return F, max(0, F)/20
sg = rd(f"{H}/signals_L106_BTC.csv"); worst = 0
for k in [300, 800, 1500, 2500, 3300]:
    F, T = target(k); worst = max(worst, abs(F-float(sg[k]["F"])), abs(T-float(sg[k]["target"]))); print(f"L-106 BTC {dd[k]}: independent F={F:.4f} target={T:.4f} | file F={float(sg[k]['F']):.4f} target={float(sg[k]['target']):.4f}")
print("  max abs diff:", f"{worst:.2e}")
cash, u = 1.0, 0.0; nreb = 0; Tg = [None]*256+[target(k)[1] for k in range(256, len(c))]
for k in range(1, len(c)):
    if Tg[k-1] is None: continue
    V = cash+u*o[k]; cur = u*o[k]/V; tg = Tg[k-1]; dl = tg-cur
    if abs(dl) > 0.10 or (tg == 0 and u > 0):
        nreb += 1
        if dl > 0: X = min(dl*V, cash); u += X/(o[k]*(1+S)*(1+FEE)); cash -= X
        else:
            q = u if tg == 0 else min(u, -dl*V/o[k]); cash += q*o[k]*(1-S)*(1-FEE); u -= q
eq = cash+u*c[-1]*(1-S)*(1-FEE) if u > 0 else cash
cv = rd(f"{H}/curve_L106.csv"); print(f"L-106 BTC independent re-simulation: final equity (after liquidation) {eq:.6f} vs file {float(cv[-1]['BTC']):.6f}; rebalances {nreb}")
ep = [r for r in rd(f"{H}/trades_L106.csv") if r["strat"] == "L106" and r["asset"] == "BTC"]; e = ep[0]; k = dd.index(e["entry_date"])
print(f"  first BTC episode {e['entry_date']} -> {e['exit_date']} ({e['exit_reason']}): target at prior close {Tg[k-1]:.4f}, entry px {o[k]*(1+S):.2f} (file {float(e['entry_px']):.2f}), net {float(e['net_ret']):.4f}")
# ---------------- L-101 : raw hourly candles
raw = {r["time"]: r for r in rd(f"{H}/data/BTCUSDT_1h.csv")}
for day in ["2024-03-05", "2021-05-19"]:
    a, b = raw[f"{day} 22:00"], raw[f"{day} 23:00"]; en = float(a["open"]); ex = float(b["close"]); net = ex*(1-S)*(1-FEE)/(en*(1+S)*(1+FEE))-1
    f = [r for r in rd(f"{H}/trades_L101_BTC.csv") if r["date"][:10] == day][0]
    print(f"L-101 BTC {day}: 22:00 open {en} (entry), 23:00 close {ex} (= 00:00 exit); gross {ex/en-1:.6f} net {net:.6f} | file gross {float(f['gross']):.6f} net {float(f['net']):.6f}; entry_time {f['entry_time']} exit_time {f['exit_time']}")
days = sorted({k[:10] for k in raw if k.endswith("22:00")}); n = 0; s = 0.0
for dday in days:
    k1, k2 = f"{dday} 22:00", f"{dday} 23:00"
    if k2 in raw and dday < "2026-10-04" and dday >= "2017-08-18":
        n += 1; en = float(raw[k1]["open"]); ex = float(raw[k2]["close"]); s += ex*(1-S)*(1-FEE)/(en*(1+S)*(1+FEE))-1
print(f"L-101 BTC independent full-sample count {n} mean net {s/n:.6f} (file: n=3332 expected, see results_L2.csv)")

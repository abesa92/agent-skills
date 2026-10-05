#!/usr/bin/env python3
"""Download Binance spot 1h klines (BTCUSDT, ETHUSDT) from data-api.binance.vision -> data/{SYM}_1h.csv. Public, no key.
Resumable (appends; rerun until it prints DONE). Only fully closed hours kept. Time budget per run: argv[1] seconds (default 140).
Columns: time(UTC open time), open, high, low, close, volume."""
import os, sys, time, requests, pandas as pd
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"); H = 3600000
BUDGET = float(sys.argv[1]) if len(sys.argv) > 1 else 140; t0 = time.time(); now = int(time.time()*1000)
sess = requests.Session(); alldone = True
for sym in ["BTCUSDT", "ETHUSDT"]:
    f = f"{D}/{sym}_1h.csv"
    if os.path.exists(f):
        last = pd.read_csv(f, usecols=["time"]).time.iloc[-1]; t = int(pd.Timestamp(last).timestamp()*1000) + H
    else:
        t = int(pd.Timestamp("2017-08-17").timestamp()*1000)
        with open(f, "w") as fh: fh.write("time,open,high,low,close,volume\n")
    while t + H <= now:
        if time.time() - t0 > BUDGET: alldone = False; break
        d = sess.get("https://data-api.binance.vision/api/v3/klines", params=dict(symbol=sym, interval="1h", startTime=t, limit=1000), timeout=30).json()
        if not d: break
        d = [r for r in d if r[0] + H <= now]
        if not d: break
        with open(f, "a") as fh:
            for r in d: fh.write(f"{pd.Timestamp(r[0], unit='ms').strftime('%Y-%m-%d %H:%M')},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]}\n")
        t = d[-1][0] + H
    n = sum(1 for _ in open(f)) - 1; print(sym, n, "rows, last", pd.read_csv(f, usecols=["time"]).time.iloc[-1])
print("DONE" if alldone else "PARTIAL - rerun")

#!/usr/bin/env python3
"""L-016 data step. Downloads Binance spot 1d klines (public, no key; data-api.binance.vision) for EVERY USDT spot symbol in exchangeInfo
(TRADING + BREAK/delisted ones that the API still serves) -> data/allusdt_1d/<SYM>.csv with columns date,open,high,low,close,volume,quote_volume.
Resumable (skips existing files), threaded, time budget per run argv[1] s (default 120). Rerun until it prints DONE. Only complete UTC days (< 2026-10-04)."""
import os, sys, time, json, requests, pandas as pd
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); D = f"{HERE}/data"; OUT = f"{D}/allusdt_1d"; os.makedirs(OUT, exist_ok=True)
BUDGET = float(sys.argv[1]) if len(sys.argv) > 1 else 120; T0 = time.time(); TODAY_MS = int(pd.Timestamp("2026-10-04").timestamp()*1000)
S = requests.Session()
fx = f"{D}/binance_usdt_symbols.csv"
if not os.path.exists(fx):
    ex = S.get("https://data-api.binance.vision/api/v3/exchangeInfo", timeout=60).json()
    rows = [dict(symbol=s["symbol"], base=s["baseAsset"], status=s["status"], spot=s["isSpotTradingAllowed"]) for s in ex["symbols"] if s["quoteAsset"] == "USDT"]
    pd.DataFrame(rows).to_csv(fx, index=False)
syms = pd.read_csv(fx).symbol.tolist()
def get(sym):
    f = f"{OUT}/{sym}.csv"
    if os.path.exists(f): return "skip"
    if time.time()-T0 > BUDGET: return "late"
    rows, t = [], 0
    for _ in range(10):
        for k in range(5):
            try:
                r = S.get("https://data-api.binance.vision/api/v3/klines", params=dict(symbol=sym, interval="1d", startTime=t, limit=1000), timeout=30)
                if r.status_code == 429: time.sleep(5); continue
                d = r.json(); break
            except Exception: time.sleep(2); d = None
        if not isinstance(d, list): return "err"
        d = [x for x in d if x[0] < TODAY_MS]
        if not d: break
        rows += d; t = d[-1][0]+86400000
        if len(d) < 1000: break
    if not rows: pd.DataFrame(columns=["date","open","high","low","close","volume","quote_volume"]).to_csv(f, index=False); return "empty"
    df = pd.DataFrame(rows).iloc[:, [0,1,2,3,4,5,7]]; df.columns = ["ts","open","high","low","close","volume","quote_volume"]
    df["date"] = pd.to_datetime(df.ts, unit="ms").dt.strftime("%Y-%m-%d")
    df[["date","open","high","low","close","volume","quote_volume"]].to_csv(f, index=False); return "ok"
with ThreadPoolExecutor(6) as ex: res = list(ex.map(get, syms))
from collections import Counter
print(Counter(res), "files:", len(os.listdir(OUT)), "of", len(syms)); print("DONE" if not any(x in ("late","err") for x in res) else "PARTIAL - rerun")

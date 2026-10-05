import pandas as pd, numpy as np
np.random.seed(0)
for s in ["S01","S02"]:
    t=pd.read_csv(f"trades_{s}.csv"); t["per"]=np.where(pd.to_datetime(t.entry_date)<"2023-06-01","IS","OOS")
    for name,sub in [("ALL",t),("MAJORS",t[t.asset.isin(["BTC","ETH","SOL"])]),("MEMES",t[~t.asset.isin(["BTC","ETH","SOL"])])]:
        for per in ["IS","OOS"]:
            r=sub[sub.per==per].net_ret.values
            if len(r)<10: continue
            bs=[np.random.choice(r,len(r)).mean() for _ in range(5000)]
            ex3=np.sort(r)[:-3]; w=ex3[ex3>0].sum(); l=-ex3[ex3<=0].sum()
            print(s,name,per,"n",len(r),"mean %.4f"%r.mean(),"95%%CI [%.4f, %.4f]"%tuple(np.percentile(bs,[2.5,97.5])),"PF ex-top3 %.2f"%(w/l),"top3 share of gross wins %.0f%%"%(100*np.sort(r)[-3:].sum()/r[r>0].sum()),"exit:",sub[sub.per==per].exit_reason.value_counts().to_dict())
t=pd.read_csv("trades_S01.csv"); t=t[pd.to_datetime(t.entry_date)>="2023-06-01"]
print(t.groupby("asset").net_ret.agg(["count","mean","median"]).round(3)); print("avg hold bars",t.bars.mean(), "open_at_end",(t.exit_reason=="open_at_end").sum())
print(pd.read_csv("trades_S01.csv").sort_values("net_ret").tail(5)[["asset","entry_date","exit_date","net_ret"]])
# hand-check first BTC S01 trade
d=pd.read_csv("data/BTCUSDT_1d.csv",parse_dates=["date"]).set_index("date")
x=pd.read_csv("trades_S01.csv"); f=x[x.asset=="BTC"].iloc[0]; print(f.to_dict())
print(d.loc[pd.Timestamp(f.entry_date)-pd.Timedelta(days=1):pd.Timestamp(f.entry_date)][["open","high","low","close"]])

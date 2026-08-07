import warnings; warnings.filterwarnings("ignore")
import io,sys
_orig=sys.stdout; sys.stdout=io.StringIO()
from analyze import parse_file, wallet_net, tag_stats, whale_stats
sys.stdout=_orig
import pandas as pd, numpy as np

PUMP = {
 "punch 1":"punch 1.csv","punch 2":"punch 2.csv","testicle":"testicle.csv","grail":"grail.csv",
 "bountywork":"bountywork.csv","assface":"assface.csv","ansem 1":"ansem 1.csv","ansem 2":"ansem 2.csv",
 "chance":"chance.csv","hoppy":"hoppy.csv"}
CTRL = {"luna_dump":"luna_dump.csv","luna_after_dump":"luna_after_dump.csv"}

def metrics(f):
    df=parse_file(f); tot=df.delta_sol.abs().sum()
    low=df.loc[df.price.idxmin(),"ts"]
    pre=df[(df.ts>=low-pd.Timedelta(hours=3))&(df.ts<=low)]
    post=df[(df.ts>low)&(df.ts<=low+pd.Timedelta(hours=3))]
    def bp(x): b=x.loc[x.side=='BUY','delta_sol'].sum(); return 100*b/x.delta_sol.abs().sum() if len(x) else 0
    # spring: candle 15min post-low dgn buy%>=55
    w=df[(df.ts>=low-pd.Timedelta(hours=1))&(df.ts<=low+pd.Timedelta(hours=2))].copy()
    w["b"]=w.ts.dt.floor("15min"); lb=low.floor("15min")
    postbins=w[w.b>lb]
    spring=postbins.groupby("b").apply(lambda s: 100*s.loc[s.side=="BUY","delta_sol"].sum()/s.delta_sol.abs().sum() if s.delta_sol.abs().sum()>0 else 0)
    nspring=(spring>=55).sum()
    # big buy 1jam setelah low
    bb=df[(df.ts>low)&(df.ts<=low+pd.Timedelta(hours=1))]; bb=bb[(bb.side=="BUY")&(bb.sol_amt>=1)]
    # retention
    lw=df[(df.ts>=low-pd.Timedelta(hours=3))&(df.ts<=low+pd.Timedelta(hours=3))]
    ww=wallet_net(lw); acc=ww[ww.net_sol>=0.5]
    after=df[df.ts>low+pd.Timedelta(hours=3)]
    asell=after[after.side=="SELL"].groupby("wallet")["delta_sol"].sum() if len(after) else pd.Series(dtype=float)
    ret=0; hold=0
    if len(acc):
        sold=acc.index.map(lambda x:-asell.get(x,0.0)); ret=((acc.net_sol-sold).clip(lower=0)/acc.net_sol*100).mean(); hold=100*(sold==0).mean()
    wh=whale_stats(df)
    return dict(
      cvd_pct=100*df.cvd_sol.iloc[-1]/tot,
      buy_tx=100*(df.side=="BUY").sum()/len(df),
      avg_buy=df.loc[df.side=="BUY","sol_amt"].mean(),
      avg_sell=df.loc[df.side=="SELL","sol_amt"].mean(),
      whale_net=wh["big_net"],
      low2close=100*(df.price.iloc[-1]/df.price.min()-1),
      pre_net=pre.delta_sol.sum(), pre_buy=bp(pre),
      post_net=post.delta_sol.sum(), post_buy=bp(post),
      post_vol=post.delta_sol.abs().sum(),
      nspring=nspring, spring_max=spring.max() if len(spring) else 0,
      bigbuy1h=bb.delta_sol.sum(),
      n_accum=len(acc), accum_net=acc.net_sol.sum() if len(acc) else 0,
      retention=ret, hold_pct=hold,
    )

rows=[]
for n,f in {**PUMP,**CTRL}.items():
    m=metrics(f); m["token"]=n; m["grup"]="PUMP" if n in PUMP else "CTRL"
    rows.append(m)
df=pd.DataFrame(rows)
cols=["token","grup","cvd_pct","buy_tx","avg_buy","avg_sell","whale_net","low2close","pre_net","post_net","post_buy","post_vol","nspring","spring_max","bigbuy1h","n_accum","retention","hold_pct"]
pd.set_option("display.width",260); pd.set_option("display.max_columns",30); pd.set_option("display.float_format",lambda v:f"{v:.2f}")
print(df[cols].to_string(index=False))
print("\n--- MEDIAN GRUP ---")
print(df.groupby("grup")[cols[2:]].median().T.to_string())

# filter pass rate
print("\n--- FILTER PASS RATE ---")
checks={
 "CVD |x|<10%": df.cvd_pct.abs()<10,
 "buy_tx >=52%": df.buy_tx>=52,
 "avgSELL > avgBUY": df.avg_sell>df.avg_buy,
 "whale_net <0": df.whale_net<0,
 "low2close >10%": df.low2close>10,
 "post_low_net>0": df.post_net>0,
 "post_low_buy>50%": df.post_buy>50,
 "nspring>=1": df.nspring>=1,
 "retention>=40%": df.retention>=40,
 "bigbuy1h>=5": df.bigbuy1h>=5,
}
res=[]
for label,mask in checks.items():
    p=mask[df.grup=="PUMP"]; c=mask[df.grup=="CTRL"]
    res.append({"filter":label,"PUMP_lolos":f"{p.sum()}/{len(p)}","CTRL_lolos":f"{c.sum()}/{len(c)}",
                "PUMP%":round(100*p.mean(),0),"CTRL%":round(100*c.mean(),0)})
print(pd.DataFrame(res).to_string(index=False))

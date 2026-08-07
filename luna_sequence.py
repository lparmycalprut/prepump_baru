import warnings; warnings.filterwarnings("ignore")
import io,sys
_orig=sys.stdout; sys.stdout=io.StringIO()
from analyze import parse_file, wallet_net
sys.stdout=_orig
import pandas as pd, numpy as np
pd.set_option("display.width",240); pd.set_option("display.float_format",lambda v:f"{v:,.3f}")

d1=parse_file("luna_dump.csv"); d2=parse_file("luna_after_dump.csv"); d3=parse_file("luna3.csv")
print("LUNA 3-hari sequence (UTC):")
for nm,df in [("Aug1 dump",d1),("Aug2 after",d2),("Aug3 pump",d3)]:
    print(f"\n=== {nm}: {df.ts.iloc[0]} -> {df.ts.iloc[-1]} ===")
    h=df.copy(); h["hr"]=h.ts.dt.strftime("%m-%d %H")
    g=h.groupby("hr")
    rows=[]
    for m,s in g:
        b=s.loc[s.side=="BUY","delta_sol"].sum(); ss=-s.loc[s.side=="SELL","delta_sol"].sum()
        rows.append({"hr":m,"tx":len(s),"buy":b,"sell":ss,"net":b-ss,"buypct":round(100*b/(b+ss),1) if b+ss>0 else 0,"plow":s.price.min(),"pclose":s.price.iloc[-1]})
    r=pd.DataFrame(rows)
    # print only jam 18:00 Aug1 onward for d1, all for d2, first 6 hours d3
    if nm.startswith("Aug1"):
        r=r[r.hr>="08-01 12"]
    elif nm.startswith("Aug3"):
        r=r.head(8)
    print(r.to_string(index=False))

# Wallet continuity: siapa yg beli di Aug1 low / Aug2, dan hold sampai Aug3
print("\n=== KONTINUITAS WALLET (yg akumulasi di low, hold sampai pump) ===")
low1=d1.loc[d1.price.idxmin(),"ts"]
lw1=d1[(d1.ts>=low1-pd.Timedelta(hours=3))&(d1.ts<=low1+pd.Timedelta(hours=3))]
a1=wallet_net(lw1); a1=a1[a1.net_sol>=0.5]
low2=d2.loc[d2.price.idxmin(),"ts"]
lw2=d2[(d2.ts>=low2-pd.Timedelta(hours=3))&(d2.ts<=low2+pd.Timedelta(hours=3))]
a2=wallet_net(lw2); a2=a2[a2.net_sol>=0.5]

# apakah wallet2 ini masih hold (tidak jual) di Aug3?
s3=d3[d3.side=="SELL"].groupby("wallet")["delta_sol"].sum()  # negative
b3=d3[d3.side=="BUY"].groupby("wallet")["delta_sol"].sum()
def report(acc,label):
    n=len(acc); sold=acc.index.map(lambda w:s3.get(w,0.0)); # negative or 0
    n_sold=(sold<-0.1).sum()
    bought3=acc.index.map(lambda w:b3.get(w,0.0)); n_b3=(bought3>0.1).sum()
    print(f"{label}: {n} akumulator. Yg JUAL di Aug3: {n_sold} ({100*n_sold/n:.0f}%). Yg NAMBAH BELI di Aug3: {n_b3}. Total net saat akumulasi: {acc.net_sol.sum():.1f} SOL")
report(a1,"Akumulator Aug1 low (20:13)")
report(a2,"Akumulator Aug2 low (23:19)")

# Top buyer Aug3 (first 6h = pump)
pump3=d3[d3.ts<=d3.ts.iloc[0]+pd.Timedelta(hours=6)]
print(f"\nAug3 6 jam pertama (pump): vol {pump3.delta_sol.abs().sum():.1f} SOL, net {pump3.delta_sol.sum():.1f}, buy% {100*pump3.loc[pump3.side=='BUY','delta_sol'].sum()/pump3.delta_sol.abs().sum():.1f}%")

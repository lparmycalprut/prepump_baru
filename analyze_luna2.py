import warnings; warnings.filterwarnings("ignore")
import io,sys
_orig=sys.stdout; sys.stdout=io.StringIO()
from analyze import parse_file, hour_stats, wallet_net, tag_stats, whale_stats, price_path, cvd_divergence, phase_detection
sys.stdout=_orig
import pandas as pd, numpy as np
pd.set_option("display.width",220); pd.set_option("display.max_columns",30)
pd.set_option("display.float_format", lambda v: f"{v:,.3f}")

for f in ["luna_dump.csv","luna_after_dump.csv"]:
    df=parse_file(f); p=price_path(df); wh=whale_stats(df); d=cvd_divergence(df); ph=phase_detection(df)
    tot=df.delta_sol.abs().sum()
    print("="*100); print(f, "|", df.ts.iloc[0].date(), "|", len(df),"tx |",df.wallet.nunique(),"wallets")
    print(f"  vol {tot:,.1f} buy {df.loc[df.side=='BUY','delta_sol'].sum():,.1f} sell {-df.loc[df.side=='SELL','delta_sol'].sum():,.1f} | CVD {df.cvd_sol.iloc[-1]:.2f} ({100*df.cvd_sol.iloc[-1]/tot:.2f}%)")
    print(f"  price open {p['open']:.8f} high {p['high']:.8f} low {p['low']:.8f} @ {p['low_time']} close {p['close']:.8f}")
    print(f"  day chg {p['change_pct']:+.1f}% low->close {p['low_to_close_pct']:+.1f}% | whale >1: {wh['big_tx']}tx net {wh['big_net']:+.1f} | avgBuy {df.loc[df.side=='BUY','sol_amt'].mean():.3f} avgSell {df.loc[df.side=='SELL','sol_amt'].mean():.3f}")
    print("  FASE:"); print(ph[["phase","tx","vol","buy_sol","sell_sol","net_sol","unique_wallets","price_open","price_close"]].to_string(index=False))
    # 3j pre/post low
    low=p["low_time"]
    pre=df[(df.ts>=low-pd.Timedelta(hours=3))&(df.ts<=low)]
    post=df[(df.ts>low)&(df.ts<=low+pd.Timedelta(hours=3))]
    def pb(x): b=x.loc[x.side=='BUY','delta_sol'].sum(); return 100*b/x.delta_sol.abs().sum() if len(x) else 0
    print(f"  3j SEBELUM low: net {pre.delta_sol.sum():+.1f} buy% {pb(pre):.1f} tx {len(pre)} | 3j SESUDAH low: net {post.delta_sol.sum():+.1f} buy% {pb(post):.1f} tx {len(post)}")
    # 15min spring
    w=df[(df.ts>=low-pd.Timedelta(hours=1))&(df.ts<=low+pd.Timedelta(hours=2))].copy()
    w["b"]=w.ts.dt.floor("15min")
    print("  candle 15min sekitar low:")
    for m,s in w.groupby("b"):
        b=s.loc[s.side=="BUY","delta_sol"].sum(); ss=-s.loc[s.side=="SELL","delta_sol"].sum()
        print(f"    {m.strftime('%H:%M')} tx{len(s):4d} buy{b:7.1f} sell{ss:7.1f} net{b-ss:7.1f} buy%{100*b/(b+ss) if b+ss>0 else 0:5.1f} pmin{s.price.min():.8f}")
    # accumulators at low & retention
    lw=df[(df.ts>=low-pd.Timedelta(hours=3))&(df.ts<=low+pd.Timedelta(hours=3))]
    ww=wallet_net(lw); acc=ww[ww.net_sol>=0.5]
    after=df[df.ts>low+pd.Timedelta(hours=3)]
    asell=after[after.side=="SELL"].groupby("wallet")["delta_sol"].sum() if len(after) else pd.Series(dtype=float)
    if len(acc):
        sold=acc.index.map(lambda x:-asell.get(x,0.0)); held=((acc.net_sol-sold).clip(lower=0)/acc.net_sol*100)
        print(f"  akumulator di low (>=0.5): {len(acc)} wallet, total {acc.net_sol.sum():.1f} SOL, tdk jual {100*(sold==0).mean():.0f}%, retention {held.mean():.0f}%")
    tdf,_=tag_stats(df)
    print("  TAG net:"); print(tdf[["tag","tx","net_sol","vol_sol","wallets"]].head(12).to_string(index=False))
    print()

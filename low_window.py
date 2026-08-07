#!/usr/bin/env python3
"""Analisis mikro di sekitar lowest-low: spring/akumulasi & sinyal pre-pump."""
import pandas as pd, numpy as np
from analyze import parse_file, hour_stats, wallet_net, FILES

pd.set_option("display.width",220); pd.set_option("display.max_columns",30)
pd.set_option("display.float_format", lambda v: f"{v:,.3f}")

for name, path in FILES.items():
    df = parse_file(path)
    p = df.set_index("ts")["price"].dropna()
    low_time = p.idxmin()
    low_price = p.min()
    # window +/- 3 jam
    t0 = low_time - pd.Timedelta(hours=3)
    t1 = low_time + pd.Timedelta(hours=3)
    win = df[(df.ts>=t0)&(df.ts<=t1)].copy()
    print("="*100)
    print(f"{name.upper()}  LOW @ {low_time}  price {low_price:.8f}")
    print(f"window ±3j: {t0} -> {t1}  | {len(win)} tx")
    win["min"] = win.ts.dt.floor("15min")
    g = win.groupby("min")
    rows=[]
    for m,sub in g:
        pb = sub.loc[sub.side=="BUY","delta_sol"].sum()
        ps = -sub.loc[sub.side=="SELL","delta_sol"].sum()
        rows.append({
            "time":m.strftime("%H:%M"),
            "tx":len(sub),
            "buy":pb,"sell":ps,"net":pb-ps,
            "buy%":round(100*pb/(pb+ps),1) if pb+ps>0 else 0,
            "p_low":sub.price.min(),"p_close":sub.price.iloc[-1],
            "wallets":sub.wallet.nunique(),
        })
    print(pd.DataFrame(rows).to_string(index=False))
    print()
    # wallet yang akumulasi di window low (net buy >0.5 SOL), dan TIDAK jual di sisa hari
    t_after = low_time + pd.Timedelta(hours=3)
    winw = wallet_net(win)
    accum = winw[winw.net_sol>=0.5].copy()
    # apakah wallet2 ini jual di sesi setelah window?
    after = df[df.ts>t1]
    after_sell = after[after.side=="SELL"].groupby("wallet")["delta_sol"].sum()  # negative
    accum["sold_after"] = accum.index.map(lambda w: -after_sell.get(w,0.0))
    accum["held_pct"] = (accum.net_sol - accum.sold_after).clip(lower=0)/accum.net_sol*100
    accum = accum.sort_values("net_sol",ascending=False)
    print(f"  Akumulator di window LOW (net >= 0.5 SOL): {len(accum)} wallet, total net {accum.net_sol.sum():.2f} SOL")
    print(f"  Yang TIDAK jual sama sekali setelah window: {(accum.sold_after==0).sum()} wallet ({100*(accum.sold_after==0).mean():.0f}%)")
    print(f"  Rata-rata retention (net yg masih dipegang): {accum.held_pct.mean():.1f}%")
    print(accum.head(8)[["net_sol","buy_sol","sell_sol","tx","wallet_trades","sold_after","held_pct","tags"]].to_string())
    print()
    # big buys di 1 jam SETELAH low
    post = df[(df.ts>low_time)&(df.ts<=low_time+pd.Timedelta(hours=1))]
    bb = post[(post.side=="BUY")&(post.sol_amt>=0.5)]
    print(f"  1 jam SETELAH low: {len(post)} tx, big buy (>=0.5 SOL) {len(bb)} tx sebesar {bb.delta_sol.sum():.2f} SOL dari {bb.wallet.nunique()} wallet")
    # bandingkan rata2 ukuran buy vs sell sepanjang hari
    print(f"  Rata2 ukuran BUY  seluruh hari: {df.loc[df.side=='BUY','sol_amt'].mean():.3f} SOL")
    print(f"  Rata2 ukuran SELL seluruh hari: {df.loc[df.side=='SELL','sol_amt'].mean():.3f} SOL")
    print(f"  Median ukuran BUY: {df.loc[df.side=='BUY','sol_amt'].median():.3f} | SELL: {df.loc[df.side=='SELL','sol_amt'].median():.3f}")
    print()

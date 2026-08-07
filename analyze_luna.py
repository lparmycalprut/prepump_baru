#!/usr/bin/env python3
"""Analisis LUNA (live, TIDAK dimasukkan ke sampel pola berikutnya)."""
import pandas as pd, numpy as np
from analyze import parse_file, hour_stats, wallet_net, tag_stats, whale_stats, price_path, cvd_divergence, phase_detection

pd.set_option("display.width",220); pd.set_option("display.max_columns",30)
pd.set_option("display.float_format", lambda v: f"{v:,.4f}")

df = parse_file("LUNA.csv")

print("="*100)
print("LUNA  |", len(df), "TX |", df.wallet.nunique(), "wallet")
print(f"window: {df.ts.iloc[0]} -> {df.ts.iloc[-1]}")
p = price_path(df)
print(f"PRICE : open {p['open']:.8f} close {p['close']:.8f} low {p['low']:.8f} @ {p['low_time']} high {p['high']:.8f} @ {p['high_time']}")
print(f"        day change {p['change_pct']:+.1f}%  low->close {p['low_to_close_pct']:+.1f}%")
tot_buy = df.loc[df.side=="BUY","delta_sol"].sum()
tot_sell = -df.loc[df.side=="SELL","delta_sol"].sum()
tot_vol = tot_buy+tot_sell
cvd = df.cvd_sol.iloc[-1]
print(f"VOL   : {tot_vol:,.2f} SOL (buy {tot_buy:,.2f} / sell {tot_sell:,.2f}) net CVD {cvd:+,.2f} ({100*cvd/tot_vol:+.2f}% of vol)")
print(f"TX    : {len(df)} (buy {(df.side=='BUY').sum()} / sell {(df.side=='SELL').sum()})  buy_tx_pct {100*(df.side=='BUY').sum()/len(df):.1f}%")
wh = whale_stats(df)
print(f"WHALES >1 SOL: {wh['big_tx']} tx ({wh['big_tx_pct']:.1f}%) buy {wh['big_buy_sol']:,.1f} sell {wh['big_sell_sol']:,.1f} net {wh['big_net']:+,.1f} SOL dari {wh['big_wallets']} wallet")
d = cvd_divergence(df)
print(f"DIVERGENSI: low harga jam {d['price_low_hour']:02d}:00 (CVD={d['cvd_at_price_low']:+.2f}); CVD min jam {d['cvd_min_hour']:02d}:00 ({d['cvd_min_val']:+.2f}) gap {d['div_timing_hours']} jam")
print(f"Rata2 BUY {df.loc[df.side=='BUY','sol_amt'].mean():.3f} SOL | SELL {df.loc[df.side=='SELL','sol_amt'].mean():.3f} SOL")
print(f"Median BUY {df.loc[df.side=='BUY','sol_amt'].median():.3f} | SELL {df.loc[df.side=='SELL','sol_amt'].median():.3f}")
print()
print("-- FASE (kuartil TX) --")
ph = phase_detection(df)
print(ph[["phase","tx","vol","buy_sol","sell_sol","net_sol","unique_wallets","price_open","price_close"]].to_string(index=False))
print()
print("-- PER JAM --")
h = hour_stats(df)
print(h[["tx","vol","buy_sol","sell_sol","delta_sol","cvd_end","buy_pct","price_low","price_high","price_close"]].round(4).to_string())
print()
w = wallet_net(df)
print("-- TOP 12 AKUMULATOR --")
print(w.head(12)[["net_sol","buy_sol","sell_sol","tx","wallet_trades","profit","balance","tags"]].to_string())
print()
print("-- TOP 12 DISTRIBUTOR --")
print(w.tail(12)[["net_sol","buy_sol","sell_sol","tx","wallet_trades","profit","balance","tags"]].to_string())
print()
tdf, tcount = tag_stats(df)
print("-- TAG BREAKDOWN --")
print(tdf.to_string(index=False))
print()

# Window di sekitar low
low_time = p["low_time"]
t0 = low_time - pd.Timedelta(hours=3); t1 = low_time + pd.Timedelta(hours=3)
win = df[(df.ts>=t0)&(df.ts<=t1)].copy()
print(f"-- WINDOW ±3J SEKITAR LOW ({t0} -> {t1}, {len(win)} tx) --")
win["bin"] = win.ts.dt.floor("15min")
rows=[]
for m,sub in win.groupby("bin"):
    pb=sub.loc[sub.side=="BUY","delta_sol"].sum(); ps=-sub.loc[sub.side=="SELL","delta_sol"].sum()
    rows.append({"time":m.strftime("%H:%M"),"tx":len(sub),"buy":pb,"sell":ps,"net":pb-ps,
                 "buy%":round(100*pb/(pb+ps),1) if pb+ps>0 else 0,"p_low":sub.price.min(),"p_close":sub.price.iloc[-1],"wallets":sub.wallet.nunique()})
print(pd.DataFrame(rows).to_string(index=False))
print()
ww = wallet_net(win)
accum = ww[ww.net_sol>=0.5].copy()
after = df[df.ts>t1]
after_sell = after[after.side=="SELL"].groupby("wallet")["delta_sol"].sum()
accum["sold_after"] = accum.index.map(lambda x: -after_sell.get(x,0.0))
accum["held_pct"] = (accum.net_sol-accum.sold_after).clip(lower=0)/accum.net_sol*100
accum = accum.sort_values("net_sol",ascending=False)
print(f"Akumulator di low (net >=0.5 SOL): {len(accum)} wallet, total net {accum.net_sol.sum():.2f} SOL")
print(f"Tidak jual setelah window: {(accum.sold_after==0).sum()} ({100*(accum.sold_after==0).mean():.0f}%)  retention rata2 {accum.held_pct.mean():.1f}%")
print(accum.head(10)[["net_sol","buy_sol","sell_sol","tx","wallet_trades","sold_after","held_pct","tags"]].to_string())
print()
post = df[(df.ts>low_time)&(df.ts<=low_time+pd.Timedelta(hours=1))]
bb = post[(post.side=="BUY")&(post.sol_amt>=0.5)]
print(f"1 jam SETELAH low: {len(post)} tx, big buy >=0.5 SOL: {len(bb)} tx = {bb.delta_sol.sum():.2f} SOL dari {bb.wallet.nunique()} wallet")

# posisi terbaru: harga close vs pola, dan jam-jam terakhir
print()
print("-- 10 TRANSAKSI TERAKHIR --")
print(df.tail(10)[["ts","side","delta_sol","cvd_sol","sol_amt","price","wallet","tags"]].to_string(index=False))

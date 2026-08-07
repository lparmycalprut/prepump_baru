#!/usr/bin/env python3
"""Batch analisis semua CSV pre-pump (1 hari sebelum pump). TIDAK termasuk LUNA (live)."""
import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np, os, sys, json, io
# import analyze tanpa memicu print main-nya
_orig = sys.stdout
sys.stdout = io.StringIO()
try:
    from analyze import parse_file, hour_stats, wallet_net, tag_stats, whale_stats, price_path, cvd_divergence, phase_detection
finally:
    sys.stdout = _orig

# File sampel (semua "sehari sebelum pump")
FILES = {
    "testicle":  "testicle.csv",
    "punch 1":   "punch 1.csv",
    "punch 2":   "punch 2.csv",
    "grail":     "grail.csv",
    "bountywork":"bountywork.csv",
    "assface":   "assface.csv",
    "ansem 1":   "ansem 1.csv",
    "ansem 2":   "ansem 2.csv",
    "chance":    "chance.csv",
    "hoppy":     "hoppy.csv",   # hanya 16 jam, catat
}
# urutkan berdasarkan tanggal
ORDER = ["punch 1","punch 2","testicle","grail","bountywork","assface","ansem 1","ansem 2","chance","hoppy"]

def low_window_metrics(df, low_time):
    """Metrik mikro di sekitar low ±3 jam."""
    t0 = low_time - pd.Timedelta(hours=3); t1 = low_time + pd.Timedelta(hours=3)
    win = df[(df.ts>=t0)&(df.ts<=t1)].copy()
    if len(win)<5: return None
    win["bin"]=win.ts.dt.floor("15min")
    rows=[]
    for m,sub in win.groupby("bin"):
        pb=sub.loc[sub.side=="BUY","delta_sol"].sum()
        ps=-sub.loc[sub.side=="SELL","delta_sol"].sum()
        rows.append({"time":m,"buy":pb,"sell":ps,"net":pb-ps,
                     "buypct": 100*pb/(pb+ps) if pb+ps>0 else 0})
    w=pd.DataFrame(rows)
    # cari candle low: bin yang mengandung low_time
    low_bin = low_time.floor("15min")
    # candle net paling negatif di window = kapitulasi; candle sesudah low
    ww = w.set_index("time")
    # spring: 1-3 candle setelah bin low dengan buy%>55
    post = w[w.time>low_bin].head(4)
    spring = post[post.buypct>=55]
    # kapitulasi: candle paling negatif di pre-low (3 candle sebelum)
    pre = w[w.time<=low_bin].tail(5)
    capit = pre.loc[pre.net.idxmin()] if len(pre)>0 else None
    # akumulator & retention
    ww_wallets = wallet_net(win)
    accum = ww_wallets[ww_wallets.net_sol>=0.5]
    after = df[df.ts>t1]
    after_sell = after[after.side=="SELL"].groupby("wallet")["delta_sol"].sum() if len(after)>0 else pd.Series(dtype=float)
    if len(accum)>0:
        sold = accum.index.map(lambda x: -after_sell.get(x,0.0))
        held = ((accum.net_sol - sold).clip(lower=0)/accum.net_sol*100)
        n_accum=len(accum); accum_net=accum.net_sol.sum()
        hold_pct=(sold==0).mean()*100; retention=held.mean()
    else:
        n_accum=0; accum_net=0; hold_pct=0; retention=0
    # big buy 1 jam setelah low
    post1 = df[(df.ts>low_time)&(df.ts<=low_time+pd.Timedelta(hours=1))]
    bb = post1[(post1.side=="BUY")&(post1.sol_amt>=0.5)]
    return dict(
        cap_net=float(capit.net) if capit is not None else 0,
        cap_buypct=float(capit.buypct) if capit is not None else 0,
        n_spring=len(spring),
        spring_max_buy=float(spring.buypct.max()) if len(spring)>0 else 0,
        spring_net=float(spring.net.sum()) if len(spring)>0 else 0,
        n_accum=n_accum, accum_net=float(accum_net),
        hold_pct=float(hold_pct), retention=float(retention),
        bigbuy_after=len(bb), bigbuy_sol=float(bb.delta_sol.sum()),
        win_tx=len(win), win_vol=float(win.delta_sol.abs().sum()),
        win_net=float(win.delta_sol.sum()),
    )

rows=[]
detail={}
for name in ORDER:
    path=FILES[name]
    df=parse_file(path)
    p=price_path(df); wh=whale_stats(df); d=cvd_divergence(df); ph=phase_detection(df)
    tot=df.delta_sol.abs().sum()
    buy=df.loc[df.side=="BUY","delta_sol"].sum()
    sell=-df.loc[df.side=="SELL","delta_sol"].sum()
    cvd=df.cvd_sol.iloc[-1]; cvdmin=df.cvd_sol.min(); cvdmax=df.cvd_sol.max()
    tdf,_=tag_stats(df)
    # tag helpers
    tagmap=tdf.set_index("tag")["net_sol"].to_dict()
    tagvol=tdf.set_index("tag")["vol_sol"].to_dict()
    # window low
    lw=low_window_metrics(df, p["low_time"])
    # phase (kuartil) - delta per phase
    ph_delta=ph.set_index("phase")["net_sol"].to_dict()
    # jam-jam terakhir (3 jam) net
    last3 = df[df.ts>=df.ts.iloc[-1]-pd.Timedelta(hours=3)].delta_sol.sum()
    # 3 jam setelah low
    after_low = df[(df.ts>p["low_time"])&(df.ts<=p["low_time"]+pd.Timedelta(hours=3))]
    after_low_net = after_low.delta_sol.sum()
    after_low_buypct = 100*after_low.loc[after_low.side=="BUY","delta_sol"].sum()/after_low.delta_sol.abs().sum() if len(after_low)>0 else 0
    r=dict(
        token=name, date=df.ts.iloc[0].strftime("%Y-%m-%d"),
        hours=round((df.ts.iloc[-1]-df.ts.iloc[0]).total_seconds()/3600,1),
        tx=len(df), wallets=df.wallet.nunique(),
        vol=round(tot,1), buy=round(buy,1), sell=round(sell,1),
        cvd=round(cvd,2), cvd_pct=round(100*cvd/tot,2),
        cvdmin_pct=round(100*cvdmin/tot,2),
        buy_tx_pct=round(100*(df.side=="BUY").sum()/len(df),1),
        avg_buy=round(df.loc[df.side=="BUY","sol_amt"].mean(),3),
        avg_sell=round(df.loc[df.side=="SELL","sol_amt"].mean(),3),
        med_buy=round(df.loc[df.side=="BUY","sol_amt"].median(),3),
        med_sell=round(df.loc[df.side=="SELL","sol_amt"].median(),3),
        whale_pct=round(wh["big_tx_pct"],1), whale_net=round(wh["big_net"],1),
        open=round(p["open"],8), close=round(p["close"],8), low=round(p["low"],8), high=round(p["high"],8),
        low_t=p["low_time"].strftime("%H:%M"),
        chg=round(p["change_pct"],1), low2close=round(p["low_to_close_pct"],1),
        cvdmin_hr=d["cvd_min_hour"], div_gap=d["div_timing_hours"],
        # tag net
        tag_bundler=round(tagmap.get("bundler",0),1),
        tag_paper=round(tagmap.get("paper_hands",0),1),
        tag_fresh=round(tagmap.get("fresh_wallet",0),1),
        tag_bluechip=round(tagmap.get("bluechip_owner",0),1),
        tag_topholder=round(tagmap.get("top_holder",0),1),
        tag_bundler_pct=round(100*tagvol.get("bundler",0)/tot,1),
        # phase
        Q1=round(ph_delta.get("Q1",0),1),Q2=round(ph_delta.get("Q2",0),1),
        Q3=round(ph_delta.get("Q3",0),1),Q4=round(ph_delta.get("Q4",0),1),
        last3_net=round(last3,2),
        after_low_net=round(after_low_net,2),
        after_low_buypct=round(after_low_buypct,1),
    )
    if lw:
        r.update({k: (round(v,2) if isinstance(v,float) else v) for k,v in lw.items()})
    rows.append(r)
    detail[name]=df

comp=pd.DataFrame(rows)
pd.set_option("display.width",300); pd.set_option("display.max_columns",60)
pd.set_option("display.float_format", lambda v: f"{v:,.3f}")

# === TABEL 1: ringkasan ===
cols1=["token","date","hours","tx","wallets","vol","cvd","cvd_pct","cvdmin_pct","buy_tx_pct","whale_pct","whale_net","low_t","chg","low2close"]
print("="*160); print("TABEL 1: RINGKASAN SEMUA TOKEN PRE-PUMP"); print("="*160)
print(comp[cols1].to_string(index=False))

# === TABEL 2: ukuran & fase ===
print("\n"+"="*160); print("TABEL 2: UKURAN ORDER & FASE (Q1=awal hari ... Q4=jelang pump)"); print("="*160)
cols2=["token","avg_buy","avg_sell","med_buy","med_sell","Q1","Q2","Q3","Q4","last3_net","after_low_net","after_low_buypct"]
print(comp[cols2].to_string(index=False))

# === TABEL 3: tag & akumulator ===
print("\n"+"="*160); print("TABEL 3: TAG WALLET (net SOL) & STRUKTUR DI LOW"); print("="*160)
cols3=["token","tag_bundler","tag_paper","tag_fresh","tag_bluechip","tag_topholder","tag_bundler_pct",
       "cap_net","n_spring","spring_max_buy","n_accum","accum_net","hold_pct","retention","bigbuy_after"]
print(comp[cols3].to_string(index=False))

# === Statistik agregat ===
print("\n"+"="*160); print("STATISTIK AGREGAT (untuk threshold sinyal)"); print("="*160)
num_cols=["cvd_pct","cvdmin_pct","buy_tx_pct","whale_pct","whale_net","avg_buy","avg_sell","low2close",
         "after_low_buypct","spring_max_buy","hold_pct","retention","tag_bundler_pct"]
desc=comp[num_cols].agg(["min","median","mean","max"]).T
print(desc.round(2).to_string())

# Cek setiap sinyal: berapa dari 10 token yang memenuhi
print("\n"+"="*160); print("BERAPA TOKEN YANG MEMENUHI SETIAP SINYAL (dari 10)"); print("="*160)
checks = {
    "CVD full-day |cvd_pct|<10%": (comp.cvd_pct.abs()<10),
    "CVD full-day |cvd_pct|<5% (ideal)": (comp.cvd_pct.abs()<5),
    "CVD terendah |cvdmin_pct|<10%": (comp.cvdmin_pct.abs()<10),
    "Buy TX >=52%": (comp.buy_tx_pct>=52),
    "Rata2 SELL > BUY (big sell eaten)": (comp.avg_sell>comp.avg_buy),
    "Whale net negatif (whale yg dibuang)": (comp.whale_net<0),
    "Spring: candle sesudah low buy%>=55%": (comp.spring_max_buy>=55),
    "Spring: >=2 candle post-low buy%>=55%": (comp.n_spring>=2),
    "Retention akumulator >=40%": (comp.retention>=40),
    "Holders di low >=50% tdk jual": (comp.hold_pct>=50),
    "3 jam setelah low net BUY": (comp.after_low_net>0),
    "3 jam setelah low buy%>52%": (comp.after_low_buypct>52),
    "Bundler net BUY >0": (comp.tag_bundler>0),
    "Bluechip net BUY >0": (comp.tag_bluechip>0),
    "Top_holder net BUY >0": (comp.tag_topholder>0),
    "Fresh_wallet net BUY >0": (comp.tag_fresh>0),
    "Sudah mark-up low->close >5%": (comp.low2close>5),
    "CVD divergence: cvdmin sebelum low (gap>=0)": (comp.div_gap>=0),
}
sig_rows=[]
for label,mask in checks.items():
    sig_rows.append({"sinyal":label,"lolos":int(mask.sum()),"dari":len(comp),"persen":f"{100*mask.sum()/len(comp):.0f}%"})
print(pd.DataFrame(sig_rows).to_string(index=False))

# === Phase pattern: kapan CVD negatif (markdown) lalu positif (markup)? ===
print("\n"+"="*160); print("POLA FASE: Q1/Q2 negatif (markdown) lalu Q3/Q4 positif (akumulasi/markup)"); print("="*160)
print(comp[["token","Q1","Q2","Q3","Q4","low2close"]].to_string(index=False))

# simpan hasil
comp.to_csv("/tmp/summary_all.csv", index=False)
print("\n[tersimpan di /tmp/summary_all.csv]")

#!/usr/bin/env python3
"""Analisis pola pre-pump (hari lowest-low) dari 3 token pump.fun."""
import pandas as pd
import numpy as np
import re
from collections import Counter

FILES = {
    "testicle": "testicle.csv",
    "assface": "assface.csv",
    "hoppy": "hoppy.csv",
}

def parse_file(path):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    # baris detail transaksi = baris setelah header kolom
    header_idx = None
    for i, ln in enumerate(lines):
        if ln.startswith("No,Timestamp"):
            header_idx = i
            break
    assert header_idx is not None, path
    from io import StringIO
    csv_text = "".join(lines[header_idx:])
    df = pd.read_csv(StringIO(csv_text))
    # bersih nama kolom
    df.columns = [c.strip() for c in df.columns]
    df["ts"] = pd.to_datetime(df["Timestamp (UTC)"], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce", utc=True)
    df = df.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)
    df["side"] = df["Arah (BUY/SELL)"].str.strip().str.upper()
    df["delta_sol"] = pd.to_numeric(df["Delta SOL (+/-)"], errors="coerce").fillna(0)
    df["delta_usd"] = pd.to_numeric(df["Delta USD (+/-)"], errors="coerce").fillna(0)
    df["sol_amt"] = pd.to_numeric(df["SOL Amount"], errors="coerce").fillna(0)
    df["token_amt"] = pd.to_numeric(df["Token Amount"], errors="coerce").fillna(0)
    df["usd_val"] = pd.to_numeric(df["USD Value"], errors="coerce").fillna(0)
    df["price"] = pd.to_numeric(df["Price USD"], errors="coerce")
    df["wallet"] = df["Wallet Address"].astype(str).str.strip()
    df["tags"] = df["Tags (Bundler/Holder/Bot)"].fillna("").astype(str)
    df["profit"] = pd.to_numeric(df["Realized Profit USD"], errors="coerce").fillna(0)
    df["balance"] = pd.to_numeric(df["Current Balance"], errors="coerce").fillna(0)
    df["wallet_trades"] = pd.to_numeric(df["Total Trades Wallet"], errors="coerce").fillna(0)
    df["hour"] = df["ts"].dt.hour
    # CVD recomputed (sama dgn kolom, tapi pastikan urutan)
    df["cvd_sol"] = df["delta_sol"].cumsum()
    return df

def hour_stats(df):
    g = df.groupby("hour")
    out = pd.DataFrame({
        "tx": g.size(),
        "buy_sol": g.apply(lambda x: x.loc[x.side=="BUY","delta_sol"].sum()),
        "sell_sol": g.apply(lambda x: -x.loc[x.side=="SELL","delta_sol"].sum()),
        "delta_sol": g["delta_sol"].sum(),
        "price_open": g["price"].first(),
        "price_close": g["price"].last(),
        "price_low": g["price"].min(),
        "price_high": g["price"].max(),
    })
    out["cvd_end"] = out["delta_sol"].cumsum()
    out["buy_pct"] = 100*out.buy_sol/(out.buy_sol+out.sell_sol)
    out["vol"] = out.buy_sol+out.sell_sol
    return out

def wallet_net(df):
    g = df.groupby("wallet")
    w = pd.DataFrame({
        "net_sol": g["delta_sol"].sum(),
        "buy_sol": g.apply(lambda x: x.loc[x.side=="BUY","delta_sol"].sum()),
        "sell_sol": g.apply(lambda x: -x.loc[x.side=="SELL","delta_sol"].sum()),
        "tx": g.size(),
        "tags": g["tags"].first(),
        "profit": g["profit"].first(),
        "balance": g["balance"].first(),
        "wallet_trades": g["wallet_trades"].first(),
        "first_ts": g["ts"].first(),
        "last_ts": g["ts"].last(),
    })
    return w.sort_values("net_sol", ascending=False)

def tag_stats(df):
    rows = []
    tags_all = []
    for t in df["tags"]:
        for x in str(t).split(";"):
            x=x.strip()
            if x: tags_all.append(x)
    tag_counts = Counter(tags_all)
    for tag in tag_counts:
        m = df["tags"].str.contains(re.escape(tag), case=False, na=False)
        sub = df[m]
        rows.append({
            "tag": tag,
            "tx": len(sub),
            "tx_pct": 100*len(sub)/len(df),
            "buy_sol": sub.loc[sub.side=="BUY","delta_sol"].sum(),
            "sell_sol": -sub.loc[sub.side=="SELL","delta_sol"].sum(),
            "net_sol": sub.delta_sol.sum(),
            "vol_sol": sub.delta_sol.abs().sum(),
            "wallets": sub.wallet.nunique(),
        })
    return pd.DataFrame(rows).sort_values("vol_sol", ascending=False), tag_counts

def whale_stats(df, top_n=10):
    """Whale buy/sell: transaksi >= 1 SOL."""
    big = df[df.sol_amt >= 1.0]
    return {
        "big_tx": len(big),
        "big_tx_pct": 100*len(big)/len(df),
        "big_buy_sol": big.loc[big.side=="BUY","delta_sol"].sum(),
        "big_sell_sol": -big.loc[big.side=="SELL","delta_sol"].sum(),
        "big_net": big.delta_sol.sum(),
        "big_wallets": big.wallet.nunique(),
    }

def price_path(df):
    p = df.set_index("ts")["price"].dropna()
    return {
        "open": p.iloc[0],
        "close": p.iloc[-1],
        "high": p.max(),
        "low": p.min(),
        "low_time": p.idxmin(),
        "high_time": p.idxmax(),
        "change_pct": 100*(p.iloc[-1]/p.iloc[0]-1),
        "low_to_close_pct": 100*(p.iloc[-1]/p.min()-1),
    }

def cvd_divergence(df):
    """Deteksi CVD vs price: di hourly mana price bikin low baru tapi CVD lebih tinggi (bullish div)."""
    h = hour_stats(df)
    price_low_hour = h["price_low"].idxmin()
    # CVD minimum sepanjang hari
    cvd_min_hour = h["cvd_end"].idxmin()
    cvd_min_val = h["cvd_end"].min()
    # cvd pada jam low harga
    cvd_at_price_low = h.loc[price_low_hour,"cvd_end"]
    return {
        "price_low_hour": price_low_hour,
        "cvd_at_price_low": cvd_at_price_low,
        "cvd_min_hour": cvd_min_hour,
        "cvd_min_val": cvd_min_val,
        "div_timing_hours": int(price_low_hour) - int(cvd_min_hour),
    }

def phase_detection(df):
    """Bagi hari jadi 4 fase (kuartil waktu, mirror laporan)."""
    q = [df.iloc[idx] for idx in np.array_split(np.arange(len(df)), 4)]
    rows = []
    for i, sub in enumerate(q, 1):
        rows.append({
            "phase": f"Q{i}",
            "start": sub.ts.iloc[0],
            "end": sub.ts.iloc[-1],
            "tx": len(sub),
            "buy_sol": sub.loc[sub.side=="BUY","delta_sol"].sum(),
            "sell_sol": -sub.loc[sub.side=="SELL","delta_sol"].sum(),
            "net_sol": sub.delta_sol.sum(),
            "vol": sub.delta_sol.abs().sum(),
            "price_open": sub.price.iloc[0],
            "price_close": sub.price.iloc[-1],
            "unique_wallets": sub.wallet.nunique(),
        })
    return pd.DataFrame(rows)

# ----------- main -----------
results = {}
for name, path in FILES.items():
    df = parse_file(path)
    results[name] = {
        "df": df,
        "hour": hour_stats(df),
        "wallets": wallet_net(df),
        "tags_df": tag_stats(df)[0],
        "tags_count": tag_stats(df)[1],
        "whales": whale_stats(df),
        "price": price_path(df),
        "div": cvd_divergence(df),
        "phase": phase_detection(df),
    }

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)
pd.set_option("display.float_format", lambda v: f"{v:,.4f}")

for name, r in results.items():
    df = r["df"]
    print("="*100)
    print(f"TOKEN: {name.upper()}  | mint di header | {len(df)} TX | {df.wallet.nunique()} wallet")
    print(f"  window : {df.ts.iloc[0]} -> {df.ts.iloc[-1]}")
    p = r["price"]
    print(f"  PRICE  : open {p['open']:.8f}  close {p['close']:.8f}  low {p['low']:.8f} @ {p['low_time']}  high {p['high']:.8f}")
    print(f"           day change {p['change_pct']:+.1f}%   low->close {p['low_to_close_pct']:+.1f}%")
    tot_buy = df.loc[df.side=="BUY","delta_sol"].sum()
    tot_sell = -df.loc[df.side=="SELL","delta_sol"].sum()
    tot_vol = tot_buy+tot_sell
    cvd_final = df.cvd_sol.iloc[-1]
    print(f"  VOL    : {tot_vol:,.2f} SOL  (buy {tot_buy:,.2f} / sell {tot_sell:,.2f})  net CVD {cvd_final:+,.2f} SOL ({100*cvd_final/tot_vol:+.2f}% of vol)")
    print(f"  TX     : {len(df)} (buy {(df.side=='BUY').sum()} / sell {(df.side=='SELL').sum()})")
    wh = r["whales"]
    print(f"  WHALES (>1 SOL/tx): {wh['big_tx']} tx ({wh['big_tx_pct']:.1f}%)  buy {wh['big_buy_sol']:,.1f} / sell {wh['big_sell_sol']:,.1f} / net {wh['big_net']:+,.1f} SOL dari {wh['big_wallets']} wallet")
    d = r["div"]
    print(f"  DIVERGENSI: low harga jam {d['price_low_hour']:02d}:00 (CVD={d['cvd_at_price_low']:+.1f}); CVD terendah jam {d['cvd_min_hour']:02d}:00 ({d['cvd_min_val']:+.1f}) -> selisih {d['div_timing_hours']} jam")
    print()
    print("  -- FASE (kuartil waktu) --")
    print(r["phase"][["phase","tx","vol","buy_sol","sell_sol","net_sol","unique_wallets","price_open","price_close"]].to_string(index=False))
    print()
    print("  -- STAT PER JAM --")
    print(r["hour"][["tx","vol","buy_sol","sell_sol","delta_sol","cvd_end","buy_pct","price_low","price_close"]].round(4).to_string())
    print()
    print("  -- TOP 10 AKUMULATOR (net BUY) --")
    print(r["wallets"].head(10)[["net_sol","buy_sol","sell_sol","tx","wallet_trades","profit","balance","tags"]].to_string())
    print()
    print("  -- TOP 10 DISTRIBUTOR (net SELL) --")
    print(r["wallets"].tail(10)[["net_sol","buy_sol","sell_sol","tx","wallet_trades","profit","balance","tags"]].to_string())
    print()
    print("  -- TAG BREAKDOWN --")
    print(r["tags_df"].to_string(index=False))
    print()

# ---------- ringkasan side-by-side ----------
print("="*100)
print("RINGKASAN KOMPARASI")
print("="*100)
rows=[]
for name,r in results.items():
    df=r["df"]; p=r["price"]; wh=r["whales"]; d=r["div"]
    tot_buy=df.loc[df.side=="BUY","delta_sol"].sum()
    tot_sell=-df.loc[df.side=="SELL","delta_sol"].sum()
    tot_vol=tot_buy+tot_sell
    cvd=df.cvd_sol.iloc[-1]
    rows.append({
        "token":name,
        "tx":len(df),
        "wallets":df.wallet.nunique(),
        "vol_sol":round(tot_vol,2),
        "buy_sol":round(tot_buy,2),
        "sell_sol":round(tot_sell,2),
        "cvd_sol":round(cvd,2),
        "cvd_pct_vol":round(100*cvd/tot_vol,2),
        "buy_tx_pct":round(100*(df.side=='BUY').sum()/len(df),1),
        "whale_tx_pct":round(wh["big_tx_pct"],1),
        "whale_net":round(wh["big_net"],1),
        "price_low_hr":d["price_low_hour"],
        "cvd_min_hr":d["cvd_min_hour"],
        "div_gap_hr":d["div_timing_hours"],
        "day_chg_pct":round(p["change_pct"],1),
        "low_to_close_pct":round(p["low_to_close_pct"],1),
    })
comp = pd.DataFrame(rows)
print(comp.to_string(index=False))

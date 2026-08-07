import warnings; warnings.filterwarnings("ignore")
import io,sys
_orig=sys.stdout; sys.stdout=io.StringIO()
from analyze import parse_file, wallet_net, tag_stats, whale_stats, price_path
sys.stdout=_orig
import pandas as pd, numpy as np
pd.set_option("display.width",220); pd.set_option("display.float_format",lambda v:f"{v:,.3f}")

for f in ["luna_dump.csv","luna_after_dump.csv","luna3.csv"]:
    df=parse_file(f); p=price_path(df); wh=whale_stats(df)
    tot=df.delta_sol.abs().sum()
    low=p["low_time"]
    print("="*90); print(f,df.ts.iloc[0].date(),"| tx",len(df),"| wallets",df.wallet.nunique())
    print(f"  vol {tot:,.1f} buy {df.loc[df.side=='BUY','delta_sol'].sum():,.1f} sell {-df.loc[df.side=='SELL','delta_sol'].sum():,.1f} | CVD {df.cvd_sol.iloc[-1]:.2f} ({100*df.cvd_sol.iloc[-1]/tot:.2f}%)")
    print(f"  buy_tx% {100*(df.side=='BUY').sum()/len(df):.1f} | avgBuy {df.loc[df.side=='BUY','sol_amt'].mean():.3f} avgSell {df.loc[df.side=='SELL','sol_amt'].mean():.3f} | whale net {wh['big_net']:.1f}")
    print(f"  price open {p['open']:.8f} high {p['high']:.8f}@{p['high_time'].strftime('%H:%M')} low {p['low']:.8f}@{low.strftime('%H:%M')} close {p['close']:.8f}")
    print(f"  chg {p['change_pct']:+.1f}% low->close {p['low_to_close_pct']:+.1f}%")

import sys, os
sys.stdout = open(os.devnull,'w')
from analyze import parse_file
sys.stdout = sys.__stdout__
import pandas as pd, numpy as np

files = {'testicle':'testicle.csv','assface':'assface.csv','hoppy':'hoppy.csv','luna':'LUNA.csv'}
rows=[]
for name,path in files.items():
    df=parse_file(path)
    tot=df.delta_sol.abs().sum()
    cvd=df.cvd_sol
    final=cvd.iloc[-1]
    cvd_min=cvd.min(); cvd_max=cvd.max()
    p=df.set_index('ts')['price']
    low_t=p.idxmin()
    idx_low=df.index[df.ts<=low_t][-1]
    cvd_at_low=df.loc[idx_low,'cvd_sol']
    # window penurunan: dari swing high terakhir sebelum low
    pre=df.iloc[:idx_low+1]
    high_idx=pre['price'].idxmax()
    cvd_at_high=df.loc[high_idx,'cvd_sol']
    drop_cvd = cvd_at_low - cvd_at_high
    win = df.iloc[high_idx:idx_low+1]
    win_vol = win.delta_sol.abs().sum()
    # juga hitung max drawdown CVD dari cvd_max ke cvd_min sepanjang hari
    rows.append({
        'token':name,
        'total_vol_SOL':round(tot,1),
        'final_CVD':round(final,2),
        'CVD_terendah':round(cvd_min,2),
        'CVD_pada_harga_low':round(cvd_at_low,2),
        '|final|/vol%':round(100*abs(final)/tot,2),
        '|CVD_min|/vol%':round(100*abs(cvd_min)/tot,2),
        'CVD@low/vol%':round(100*cvd_at_low/tot,2),
        'penurunan_harga%':round(100*(df.loc[high_idx,'price']/p.min()-1),1),
        'CVD_drop_saat_turun':round(drop_cvd,2),
        'CVD_drop%_vs_vol_window':round(100*abs(drop_cvd)/win_vol,2) if win_vol else 0,
    })
df_out=pd.DataFrame(rows)
print(df_out.to_string(index=False))

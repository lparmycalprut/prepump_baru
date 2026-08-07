# Analisis Pola Pre-Pump (Hari Lowest-Low)

Data: 3 file CSV GMGN — `testicle.csv`, `assface.csv`, `hoppy.csv`.
Setiap file merekam transaksi kronologis 1 hari di sekitar **lowest-low** sebelum pump, lengkap dengan CVD, volume, wallet, dan tag.
Semua angka di bawah dihitung ulang dari transaksi mentah (bukan cuma rekap header) memakai `analyze.py` dan `low_window.py`.

---

## 1. Ringkasan Per Token

| Metrik | TESTICLE | ASSFACE | HOPPY |
|---|--:|--:|--:|
| Tanggal (UTC) | 2025-12-25 | 2026-04-21 | 2026-07-16 |
| Window rekaman | 00:00–23:47 | 00:00–22:38 | 00:01–16:25 |
| Total TX | 13.268 | 4.306 | 390 |
| Unique wallet | 1.624 | 886 | 171 |
| Total Volume (SOL) | 8.875,14 | 2.541,40 | 228,51 |
| Buy (SOL) | 4.473,75 | 1.256,90 | 106,24 |
| Sell (SOL) | 4.401,39 | 1.284,50 | 122,27 |
| **Net CVD (SOL)** | **+72,36** | **−27,60** | **−16,99** |
| **CVD / Total Volume** | **+0,82%** | **−1,09%** | **−7,43%** |
| Buy TX % | 52,4% | 52,5% | 53,8% |
| Rata2 ukuran BUY (SOL) | 0,643 | 0,556 | 0,506 |
| Rata2 ukuran SELL (SOL) | 0,697 | 0,628 | 0,691 |
| Whale >1 SOL/tx (TX %) | 16,8% | 13,3% | 14,1% |
| **Whale net (SOL)** | **−216,2** | **−130,8** | **−31,9** |
| Low harga (UTC) | 08:56 | 20:22 | 11:30 |
| CVD minimum jam | 19:00 | 19:00 | 14:00 |
| Low → Close | **+119,7%** | **+13,1%** | **+58,8%** |
| Day change open→close | −0,9% | −68,5% | −35,4% |

> Skala volume sangat berbeda (228 SOL s/d 8.875 SOL), tapi **polanya identik secara rasio**.

---

## 2. Pola Yang Sama di Ketiga Token

### 2.1 CVD nyaris datar walau harga bikin low — ada "penyerap"
Net CVD cuma **−7,4% s/d +0,8% dari total volume**. Artinya di hari terjadinya lowest-low, penjualan besar-besaran **selalu dilawan oleh pembelian dengan ukuran yang hampir sebanding**. Kalau murni distribusi/panic sell tanpa akumulator, CVD akan jauh lebih negatif (puluhan persen dari volume).

### 2.2 Jumlah transaksi BUY selalu lebih banyak dari SELL (52–54%)
Tapi nominal SOL sisi SELL lebih besar. Ini jejak klasik **distribusi lemah vs akumulasi tersembunyi**:
- Banyak transaksi BUY berukuran kecil/menengah (akumulator bertahap).
- Sedikit transaksi SELL berukuran besar (weak hands / insider / sniper bot yang buang di low).

Konfirmasi: rata-rata dan median ukuran SELL **lebih besar** dari BUY di ketiga token (di atas).

### 2.3 Wallet "whale" (>1 SOL/tx) justru **net SELLER** di hari itu
| Token | Whale net |
|---|--:|
| Testicle | −216,2 SOL |
| Assface | −130,8 SOL |
| Hoppy | −31,9 SOL |

Jadi yang menekan harga ke low adalah transaksi-transaksi besar. Tapi harga tetap bertahan dan CVD nyaris seimbang → **ada kumpulan wallet kecil-menengah yang menyerap** semua dump besar itu. Inikah inti fase akumulasi.

### 2.4 "Spring" / capitulation di low, langsung diserap
Lihat tabel 15-menit di sekitar low (dari `low_window.py`):

**Testicle (low 08:56):**
- 08:00 net −7,91 SOL (buy% 43,4%) — tekanan jual puncak
- **08:45 net +21,42 SOL (buy% 59,2%) — langsung balik menyerap di candle low**
- 09:00 +6,59 (55%), 09:15 +10,17 (58,5%)

**Assface (low 20:22):**
- 19:00 net −6,09 (37,1%), 19:30 net −6,50 (40,9%) — jual menjelang low
- **20:30 net +9,49 SOL (buy% 61,5%) — serapan besar persis setelah low**
- 21:15 +5,41 (61,8%), 22:00 +2,40 (70,7%)

**Hoppy (low 11:30):**
- 11:00 net −2,10 (34,5%), 11:15 −2,97 (25,5%), **11:30 −4,59 (39,9%) — candle capitulation**
- **11:45 net +1,55 (59,1%), 12:00 +2,90 (63,9%), 13:30 +2,23 (74,3%)** — berturut-turut dibeli

Polanya: **satu candle 15-menit berisi sell besar (kapitulasi), lalu 1–4 candle berikutnya selalu net BUY dengan rasio buy 55–75%.** Inilah "spring" Wyckoff — penjual terakhir keluar, akumulator memborong.

### 2.5 Divergensi CVD vs harga
- **Assface**: harga low jam 20:00, tapi CVD terendah sudah jam 19:00 (−49,3 → −31,1). Harga bikin low baru tapi CVD **lebih tinggi** → divergensi bullish klasik.
- **Hoppy**: low 11:30, CVD min jam 14:00 (setelah harga sudah memantul) → pengocokan terakhir (shakeout) sebelum lanjut.
- **Testicle**: low 08:00 dengan CVD +72; CVD sepanjang hari tidak pernah jauh di bawah nol. Tiap harga turun, net flow tetap positif — akumulasi paling agresif.

### 2.6 Akumulator di low TIDAK menjual — "supply lock"
Setelah window ±3 jam di sekitar low, lacak apakah pembeli di low melepas lagi:

| Token | Wallet net-buy ≥0,5 SOL di low | Total net diambil | **Tidak jual setelahnya** | Rata2 retention |
|---|--:|--:|--:|--:|
| Testicle | 75 | +147,5 SOL | 17 wallet (23%) | 27,7% |
| Assface | 35 | +51,6 SOL | **35 wallet (100%)** | **100%** |
| Hoppy | 9 | +18,9 SOL | 4 wallet (44%) | 44,4% |
| Testicle (inti 100% hold) | H5d8..., DnfS..., AgmL... | +14,4 SOL | tidak jual sampai tutup hari | 100% |

Artinya: koin yang dibeli di low **nyangkut/ditahan**, tidak dilepas balik. Ini yang mengeringkan supply di lantai harga — syarat utama pump berikutnya. Assface paling jelas: **semua 35 akumulator di low hold 100%**.

Dalam 1 jam SETELAH low pun muncul big-buy terukur:
- Testicle: 72 big buy (≥0,5 SOL) = 96,9 SOL dari 43 wallet
- Assface: 46 big buy = 52,6 SOL dari 29 wallet
- Hoppy: 8 big buy = 11,7 SOL dari 8 wallet

---

## 3. Siapa Akumulator & Siapa Distributor?

### TESTICLE
- **Top akumulator:** `AgmLJBMDCq...` +148,96 SOL (tag `sandwich_bot; bundler`), `9KnRHUc...` +70,16 (sandwich bot/bundler, volume 986 SOL, market-maker dominan), `H5d8DM...` +54,11 (bundler, **tidak jual**).
- **Top distributor:** `51ktg8vY...` −58,97 (`rat_trader`, murni jual 27 tx), `EozzmVq...` −20,24 (`smart_degen`, high turnover), trojan/photon/axiom net seller.
- Tag: **bundler 57,6% TX net +226 SOL**, **fresh_wallet net +90 SOL** (akumulator ritel baru), sandwich_bot net +204. Sementara `gmgn` net −65, `trojan` −45, `rat_trader` −71.
- Bacaan: bot/bundler menyerap akumulasi; snipers & trader komunitas (gmgn/trojan/rat) yang dibuang di low.

### ASSFACE
- **Top akumulator:** `9r75WXE...` +12,17 (tag `paper_hands` — justru net buy), `5EPkHhz...` +9,80 (`top_holder; bundler`, masih hold 44 token), `8GxtiR...` +7,43 (fresh_wallet, akumulasi 29 tx), banyak `paper_hands` kecil.
- **Top distributor:** `75ZGm6...` −16,41 (`top_holder`, 1 tx dump), `4sB9i1...` −14,63 (`top_holder`), `D6XMjB...` −7,88 (`padre; top_holder`), `54Pz1e3...` −6,02 (sandwich/bundler, bluechip).
- Tag: **`paper_hands` net +216 SOL (384 buy vs 168 sell)** — ironis, justru kelompok ini yang mengakumulasi; **`top_holder` net −48 SOL** (holder lama distribusi di low); `padre` −21, `trojan` −15.
- Bacaan: holder lama/insider buang di dasar, tapi `paper_hands` & fresh wallet masuk menahan.

### HOPPY
- **Top akumulator:** `HZBmjtg...` +4,82 (`bluechip_owner`, 1 tx, hold), `DnApLhf...` +4,75 (fresh/top_holder, profit +1.243), `4T24RZ...` +2,78 (top_holder), `974ThxX...` +1,88 (fresh/top_holder, profit +5.678).
- **Top distributor:** `7ULAUNC...` −10,41 (1 tx), `GzSYnjh...` −7,31 (fresh; bundler), `4Y45ejz...` −4,62 (bluechip; top_holder), `28pryh8...` −5,02 (single dump).
- Tag: **`top_holder` net +18,5 SOL** (holder baru justru nambah), `paper_hands` +11,4, `fresh_wallet` +1,7, `bluechip_owner` +0,6. Sisi jual: `bundler` −7,8, `trojan` −1,1.
- Bacaan: skala kecil, tapi top_holder/bluechip & fresh wallet yang masuk di low tidak melepas.

### Benang merah karakter wallet
- **Yang menjual di low:** wallet bertag `top_holder` lama (assface), `rat_trader`, `gmgn/trojan/padre` (komunitas sniper), dan single-tx dumper (hoppy: 7ULA, 28pry; assface: 75ZGm6, 4sB9i1).
- **Yang membeli di low:** `fresh_wallet`, `paper_hands`, `top_holder` baru, `bluechip_owner`, dan `bundler` (yang di testicle/assface net positif). Wallet-wallet inilah yang menahan supply.

---

## 4. Struktur Fase Akumulasi (versi Wyckoff)

Semua tiga token menjalani fase yang sama, bisa dibagi 4 (dari kuartil TX + konfirmasi 15-menit):

### Fase A — Markdown / tekanan jual (awal hari)
- CVD bergerak negatif/netral, harga turun terus.
- Testicle Q1: 1.874 vol, net +66 (sudah ada penyerapan dini); Assface Q1 net −13, Q2 −25 (terbesar negatifnya); Hoppy Q1 −10,4, Q2 −15,2.
- Sell block besar muncul (assface: dump −6,39 SOL di menit-menit awal; testicle: sell block ratusan SOL).

### Fase B — "Spring" / capitulation (lowest-low)
- Muncul candle cluster dengan sell besar yang menembus support (testicle 08:00–08:45; assface 19:00–20:00; hoppy 11:00–11:30).
- **Persis di/atau setelah low, 15-min langsung net BUY 55–75%** — akumulator mengangkat semua jual panik.
- Divergensi CVD mulai kelihatan (CVD sudah tidak bikin low baru).

### Fase C — Akumulasi & pengeringan supply
- Setelah low, buy count tetap > sell count, ukuran sell yang muncul lebih kecil (tidak ada lagi dump besar).
- Banyak wallet net-buy di low **hold 100%** (assface paling murni).
- Harga membentuk higher-low pertama (testicle sesudah 09:00; assface sesudah 20:30; hoppy sesudah 11:45).
- CVD bergerak naik/datar membanjiri tiap jual kecil.

### Fase D — Mark-up awal (sore/penutupan hari)
- Testicle Q4 net +44,9 SOL, harga naik dari 0,0001 ke 0,0002 (low→close **+120%**) — pump-nya memang mulai sore hari itu (puncak intraday 0,00053 di jam 18:00).
- Assface Q4 net −9,9 tapi harga sudah stabil dari 0,00003178 ke 0,00003595 (**+13%**), lantai mengeras.
- Hoppy Q4 net +9,3, harga dari 0,00001114 ke 0,00001769 (**+59%**) sampai rekaman berakhir 16:25.
- Inilah pangkal pump yang berlanjut ke hari berikutnya.

---

## 5. Kenapa Besoknya Bisa Pump?

Dirangkai dari bukti di atas:

1. **Supply di lantai terserap habis.** CVD yang nyaris 0% di tengah volume besar menunjukkan keseimbangan baru: setiap jual ada pembeli. Setelah capitulation, penjual besar kehabisan stok (whale net negatif tapi tidak bisa menekan harga lebih rendah lagi).
2. **Supply terkunci (locked supply).** Mayoritas koin yang dibeli di low dihold (assface 100%, hoppy 44%, testicle ada inti 100%-holders). Tidak ada yang mau jual rugi di harga itu.
3. **Harga gagal membuat low baru walaupun ada jual.** Divergensi CVD-harga (assface & testicle) = tekanan jual makin lemah.
4. **Akun-akun "smart" ikut menyerap.** `bluechip_owner`, `top_holder` baru, `fresh_wallet` besar, dan `bundler` net long di low. Tag ini (khususnya bluechip/top_holder baru di hoppy & assface) sering jadi sinyal early money.
5. **Rasio BUY/SELL by count selalu >52%** sepanjang hari — basis pemegang ritel yang lebih luas ikut terakumulasi, bukan cuma satu whale.
6. **Setelah low, big-buy berdatangan dalam 1 jam pertama** (testicle 97 SOL, assface 53 SOL, hoppy 12 SOL) — pemain terukur konfirmasi entry.
7. **Mark-up sudah dimulai sebelum tutup hari** (+13% s/d +120% dari low). Tren harian dari turun → datar/naik memberi momentum untuk kelanjutan pump keesokan harinya.

---

## 6. Checklist Cepat "Bakal Pump" (pola yang bisa dipakai filter)

Dari 3 sampel ini, sinyal yang **konsisten muncul** di hari lowest-low:

- [x] CVD harian |CVD/Vol| < ~7% (dekat nol) padahal harga bikin low besar — ada penyerap.
- [x] Buy TX > Sell TX (≥52%) tapi rata2 ukuran SELL > BUY (banyak small buy makan big sell).
- [x] Whale (>1 SOL) net negatif (mereka yang dibuang), tapi harga tetap bertahan.
- [x] Di candle 15-menit low, rasio buy melonjak ke 55–75% dan net CVD positif.
- [x] CVD tidak bikin low baru saat harga bikin low baru (bullish divergence).
- [x] Big-buy (≥0,5 SOL) muncul bertubi-tubi dalam 1 jam setelah low.
- [x] Akumulator di low mayoritas hold (≥40% retention; assface 100%).
- [x] Tag positif di pembeli low: `bluechip_owner`, `top_holder` baru, `fresh_wallet` besar, `bundler` net buy.
- [x] Tag negatif di penjual: `rat_trader`, `gmgn/trojan/padre` sniper, `top_holder` lama single-tx dump.
- [x] Sudah ada pemantulan +10% s/d +120% dari low menuju penutupan hari.

---

## 7. Tambahan: Fase akumulasi bisa 2–3 hari (studi kasus LUNA)

Analisis awal (3 token) dan 10 token berikutnya mayoritas menunjukkan pola
"spring dan pump di hari yang sama" (tipe cepat). Tapi urutan 3 hari LUNA
(`luna_dump.csv` 1 Agu, `luna_after_dump.csv` 2 Agu, `luna3.csv` 3 Agu)
membuktikan ada **tipe lambat** yang HARUS diperhitungkan — filter 1-hari
saja bisa salah menolak di H-1:

| Hari | Harga | CVD | Buy TX | Vol | Baca |
|---|--:|--:|--:|--:|---|
| 1 Agu (dump) | open 0,000076 → low 0,0000217 (−67%), close +16,6% | −3,58% | 44,7% | 1.233 SOL | Markdown + spring 20:13; 17 akumulator 31 SOL, **100% hold** |
| 2 Agu (H-1) | open 0,000025, range 0,000023–0,000040, close −0,4% | +0,40% | **49,9%** | **338 SOL (−73%)** | Higher-low 23:19, **volume kering**, supply habis (fase tes/LPS) |
| 3 Agu (pump) | open 0,0000247 → high 0,0000691 (**+180%**) di 00:19, close +37% | +2,10% | 53,1% | 1.360 SOL | Mark-up: 564 tx / +34,8 SOL di 1 jam pertama |

Pelajaran kunci:
1. **Jangan analisa 1 hari saja** — di H-1 tipe lambat, filter yang tadinya
   "wajib" (buy TX ≥52%, avg SELL > avg BUY, whale net negatif) justru TIDAK
   muncul (LUNA Aug2: 49,9%; buy ≈ sell; whale net +4).
2. **Volume kering di H-1 adalah sinyal BULLISH**, bukan kelemahan:
   vol turun ≥50% dari hari dump + higher-low + CVD datar = supply habis.
3. **Retention lintas hari lebih penting dari retensi 1 hari:** 59% akumulator
   Aug1 masih hold sampai pump Aug3.
4. Pump bisa picu **tepat di awal hari baru** (00:02 UTC) dengan lonjakan
   tx/CVD — multi-timeframe 30m/1h akan menangkapnya, tapi detektor harus
   punya STATE 2–3 hari, bukan snapshot.
5. Label "kontrol non-pump" yang sempat saya pasang ke Aug1/Aug2 **salah** —
   keduanya bagian dari fase akumulasi. Sampel non-pump asli belum ada.

### Filter yang direvisi
- **Tetap andal di kedua tipe:** |CVD harian| <10%; spring + retention;
  higher-low; volume kering di hari tes.
- **Hanya WAJIB di tipe cepat (hari spring=pump):** buy TX ≥52%; avg SELL >
  avg BUY; whale net negatif besar. Jangan hard-fail untuk H-1 tipe lambat.
- **Tambahan untuk multi-hari:** lacak (a) spring di hari sebelumnya dengan
  retention ≥50%, (b) H-1 higher-low + vol kering ≥50%, (c) CVD H-1 tetap
  datar/positif, (d) lonjakan tx/CVD awal hari-H.

## 8. Catatan / Keterbatasan

- `testicle` low 25 Des jam 08:56 dan pump intraday ke 0,00053 sudah terjadi sore hari itu (bukan "besok"); tetap merefleksikan pola akumulasi yang sama.
- `hoppy` window rekaman hanya sampai 16:25 (16 jam), jadi fase penutupan lebih pendek.
- Sebagian net buy besar di testicle berasal dari `sandwich_bot/bundler` yang juga high-frequency; angka net mereka nyata, tapi perlu diingat mereka bisa atur posisi dua arah. Wallet yang paling bisa diandalkan sebagai sinyal adalah yang **net buy di low dan tidak menjual sampai akhir window** (sudah difilter di Tabel 2.6).
- 3 sampel belum cukup untuk kesimpulan statistik, tapi pola Wyckoff-nya sangat konsisten.

---

*File pendukung: `analyze.py` (metrik lengkap per jam/fase/wallet/tag), `low_window.py` (mikro struktur di sekitar low).*

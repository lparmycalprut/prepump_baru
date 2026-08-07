# Panduan Implementasi Deteksi Pre-Pump (Handoff ke wallet-depth)

> **Dokumen ini untuk AI sesi baru di repo [`lparmycalprut/wallet-depth`](https://github.com/lparmycalprut/wallet-depth).**
> Pemilik ingin **MEMFOKUSKAN ULANG** proyek agar hanya mendeteksi pola akumulasi
> pre-pump yang sudah divalidasi dari data GMGN nyata (12 token / 13 hari-hari
> sampel), dan **MEMBUANG fungsi-fungsi lain** yang tidak relevan.

Baca dokumen ini bersama:
- `ANALISIS_POLA_PUMP.md` — analisa lengkap & angka per-token (repo prepump_baru).
- `prepump_detector.py` — modul yang **dipertahankan & dikalibrasi ulang**.
- `DISABLED.md` — daftar fitur yang sudah/akan dimatikan.

---

## 0. Ringkasan satu paragraf

Pola yang terbukti di 10 token pump + urutan 3 hari LUNA adalah: **sebelum
pump, harga bikin low baru (capitulation) lalu diserap — tapi flow-nya nyaris
seimbang (|CVD/vol| < 10%) karena whale membuang posisi dan banyak wallet
kecil-menengah menampung. Akumulasi bisa sehari (tipe cepat) atau 2–3 hari
(tipe lambat).** Yang paling membedakan pump vs non-pump BUKAN CVD absolut
atau retention (itu sama di non-pump), melainkan **LEBAR partisipasi**:
jumlah transaksi BUY ≥ 52% dan rasio **ukuran SELL > ukuran BUY**. Selain itu,
pump selalu ditandai dengan spring di candle 15-menit (buy% ≥ 55% sesudah
candle capitulation), volume follow-through yang tidak kering, dan pemantulan
≥15% dari low di hari yang sama.

---

## 1. Dataset yang dipakai (jangan tebak-tebakan)

Repo `prepump_baru` berisi CSV GMGN format **per-transaksi** (bukan agregat).
Semua kolom yang dibutuhkan detector ada: `timestamp, side, delta_sol, running
CVD, sol_amount, token_amount, price, wallet, tags, realized_profit, balance,
wallet_trades`.

Sampel terkonfirmasi pump (1 hari sebelum/saat pump):

| Token | File | Tipe |
|---|---|---|
| testicle | testicle.csv | cepat (pump sore hari yg sama) |
| punch 1 | punch 1.csv | cepat |
| punch 2 | punch 2.csv | cepat |
| grail | grail.csv | cepat |
| bountywork | bountywork.csv | cepat |
| assface | assface.csv | cepat |
| ansem 1 | ansem 1.csv | cepat |
| ansem 2 | ansem 2.csv | cepat (CVD −13,3% krn 1 dump tunggal) |
| chance | chance.csv | cepat |
| hoppy | hoppy.csv | cepat (window 16 jam) |

Studi kasus 3 hari (LUNA, mint `H78WENHosTWPFuQvtm8swi83ipTqANJi921iG51Apump`):

| Hari | File | Yang terjadi |
|---|---|---|
| 2026-08-01 | luna_dump.csv | Dump −67%, spring di 20:13, 17 akumulator (31 SOL) |
| 2026-08-02 | luna_after_dump.csv | Higher-low 23:19, volume kering −73%, buy TX 49,9% (hari tes) |
| 2026-08-03 | luna3.csv | **Pump +180% intraday** di 00:02–00:19, CVD +2,1% |

**PENTING:** `LUNA.csv` (live, 2 Agu 16 jam) yang dipakai pemilik untuk trading
TIDAK termasuk dataset — jangan dicampur. Hanya `luna_dump/luna_after_dump/luna3`.

Script referensi:
- `analyze.py` — parser CSV + metrik per token (CVD, wallet, tag, whale, fase).
- `low_window.py` — analisa mikro 15-menit di sekitar low.
- `batch_analyze.py` — hitung semua metrik untuk 10 token pump.
- `compare_luna.py` — bandingkan pump vs LUNA (2 kontrol semu).
- `luna_sequence.py`, `analyze_luna2.py`, `analyze_luna3.py` — studi LUNA.

---

## 2. Sinyal yang SUDAH divalidasi (dari 10 pump + LUNA)

### 2.1 Sinyal 1-hari (tipe CEPAT) — dipakai `prepump_detector.py`

Dari 10 token pump, ini tingkat kemunculannya:

| Sinyal | Lolos | Catatan |
|---|:--:|---|
| **Rata2 SELL > rata2 BUY** (per transaksi) | **10/10** | "big sell dimakan small buy" |
| **Whale (>1 SOL/tx) net NEGATIF** | **10/10** | whale membuang di low |
| **Sudah pantul >5% dari low** (low→close positif) | **10/10** | spring tervalidasi |
| **CVD full-day \|cvd/vol\| < 10%** | 9/10 | ansem 2 −13,3% krn 1 dump wallet, tetap pump |
| **Buy TX ≥ 52%** (LEBAR partisipasi) | 9/10 | sinyal terkuat membedakan pump vs non-pump |
| **3 jam setelah low net BUY** | 9/10 | pergeseran tekanan jual→beli |
| **Spring: ada candle 15m post-low buy% ≥ 55%** | 9/10 | |
| \|CVD terendah intraday\| < 10% | 8/10 | |
| Retention akumulator di low ≥ 40% | 8/10 | |
| 3 jam setelah low buy% > 52% | 7/10 | |
| ≥2 candle spring post-low | 6/10 | |
| Holder di low ≥50% tidak jual | 6/10 | |

**Sinyal yang JANGAN dipakai sendirian** (muncul juga di non-pump / tidak konsisten):
- Retention tinggi (LUNA 100% juga, bukan pembeda).
- CVD datar (LUNA juga datar).
- Ada spring candle (LUNA juga ada).
- Label tag GMGN (`bluechip_owner`, `bundler`, `fresh_wallet`) — hanya
  30–60% konsisten; token baru sering belum ke-tag. **Jangan jadikan pilar utama.**
- Pola fase Q1/Q2 negatif → Q3/Q4 positif (variatif antar token).

### 2.2 Sinyal multi-hari (tipe LAMBAT) — ini yang BELUM ada di detector

LUNA mengajarkan bahwa di H-1 (sehari sebelum pump), filter 1-hari bisa
TERLIHAT NEGATIF (buy TX 49,9%, ukuran BUY ≥ SELL, vol kering, whale net
+4). Itu bukan kegagalan — itu **fase "spring test / LPS"**. Detektor harus
mendeteksi RANGKAIAN 2–3 hari, bukan menolak token di hari tes:

1. **Hari −2 / −1: dump besar** (penurunan >40%) lalu **spring** di low:
   candle 15m dengan buy% ≥55% sesudah candle capitulation.
2. **Retention akumulator lintas hari ≥50%** — mayoritas pembeli di low
   TIDAK melepas sampai hari-H (di LUNA: 59% masih hold sampai 3 Agu).
3. **Hari H-1: higher low** (low baru TIDAK menembus low spring sebelumnya)
   + **volume kering ≥50%** dari volume dump (LUNA: 1.233 → 338 SOL) +
   CVD tetap datar/positif. Inilah "supply kering" sebelum pump.
4. **Hari-H (ignition): lonjakan TX & CVD di awal hari** — LUNA pump
   jam 00:02 dengan 564 tx di 1 jam, net +34,8 SOL. Detektor multi-timeframe
   30m/1h existing (`PREPUMP_TF_CONFIGS`) harus menangkap ini.

Koreksi penting terhadap §2.1: **Buy TX ≥52% dan avg SELL>BUY bersifat WAJIB
di hari spring yang sama dengan pump (tipe cepat)**, tapi TIDAK muncul di hari
tes tipe lambat. Jadi detektor butuh STATE lintas-hari, bukan cuma snapshot.

### 2.3 Ambang toleransi CVD (jawaban terukur)

- **Net CVD full-day |cvd/vol| < 10%** → aman (9/10 pump lolos; ideal <5%).
- **CVD terendah intraday |cvd_min/vol| < 10%** → 8/10.
- **CVD DALAM WINDOW PENURUNAN ke low** → BISA −15% sampai −50% (hoppy −50%,
  luna Aug1 dalam). JANGAN pakai 10% di window pendek — yang penting
  SETELAH low CVD berbalik (spring + divergence).
- Jika CVD di bawah −10% sampai −15%, cek apakah penyebabnya **satu dump
  wallet besar** (ansem 2: 1 wallet −1.435 SOL di 1 candle) — kalau iya
  dan spring tetap muncul, masih valid. Jika banyak seller, itu distribusi.

---

## 3. Perubahan yang diminta pemilik wallet-depth

### 3.1 YANG DIPERTAHANKAN & DIPERKUAT
- `prepump_detector.py` — **satu-satunya inti deteksi**. Kalibrasi 4 pilar
  25-poinnya agar sejalan dengan §2 (khususnya P1 compression, P2 size
  asymmetry, P3 accumulator conviction, P4 ignition).
- Multi-timeframe 30m/1h/4h/12h + confluence di `prepump_detector.py` —
  ini sudah mengakomodasi tipe cepat (30m/1h ignition) DAN lambat (4h/12h
  accumulation). Pastikan confluence "SLEEPER" (makro tinggi, mikro sepi)
  dipertahankan — itulah pola LUNA H-1.
- `cvd.py` — penyimpanan swap & perhitungan CVD/wallet profile tetap
  dibutuhkan sebagai input detector.
- `signals.py` — logging sinyal pre-pump ke `signals.json` + Telegram digest.
- `pages/12_🎯_Prepump_Checker.py` — UI manual check (sudah ada).
- `watchlist.py`, `core.py` (Helius/DexScreener/GeckoTerminal helper).
- Cron `cvd-update.yml` (jam :30) & `memecoin-scanner.yml` — hanya jika
  mengarah ke prepump; scanner lain yang tidak relevan matikan.

### 3.2 YANG DIBUANG / DIMATIKAN
Hapus atau nonaktifkan (ikuti pola `DISABLED.md` — `st.stop()` di halaman,
jangan hapus file dulu agar revert mudah):
- `breakout_guard.py` + level D1 / H4 close — pemilik cuma mau pre-pump,
  bukan breakout guard.
- `telegram_monitor_alerts.py` / `monitor_alerts.py` (alerts generik).
- `cto_deep_scan.py` + `lp_safe_radar.py` + `memecoin_scanner.py` +
  `incubation_radar.py` + workflow terkait (CTO radar, LP safe, memecoin
  scanner) — di luar fokus pre-pump.
- `pages/1_⚖️_Compare.py`, `7_💀_CTO_Radar.py`, `8_💧_LP_Safe_Radar.py`,
  `10_📈_Accumulation_History.py`, `11_🤖_Memecoin_Scanner.py`.
- `breakout_log.py`, `breakouts.json`, `levels.json`, `breakout_guard`
  references di `signals.py`.
- `focus.py` boleh dihapus (logika collapse badge tidak relevan setelah
  detector jadi satu-satunya output).
- `ai_prompt.py`, `share_card.py` — opsional, buang jika tidak dipakai checker.
- `conviction.json`, `holder_snapshots` jika hanya melayani modul mati.
- Health score, watchlist ticker bar, fitur-fitur non-detector di `app.py`
  (ditandai di `DISABLED.md`).

### 3.3 Aturan kerja untuk AI sesi baru
1. **JANGAN melonggarkan ambang risiko diam-diam.** Kalau mengubah skor/
   threshold, buktikan dengan menjalankan ulang detektor terhadap 13 file
   CSV di §1 dan tunjukkan hasilnya berupa tabel skor per token. Skor
   idealnya: 10 pump ≥75 (imminent) atau ≥55 (forming), LUNA Aug2
   terbaca sebagai "sleeper", dan token yang jelas-jelas sepi tidak
   false-positive.
2. **Pakai data CSV di `prepump_baru` sebagai ground truth**, jangan klaim
   dari inginan/model. Jalankan script di `prepump_baru` untuk reproduksi
   angka (sudah di-push ke branch `arena/019fd86c-prepump-baru`).
3. **Bahasa:** Indonesia untuk UI/pesan ke pemilik, Inggris untuk komen &
   docstring kode (konvensi wallet-depth).
4. **Jalankan test** `python -m unittest discover tests` setelah perubahan;
   pastikan tidak ada import modul yang sudah dimatikan.
5. **Jangan aktifkan kembali halaman/fungsi di `DISABLED.md` tanpa
   persetujuan eksplisit.** Pemilik ingin fokus sempit.
6. Setelah mengubah perilaku, perbarui `AGENTS.md` + `docs/PROGRESS.md`
   di commit yang sama (aturan repo wallet-depth).

---

## 4. Kalibrasi yang disarankan di `prepump_detector.py`

Petunjuk spesifik (bukan instruksi buta — cek kode dulu):

- **P1 (Volume Compression & Seller Exhaustion):** pastikan menghargai
  "volume kering H-1" sebagai sinyal BULLISH (sleeper), bukan bearish.
  LUNA Aug2 vol turun 73%.
- **P2 (Order-Flow Size Asymmetry):** jadikan **avg SELL > avg BUY** dan
  **buy TX% ≥ 52%** sebagai bobot tinggi — ini pembeda terkuat. Tapi
  JANGAN hard-fail kalau multi-hari menunjukkan pola lambat (pakai
  konteks 4h/12h).
- **P3 (Pure Accumulator Conviction):** hitung retention LINTAS-HARI
  (wallet yang beli di low spring masih hold di hari-H), bukan cuma
  within-window. Tag smart-money (`PREPUMP_SMART_TAGS`) jangan dijadikan
  pilar utama — banyak token pump tanpa tag.
- **P4 (Terminal Ignition):** pertahankan deteksi lonjakan TX/CVD awal
  hari (pola LUNA 00:02). Tambahkan deteksi spring 15m (buy ≥55%
  sesudah capitulation) sebagai sinyal mikro.
- **Confluence:** kategori `SLEEPER` (macro 4h/12h ≥65, mikro <40)
  persisnya adalah LUNA sehari sebelum pump — JANGAN turunkan bobotnya;
  ini justru sinyal early yang berharga.

---

## 5. Quick check reproduksi (dari repo prepump_baru)

```bash
pip install pandas numpy --break-system-packages
python batch_analyze.py    # metrik 10 token pump
python compare_luna.py     # tabel pump vs LUNA + pass-rate filter
python luna_sequence.py    # urutan 3 hari LUNA
```

Output yang diharapkan: 10/10 pump punya avg SELL > avg BUY & whale net
negatif; buy TX ≥52% di 9/10; LUNA Aug2 buy TX 49,9% & vol turun 73%
tapi Aug3 pump +180%.

---

_Dibuat dari analisa 10 token pump + urutan 3 hari LUNA (Agu 2026). Untuk
detail angka per token lihat `ANALISIS_POLA_PUMP.md` dan tabel di
`/tmp/summary_all.csv` (hasil `batch_analyze.py`)._

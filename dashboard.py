# ==========================================
# LANGKAH 1: IMPORT LIBRARY & SETUP HALAMAN
# ==========================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="MACO Refueling 39", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# REVISI LANGKAH 2: CUSTOM CSS (FORCE DARK & NEON)
# ==========================================
st.markdown("""
    <style>
    /* --- 1. PAKSA BACKGROUND GELAP (GLOBAL) --- */
    /* Ini akan menimpa settingan Light Mode browser user */
    [data-testid="stAppViewContainer"] {
        background-color: #0d1b2a !important;
        color: #ffffff !important;
    }
    
    /* Header bagian atas (tempat tombol menu) juga digelapkan */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important; /* Transparan */
    }

    /* Warna teks default dipaksa putih semua */
    h1, h2, h3, h4, h5, h6, p, li, span, div {
        color: #ffffff;
    }
    
    /* --- 2. JUDUL DASHBOARD (ANIMASI SETRUM) --- */
    @keyframes flicker {
        0%, 18%, 22%, 25%, 53%, 57%, 100% {
            text-shadow: 
                0 0 10px #00e5ff, 
                0 0 20px #00e5ff, 
                0 0 40px #00e5ff, 
                0 0 80px #00e5ff, 
                0 0 100px #00e5ff;
            opacity: 1;
        }
        20%, 24%, 55% {
            text-shadow: none;
            opacity: 0.4;
        }
    }

    .main-title {
        text-align: center; 
        color: #ffffff; 
        font-size: 65px; 
        font-weight: 900; 
        margin-bottom: 30px; 
        margin-top: -20px;
        letter-spacing: 4px;
        font-family: sans-serif;
        animation: flicker 2.5s infinite alternate; 
    }

    /* --- 3. KARTU METRIK (COMPACT) --- */
    div[data-testid="stMetric"] {
        background-color: #1b263b !important; 
        border: 1px solid #00e5ff !important;
        padding: 10px; 
        border-radius: 10px; 
        box-shadow: 0 0 8px #00e5ff;
    }
    /* Label Kecil */
    div[data-testid="stMetricLabel"] p {
        font-size: 14px !important; 
        color: #b0c4de !important;
    }
    /* Angka Besar */
    div[data-testid="stMetricValue"] div {
        font-size: 26px !important; 
        color: #00e5ff !important;
        font-weight: bold;
    }

    /* --- 4. JAM DIGITAL --- */
    .clock-card {
        background-color: #000000;
        border: 2px solid #333;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.9);
    }
    .digital-font {
        font-family: 'Courier New', Courier, monospace;
        font-size: 48px;
        font-weight: bold;
        color: #39ff14; 
        text-shadow: 0 0 10px #39ff14;
        background-color: #0d0d0d;
        padding: 10px;
        border-radius: 5px;
        border: 1px inset #333;
        letter-spacing: 4px;
        margin: 10px 0;
    }

    /* --- 5. HILANGKAN PADDING ATAS BAWAAN STREAMLIT --- */
    .block-container { padding-top: 4rem; } 
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# LANGKAH 3: KONEKSI DATA (ANTI-ERROR)
# ==========================================
SHEET_ID = "1NN_rGKQBZzhUIKnfY1aOs1gvCP2aFiVo6j1RFagtb4s"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL) 
        df.columns = df.columns.str.lower().str.strip()
        
        rename_map = {
            'timestamp': 'timestamp', 'kode unit': 'unit', 
            'lokasi': 'location', 'quantity': 'quantity', 'hm': 'hm'
        }
        df.rename(columns=rename_map, inplace=True)
        df = df.dropna(subset=['unit', 'quantity'], how='all')

        if 'timestamp' in df.columns:
            raw_ts = df['timestamp'].astype(str)
            df['timestamp'] = pd.to_datetime(raw_ts, dayfirst=True, errors='coerce')
            
            mask_failed = df['timestamp'].isna()
            if mask_failed.any():
                df.loc[mask_failed, 'timestamp'] = pd.to_datetime(
                    raw_ts[mask_failed], dayfirst=False, errors='coerce'
                )
            
            df = df.sort_values('timestamp').reset_index(drop=True)

        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
        if 'hm' in df.columns:
            df['hm'] = pd.to_numeric(df['hm'], errors='coerce')
        if 'shift' in df.columns:
            df['shift'] = df['shift'].astype(str).str.upper().str.strip()
            
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

df = load_data()

# ==========================================
# REVISI LANGKAH 4: LOGIKA DATA & ANOMALI
# ==========================================
if not df.empty:
    # 1. Judul & Header (Tetap)
    st.markdown('<p class="main-title">DASHBOARD REFUELING PITSTOP KM 39</p>', unsafe_allow_html=True)

    # 2. Filter & Refresh (Tetap)
    col_filter, col_btn = st.columns([4, 1]) 
    with col_filter:
        unit_list = sorted(df['unit'].unique().tolist())
        filter_options = ["ALL UNITS"] + unit_list
        selected_unit = st.selectbox("🔍 Filter No Lambung Unit:", options=filter_options, index=0)

    with col_btn:
        st.write(" "); st.write(" ") 
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # 3. Saring Data
    df_filtered = df if selected_unit == "ALL UNITS" else df[df['unit'] == selected_unit]
    
    if df_filtered.empty:
        st.warning("⚠️ Tidak ada data untuk unit yang dipilih.")
        st.stop()

    # --- LOGIKA BARU: DETEKSI EARLY REFILL (VOLVO FMX) ---
    # Batas Minimum Pengisian yang Efektif (Setengah Tangki / 160L)
    MIN_REFILL_TARGET = 160.0 
    
    # Kita butuh df ini untuk visualisasi grafik nanti
    # Menandai baris mana saja yang Quantity-nya "Pelit" (Anomali)
    df_filtered['is_anomali'] = df_filtered['quantity'] < MIN_REFILL_TARGET

    # 4. Fungsi Analisa Performa (Tetap)
    def get_performance_df(data_source):
        active_units = data_source['unit'].unique()
        performance_data = []
        for unit in active_units:
            u_data = data_source[data_source['unit'] == unit]
            duration = (u_data['timestamp'].max() - u_data['timestamp'].min()).total_seconds() / 3600
            l_hr = u_data['quantity'].sum() / duration if duration > 0 else 0
            
            num_days_unit = u_data['timestamp'].dt.date.nunique()
            refills_day = len(u_data) / num_days_unit if num_days_unit > 0 else 0
            
            performance_data.append({
                'unit': unit, 
                'l_hr': l_hr, 
                'refills_day': refills_day
            })
        return pd.DataFrame(performance_data)

    df_perf_global = get_performance_df(df)
    df_perf_filtered = get_performance_df(df_filtered)

    # Rata-rata & Metrik (Tetap)
    if not df_perf_filtered.empty:
        avg_l_per_hr = df_perf_filtered['l_hr'][df_perf_filtered['l_hr'] > 0].mean()
        avg_refills_per_day = df_perf_filtered['refills_day'].mean()
    else:
        avg_l_per_hr = 0
        avg_refills_per_day = 0

    total_qty = df_filtered['quantity'].sum()
    total_trx = len(df_filtered)
    last_update_raw = df_filtered['timestamp'].max()
    last_update_str = last_update_raw.strftime('%d %b, %H:%M') if pd.notnull(last_update_raw) else "-"
    achievement_rate = (1 - 0.1017) * 100

    # ==========================================
    # LANGKAH 5: METRIC CARDS
    # ==========================================
    st.write("") 
    c1, c2, c3, c4, c5 = st.columns(5)
    
    c1.metric("Total Pemakaian Solar", f"{total_qty:,.0f} L")
    c2.metric("Total Pengisian", f"{total_trx} Kali")
    c3.metric("Rata-Rata Pengisian", f"{avg_refills_per_day:.1f} Kali/Hari")
    c4.metric("Fuel Consumption", f"{avg_l_per_hr:.1f} Liter/Jam")
    c5.metric("Update Data Terakhir", last_update_str)

    st.write("---")
    
    # Setup Tab
    tab1, tab2 = st.tabs(["📊 RINGKASAN VISUAL", "📋 LOGSHEET KESELURUHAN"])

# ==========================================
# REVISI LANGKAH 6: INTEGRASI DAFTAR ANOMALI (EARLY REFILL LIST)
# ==========================================
    with tab1:
        # --- 1. ALERT BOX (PERINGATAN ATAS) ---
        MIN_REFILL_TARGET = 160.0
        # Filter data anomali dari data yang sedang aktif
        df_early_refill = df_filtered[df_filtered['quantity'] < MIN_REFILL_TARGET].copy()

        if not df_early_refill.empty:
            st.markdown(f"""
            <div style="background-color: #441111; border: 2px solid #ff4b4b; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                <h3 style="color: #ff4b4b; margin: 0; font-size: 20px;">⚠️ PERINGATAN: TERDETEKSI PENGISIAN ANOMALI</h3>
                <p style="color: #ffffff; font-size: 14px; margin-top: 5px;">
                    Terdeteksi <b>{len(df_early_refill)} kali</b> unit masuk pitstop dengan kondisi tangki fuel di bawah {MIN_REFILL_TARGET} Liter. 
                    menyebabkan antrean tidak efektif!
                </p>
            </div>
            """, unsafe_allow_html=True)

        # --- BARIS 1: GRAFIK TREN & TOP 5 (TETAP) ---
        row1_c1, row1_c2 = st.columns([1.5, 1])

        with row1_c1:
            df_trend = df_filtered.copy().sort_values('timestamp')
            
            # Layer Biru (Normal)
            fig_trend = px.area(
                df_trend, x='timestamp', y='quantity', 
                title="📈 TREN KONSUMSI SOLAR", 
                hover_data={'timestamp': '|%d %b %Y, %H:%M'}
            )
            fig_trend.update_traces(line_color='#00e5ff', fillcolor='rgba(0, 229, 255, 0.2)')
            
            # Layer Merah (Anomali)
            anomali_points = df_trend[df_trend['quantity'] < MIN_REFILL_TARGET]
            if not anomali_points.empty:
                fig_trend.add_trace(go.Scatter(
                    x=anomali_points['timestamp'], y=anomali_points['quantity'],
                    mode='markers', name='Early Refill',
                    marker=dict(color='#ff4b4b', size=10, symbol='x', line=dict(width=2, color='white')),
                    hovertemplate='<b>EARLY REFILL!</b><br>Vol: %{y} L<br>Waktu: %{x}<extra></extra>'
                ))

            fig_trend.update_layout(
                height=400, margin=dict(l=10, r=10, t=80, b=10), 
                template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)',
                title_font_size=24,
                xaxis=dict(title="Waktu Pengisian", title_font=dict(size=18), tickfont=dict(size=14)),
                yaxis=dict(title="Volume (Liter)", title_font=dict(size=18), tickfont=dict(size=14)),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        with row1_c2:
            df_boros = df_perf_global.nlargest(5, 'l_hr').sort_values('l_hr', ascending=True)
            fig_boros = px.bar(
                df_boros, x="l_hr", y="unit", orientation='h', 
                title="🔥 TOP 5 UNIT TERBOROS", 
                color_discrete_sequence=['#ff4b4b'], text_auto='.1f'
            )
            fig_boros.update_layout(
                height=400, margin=dict(l=10, r=10, t=80, b=10), 
                template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)',
                title_font_size=24,
                xaxis=dict(title="Liter/Jam", title_font=dict(size=18), tickfont=dict(size=14)),
                yaxis=dict(title="Unit", title_font=dict(size=18), tickfont=dict(size=14))
            )
            st.plotly_chart(fig_boros, use_container_width=True)

        # --- BARIS 2: TIGA KOLOM (LIST ANOMALI | TRAFFIC | JAM) ---
        st.write("---")
        # Layout: Kiri (List) - Tengah (Chart) - Kanan (Jam)
        col_list, col_chart, col_clock = st.columns([1.5, 2.5, 1])
        
        # --- KOLOM 1: DAFTAR UNIT PELANGGAR (FITUR BARU) ---
        with col_list:
            st.markdown('<p style="font-size: 18px; color: #ff4b4b; font-weight: bold; text-align: center; margin-bottom: 10px;">📋 DAFTAR "EARLY REFILL"</p>', unsafe_allow_html=True)
            
            if not df_early_refill.empty:
                # Rapikan tabel untuk tampilan
                df_show = df_early_refill[['timestamp', 'unit', 'quantity']].copy()
                df_show = df_show.sort_values('timestamp', ascending=False) # Yang terbaru paling atas
                
                # Format Waktu agar enak dibaca (Jam:Menit)
                df_show['Waktu'] = df_show['timestamp'].dt.strftime('%d %b, %H:%M')
                
                # Rename kolom
                df_show = df_show.rename(columns={'unit': 'No Unit', 'quantity': 'Isi (L)'})
                
                # Tampilkan tabel tanpa index
                st.dataframe(
                    df_show[['Waktu', 'No Unit', 'Isi (L)']], 
                    use_container_width=True, 
                    hide_index=True,
                    height=350 # Tinggi disamakan dengan grafik sebelahnya
                )
            else:
                st.success("✅ Tidak ada unit yang melanggar batas minimum pengisian.")

        # --- KOLOM 2: GRAFIK TRAFFIC (TENGAH) ---
        with col_chart:
            # 1. SETUP SESSION STATE
            if 'chart_date' not in st.session_state:
                st.session_state.chart_date = df['timestamp'].max().date()

            # 2. NAVIGASI TANGGAL
            c_prev, c_date, c_next = st.columns([1, 4, 1])
            with c_prev:
                if st.button("⬅️ Prev", use_container_width=True):
                    st.session_state.chart_date -= pd.Timedelta(days=1); st.rerun()
            with c_next:
                if st.button("Next ➡️", use_container_width=True):
                    st.session_state.chart_date += pd.Timedelta(days=1); st.rerun()
            with c_date:
                hari_dict = {'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu', 'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'}
                bulan_dict = {'January': 'Januari', 'February': 'Februari', 'March': 'Maret', 'April': 'April', 'May': 'Mei', 'June': 'Juni', 'July': 'Juli', 'August': 'Agustus', 'September': 'September', 'October': 'Oktober', 'November': 'November', 'December': 'Desember'}
                
                eng_day = st.session_state.chart_date.strftime("%A")
                eng_month = st.session_state.chart_date.strftime("%B")
                tgl_angka = st.session_state.chart_date.day
                tahun = st.session_state.chart_date.year
                indo_str = f"{hari_dict.get(eng_day, eng_day)}, {tgl_angka} {bulan_dict.get(eng_month, eng_month)} {tahun}"
                
                st.markdown(f"<h3 style='text-align: center; color: #00e5ff; margin: 0; font-size: 20px;'>{indo_str}</h3>", unsafe_allow_html=True)

            # 3. RENDER GRAFIK
            df_daily = df[df['timestamp'].dt.date == st.session_state.chart_date].copy()
            if not df_daily.empty:
                df_daily['jam'] = df_daily['timestamp'].dt.hour
                hourly_counts = df_daily.groupby('jam').size().reset_index(name='jumlah')
                hourly_counts = hourly_counts.sort_values('jam')
                hourly_counts['jam_label'] = hourly_counts['jam'].apply(lambda x: f"{x:02d}:00")

                fig_daily = px.bar(
                    hourly_counts, x='jam_label', y='jumlah',
                    title=f"📊 TRAFFIC ANTREAN",
                    text_auto=True, labels={'jam_label': 'Jam', 'jumlah': 'Unit'}
                )
                fig_daily.update_traces(marker_color='#00e5ff', width=0.6)
                fig_daily.update_layout(
                    height=350, margin=dict(l=20, r=20, t=50, b=20),
                    template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)',
                    title_font_size=18,
                    xaxis=dict(type='category', title_font=dict(size=14), tickfont=dict(size=12)), 
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title_font=dict(size=14), tickfont=dict(size=12))
                )
                st.plotly_chart(fig_daily, use_container_width=True)
            else:
                st.info(f"💤 Tidak ada data pada {indo_str}.")

        # --- KOLOM 3: JAM DIGITAL (KANAN) ---
        with col_clock:
            st.write(""); st.write("") 
            html_clock = """
<div class="clock-card" style="margin-top: 10px; padding: 15px;">
<p style="color: #888; font-size: 12px; margin-bottom: 5px;"> TARGET DURASI</p>
<div class="digital-font" style="font-size: 30px;">
08:00
</div>
<p style="font-size: 14px; color: #00e5ff;">MENIT / UNIT</p>
</div>
"""
            st.markdown(html_clock, unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align: center; color: #aaa; font-size: 11px; margin-top: 10px;">
            <i>*SOP Waktu: Masuk s/d Keluar Bays.</i>
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # LANGKAH 7: TABEL DATA
    # ==========================================
    with tab2:
        st.subheader("📋 Riwayat Lengkap Logsheet (Terfilter)")
        df_full = df_filtered.sort_values(by='timestamp', ascending=False).copy()
        df_full['timestamp'] = df_full['timestamp'].dt.strftime('%d/%m/%Y %H:%M:%S')
        st.dataframe(df_full, use_container_width=True, height=600, hide_index=True)

# --- BAGIAN INI UNTUK MENANGANI JIKA DATA KOSONG ---
else:
    st.warning("Menunggu data... Pastikan Google Sheet Anda dapat diakses publik (CSV Mode).")
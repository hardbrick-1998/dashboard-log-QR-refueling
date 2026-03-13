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
# REVISI LANGKAH 2: CUSTOM CSS (CYBERPUNK EDITION)
# ==========================================
st.markdown("""
    <style>
    /* --- 1. GLOBAL SETTINGS --- */
    [data-testid="stAppViewContainer"] {
        background-color: #0d1b2a !important;
        color: #ffffff !important;
        background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px), 
                          linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
    }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    h1, h2, h3, h4, h5, h6, p, li, span, div { color: #ffffff; }
    
    /* --- 2. JUDUL DASHBOARD (BOX NEON) --- */
    .cyberpunk-title-container {
        background-color: rgba(13, 27, 42, 0.8);
        border: 3px solid #00e5ff;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        margin-bottom: 30px; margin-top: -20px;
        box-shadow: 0 0 20px rgba(0, 229, 255, 0.6), inset 0 0 30px rgba(0, 229, 255, 0.3);
        backdrop-filter: blur(5px);
    }
    @keyframes flicker {
        0%, 18%, 22%, 25%, 53%, 57%, 100% {
            text-shadow: 0 0 10px #00e5ff, 0 0 20px #00e5ff, 0 0 40px #00e5ff; opacity: 1;
        }
        20%, 24%, 55% { text-shadow: none; opacity: 0.5; }
    }
    .main-title {
        font-size: 55px; font-weight: 900; margin: 0; letter-spacing: 4px;
        font-family: 'Verdana', sans-serif; text-transform: uppercase;
        animation: flicker 3s infinite alternate;
    }

    /* --- 3. KARTU METRIK --- */
    div[data-testid="stMetric"] {
        background-color: #1b263b !important; border: 1px solid #00e5ff !important;
        padding: 10px; border-radius: 10px; box-shadow: 0 0 8px #00e5ff;
    }
    div[data-testid="stMetricLabel"] p { font-size: 14px !important; color: #b0c4de !important; }
    div[data-testid="stMetricValue"] div { font-size: 26px !important; color: #00e5ff !important; font-weight: bold; }

    /* --- 4. JAM DIGITAL --- */
    .clock-card {
        background-color: #000000; border: 2px solid #333; border-radius: 10px; 
        padding: 20px; text-align: center; box-shadow: inset 0 0 20px rgba(0,0,0,0.9);
    }
    .digital-font {
        font-family: 'Courier New', Courier, monospace; font-size: 48px; font-weight: bold; 
        color: #39ff14; text-shadow: 0 0 10px #39ff14; background-color: #0d0d0d; 
        padding: 10px; border-radius: 5px; border: 1px inset #333; letter-spacing: 4px; margin: 10px 0;
    }

    /* --- 5. TABEL GLOWING --- */
    [data-testid="stDataFrame"] {
        border: 2px solid #00e5ff !important;
        box-shadow: 0 0 20px rgba(0, 229, 255, 0.4) !important;
        border-radius: 5px !important;
        background-color: rgba(13, 27, 42, 0.8) !important;
    }
    
    /* Header Tabel: Paksa Hijau Neon & Center */
    [data-testid="stDataFrame"] th {
        color: #39ff14 !important; /* HIJAU NEON */
        border-bottom: 2px solid #39ff14 !important;
        text-align: center !important; /* PAKSA TENGAH */
        font-weight: 900 !important;
        text-transform: uppercase !important;
        vertical-align: middle !important;
    }
    
    .block-container { padding-top: 3rem; } 
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# LANGKAH 3: KONEKSI DATA (ANTI-ERROR & DETEKSI TANGGAL RUSAK)
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
            # Bersihkan spasi nakal sebelum dibaca
            raw_ts = df['timestamp'].astype(str).str.strip()
            df['timestamp'] = pd.to_datetime(raw_ts, dayfirst=True, errors='coerce')
            
            mask_failed = df['timestamp'].isna()
            if mask_failed.any():
                df.loc[mask_failed, 'timestamp'] = pd.to_datetime(
                    raw_ts[mask_failed], dayfirst=False, errors='coerce'
                )
            
            # --- ALARM BARU: Hitung berapa data yang tanggalnya gagal dibaca ---
            if df['timestamp'].isna().any():
                failed_count = df['timestamp'].isna().sum()
                st.warning(f"⚠️ Peringatan: Ada {failed_count} baris di Google Sheets yang format tanggalnya salah/tidak terbaca sistem. Grafik mungkin tidak lengkap.")
            
            # Buang data yang tanggalnya benar-benar hancur biar grafik nggak error
            df = df.dropna(subset=['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)

        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
        
        # Paksa nama unit jadi Huruf Besar
        df['unit'] = df['unit'].astype(str).str.upper().str.strip()

        if 'hm' in df.columns:
            df['hm'] = pd.to_numeric(df['hm'], errors='coerce').fillna(0).astype(int).astype(str)
            
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
    # --- INISIALISASI MEMORI TANGGAL (SESSION STATE) ---
    if 'filter_date' not in st.session_state:
        st.session_state.filter_date = df['timestamp'].max().date()

    # --- JUDUL DASHBOARD DALAM KOTAK CYBERPUNK ---
    st.markdown("""
    <div class="cyberpunk-title-container">
        <p class="main-title">DASHBOARD REFUELING PITSTOP KM 39</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Filter & Refresh (KALENDER TERKONEKSI)
    col_filter_unit, col_filter_date, col_btn = st.columns([2, 2, 1]) 
    
    with col_filter_unit:
        unit_list = sorted(df['unit'].unique().tolist())
        filter_options = ["ALL UNITS"] + unit_list
        selected_unit = st.selectbox("🔍 Pilih Unit:", options=filter_options, index=0)

    with col_filter_date:
        # --- INI OBATNYA MAS ---
        # Jangan pakai key="filter_date", pakai 'value' saja biar nggak dikunci sistem
        temp_date = st.date_input("📅 Tanggal (Kalender):", value=st.session_state.filter_date)
        # Tulis ulang nilainya ke memori
        st.session_state.filter_date = temp_date

    with col_btn:
        st.write(" "); st.write(" ") 
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Tarik tanggal yang sedang aktif dari memori
    selected_date = st.session_state.filter_date

    # 3. Saring Data (DITAMBAH .copy() AGAR CACHE TIDAK ERROR)
    df_filtered = df.copy() if selected_unit == "ALL UNITS" else df[df['unit'] == selected_unit].copy()
    
    if df_filtered.empty:
        st.warning("⚠️ Tidak ada data untuk unit yang dipilih.")
        st.stop()

    # --- LOGIKA BARU: DETEKSI EARLY REFILL (VOLVO FMX) ---
    MIN_REFILL_TARGET = 160.0 
    df_filtered['is_anomali'] = df_filtered['quantity'] < MIN_REFILL_TARGET

    # 4. Fungsi Analisa Performa (Tetap) berdasarkan nilai Timestamp
    def get_performance_df(data_source):
        active_units = data_source['unit'].unique()
        performance_data = []
        for unit in active_units:
            u_data = data_source[data_source['unit'] == unit]
            duration = (u_data['timestamp'].max() - u_data['timestamp'].min()).total_seconds() / 3600
            l_hr = u_data['quantity'].sum() / duration if duration > 0 else 0

            num_days_unit = u_data['timestamp'].dt.date.nunique()
            refills_day = len(u_data) / num_days_unit if num_days_unit > 0 else 0
            
            performance_data.append({'unit': unit, 'l_hr': l_hr, 'refills_day': refills_day})
            
        # Posisi return sejajar dengan for (mundur ke kiri)
        return pd.DataFrame(performance_data)

    # Posisi pemanggilan fungsi sejajar dengan def (mundur ke kiri lagi)
    df_perf_global = get_performance_df(df)
    df_perf_filtered = get_performance_df(df_filtered)

    # Rata-rata & Metrik (Tetap)
    if not df_perf_filtered.empty:
        avg_l_per_hr = df_perf_filtered['l_hr'][df_perf_filtered['l_hr'] > 0].mean()
        avg_refills_per_day = df_perf_filtered['refills_day'].mean()
    else:
        avg_l_per_hr = 0
        avg_refills_per_day = 0

    # --- LOGIKA TANGGAL OPERASIONAL (SHIFT BASE) ---
    # Shift lapangan: 06:00 s/d 05:59 besoknya. 
    # Trik: Mundurkan timestamp 6 jam untuk mendeteksi tanggal produksinya.
    df_filtered['operational_date'] = (df_filtered['timestamp'] - pd.Timedelta(hours=6)).dt.date
    daily_consumption = df_filtered.groupby('operational_date')['quantity'].sum()
    avg_daily_qty = daily_consumption.mean() if not daily_consumption.empty else 0

    # --- HITUNG POPULASI UNIT (VARIASI UNIT UNIK DIKUNCI) ---
    total_populasi_unit = df['unit'].nunique()

    # Variabel bawaan lainnya (biarkan saja)
    total_qty = df_filtered['quantity'].sum()
    total_trx = len(df_filtered)
    last_update_raw = df_filtered['timestamp'].max()
    last_update_str = last_update_raw.strftime('%d %b, %H:%M') if pd.notnull(last_update_raw) else "-"
    achievement_rate = (1 - 0.1017) * 100

# ==========================================
# REVISI LANGKAH 5: METRIC CARDS
# ==========================================
    st.write("") 
    c1, c2, c3, c4, c5 = st.columns(5)
    
    # Metrik 1: Rata-rata Pemakaian Harian (Sesuai Shift)
    c1.metric("Rata-Rata Pemakaian", f"{avg_daily_qty:,.0f} L/Hari")
    
    # Metrik 2: Populasi Unit (Variasi Lambung)
    c2.metric("Populasi Unit", f"{total_populasi_unit} Unit")
    
    # Metrik 3, 4, 5 (Tetap)
    c3.metric("Rata-Rata Pengisian", f"{avg_refills_per_day:.1f} Kali/Hari")
    c4.metric("Fuel Consumption", f"{avg_l_per_hr:.1f} Liter/Jam")
    c5.metric("Update Pengisian Terakhir", last_update_str)

    st.write("---")
    
    # --- INI BARIS YANG TADI HILANG ---
    tab1, tab2 = st.tabs(["📊 RINGKASAN VISUAL", "📋 RIWAYAT LOGSHEET"])

# ==========================================
# REVISI LANGKAH 6: VISUALISASI DASHBOARD (NEW LAYOUT)
# ==========================================
    with tab1:
        # ========================================================
        # --- 1. GRAFIK TREN KONSUMSI SOLAR (SMART DYNAMIC CHART) ---
        # ========================================================
        target_month = selected_date.month
        target_year = selected_date.year
        
        df_trend = df_filtered[
            (df_filtered['timestamp'].dt.month == target_month) & 
            (df_filtered['timestamp'].dt.year == target_year)
        ].copy().sort_values('timestamp')
        
        # Translate Bulan untuk Judul
        bulan_dict = {'January': 'JANUARI', 'February': 'FEBRUARI', 'March': 'MARET', 'April': 'APRIL', 'May': 'MEI', 'June': 'JUNI', 'July': 'JULI', 'August': 'AGUSTUS', 'September': 'SEPTEMBER', 'October': 'OKTOBER', 'November': 'NOVEMBER', 'December': 'DESEMBER'}
        nama_bulan = bulan_dict.get(selected_date.strftime("%B"), selected_date.strftime("%B").upper())

        MIN_REFILL_TARGET = 160.0 # Patokan Anomali

        if selected_unit == "ALL UNITS":
            # --- LOGIKA BARU: GRAFIK BATANG PER SHIFT (CYAN & UNGU NEON) ---
            if 'shift' in df_trend.columns:
                # Group by tanggal operasional dan shift
                df_shift = df_trend.groupby(['operational_date', 'shift'])['quantity'].sum().reset_index()
                df_shift = df_shift.sort_values(['operational_date', 'shift']) # Pastikan urutan shift rapi
                df_shift['tanggal_str'] = pd.to_datetime(df_shift['operational_date']).dt.strftime('%d %b %Y')

                # --- UPDATE: KUNCI MATI WARNA & URUTAN KIRI-KANAN ---
                fig_trend = px.bar(
                    df_shift, x='operational_date', y='quantity', color='shift',
                    barmode='group', # Baris berdampingan
                    title=f"📈 TREN KONSUMSI SOLAR HARIAN PER SHIFT (BULAN {nama_bulan} {target_year})",
                    color_discrete_map={"SHIFT 1": "#00e5ff", "SHIFT 2": "#bc13fe"}, # PAKSA WARNA: S1=Cyan, S2=Ungu
                    category_orders={"shift": ["SHIFT 1", "SHIFT 2"]}, # PAKSA URUTAN: S1 Kiri, S2 Kanan
                    custom_data=['tanggal_str', 'shift']
                )

                fig_trend.update_traces(
                    hovertemplate='Tanggal: %{customdata[0]}<br>Shift: %{customdata[1]}<br>Total: %{y:,.0f} Liter<extra></extra>'
                )

                fig_trend.update_layout(
                    height=400, margin=dict(l=10, r=10, t=50, b=10),
                    template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)',
                    title_font_size=24,
                    xaxis=dict(title="Tanggal Operasional", title_font=dict(size=18), tickformat="%d %b"),
                    yaxis=dict(title="Volume (Liter)", title_font=dict(size=18)),
                    legend=dict(title="Shift", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
            else:
                st.warning("⚠️ Kolom 'shift' tidak ditemukan di data.")
                fig_trend = go.Figure()
        else:
            # --- LOGIKA LAMA: GRAFIK AREA + ANOMALI (KHUSUS 1 UNIT) ---
            df_trend['waktu_hover'] = df_trend['timestamp'].dt.strftime('%d %b %Y %H:%M')
            
            fig_trend = px.area(
                df_trend, x='timestamp', y='quantity', 
                title=f"📈 TREN KONSUMSI SOLAR - {selected_unit} (BULAN {nama_bulan} {target_year})",
                custom_data=['waktu_hover']
            )
            
            fig_trend.update_traces(
                mode='lines+markers', marker=dict(size=6, color='#00e5ff'), 
                line_color='#00e5ff', fillcolor='rgba(0, 229, 255, 0.2)',
                hovertemplate='Waktu Pengisian : %{customdata[0]}<br>Qty : %{y} Liter<extra></extra>'
            )

            # Layer Merah (Anomali) khusus untuk unit tersebut
            anomali_points = df_trend[df_trend['quantity'] < MIN_REFILL_TARGET].copy()
            if not anomali_points.empty:
                anomali_points['waktu_hover'] = anomali_points['timestamp'].dt.strftime('%d %b %Y %H:%M')
                fig_trend.add_trace(go.Scatter(
                    x=anomali_points['timestamp'], y=anomali_points['quantity'],
                    customdata=anomali_points[['waktu_hover']], 
                    mode='markers', name='Anomali Pengisian',
                    marker=dict(color='#ff4b4b', size=10, symbol='x', line=dict(width=2, color='white')),
                    hovertemplate='<b>Anomali Pengisian!</b><br>Waktu Pengisian : %{customdata[0]}<br>Qty : %{y} Liter<extra></extra>'
                ))

            fig_trend.update_layout(
                height=400, margin=dict(l=10, r=10, t=50, b=10), 
                template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)',
                title_font_size=24,
                xaxis=dict(title="Waktu Pengisian", title_font=dict(size=18), tickformat="%d %b %Y"),
                yaxis=dict(title="Volume (Liter)", title_font=dict(size=18)),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

        st.plotly_chart(fig_trend, use_container_width=True)

        # ========================================================
        # --- 2. DUAL ALERT BOX (DI TENGAH) ---
        # ========================================================
        df_early_refill = df_filtered[df_filtered['quantity'] < MIN_REFILL_TARGET].copy()
        
        df_filtered['hm_numeric'] = pd.to_numeric(df_filtered['hm'], errors='coerce').fillna(0)
        df_filtered = df_filtered.sort_values(['unit', 'timestamp'])
        df_filtered['hm_diff'] = df_filtered.groupby('unit')['hm_numeric'].diff()
        df_filtered = df_filtered.sort_values('timestamp')
        
        df_hm_anomali = df_filtered[df_filtered['hm_diff'].abs() > 30].copy()

        if (not df_early_refill.empty) or (not df_hm_anomali.empty):
            st.write("") 
            col_alert1, col_alert2 = st.columns(2)
            
            with col_alert1:
                if not df_early_refill.empty:
                    st.markdown(f"""
                    <div style="background-color: rgba(68, 17, 17, 0.8); border: 2px solid #ff4b4b; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 0 15px rgba(255, 75, 75, 0.3); height: 100%;">
                        <h3 style="color: #ff4b4b; margin: 0; font-size: 20px;">⚠️ PERINGATAN: TERDETEKSI PENGISIAN ANOMALI</h3>
                        <p style="color: #ffffff; font-size: 14px; margin-top: 5px;">
                            Terdeteksi <b>{len(df_early_refill)} kali</b> unit masuk pitstop dengan tangki fuel > {MIN_REFILL_TARGET} Liter.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_alert2:
                if not df_hm_anomali.empty:
                    st.markdown(f"""
                    <div style="background-color: rgba(68, 50, 17, 0.8); border: 2px solid #ffeb3b; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 0 15px rgba(255, 235, 59, 0.3); height: 100%;">
                        <h3 style="color: #ffeb3b; margin: 0; font-size: 20px;">⚠️ PERINGATAN: ANOMALI HOUR METER (HM)</h3>
                        <p style="color: #ffffff; font-size: 14px; margin-top: 5px;">
                            Terdeteksi <b>{len(df_hm_anomali)} kasus</b> lonjakan/penurunan HM tidak wajar (selisih > 30 jam).
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        # ========================================================
        # --- 3. GRAFIK PEMANTAUAN HM (SMART DYNAMIC CHART - FULL WIDTH) ---
        # ========================================================
        st.write("---")
        df_hm_trend = df_filtered[
            (df_filtered['timestamp'].dt.month == target_month) & 
            (df_filtered['timestamp'].dt.year == target_year)
        ].copy().sort_values(['unit', 'timestamp'])
        
        df_hm_trend = df_hm_trend[(df_hm_trend['hm_numeric'] > 0) & (df_hm_trend['hm_diff'].notna())]
        
        if not df_hm_trend.empty:
            df_hm_trend['waktu_hover'] = df_hm_trend['timestamp'].dt.strftime('%d %b %Y %H:%M')

            if selected_unit == "ALL UNITS":
                df_only_anomali = df_hm_trend[(df_hm_trend['hm_diff'].abs() > 30) | (df_hm_trend['hm_diff'] < 0)].copy()

                if not df_only_anomali.empty:
                    anomali_counts = df_only_anomali.groupby('unit').size().reset_index(name='jumlah_anomali')
                    anomali_counts = anomali_counts.sort_values('jumlah_anomali', ascending=True).tail(10) 

                    fig_hm = px.bar(
                        anomali_counts, x="jumlah_anomali", y="unit", orientation='h',
                        title=f"🚨 TOP 10 UNIT DENGAN HM ANOMALI (BULAN {nama_bulan} {target_year})",
                        text_auto=True, color_discrete_sequence=['#ffeb3b']
                    )
                    fig_hm.update_traces(hovertemplate='Unit : %{y}<br>Jumlah Error : %{x} Kali<extra></extra>')
                    fig_hm.update_layout(
                        height=400, margin=dict(l=10, r=10, t=50, b=10),
                        template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', title_font_size=24,
                        xaxis=dict(title="Total Kesalahan Input HM (Kali)"), yaxis=dict(title="No Lambung Unit")
                    )
                    st.plotly_chart(fig_hm, use_container_width=True)
                else:
                    st.success(f"✨ LUAR BIASA! Tidak ada anomali HM sama sekali di bulan {nama_bulan.capitalize()} {target_year}. Semua data akurat!")
            else:
                fig_hm = px.line(
                    df_hm_trend, x='timestamp', y='hm_numeric', markers=True,
                    title=f"⏱️ TREN PERGERAKAN HOUR METER - {selected_unit} (BULAN {nama_bulan} {target_year})",
                    custom_data=['waktu_hover', 'unit']
                )
                
                # --- UPDATE 1: PAKSA HOVER TAMPILKAN ANGKA MURNI TANPA K ---
                fig_hm.update_traces(
                    line=dict(width=3, color='#00e5ff'), marker=dict(size=8, color='#00e5ff'),
                    hovertemplate='Waktu: %{customdata[0]}<br>HM : %{y:.0f}<extra></extra>'
                )

                hm_anomali_points = df_hm_trend[(df_hm_trend['hm_diff'].abs() > 30) | (df_hm_trend['hm_diff'] < 0)]
                if not hm_anomali_points.empty:
                    # --- UPDATE 2: PAKSA HOVER ANOMALI TAMPILKAN ANGKA MURNI ---
                    fig_hm.add_trace(go.Scatter(
                        x=hm_anomali_points['timestamp'], y=hm_anomali_points['hm_numeric'],
                        customdata=hm_anomali_points[['waktu_hover', 'unit', 'hm_diff']],
                        mode='markers', name='Anomali HM',
                        marker=dict(color='#ffeb3b', size=14, symbol='x', line=dict(width=2, color='white')),
                        hovertemplate='<b>⚠️ ANOMALI HM!</b><br>Waktu: %{customdata[0]}<br>HM: %{y:.0f}<br>Selisih: %{customdata[2]:.0f} Jam<extra></extra>'
                    ))
                    
                fig_hm.update_layout(
                    height=400, margin=dict(l=10, r=10, t=50, b=10),
                    template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', title_font_size=24,
                    xaxis=dict(title="Tanggal Pengisian", tickformat="%d %b %Y"), 
                    # --- UPDATE 3: PAKSA SUMBU Y MURNI ANGKA TANPA K ---
                    yaxis=dict(title="Nilai HM", tickformat=".0f"), 
                    showlegend=False
                )
                st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("📉 Tidak ada data HM yang valid untuk bulan/unit ini.")

        # ========================================================
        # --- 4. BARIS BARU: TOP 5 TERBOROS & DAFTAR PELANGGAR 160L ---
        # ========================================================
        st.write("---")
        col_boros, col_pelanggar = st.columns([1, 1]) # Dibagi rata kiri-kanan
        
        with col_boros:
            df_boros = df_perf_global.nlargest(5, 'l_hr').sort_values('l_hr', ascending=True)
            fig_boros = px.bar(
                df_boros, x="l_hr", y="unit", orientation='h', 
                title="🔥 TOP 5 UNIT TERBOROS", 
                color_discrete_sequence=['#ff4b4b'], text_auto='.1f'
            )
            fig_boros.update_traces(hovertemplate='Fuel Cons : %{x:.1f} L/Hour<br>Unit : %{y}<extra></extra>')
            fig_boros.update_layout(
                height=350, margin=dict(l=10, r=10, t=50, b=10), 
                template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', title_font_size=20,
                xaxis=dict(title="Liter/Jam"), yaxis=dict(title="Unit")
            )
            st.plotly_chart(fig_boros, use_container_width=True)

        with col_pelanggar:
            st.markdown('<p style="font-size: 20px; color: #ff4b4b; font-weight: bold; text-align: center; margin-bottom: 15px; margin-top: 10px;">📋 DAFTAR UNIT REFUELING DIBAWAH 160L</p>', unsafe_allow_html=True)
            
            if not df_early_refill.empty:
                df_show = df_early_refill[['timestamp', 'unit', 'quantity']].copy()
                df_show = df_show.sort_values('timestamp', ascending=False)
                df_show['Waktu'] = df_show['timestamp'].dt.strftime('%d %b, %H:%M')
                df_show = df_show.rename(columns={'unit': 'No Unit', 'quantity': 'Isi (L)'})
                
                st.dataframe(df_show[['Waktu', 'No Unit', 'Isi (L)']], use_container_width=True, hide_index=True, height=300)
            else:
                st.success("✅ Tidak ada unit yang melanggar batas minimum pengisian.")

        # ========================================================
        # --- 5. BARIS BARU: TRAFFIC ANTREAN & JAM DIGITAL ---
        # ========================================================
        st.write("---")
        col_traffic, col_clock = st.columns([3, 1]) # Porsi 3 untuk grafik antrean, 1 untuk jam
        
        with col_traffic:
            c_prev, c_date, c_next = st.columns([1, 4, 1])
            with c_prev:
                if st.button("⬅️ Prev", use_container_width=True): 
                    st.session_state.filter_date -= pd.Timedelta(days=1); st.rerun()
            with c_next:
                if st.button("Next ➡️", use_container_width=True): 
                    st.session_state.filter_date += pd.Timedelta(days=1); st.rerun()
            
            with c_date:
                hari_dict = {'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu', 'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'}
                bulan_dict = {'January': 'Januari', 'February': 'Februari', 'March': 'Maret', 'April': 'April', 'May': 'Mei', 'June': 'Juni', 'July': 'Juli', 'August': 'Agustus', 'September': 'September', 'October': 'Oktober', 'November': 'November', 'December': 'Desember'}
                
                eng_day = selected_date.strftime("%A")
                eng_month = selected_date.strftime("%B")
                tgl_angka = selected_date.day
                tahun = selected_date.year
                indo_str = f"{hari_dict.get(eng_day, eng_day)}, {tgl_angka} {bulan_dict.get(eng_month, eng_month)} {tahun}"
                
                st.markdown(f"<h3 style='text-align: center; color: #00e5ff; margin: 0; font-size: 20px; padding-bottom: 10px;'>{indo_str}</h3>", unsafe_allow_html=True)

            df_daily = df[df['timestamp'].dt.date == selected_date].copy()
            if not df_daily.empty:
                df_daily['jam'] = df_daily['timestamp'].dt.hour
                hourly_counts = df_daily.groupby('jam').size().reset_index(name='jumlah').sort_values('jam')
                hourly_counts['jam_label'] = hourly_counts['jam'].apply(lambda x: f"{x:02d}:00")
                
                fig_daily = px.bar(hourly_counts, x='jam_label', y='jumlah', title=f"📊 TRAFFIC ANTREAN", text_auto=True, labels={'jam_label': 'Jam', 'jumlah': 'Unit'})
                fig_daily.update_traces(marker_color='#00e5ff', width=0.6)
                fig_daily.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20), template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', title_font_size=20, xaxis=dict(type='category'))
                st.plotly_chart(fig_daily, use_container_width=True)
            else:
                st.info(f"💤 Tidak ada data pada {indo_str}.")

        with col_clock:
            st.write(""); st.write("") 
            html_clock = """<div class="clock-card" style="margin-top: 50px; padding: 15px;"><p style="color: #888; font-size: 12px; margin-bottom: 5px;"> DURASI REFUELING</p><div class="digital-font" style="font-size: 30px;">08:00</div><p style="font-size: 14px; color: #00e5ff;">MENIT / UNIT</p></div>"""
            st.markdown(html_clock, unsafe_allow_html=True)
            st.markdown("""<div style="text-align: center; color: #aaa; font-size: 11px; margin-top: 10px;"><i>*Durasi refueling diambil dari hasil observasi ketika unit masuk bays s/d keluar bays.</i></div>""", unsafe_allow_html=True)

# ==========================================
# REVISI LANGKAH 7: RIWAYAT LOGSHEET (FIX HM, HEADER & CENTER ALIGN)
# ==========================================
    with tab2:
        # Judul Bagian Tabel (Menyala & Tebal)
        st.markdown("""
        <h3 style='text-align: center; color: #00e5ff; font-weight: 900; 
                   text-transform: uppercase; letter-spacing: 2px;
                   text-shadow: 0 0 15px rgba(0, 229, 255, 0.9); margin-bottom: 20px;'>
            📋 RIWAYAT LOGSHEET (7 HARI TERAKHIR)
        </h3>
        """, unsafe_allow_html=True)
        
        if not df_filtered.empty:
            # 1. FILTER 7 HARI TERAKHIR
            max_ts = df_filtered['timestamp'].max()
            cutoff_date = max_ts - pd.Timedelta(days=7)
            
            df_show = df_filtered[df_filtered['timestamp'] >= cutoff_date].copy()
            df_show = df_show.sort_values(by='timestamp', ascending=False)
            
            # 2. FORMAT TANGGAL
            df_show['timestamp'] = df_show['timestamp'].dt.strftime('%d/%m/%Y %H:%M')
            
            # 3. BUANG KOLOM TEKNIS SEBELUM DITAMPILKAN
            cols_to_hide = ['device', 'status', 'is_anomali', 'operational_date', 'hm_numeric', 'hm_diff']
            existing_cols = [c for c in cols_to_hide if c in df_show.columns]
            df_show = df_show.drop(columns=existing_cols)
            
            # 4. MEMBUAT HEADER JADI CAPSLOCK
            df_show.columns = df_show.columns.str.upper()
            
            # 5. STYLING TABEL (PAKSA RATA TENGAH UNTUK HEADER & ISI)
            styled_df = df_show.style.format({
                'QUANTITY': '{:.0f}'  # Quantity dibulatkan
            }).set_properties(**{
                'text-align': 'center', 
                'font-weight': 'bold',
                'background-color': '#0d1b2a',
                'color': '#ffffff',
                'border-color': '#1b263b'
            }).set_table_styles([
                # Styling khusus Header (Warna Hijau Neon & Center)
                {'selector': 'th', 'props': [
                    ('background-color', '#1b263b'),
                    ('color', '#39ff14'),   # HIJAU NEON
                    ('font-weight', '900'), 
                    ('text-align', 'center !important'), # PAKSA HEADER TENGAH
                    ('border', '1px solid #39ff14'),
                    ('text-transform', 'uppercase'),
                    ('font-size', '16px')
                ]},
                # Styling khusus Isi Kolom (Sel Data)
                {'selector': 'td', 'props': [
                    ('text-align', 'center !important')  # PAKSA ISI TENGAH
                ]}
            ])
            
            # 6. TAMPILKAN TABEL GLOWING
            st.dataframe(
                styled_df, 
                use_container_width=True, 
                height=600, 
                hide_index=True
            )
            
            st.caption(f"ℹ️ Menampilkan data operasional dari {cutoff_date.strftime('%d/%m/%Y')} s/d {max_ts.strftime('%d/%m/%Y')}.")
            
        else:
            st.info("📭 Data tidak tersedia.")

# --- BAGIAN ERROR HANDLING ---
else:
    st.warning("Menunggu data... Pastikan Google Sheet Anda dapat diakses publik (CSV Mode).")
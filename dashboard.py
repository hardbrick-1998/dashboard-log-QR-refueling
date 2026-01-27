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
# REVISI LANGKAH 2: CUSTOM CSS
# ==========================================
st.markdown("""
    <style>
    .main { background-color: #0d1b2a; color: #00e5ff; }
    .main-title {
        text-align: center; color: #ffffff; font-size: 38px;
        font-weight: bold; text-shadow: 0 0 10px #00e5ff;
        margin-bottom: 25px; 
        margin-top: -10px; /* <--- KURANGI DARI -30px AGAR TIDAK KEPOTONG */
    }
    div[data-testid="stMetric"] {
        background-color: #1b263b; border: 1px solid #00e5ff;
        padding: 10px; border-radius: 8px; box-shadow: 0 0 8px #00e5ff;
    }
    /* LONGGARKAN JARAK ATAS CONTAINER */
    .block-container { padding-top: 4rem; } 
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# REVISI LANGKAH 3: KONEKSI DATA & PEMBERSIHAN
# ==========================================

# --- ALAMAT GUDANG DATA ---
SHEET_ID = "1NN_rGKQBZzhUIKnfY1aOs1gvCP2aFiVo6j1RFagtb4s"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        # 1. Tarik data mentah dari CSV
        df = pd.read_csv(CSV_URL) 
        
        # 2. Bersihkan nama kolom (Lowercase & Buang Spasi)
        df.columns = df.columns.str.lower().str.strip()
        
        # 3. Mapping Nama Kolom agar seragam
        rename_map = {
            'timestamp': 'timestamp', 'kode unit': 'unit', 
            'lokasi': 'location', 'quantity': 'quantity', 'hm': 'hm'
        }
        df.rename(columns=rename_map, inplace=True)
        
        # 4. Hapus baris sampah yang benar-benar kosong
        df = df.dropna(subset=['unit', 'quantity'], how='all')

        # 5. LOGIKA FLEKSIBEL TIMESTAMP (Solusi MM/DD vs DD/MM)
        if 'timestamp' in df.columns:
            # Simpan data asli dalam bentuk string untuk diproses
            raw_ts = df['timestamp'].astype(str)
            
            # Tahap A: Coba format Day-First (Indo: 31/12/2025)
            df['timestamp'] = pd.to_datetime(raw_ts, dayfirst=True, errors='coerce')
            
            # Tahap B: Cari yang masih gagal (NaT) dan coba format Month-First (US: 12/31/2025)
            mask_failed = df['timestamp'].isna()
            if mask_failed.any():
                df.loc[mask_failed, 'timestamp'] = pd.to_datetime(
                    raw_ts[mask_failed], dayfirst=False, errors='coerce'
                )
            
            # Sortir data agar grafik tidak berantakan (Penting!)
            df = df.sort_values('timestamp').reset_index(drop=True)

        # 6. Standarisasi Tipe Data Numerik
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
        if 'hm' in df.columns:
            df['hm'] = pd.to_numeric(df['hm'], errors='coerce')
        if 'shift' in df.columns:
            df['shift'] = df['shift'].astype(str).str.upper().str.strip()
            
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

# Eksekusi penarikan data
df = load_data()

# ==========================================
# REVISI LANGKAH 4: FILTER UNIT & DATA LOGIC
# ==========================================
if not df.empty:
    # 1. Judul Dashboard
    st.markdown('<p class="main-title">DASHBOARD REFUELING PITSTOP 39</p>', unsafe_allow_html=True)

    # 2. Filter Dropdown & Tombol Refresh
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

    # 3. Logika Penyaringan Data
    df_filtered = df if selected_unit == "ALL UNITS" else df[df['unit'] == selected_unit]
    
    if df_filtered.empty:
        st.warning("⚠️ Tidak ada data untuk unit yang dipilih.")
        st.stop()

    # 4. FUNGSI ANALISA PERFORMA (INDIVIDUAL PER UNIT) 
    def get_performance_df(data_source):
        """Menghitung L/Hr dan Avg Pengisian Harian per Unit"""
        active_units = data_source['unit'].unique()
        performance_data = []
        
        for unit in active_units:
            u_data = data_source[data_source['unit'] == unit]
            
            # A. Kalkulasi L/Hr
            duration = (u_data['timestamp'].max() - u_data['timestamp'].min()).total_seconds() / 3600
            l_hr = u_data['quantity'].sum() / duration if duration > 0 else 0
            
            # B. Kalkulasi Pengisian per Hari (Individual)
            num_days_unit = u_data['timestamp'].dt.date.nunique()
            refills_day = len(u_data) / num_days_unit if num_days_unit > 0 else 0
            
            performance_data.append({
                'unit': unit, 
                'l_hr': l_hr, 
                'refills_day': refills_day
            })
        
        return pd.DataFrame(performance_data)

    # --- EKSEKUSI KALKULASI ---
    
    # Performa Global (Untuk Grafik Top 5)
    df_perf_global = get_performance_df(df)
    
    # Performa Terfilter (Untuk Metric Cards)
    df_perf_filtered = get_performance_df(df_filtered)

    # --- RATA-RATA DARI RATA-RATA (AVERAGE OF AVERAGES) ---
    if not df_perf_filtered.empty:
        # Kita ambil rata-rata dari kolom hasil perhitungan per unit
        avg_l_per_hr = df_perf_filtered['l_hr'][df_perf_filtered['l_hr'] > 0].mean()
        avg_refills_per_day = df_perf_filtered['refills_day'].mean()
    else:
        avg_l_per_hr = 0
        avg_refills_per_day = 0

    # 5. METRIK PENDUKUNG
    total_qty = df_filtered['quantity'].sum()
    total_trx = len(df_filtered)
    last_update_raw = df_filtered['timestamp'].max()
    last_update_str = last_update_raw.strftime('%d %b, %H:%M') if pd.notnull(last_update_raw) else "-"
    
    # Target Efisiensi
    achievement_rate = (1 - 0.1017) * 100
    
# ==========================================
# REVISI LANGKAH 5: METRIC CARDS (5 KOLOM)
# ==========================================
    # Memberikan sedikit ruang napas di bawah filter
    st.write("") 

    # Membuat 5 kolom untuk baris ringkasan (Summary)
    # 
    c1, c2, c3, c4, c5 = st.columns(5)
    
    # Kartu 1: Total Volume Solar
    c1.metric("Total Pemakaian Solar", f"{total_qty:,.0f} L")
    
    # Kartu 2: Total Pengisian (Kumulatif)
    c2.metric("Total Transaksi Refueling", f"{total_trx} Kali")
    
    # --- KARTU BARU: RATA-RATA PENGISIAN PER HARI ---
    # Menampilkan variabel 'avg_refills_per_day' yang dihitung di Langkah 4
    c3.metric("Refueling Activity", f"{avg_refills_per_day:.1f} Kali/Hari")
    
    # Kartu 4: Performa Unit (Average of Averages)
    c4.metric("Fuel Consumption", f"{avg_l_per_hr:.1f} L/Hr")
    
    # Kartu 5: Status Waktu Terakhir
    c5.metric("Update Terakhir", last_update_str)

    st.write("---")
    
    # Sistem Tab untuk navigasi Visual vs Tabel Data
    tab1, tab2 = st.tabs(["📊 RINGKASAN VISUAL", "📋 LOGSHEET KESELURUHAN"])

# ==========================================
# REVISI LANGKAH 6: VISUALISASI GRAFIK (TAB 1)
# ==========================================
    with tab1: 
        # --- BARIS 1: TREN DETAIL (FILTERED) & GLOBAL TOP TERBOROS (LOCKED) ---
        row1_c1, row1_c2 = st.columns([1.5, 1])

        with row1_c1:
            # 1. Tren Konsumsi Detail (Mengikuti Filter)
            df_trend = df_filtered.copy().sort_values('timestamp')
            fig_trend = px.area(
                df_trend, 
                x='timestamp', 
                y='quantity', 
                title="📈 Tren Konsumsi Solar (Detail per Waktu)",
                hover_data={'timestamp': '|%d %b %Y, %H:%M'}
            )
            fig_trend.update_traces(
                mode='lines+markers', 
                line_color='#00e5ff', 
                fillcolor='rgba(0, 229, 255, 0.2)',
                marker=dict(size=6)
            )
            fig_trend.update_layout(
                height=350, margin=dict(l=10, r=10, t=80, b=10), 
                template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title="Waktu Pengisian", tickformat="%H:%M\n%d %b %Y", tickangle=0)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        with row1_c2:
            # 2. GRAFIK TOP 5 UNIT TERBOROS (BERDASARKAN L/HR)
            # Ambil 5 unit dengan l_hr tertinggi dari data global
            df_boros = df_perf_global.nlargest(5, 'l_hr').sort_values('l_hr', ascending=True)
            
            fig_boros = px.bar(
                df_boros, 
                x="l_hr", 
                y="unit", 
                orientation='h', 
                title="🔥 Top 5 Unit Terboros (Avg L/Hr)", 
                color_discrete_sequence=['#ff4b4b'], # Warna merah untuk indikasi boros
                text_auto='.1f' # Menampilkan angka L/Hr di ujung batang
            )
            
            fig_boros.update_layout(
                height=350, 
                margin=dict(l=10, r=10, t=80, b=10), 
                template="plotly_dark", 
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Average Liter per Hour",
                yaxis_title="No Lambung Unit"
            )
            st.plotly_chart(fig_boros, use_container_width=True)

        # --- BARIS 2: SPEEDOMETER EFISIENSI (FILTERED) ---
        st.write("---")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = achievement_rate,
            gauge = {
                'axis': {'range': [80, 100], 'tickcolor': "#00e5ff"},
                'bar': {'color': "#00e5ff"}, 'bgcolor': "#1b263b",
                'threshold': {'line': {'color': "red", 'width': 4}, 'value': 99.9}
            },
            title = {'text': "Pencapaian Efisiensi (%)", 'font': {'color': "#00e5ff", 'size': 18}}
        ))
        
        fig_gauge.update_layout(
            height=350, margin=dict(l=20, r=20, t=120, b=20), 
            paper_bgcolor='rgba(0,0,0,0)', font={'color': "#00e5ff"}
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

# ==========================================
# REVISI LANGKAH 7: TABEL DETAIL (TAB 2)
# ==========================================
    with tab2:
        st.subheader("📋 Riwayat Lengkap Logsheet (Terfilter)")
        
        # Sortir berdasarkan waktu terbaru
        df_full = df_filtered.sort_values(by='timestamp', ascending=False).copy()
        
        # Ubah format tampilan tanggal agar terbaca di tabel
        df_full['timestamp'] = df_full['timestamp'].dt.strftime('%d/%m/%Y %H:%M:%S')
        
        # Tampilkan tabel tanpa Index asli agar urutannya tidak melompat
        st.dataframe(df_full, use_container_width=True, height=600, hide_index=True)

else:
    st.warning("Menunggu data... Pastikan Google Sheet Anda dapat diakses publik (CSV Mode).")
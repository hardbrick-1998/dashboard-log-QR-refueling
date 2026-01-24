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

# --- ALAMAT GUDANG DATA (WAJIB ADA) ---
SHEET_ID = "1NN_rGKQBZzhUIKnfY1aOs1gvCP2aFiVo6j1RFagtb4s"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        # Sekarang CSV_URL di bawah ini sudah punya "definisi"
        df = pd.read_csv(CSV_URL) 
        
        # 1. Bersihkan nama kolom
        df.columns = df.columns.str.lower().str.strip()
        
        # 2. Mapping Nama Kolom
        rename_map = {
            'timestamp': 'timestamp', 'kode unit': 'unit', 
            'lokasi': 'location', 'quantity': 'quantity', 'hm': 'hm'
        }
        df.rename(columns=rename_map, inplace=True)
        
        # 3. Hapus baris kosong
        df = df.dropna(subset=['unit', 'quantity'], how='all')
        
        # 4. Paksa format Tanggal dd/mm/yyyy hh:mm:ss
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True, errors='coerce')
            
        # 5. Standarisasi Tipe Data
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
        if 'shift' in df.columns:
            df['shift'] = df['shift'].astype(str).str.upper().str.strip()
            
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

# Panggil fungsinya
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
        st.write(" ")
        st.write(" ") 
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # 3. Logika Penyaringan Data
    df_filtered = df if selected_unit == "ALL UNITS" else df[df['unit'] == selected_unit]
    
    if df_filtered.empty:
        st.warning("⚠️ Tidak ada data untuk unit yang dipilih.")
        st.stop()

    # 4. FUNGSI ANALISA PERFORMA (L/HR) INDIVIDUAL
    def get_performance_df(data_source):
        """Menghitung L/Hr untuk setiap unit dalam dataset yang diberikan"""
        active_units = data_source['unit'].unique()
        performance_data = []
        
        for unit in active_units:
            u_data = data_source[data_source['unit'] == unit]
            # Hitung durasi (Max - Min Timestamp)
            duration = (u_data['timestamp'].max() - u_data['timestamp'].min()).total_seconds() / 3600
            
            if duration > 0:
                total_liter = u_data['quantity'].sum()
                rate = total_liter / duration
                performance_data.append({'unit': unit, 'l_hr': rate})
        
        return pd.DataFrame(performance_data)

    # --- EKSEKUSI DATA PERFORMA ---
    
    # A. Performa Global (Untuk Grafik Top 5 Terboros - Selalu ALL DATA)
    df_perf_global = get_performance_df(df)
    
    # B. Performa Terfilter (Untuk Kartu Metrik Avg L/Jam Unit)
    df_perf_filtered = get_performance_df(df_filtered)
    
    # Hitung nilai rata-rata untuk kartu metrik (Average of Averages)
    if not df_perf_filtered.empty:
        avg_l_per_hr = df_perf_filtered['l_hr'].mean()
    else:
        avg_l_per_hr = 0

    # 5. METRIK PENDUKUNG LAINNYA
    total_qty = df_filtered['quantity'].sum()
    total_trx = len(df_filtered)
    
    # Ambil waktu terakhir
    last_update_raw = df_filtered['timestamp'].max()
    last_update_str = last_update_raw.strftime('%d %b, %H:%M') if pd.notnull(last_update_raw) else "-"
    
    # Perhitungan Efisiensi (Dummy Target)
    anomali_rate = 0.1017 
    achievement_rate = (1 - anomali_rate) * 100
    
    

# ==========================================
# REVISI LANGKAH 5: METRIC CARDS & TAB SYSTEM
# ==========================================
    # Beri sedikit ruang antara filter dan kartu
    st.write("") 

    # Baris Kartu Ringkasan (Summary) 
    c1, c2, c3, c4 = st.columns(4)
    
    # Kartu 1: Total Volume
    c1.metric("Total Solar", f"{total_qty:,.0f} L")
    
    # Kartu 2: TOTAL PENGISIAN (Perubahan Satuan ke 'Kali')
    c2.metric("Total Pengisian", f"{total_trx} Kali") 
    
    # Kartu 3: Performa Unit
    c3.metric("Avg L/Jam Unit", f"{avg_l_per_hr:.1f} L/Hr")
    
    # Kartu 4: Status Terakhir
    c4.metric("Update Terakhir", last_update_str)

    st.write("---")
    
    # Sistem Tab untuk memisahkan Visual dan Data
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
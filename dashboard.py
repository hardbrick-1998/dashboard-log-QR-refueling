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
    # 1. Judul Dashboard Paling Atas (Tengah)
    st.markdown('<p class="main-title">DASHBOARD REFUELING PITSTOP 39</p>', unsafe_allow_html=True)

    # 2. Letakkan Filter & Tombol Refresh berdampingan
    # Membuat 2 kolom: kolom_kiri untuk filter, kolom_kanan untuk tombol
    col_filter, col_btn = st.columns([4, 1]) 

    with col_filter:
        unit_list = sorted(df['unit'].unique().tolist())
        filter_options = ["ALL UNITS"] + unit_list
        selected_unit = st.selectbox(
            "🔍 Filter No Lambung Unit:", 
            options=filter_options, 
            index=0
        )

    with col_btn:
        st.write(" ") # Memberi jarak atas agar tombol sejajar dengan filter
        st.write(" ") 
        # Tombol Refresh untuk membersihkan cache dan menarik data terbaru
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear() # Membersihkan cache
            st.rerun() # Menjalankan ulang aplikasi

    # 3. Logika Penyaringan Data
    if selected_unit == "ALL UNITS":
        df_filtered = df
    else:
        df_filtered = df[df['unit'] == selected_unit]
    
    # Proteksi tambahan
    if df_filtered.empty:
        st.warning("⚠️ Tidak ada data untuk unit yang dipilih.")
        st.stop()

    # 4. Kalkulasi Metrik (Berdasarkan df_filtered)
    total_qty = df_filtered['quantity'].sum()
    total_trx = len(df_filtered)
    
    # NaT Check untuk Last Update
    last_update_raw = df_filtered['timestamp'].max()
    last_update_str = last_update_raw.strftime('%d %b, %H:%M') if pd.notnull(last_update_raw) else "-"
    
    # Kalkulasi Liter/Jam
    duration_hrs = (df_filtered['timestamp'].max() - df_filtered['timestamp'].min()).total_seconds() / 3600
    avg_l_per_hr = total_qty / duration_hrs if duration_hrs > 0 else 0
    
    # Achievement Rate
    anomali_rate = 0.1017 
    achievement_rate = (1 - anomali_rate) * 100
    
    

# ==========================================
# REVISI LANGKAH 5: METRIC CARDS & TAB SYSTEM
# ==========================================
    # Beri sedikit ruang antara filter dan kartu
    st.write("") 

    # Baris Kartu Ringkasan (Summary)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Solar", f"{total_qty:,.0f} L")
    c2.metric("Total Transaksi", f"{total_trx} Trx")
    c3.metric("Avg L/Jam Unit", f"{avg_l_per_hr:.1f} L/Hr")
    c4.metric("Update Terakhir", last_update_str)

    st.write("---")
    
    # Sistem Tab untuk memisahkan Visual dan Data
    tab1, tab2 = st.tabs(["📊 RINGKASAN VISUAL", "📋 LOGSHEET KESELURUHAN"])

# ==========================================
# REVISI LANGKAH 6: VISUALISASI GRAFIK (TAB 1)
# ==========================================
    with tab1: # <--- WAJIB TAMBAHKAN INI AGAR GRAFIK MASUK KE TAB 1
        # --- BARIS 1: TREN (FILTERED) & GLOBAL TOP UNIT (LOCKED) ---
        row1_c1, row1_c2 = st.columns([1.5, 1])

        with row1_c1:
            # Tren Harian (Mengikuti Filter)
            df_daily = df_filtered.copy()
            df_daily['date_only'] = df_daily['timestamp'].dt.date
            df_daily = df_daily.groupby('date_only')['quantity'].sum().reset_index()
            
            fig_trend = px.area(df_daily, x='date_only', y='quantity', title="Tren Konsumsi Harian (Terfilter)")
            fig_trend.update_traces(mode='lines+markers', line_color='#00e5ff', fillcolor='rgba(0, 229, 255, 0.2)')
            fig_trend.update_layout(height=300, margin=dict(l=10, r=10, t=80, b=10), template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_trend, use_container_width=True)

        with row1_c2:
            # Global Top 5 Unit (TERKUNCI KE ALL DATA - menggunakan 'df' asli)
            df_top_global = df.groupby("unit")["quantity"].sum().nlargest(5).reset_index()
            fig_top_all = px.bar(df_top_global, x="quantity", y="unit", orientation='h', 
                                 title="🏆 Global Top 5 Unit (All Data)", color_discrete_sequence=['#00e5ff'])
            fig_top_all.update_layout(height=300, margin=dict(l=10, r=10, t=80, b=10), template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_top_all, use_container_width=True)

        # --- BARIS 2: SPEEDOMETER (FILTERED) ---
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
        # Margin 't' (top) 120 agar judul "Pencapaian Efisiensi" tidak kepotong
        fig_gauge.update_layout(height=350, margin=dict(l=20, r=20, t=120, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'color': "#00e5ff"})
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
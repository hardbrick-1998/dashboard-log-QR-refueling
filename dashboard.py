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
SHEET_ID = "1NN_rGKQBZzhUIKnfY1aOs1gvCP2aFiVo6j1RFagtb4s"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        # 1. Bersihkan nama kolom dari spasi dan jadikan huruf kecil
        df.columns = df.columns.str.lower().str.strip()
        
        # 2. KAMUS PENERJEMAH KOLOM (Pastikan nama di kiri sesuai yang ada di Sheet)
        rename_map = {
            'kode unit': 'unit', 'unit id': 'unit', 'kode_unit': 'unit',
            'qty': 'quantity', 'liter': 'quantity', 'jumlah': 'quantity',
            'date': 'timestamp', 'tanggal': 'timestamp', 'waktu': 'timestamp', 
            'tanggal aktual': 'timestamp', 'timestamp': 'timestamp',
            'hours meter': 'hm', 'hour meter': 'hm', 'hm': 'hm' # Tambahkan ini agar HM terbaca
        }
        df.rename(columns=rename_map, inplace=True)
        
        # 3. Konversi Tipe Data (Handle NaT/None secara aman)
        if 'timestamp' in df.columns:
            # Menggunakan format dayfirst=True jika tanggal di sheet Mas Faiz formatnya DD/MM/YYYY
            df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True, errors='coerce')
            
        if 'shift' in df.columns:
            df['shift'] = df['shift'].astype(str).str.upper().str.strip()
            
        if 'quantity' in df.columns:
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
            
        if 'hm' in df.columns:
            df['hm'] = pd.to_numeric(df['hm'], errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

df = load_data()

# ==========================================
# REVISI LANGKAH 4: FILTER & KALKULASI METRIK
# ==========================================
if not df.empty:
    st.sidebar.header("🕹️ Control Panel")
    all_units = sorted(df['unit'].unique().tolist())
    selected_units = st.sidebar.multiselect("Pilih No Lambung Unit:", options=all_units, default=all_units)
    
    df_filtered = df[df['unit'].isin(selected_units)]
    
    if not df_filtered.empty:
        total_qty = df_filtered['quantity'].sum()
        total_trx = len(df_filtered)
        
        # Penanganan Error NaT: Cek apakah ada tanggal yang valid
        last_update_raw = df_filtered['timestamp'].max()
        # Jika NaT, maka tampilkan "-"
        last_update_str = last_update_raw.strftime('%H:%M') if pd.notnull(last_update_raw) else "-"
        
        # Kalkulasi Liter/Jam
        duration_hrs = (df_filtered['timestamp'].max() - df_filtered['timestamp'].min()).total_seconds() / 3600
        avg_l_per_hr = total_qty / duration_hrs if duration_hrs > 0 else 0
        
        # Achievement Rate
        anomali_rate = 0.1017 
        achievement_rate = (1 - anomali_rate) * 100
    else:
        st.warning("⚠️ Silakan pilih minimal satu unit di sidebar.")
        st.stop()
    

# ==========================================
# REVISI LANGKAH 5: HEADER & METRIC CARDS
# ==========================================
    st.markdown('<p class="main-title">DASHBOARD REFUELING PITSTOP 39</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📊 RINGKASAN VISUAL", "📋 LOGSHEET KESELURUHAN"])

    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Solar", f"{total_qty:,.0f} L")
        c2.metric("Total Unit", f"{total_trx} Trx")
        c3.metric("Avg L/Jam Unit", f"{avg_l_per_hr:.1f} L/Hr")
        c4.metric("Last Update", last_update_str) # <--- MENGGUNAKAN VARIABEL YANG SUDAH AMAN

        st.write("---")

# ==========================================
# REVISI LANGKAH 6: VISUALISASI GRAFIK (TAB 1)
# ==========================================
        col_left, col_right = st.columns([1, 1.5])

        with col_left:
            # Gauge Achievement (Tetap sama, pastikan margin aman)
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = achievement_rate,
                gauge = {
                    'axis': {'range': [80, 100], 'tickcolor': "#00e5ff"},
                    'bar': {'color': "#00e5ff"}, 'bgcolor': "#1b263b",
                    'threshold': {'line': {'color': "red", 'width': 4}, 'value': 99.9}
                },
                title = {'text': "Pencapaian Efisiensi (%)", 'font': {'color': "#00e5ff", 'size': 16}}
            ))
            fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=120, b=10), 
                                    paper_bgcolor='rgba(0,0,0,0)', font={'color': "#00e5ff"})
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_right:
            # --- GRAFIK BARU: PEMAKAIAN PER TANGGAL ---
            # 1. Siapkan data harian
            df_daily = df_filtered.copy()
            df_daily['date_only'] = df_daily['timestamp'].dt.date
            df_daily = df_daily.groupby('date_only')['quantity'].sum().reset_index()
            
            # 2. Buat Grafik Area/Garis agar mirip Power BI
            fig_trend = px.area(df_daily, x='date_only', y='quantity', 
                                title="Tren Konsumsi Solar Harian (L)",
                                markers=True)
            
            # 3. Styling Futuristik
            fig_trend.update_traces(line_color='#00e5ff', fillcolor='rgba(0, 229, 255, 0.2)')
            fig_trend.update_layout(height=300, margin=dict(l=10, r=10, t=80, b=10), 
                                    template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)',
                                    xaxis_title="Tanggal", yaxis_title="Total Liter")
            
            st.plotly_chart(fig_trend, use_container_width=True)

        # Baris Peringkat Unit
        st.subheader("Top 5 Unit Pengisian Terbanyak")
        df_top = df_filtered.groupby("unit")["quantity"].sum().nlargest(5).reset_index()
        fig_top = px.bar(df_top, x="quantity", y="unit", orientation='h', 
                         color_discrete_sequence=['#00e5ff'])
        fig_top.update_layout(height=250, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_top, use_container_width=True)

# ==========================================
# REVISI LANGKAH 7: TABEL DETAIL (TAB 2)
# ==========================================
    with tab2:
        st.subheader("📋 Riwayat Lengkap Logsheet (Terfilter)")
        # Mengurutkan berdasarkan timestamp terbaru
        df_full = df_filtered.sort_values(by='timestamp', ascending=False).copy()
        
        # Pastikan kolom timestamp diformat string hanya jika datanya ada
        if not df_full['timestamp'].isna().all():
            df_full['timestamp'] = df_full['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Mengisi nilai HM yang kosong dengan "-" agar lebih rapi dilihat
        if 'hm' in df_full.columns:
            df_full['hm'] = df_full['hm'].fillna("-")

        st.dataframe(df_full, use_container_width=True, height=550)

else:
    st.warning("Menunggu data... Pastikan Google Sheet Anda dapat diakses publik (CSV Mode).")
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
# LANGKAH 2: CUSTOM CSS (TEMA FUTURISTIK & GLOW)
# ==========================================
st.markdown("""
    <style>
    .main { background-color: #0d1b2a; color: #00e5ff; }
    /* Judul Tengah Neon */
    .main-title {
        text-align: center; color: #ffffff; font-size: 38px;
        font-weight: bold; text-shadow: 0 0 10px #00e5ff;
        margin-bottom: 25px; margin-top: -30px;
    }
    /* Metric Card Glow */
    div[data-testid="stMetric"] {
        background-color: #1b263b; border: 1px solid #00e5ff;
        padding: 10px; border-radius: 8px; box-shadow: 0 0 8px #00e5ff;
    }
    label[data-testid="stMetricLabel"] { color: #00e5ff !important; font-size: 14px !important; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 24px !important; }
    .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# LANGKAH 3: KONEKSI DATA & PEMBERSIHAN (CLEANING)
# ==========================================
SHEET_ID = "1NN_rGKQBZzhUIKnfY1aOs1gvCP2aFiVo6j1RFagtb4s"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.lower().str.strip()
        
        # Mapping Nama Kolom (Solusi Timestamp 'None')
        rename_map = {
            'kode unit': 'unit', 'kode_unit': 'unit', 
            'qty': 'quantity', 'liter': 'quantity',
            'date': 'timestamp', 'tanggal': 'timestamp', 
            'tanggal aktual': 'timestamp'
        }
        df.rename(columns=rename_map, inplace=True)
        
        # Standarisasi Tipe Data
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        if 'shift' in df.columns:
            df['shift'] = df['shift'].astype(str).str.upper().str.strip()
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

df = load_data()

# ==========================================
# LANGKAH 4: KALKULASI METRIK & TARGET
# ==========================================
if not df.empty:
    total_qty = df['quantity'].sum()
    total_trx = len(df)
    
    # Hitung Liter/Jam
    duration_hrs = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
    avg_l_per_hr = total_qty / duration_hrs if duration_hrs > 0 else 0
    
    # Invert Gauge Achievement (Target 0.1% Anomali)
    anomali_rate = 0.1017 
    achievement_rate = (1 - anomali_rate) * 100

# ==========================================
# LANGKAH 5: HEADER & METRIC CARDS (BARIS ATAS)
# ==========================================
    st.markdown('<p class="main-title">DASHBOARD REFUELING PITSTOP 39</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📊 RINGKASAN VISUAL", "📋 LOGSHEET KESELURUHAN"])

    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Solar", f"{total_qty:,.0f} L")
        c2.metric("Total Unit", f"{total_trx} Trx")
        c3.metric("Rata-rata L/Jam", f"{avg_l_per_hr:.1f} L/Hr")
        c4.metric("Last Update", df['timestamp'].max().strftime('%H:%M'))

        st.write("---")

# ==========================================
# LANGKAH 6: VISUALISASI GRAFIK (TAB 1)
# ==========================================
        col_left, col_right = st.columns([1, 1.5])

        with col_left:
            # Gauge Achievement
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = achievement_rate,
                gauge = {
                    'axis': {'range': [80, 100], 'tickcolor': "#00e5ff"},
                    'bar': {'color': "#00e5ff"}, 'bgcolor': "#1b263b",
                    'threshold': {'line': {'color': "red", 'width': 4}, 'value': 99.9}
                },
                title = {'text': "Pencapaian Efisiensi (%)", 'font': {'color': "#00e5ff", 'size': 16}}
            ))
            fig_gauge.update_layout(height=240, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "#00e5ff"})
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_right:
            # Konsumsi per Shift
            df_shift = df.groupby("shift")["quantity"].sum().reset_index()
            fig_shift = px.bar(df_shift, x="shift", y="quantity", color="shift",
                               title="Total Liter per Shift",
                               color_discrete_map={"SHIFT 1": "#00e5ff", "SHIFT 2": "#d400ff"})
            fig_shift.update_layout(height=240, margin=dict(l=10, r=10, t=40, b=10), template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_shift, use_container_width=True)

        # Baris Bawah: Top 5 Unit
        st.subheader("Top 5 Unit Pengisian Terbanyak")
        df_top = df.groupby("unit")["quantity"].sum().nlargest(5).reset_index()
        fig_top = px.bar(df_top, x="quantity", y="unit", orientation='h', color_discrete_sequence=['#00e5ff'])
        fig_top.update_layout(height=200, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_top, use_container_width=True)

# ==========================================
# LANGKAH 7: TABEL DETAIL (TAB 2)
# ==========================================
    with tab2:
        st.subheader("📋 Riwayat Lengkap Logsheet")
        df_full = df.sort_values(by='timestamp', ascending=False).copy()
        df_full['timestamp'] = df_full['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        st.dataframe(df_full, use_container_width=True, height=550)

else:
    st.warning("Menunggu data... Pastikan Google Sheet Anda dapat diakses publik (CSV Mode).")
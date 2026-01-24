import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="DASHBOARD REFUELING - Pitstop 39", layout="wide")

# Tema Futuristik AlamTri
st.markdown("""
    <style>
    .main { background-color: #0d1b2a; color: #00e5ff; }
    .stMetric { 
        background-color: #1b263b; 
        border: 1px solid #00e5ff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 0 10px #00e5ff; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. AMBIL DATA (MODE CSV) ---
# Link Google Sheet Mas Faiz yang sudah dikonversi ke format export CSV
SHEET_ID = "1NN_rGKQBZzhUIKnfY1aOs1gvCP2aFiVo6j1RFagtb4s"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        
        # 1. Kecilkan semua nama kolom dan buang spasi di awal/akhir
        df.columns = df.columns.str.lower().str.strip()
        
        # 2. Mapping Manual (Pastikan 'kode unit' diubah jadi 'unit')
        # Tambahkan baris ini untuk memastikan kolom KODE UNIT terdeteksi
        rename_map = {
            'kode unit': 'unit', 
            'unit id': 'unit',
            'kode_unit': 'unit'
        }
        df.rename(columns=rename_map, inplace=True)
        
        # 3. Pembersihan Shift (Sesuai permintaan: Uppercase)
        if 'shift' in df.columns:
            df['shift'] = df['shift'].astype(str).str.upper().str.strip()
            
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

df = load_data()

# --- CEK DATA ---
if df.empty:
    st.warning("⚠️ Data kosong atau link CSV tidak dapat diakses.")
else:
    st.title("📊 Monitoring Refueling - Pitstop 39")
    
    # --- 3. LOGIKA GAUGE ACHIEVEMENT (INVERT) ---
    # Target Anomali 0.1%
    total_trx = len(df)
    # Contoh: Anggap data dengan 'KODE UNIT' tertentu sebagai anomali (sesuaikan logika Mas)
    # Di sini kita gunakan data Desember sebagai acuan
    anomali_rate = 0.1017 # Contoh data 10.17% dari Desember
    achievement_rate = (1 - anomali_rate) * 100

    # --- 4. DASHBOARD LAYOUT ---
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        st.metric("Total Solar Keluar", f"{df['quantity'].sum():,.0f} L")
        st.metric("Total Transaksi", f"{len(df)} Unit")
    
    with col_b:
        # Gauge Achievement Invert
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = achievement_rate,
            gauge = {
                'axis': {'range': [80, 100], 'tickcolor': "#00e5ff"},
                'bar': {'color': "#00e5ff"},
                'bgcolor': "#1b263b",
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 99.9 # Target 0.1% anomali
                }
            },
            title = {'text': "Efisiensi vs Target 0.1% Anomali", 'font': {'color': "#00e5ff"}}
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'color': "#00e5ff"})
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.divider()

    # --- 5. VISUALISASI UTAMA ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Konsumsi per Shift (Cleaned)")
        # Shift sekarang sudah rapi (SHIFT 1 & SHIFT 2 saja)
        df_shift = df.groupby("shift")["quantity"].sum().reset_index()
        fig_shift = px.bar(df_shift, x="shift", y="quantity", color="shift",
                           color_discrete_map={"SHIFT 1": "#00e5ff", "SHIFT 2": "#d400ff"})
        fig_shift.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_shift, use_container_width=True)

    with c2:
        st.subheader("Top 5 Unit Pengisian")
        df_top = df.groupby("unit")["quantity"].sum().nlargest(5).reset_index()
        fig_top = px.bar(df_top, x="quantity", y="unit", orientation='h', color_discrete_sequence=['#00e5ff'])
        fig_top.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_top, use_container_width=True)

    # Tabel Detail
    st.subheader("📋 Logsheet Detail")
    st.dataframe(df.sort_values(by='timestamp', ascending=False), use_container_width=True)
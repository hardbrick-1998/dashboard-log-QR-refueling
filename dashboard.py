import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard MACO", layout="wide")

# --- 1. AMBIL DATA DARI GOOGLE SHEETS API ---
# Masukkan Link Web App Google Script Bapak di sini:
API_URL = "https://script.google.com/macros/s/AKfycbwfHexkGPjRCiwxUpqaWKB6ExMfns_QSMTfbdtJIYC0XHSdxBC0bN0IQeTQJX_hDawaDQ/exec"

@st.cache_data(ttl=60) # Update data setiap 60 detik
def load_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            
            # --- PEMBERSIHAN DATA AGAR TIDAK ERROR ---
            # 1. Pastikan kolom quantity jadi angka
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
            
            # 2. Pastikan kolom timestamp jadi format waktu
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            # 3. Filter hanya data yang statusnya 'ALLOWED'
            # (Pastikan kolom 'status' ada di JSON Bapak, jika beda sesuaikan namanya)
            if 'status' in df.columns:
                 df = df[df['status'].str.contains('ALLOWED', case=False, na=False)]
            
            return df
        else:
            st.error("Gagal mengambil data dari API. Cek URL Web App.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Terjadi kesalahan koneksi: {e}")
        return pd.DataFrame()

# Load Data Awal
df = load_data()

# --- 2. JUDUL DASHBOARD ---
st.title("📊 MACO Refueling Dashboard")
st.markdown("Monitoring penggunaan bahan bakar **Pitstop 39** secara Real-Time.")
st.divider()

if not df.empty:
    # --- 3. FILTER SIDEBAR (Sebelah Kiri) ---
    st.sidebar.header("Filter Data")
    
    # Filter Unit
    all_units = sorted(df["unit"].unique())
    selected_units = st.sidebar.multiselect("Pilih Unit:", all_units, default=all_units)
    
    # Filter Shift (Opsional)
    all_shifts = df["shift"].unique()
    selected_shift = st.sidebar.multiselect("Pilih Shift:", all_shifts, default=all_shifts)

    # Terapkan Filter
    df_filtered = df[
        (df["unit"].isin(selected_units)) & 
        (df["shift"].isin(selected_shift))
    ]

    # --- 4. KARTU RINGKASAN (METRICS) ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_liter = df_filtered['quantity'].sum()
    total_transaksi = len(df_filtered)
    # Rata-rata pemakaian
    avg_liter = df_filtered['quantity'].mean() if total_transaksi > 0 else 0
    
    col1.metric("Total Solar Keluar", f"{total_liter:,.0f} L")
    col2.metric("Total Pengisian", f"{total_transaksi} Unit")
    col3.metric("Rata-rata per Unit", f"{avg_liter:,.0f} L")
    
    # Last Update (Ambil waktu paling baru di data)
    last_time = df_filtered['timestamp'].max()
    col4.metric("Data Terakhir", last_time.strftime('%d/%m %H:%M') if pd.notnull(last_time) else "-")

    st.markdown("---")

    # --- 5. GRAFIK VISUAL (Plotly) ---
    c1, c2 = st.columns((2, 1))

    with c1:
        st.subheader("Tren Harian Konsumsi Solar")
        # Group by Tanggal
        df_daily = df_filtered.groupby(df_filtered['timestamp'].dt.date)['quantity'].sum().reset_index()
        fig_trend = px.line(df_daily, x='timestamp', y='quantity', markers=True, 
                            title="Grafik Garis: Total Liter per Hari")
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        st.subheader("Perbandingan Shift")
        df_shift = df_filtered.groupby('shift')['quantity'].sum().reset_index()
        fig_pie = px.pie(df_shift, values='quantity', names='shift', 
                         title="Proporsi Siang vs Malam", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- 6. TABEL DATA DETAIL ---
    st.subheader("Riwayat Logsheet Lengkap")
    # Tampilkan tabel yang bisa di-sort
    st.dataframe(
        df_filtered[['timestamp', 'shift', 'unit', 'location', 'quantity', 'hm']].sort_values(by='timestamp', ascending=False),
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("Menunggu data... Pastikan URL API benar atau belum ada transaksi 'ALLOWED'.")
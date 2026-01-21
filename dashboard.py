import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Dashboard MACO", layout="wide")

# --- 1. AMBIL DATA ---
# GANTI DENGAN URL API WEB APP BAPAK
API_URL = "https://script.google.com/macros/s/AKfycbwfHexkGPjRCiwxUpqaWKB6ExMfns_QSMTfbdtJIYC0XHSdxBC0bN0IQeTQJX_hDawaDQ/exec"

@st.cache_data(ttl=60)
def load_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            
            # Ubah semua nama kolom jadi huruf kecil biar aman
            df.columns = df.columns.str.lower()
            
            # --- BAGIAN INI YANG SAYA REVISI ---
            # Mapping nama kolom (Kamus Penerjemah)
            rename_map = {
                'kode_unit': 'unit',  # <--- INI TAMBAHANNYA
                'unit id': 'unit', 'id unit': 'unit', 'unit_id': 'unit',
                'lokasi': 'location', 'loc': 'location',
                'hm': 'hm', 'hours meter': 'hm',
                'qty': 'quantity', 'liter': 'quantity',
                'shift': 'shift',
                'timestamp': 'timestamp', 'waktu': 'timestamp', 'date': 'timestamp'
            }
            
            # Ganti nama kolom sesuai kamus di atas
            df.rename(columns=rename_map, inplace=True)
            
            # Konversi Tipe Data (Pembersihan)
            if 'quantity' in df.columns:
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                
            return df
        else:
            st.error("Gagal koneksi ke API.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error Python: {e}")
        return pd.DataFrame()

df = load_data()

# --- 2. CEK DATA ---
if df.empty:
    st.warning("Data belum masuk atau API bermasalah.")
else:
    # --- 3. JUDUL ---
    st.title("📊 Monitoring Refueling - Pitstop 39")
    
    # Cek kolom wajib (Sekarang harusnya aman)
    required_cols = ['unit', 'shift', 'quantity']
    missing = [c for c in required_cols if c not in df.columns]
    
    if missing:
        st.error(f"⚠️ Kolom berikut masih hilang: {missing}")
        st.info(f"Nama kolom yang tersedia: {list(df.columns)}")
        st.stop() 

    # --- 4. SIDEBAR FILTER ---
    st.sidebar.header("Filter")
    # Urutkan unit biar rapi
    unique_units = sorted(df["unit"].astype(str).unique())
    pilihan_unit = st.sidebar.multiselect("Pilih Unit:", unique_units, default=unique_units)
    
    # Filter Data
    df_filtered = df[df["unit"].isin(pilihan_unit)]

    # --- 5. VISUALISASI ---
    # Baris 1: Ringkasan Angka
    col1, col2, col3 = st.columns(3)
    total_qty = df_filtered['quantity'].sum()
    total_trx = len(df_filtered)
    
    col1.metric("Total Solar Keluar", f"{total_qty:,.0f} L")
    col2.metric("Total Transaksi", f"{total_trx} Unit")
    # Ambil waktu terakhir update
    last_update = df_filtered['timestamp'].max()
    col3.metric("Update Terakhir", str(last_update) if pd.notnull(last_update) else "-")
    
    st.divider()

    # Baris 2: Grafik & Tabel
    c1, c2 = st.columns([1, 1]) # Bagi layar jadi 2 kolom
    
    with c1:
        st.subheader("Konsumsi per Shift")
        if 'shift' in df_filtered.columns:
            # Hitung total per shift
            df_shift = df_filtered.groupby("shift")["quantity"].sum().reset_index()
            fig = px.bar(df_shift, x="shift", y="quantity", 
                         title="Total Liter per Shift", color="shift")
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.subheader("Top 5 Unit Boros")
        # Hitung top 5 unit
        df_top = df_filtered.groupby("unit")["quantity"].sum().nlargest(5).reset_index()
        fig2 = px.bar(df_top, x="quantity", y="unit", orientation='h',
                      title="Top Konsumsi Solar", color="quantity")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Baris 3: Tabel Data
    st.subheader("Riwayat Logsheet Detail")
    # Tampilkan kolom tertentu saja biar rapi
    tabel_view = df_filtered[['timestamp', 'shift', 'unit', 'location', 'quantity', 'hm']]
    st.dataframe(tabel_view.sort_values(by='timestamp', ascending=False), use_container_width=True)
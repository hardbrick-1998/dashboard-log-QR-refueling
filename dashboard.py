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
# REVISI LANGKAH 2: CUSTOM CSS (VISUAL UPGRADE)
# ==========================================
st.markdown("""
    <style>
    /* 1. Background Utama */
    .main { background-color: #0d1b2a; color: #00e5ff; }
    
    /* 2. Judul Dashboard (UKURAN JUMBO & NEON KUAT) */
    .main-title {
        text-align: center; 
        color: #ffffff; 
        font-size: 52px; /* <-- Diperbesar dari 38px */
        font-weight: 800; /* Lebih Tebal */
        text-shadow: 0 0 10px #00e5ff, 0 0 20px #00e5ff, 0 0 40px #00e5ff; /* Glow Bertingkat */
        margin-bottom: 30px; 
        margin-top: -20px;
        letter-spacing: 2px; /* Jarak antar huruf biar elegan */
    }

    /* 3. Styling Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #1b263b; border: 1px solid #00e5ff;
        padding: 15px; border-radius: 10px; box-shadow: 0 0 8px #00e5ff;
    }

    /* 4. Digital Clock Container */
    .clock-card {
        background-color: #000000;
        border: 2px solid #333;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.9);
    }

    /* 5. Angka Jam Digital */
    .digital-font {
        font-family: 'Courier New', Courier, monospace;
        font-size: 48px;
        font-weight: bold;
        color: #39ff14; /* Hijau Neon Digital */
        text-shadow: 0 0 10px #39ff14;
        background-color: #0d0d0d;
        padding: 10px;
        border-radius: 5px;
        border: 1px inset #333;
        letter-spacing: 4px;
        margin: 10px 0;
    }

    /* 6. Pengaturan Container */
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
# LANGKAH 4: FILTER & LOGIKA DATA
# ==========================================
if not df.empty:
    # 1. Judul
    st.markdown('<p class="main-title">DASHBOARD REFUELING PITSTOP 39</p>', unsafe_allow_html=True)

    # 2. Filter & Refresh
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

    # 4. Fungsi Analisa Performa
    def get_performance_df(data_source):
        active_units = data_source['unit'].unique()
        performance_data = []
        
        for unit in active_units:
            u_data = data_source[data_source['unit'] == unit]
            
            # A. L/Hr
            duration = (u_data['timestamp'].max() - u_data['timestamp'].min()).total_seconds() / 3600
            l_hr = u_data['quantity'].sum() / duration if duration > 0 else 0
            
            # B. Avg Pengisian Harian
            num_days_unit = u_data['timestamp'].dt.date.nunique()
            refills_day = len(u_data) / num_days_unit if num_days_unit > 0 else 0
            
            performance_data.append({
                'unit': unit, 
                'l_hr': l_hr, 
                'refills_day': refills_day
            })
        return pd.DataFrame(performance_data)

    # Eksekusi Analisa
    df_perf_global = get_performance_df(df)
    df_perf_filtered = get_performance_df(df_filtered)

    # Rata-rata dari Rata-rata
    if not df_perf_filtered.empty:
        avg_l_per_hr = df_perf_filtered['l_hr'][df_perf_filtered['l_hr'] > 0].mean()
        avg_refills_per_day = df_perf_filtered['refills_day'].mean()
    else:
        avg_l_per_hr = 0
        avg_refills_per_day = 0

    # Metrik Lain
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
# REVISI LANGKAH 6: VISUALISASI CLEAN (NO SPEEDOMETER)
# ==========================================
    with tab1: 
        # --- BARIS 1: GRAFIK TREN & TOP 5 (POSISI TETAP) ---
        row1_c1, row1_c2 = st.columns([1.5, 1])

        with row1_c1:
            df_trend = df_filtered.copy().sort_values('timestamp')
            fig_trend = px.area(
                df_trend, x='timestamp', y='quantity', 
                title="📈 TREN KONSUMSI SOLAR", 
                hover_data={'timestamp': '|%d %b %Y, %H:%M'}
            )
            fig_trend.update_traces(line_color='#00e5ff', fillcolor='rgba(0, 229, 255, 0.2)')
            fig_trend.update_layout(
                height=400, margin=dict(l=10, r=10, t=80, b=10), 
                template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)',
                title_font_size=24,
                xaxis=dict(title="Waktu Pengisian", title_font=dict(size=18), tickfont=dict(size=14)),
                yaxis=dict(title="Volume (Liter)", title_font=dict(size=18), tickfont=dict(size=14))
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

        # --- BARIS 2: TRAFFIC HARIAN (KIRI) & JAM DIGITAL (KANAN) ---
        st.write("---")
        
        # Bagi layar: Kiri (Grafik) 3 bagian, Kanan (Jam) 1 bagian
        col_traffic, col_clock = st.columns([3, 1])
        
        # --- KOLOM KIRI: GRAFIK & NAVIGASI ---
        with col_traffic:
            # 1. SETUP SESSION STATE
            if 'chart_date' not in st.session_state:
                st.session_state.chart_date = df['timestamp'].max().date()

            # 2. NAVIGASI TANGGAL
            c_prev, c_date, c_next = st.columns([1, 4, 1])
            
            with c_prev:
                if st.button("⬅️ Sebelumnya", use_container_width=True):
                    st.session_state.chart_date -= pd.Timedelta(days=1)
                    st.rerun()

            with c_next:
                if st.button("Berikutnya ➡️", use_container_width=True):
                    st.session_state.chart_date += pd.Timedelta(days=1)
                    st.rerun()
            
            with c_date:
                # KAMUS INDONESIA
                hari_dict = {
                    'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu', 
                    'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
                }
                bulan_dict = {
                    'January': 'Januari', 'February': 'Februari', 'March': 'Maret', 
                    'April': 'April', 'May': 'Mei', 'June': 'Juni', 
                    'July': 'Juli', 'August': 'Agustus', 'September': 'September', 
                    'October': 'Oktober', 'November': 'November', 'December': 'Desember'
                }
                
                eng_day = st.session_state.chart_date.strftime("%A")
                eng_month = st.session_state.chart_date.strftime("%B")
                tgl_angka = st.session_state.chart_date.day
                tahun = st.session_state.chart_date.year
                
                indo_str = f"{hari_dict.get(eng_day, eng_day)}, {tgl_angka} {bulan_dict.get(eng_month, eng_month)} {tahun}"
                
                st.markdown(f"<h3 style='text-align: center; color: #00e5ff; margin: 0; font-size: 24px;'>{indo_str}</h3>", unsafe_allow_html=True)

            # 3. FILTER & RENDER GRAFIK
            df_daily = df[df['timestamp'].dt.date == st.session_state.chart_date].copy()

            if not df_daily.empty:
                df_daily['jam'] = df_daily['timestamp'].dt.hour
                hourly_counts = df_daily.groupby('jam').size().reset_index(name='jumlah')
                hourly_counts = hourly_counts.sort_values('jam')
                hourly_counts['jam_label'] = hourly_counts['jam'].apply(lambda x: f"{x:02d}:00")

                fig_daily = px.bar(
                    hourly_counts, x='jam_label', y='jumlah',
                    title=f"📊 KEPADATAN ANTREAN ({indo_str})",
                    text_auto=True,
                    labels={'jam_label': 'Jam', 'jumlah': 'Unit'}
                )
                fig_daily.update_traces(marker_color='#00e5ff', width=0.6)
                fig_daily.update_layout(
                    height=400, margin=dict(l=20, r=20, t=60, b=20),
                    template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)',
                    title_font_size=24,
                    xaxis=dict(type='category', title_font=dict(size=18), tickfont=dict(size=14)), 
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title_font=dict(size=18), tickfont=dict(size=14))
                )
                st.plotly_chart(fig_daily, use_container_width=True)
            else:
                st.info(f"💤 Tidak ada aktivitas refueling tercatat pada {indo_str}.")

        # --- KOLOM KANAN: JAM DIGITAL (DURASI) ---
        with col_clock:
            st.write("") # Spacer agar turun sedikit sejajar dengan grafik
            st.write("") 
            
            # HTML JAM DIGITAL
            html_clock = """
<div class="clock-card" style="margin-top: 20px;">
<p style="color: #888; font-size: 14px; margin-bottom: 5px;"> DURASI REFUELING / UNIT</p>
<div class="digital-font" style="font-size: 38px;">
08:00 <span style="font-size: 18px; color: #00e5ff;">MENIT</span>
</div>
<p style="color: #00e5ff; font-size: 13px; margin-top: 10px; font-weight: bold;">HASIL OBSERVASI LAPANGAN</p>
</div>
"""
            st.markdown(html_clock, unsafe_allow_html=True)
            
            # Bisa tambahkan info tambahan teks kecil di bawah jam jika mau
            st.markdown("""
            <div style="text-align: center; color: #aaa; font-size: 12px; margin-top: 10px;">
            <i>*Durasi refueling dihitung dari unit masuk bays hingga keluar dari bays.</i>
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
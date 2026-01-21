import sys
import os
from streamlit.web import cli as stcli

def main():
    # 1. Cari lokasi folder tempat file run.py ini berada
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Gabungkan folder tersebut dengan nama file dashboard.py
    # Jadi alamatnya lengkap, misal: C:/Users/Faiz/Project/dashboard.py
    path_to_dashboard = os.path.join(current_dir, "dashboard.py")
    
    # 3. Cek dulu apakah filenya benar-benar ada di sana
    if not os.path.exists(path_to_dashboard):
        print(f"❌ ERROR: File tidak ketemu di: {path_to_dashboard}")
        print("Pastikan nama filenya 'dashboard.py' (huruf kecil semua) dan ada di folder yang sama.")
        return

    # 4. Jalankan Streamlit dengan alamat lengkap
    sys.argv = ["streamlit", "run", f"{path_to_dashboard}"]
    sys.exit(stcli.main())

if __name__ == '__main__':
    main()
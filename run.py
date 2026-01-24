import sys
import os
from streamlit.web import cli as stcli

if __name__ == '__main__':
    # 1. Pastikan nama filenya sesuai dengan file utama Mas Faiz
    target_file = "dashboard.py"
    
    # 2. Trik 'Menipu' Python agar menjalankan perintah: streamlit run dashboard.py
    sys.argv = ["streamlit", "run", target_file]
    
    # 3. Panggil mesin utama Streamlit
    sys.exit(stcli.main())
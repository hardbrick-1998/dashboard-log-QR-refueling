import sys
from streamlit.web import cli as stcli

if __name__ == '__main__':
    # Ini trik memanipulasi sistem agar berpikir kita mengetik perintah di terminal
    sys.argv = ["streamlit", "run", "dashboard.py"]
    
    # Jalankan Streamlit
    sys.exit(stcli.main())
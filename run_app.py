import os
import webbrowser
import time
import threading

def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8501")

threading.Thread(target=open_browser).start()

os.system("streamlit run web_app.py --server.headless true")
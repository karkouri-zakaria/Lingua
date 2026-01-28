from io import BytesIO
from json import dumps
from webbrowser import open as openURL

from pandas import DataFrame
import time
from streamlit import button, code, columns, download_button, fragment, metric, rerun, session_state, sidebar, write, expander, link_button
def start_timer():
    if not session_state.running:
        session_state.running = True
        session_state.start_time = time.time() - session_state.elapsed_time
def stop_timer():
    if session_state.running:
        session_state.running = False
        session_state.elapsed_time = time.time() - session_state.start_time
def reset_timer():
    session_state.running = False
    session_state.start_time = None
    session_state.elapsed_time = 0
class AppSidebar:
    def __init__(self):
        """Initialize the Sidebar class."""
        self.user_input = None
        self.front_text = None
        self.back_text = None
    @fragment(run_every=0.4)
    def timer(self):
        if 'running' not in session_state:
            session_state.running = False
        if 'start_time' not in session_state:
            session_state.start_time = None
        if 'elapsed_time' not in session_state:
            session_state.elapsed_time = 0
        if session_state.running:
            session_state.elapsed_time = time.time() - session_state.start_time
        elapsed_minutes = int(session_state.elapsed_time // 60)
        elapsed_seconds = int(session_state.elapsed_time % 60)
        col1, col2, col3 = columns([4,2,2], gap="small", vertical_alignment="center")
        col1.metric(
                    label="Timer:",
                    value=f"{elapsed_seconds} s",
                    delta=f"{elapsed_minutes} min",
                    help="Minutes:Seconds",
                    label_visibility="collapsed",
                )
        icon = "❚❚" if session_state.running else "▶"
        with col2:
            if button(label=icon, width='stretch'):
                if not session_state.running:
                    start_timer()
                else:
                    stop_timer()
                    rerun()
        with col3:
            if button("⏹", width='stretch', disabled=session_state.elapsed_time==0 or session_state.running):
                reset_timer()
    def download_answers(self):
        with expander("Download", expanded=False, icon="📥"):
            buffer = BytesIO()
            DataFrame([[r[1], r[2]] for r in session_state.Answers if not r[3]], columns=["Source", "Target"]).to_excel(buffer, index=False, engine='xlsxwriter')
            download_button("💹 Mistakes.xlsx", buffer.getvalue(), f"Mistakes_{session_state.uploaded_file_data.name.split('.')[0]}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width='stretch')
            download_button("🗃️ Answers.json", dumps([[d[0], d[1], d[2], d[3]] for d in session_state.Answers], ensure_ascii=False, indent=4), f"Answers_{session_state.uploaded_file_data.name.split('.')[0]}.json", width='stretch')

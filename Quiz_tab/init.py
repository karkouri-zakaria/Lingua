from streamlit import session_state
def init_session_state():
    defaults = {
        "flashcards_df": None,
        "uploaded_file_data": None,
        "original_flashcards_df": None,
        "success_value": False,
        "auto_continue": False,
        "Show_all_anwsers": False,
        "Results": [],
        "show_wrongs": False,
        "flashcard_index": 0,
    }
    for key, value in defaults.items():
        if key not in session_state:
            session_state[key] = value
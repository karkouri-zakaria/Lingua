from streamlit import session_state, text_area, button, text_input, success, error, warning, rerun, markdown, columns, progress, audio
from Audio_gen.generate_audio import generate_audio
import unicodedata

def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def conjugation_view():
    # Initialize Session State
    if "conj_mode" not in session_state:
        session_state.conj_mode = "input"
    if "conj_data" not in session_state:
        session_state.conj_data = {}
    if "conj_idx" not in session_state:
        session_state.conj_idx = 0

    # Logic Controller
    if session_state.conj_mode == "input":
        _input_screen()
    elif session_state.conj_mode == "quiz":
        _quiz_screen()

def _input_screen():
    markdown("### 📝 Conjugation Input")
    
    # Recover previous text if available
    default_text = session_state.get("conj_raw_text", "")
    
    text = text_area(
        "Enter verb and conjugations (one per line):", 
        value=default_text,
        height=300, 
        placeholder="Verb\nConjugation 1\nConjugation 2\n...",
        key="conj_input_widget"
    )
    
    if button("Start Quiz", type="primary", use_container_width=True):
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
        if len(lines) < 2:
            warning("⚠️ Please enter a verb and at least one conjugation.")
        else:
            session_state.conj_data = {
                "verb": lines[0],
                "conjugations": lines[1:]
            }
            session_state.conj_idx = 0
            session_state.conj_mode = "quiz"
            session_state.conj_raw_text = text # Save for return
            rerun()

def _quiz_screen():
    verb = session_state.conj_data["verb"]
    conjugations = session_state.conj_data["conjugations"]
    idx = session_state.conj_idx
    total = len(conjugations)

    # Check if finished
    if idx >= total:
        success(f"🎉 Conjugation quiz for **{verb}** finished!")
        if button("🔄 Return to Input", type="primary", use_container_width=True):
            session_state.conj_mode = "input"
            rerun()
        if button("🔁 Restart Quiz", use_container_width=True):
            session_state.conj_idx = 0
            rerun()
        return

    target = conjugations[idx]
    
    # Display
    markdown(f"### Verb: **{verb}**")
    progress((idx) / total, text=f"Progress: {idx}/{total}")
    
    # Feedback mechanism
    if "conj_last_error" in session_state:
        error(session_state.conj_last_error)
        del session_state.conj_last_error

    def check_answer():
        user_val = session_state.conj_quiz_input.strip()
        if normalize(user_val.lower()) == normalize(target.lower()):
            session_state.conj_idx += 1
            session_state.conj_quiz_input = "" # Clear for next
            session_state.conj_audio = target
        else:
            session_state.conj_last_error = f"❌ Incorrect! Expected: **{target}**"

    markdown(f"**Conjugation #{idx + 1}:**")
    text_input(
        label="Answer",
        label_visibility="collapsed",
        key="conj_quiz_input",
        on_change=check_answer
    )
    
    def skip_answer():
        session_state.conj_last_error = f"Skipped. Answer: **{target}**"
        session_state.conj_idx += 1
        session_state.conj_quiz_input = ""
        session_state.conj_audio = target
    
    col1, col2, col3, col4 = columns(4)
    # Audio Feedback
    if "conj_audio" in session_state:
        with col3:
            button(session_state.conj_audio, width="stretch", disabled=True, key="conj_audio_button")
        try:
            with open(generate_audio(session_state.conj_audio), "rb") as f:
                col4.audio(f, format="audio/mp3", autoplay=True)
        except Exception: pass
        del session_state.conj_audio
    with col1:
        button("⏭️ Skip", use_container_width=True, on_click=skip_answer)
    with col2:
        if button("🛑 Quit", use_container_width=True):
            session_state.conj_mode = "input"
            rerun()
from streamlit import session_state, text_area, button, text_input, markdown, warning, rerun, markdown, columns, progress, audio, multiselect, dataframe
from Audio_gen.generate_audio import generate_audio
from Answers.colorize import colorize_conjugation
from time import sleep
import unicodedata
import re
import json
import os

HISTORY_FILE = "History/conjugation_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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
    elif session_state.conj_mode == "list":
        _list_screen()

def _input_screen():
    markdown("### 📝 Conjugation Input")
    
    history = load_history()
    selected_history = []
    if history:
        options = ["All"] + list(history.keys())
        selection = multiselect("Select verbs from history:", options=options)
        if "All" in selection:
            selected_history = list(history.keys())
        else:
            selected_history = selection

    # Recover previous text if available
    default_text = session_state.get("conj_raw_text", "")
    
    text = text_area(
        "Enter verbs and conjugations (separated by empty lines):", 
        value=default_text,
        height=300, 
        placeholder="Verb1\nConjugation 1\nConjugation 2\n\nVerb2\nConjugation 1...",
        key="conj_input_widget"
    )
    
    col1, col2 = columns(2)
    with col1:
        start_quiz = button("Start Quiz", type="primary", width="stretch")
    with col2:
        if button("📋 View List", width="stretch"):
            session_state.conj_mode = "list"
            rerun()

    if start_quiz:
        blocks = re.split(r'\n\s*\n', text.strip())
        parsed_data = {}
        if text.strip():
            for block in blocks:
                lines = [line.strip() for line in block.split('\n') if line.strip()]
                if len(lines) >= 2:
                    parsed_data[lines[0]] = lines[1:]

        # Update history
        if parsed_data:
            history.update(parsed_data)
            save_history(history)

        # Combine selected history and parsed input
        final_data = []
        # Add selected verbs from history (using updated history to get latest conjugations)
        for verb in selected_history:
            final_data.append({"verb": verb, "conjugations": history[verb]})
        
        # Add parsed verbs if not already added via selection
        for verb, conjugations in parsed_data.items():
            if verb not in selected_history:
                final_data.append({"verb": verb, "conjugations": conjugations})

        if not final_data:
            warning("⚠️ Please enter at least one verb and one conjugation or select from history.")
        else:
            session_state.conj_data = final_data
            session_state.conj_idx = 0
            session_state.conj_verb_idx = 0
            session_state.conj_mode = "quiz"
            session_state.conj_raw_text = text # Save for return
            rerun()

def _quiz_screen():
    data = session_state.conj_data
    if isinstance(data, dict):
        data = [data]

    if "conj_verb_idx" not in session_state:
        session_state.conj_verb_idx = 0
    
    verb_idx = session_state.conj_verb_idx
    
    if verb_idx >= len(data):
        col1, col2, col3, col4, col5 = columns(5)
        col4.button(session_state.conj_audio, width="stretch", disabled=True, key="conj_audio_button")
        with open(generate_audio(session_state.conj_audio), "rb") as f:
            col5.audio(f, format="audio/mp3", autoplay=True)
        sleep(1)
        markdown(f"🎉 All conjugation quizzes finished!")
        if col1.button("🔄 Return to Input", type="primary", width="stretch"):
            session_state.conj_mode = "input"
            rerun()
        if col2.button("🔁 Restart Quiz", width="stretch"):
            session_state.conj_idx = 0
            session_state.conj_verb_idx = 0
            rerun()
        return

    current_verb_data = data[verb_idx]
    verb = current_verb_data["verb"]
    conjugations = current_verb_data["conjugations"]
    idx = session_state.conj_idx
    total = len(conjugations)

    if idx >= total:
        session_state.conj_verb_idx += 1
        session_state.conj_idx = 0
        rerun()
        return

    target = conjugations[idx]
    
    # Display
    markdown(f"### Verb: **{verb}**", unsafe_allow_html=True)
    progress((idx) / total, text=f"Progress: {idx}/{total} (Verb {verb_idx + 1}/{len(data)})")
    
    # Feedback mechanism
    if "conj_last_markdown" in session_state:
        markdown(session_state.conj_last_markdown, unsafe_allow_html=True)
        del session_state.conj_last_markdown

    def check_answer():
        user_val = session_state.conj_quiz_input.strip()
        # Normalize for comparison (removes accents/case for the "Correct" check)
        if normalize(user_val.lower()) == normalize(target.lower()):
            session_state.conj_idx += 1
            session_state.conj_quiz_input = "" 
            session_state.conj_audio = target
        else:
            # The colorize_conjugation function handles the slash splitting now
            colored_answer = colorize_conjugation(verb, target)
            session_state.conj_last_markdown = f"❌ Incorrect! Expected: **{colored_answer}**"

    pronouns = ["Yo", "Tú", "Él / Ella / Usted", "Nosotros / Nosotras", "Vosotros / Vosotras", "Ellos / Ellas / Ustedes"]
    current_pronoun = pronouns[idx] if idx < len(pronouns) else f"#{idx + 1}"

    c1, c2 = columns([1, 2])
    with c1:
        button(current_pronoun, disabled=True, width="stretch", key=f"pronoun_{verb_idx}_{idx}")
    with c2:
        text_input(
            label="Answer",
            label_visibility="collapsed",
            key="conj_quiz_input",
            on_change=check_answer
        )
    
    def skip_answer():
        session_state.conj_last_markdown = f"Skipped. Answer: **{colorize_conjugation(verb, target)}**"
        session_state.conj_idx += 1
        session_state.conj_quiz_input = ""
        session_state.conj_audio = target
    
    col1, col2, col3, col4, col5 = columns(5)
    # Audio Feedback
    if "conj_audio" in session_state:
        with col4:
            button(session_state.conj_audio, width="stretch", disabled=True, key="conj_audio_button")
        try:
            with open(generate_audio(session_state.conj_audio), "rb") as f:
                col5.audio(f, format="audio/mp3", autoplay=True)
        except Exception: pass
        del session_state.conj_audio
    with col1:
        button("⏭️ Skip", width="stretch", on_click=skip_answer)
    with col2:
        if button("🛑 Quit", width="stretch"):
            session_state.conj_mode = "input"
            rerun()
    with col3:
        if button("🪔 Show", width="stretch"):
            session_state.conj_last_markdown = f"Answer: **{colorize_conjugation(verb, target)}**"
def _list_screen():
    from pandas import DataFrame
    
    markdown("### 📋 Verb List")
    
    if button("🔙 Back", width="stretch"):
        session_state.conj_mode = "input"
        rerun()

    history = load_history()
    if not history:
        markdown("No verbs found in history.")
        return

    data = []
    pronouns = ["Yo", "Tú", "Él / Ella / Usted", "Nosotros / Nosotras", "Vosotros / Vosotras", "Ellos / Ellas / Ustedes"]
    
    for verb, conjugations in history.items():
        row = {"Verb": verb}
        for idx, conj in enumerate(conjugations):
            col_name = pronouns[idx] if idx < len(pronouns) else f"#{idx + 1}"
            # This will now return the joined string if 'verb' has a '/'
            row[col_name] = colorize_conjugation(verb, conj)
        data.append(row)

    if data:
        df = DataFrame(data)
        cols = ["Verb"] + [p for p in pronouns if p in df.columns] + [c for c in df.columns if c not in pronouns and c != "Verb"]
        df = df[cols]
        markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
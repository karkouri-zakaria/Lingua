from streamlit import (
    session_state, text_area, button, text_input, markdown, warning, success,
    rerun, columns, progress, audio, multiselect, selectbox, expander,
    balloons, container, form, form_submit_button, toggle, download_button
)
from Audio_gen.generate_audio import generate_audio
from Answers.colorize import colorize_conjugation
from conjugation.termination_table import render_termination_table
from pandas import DataFrame
import streamlit.components.v1 as components
import unicodedata
import re
import json
import os

HISTORY_FILE = "History/conjugation_history.json"
ALL_VERBS_FILE = "History/all_verbs.json"
PRONOUNS = ["Yo", "Tú", "Él/Ella/Utd", "Nosotros/as", "Vosotros/as", "Ellos/as/Utds"]
PRONOUN_GROUPS = [PRONOUNS[:3], PRONOUNS[3:]]
STANDARD_TENSE_ORDER = [
    "past", "imperfecto", "perfecto", "present", "presente progresivo", "future"
]
DEFAULT_TENSES = STANDARD_TENSE_ORDER.copy()
COMPOSITE_TENSES = {"perfecto", "presente progresivo"}
COMPOSITE_AUXILIARIES = {
    "perfecto": ["he", "has", "ha", "hemos", "habéis", "han"],
    "presente progresivo": ["estoy", "estás", "está", "estamos", "estáis", "están"]
}


def format_tense_value(tense, value, pronoun_index):
    """Add the auxiliary when composite tense data stores only its main form."""
    if tense.lower() not in COMPOSITE_TENSES or " " in value:
        return value
    auxiliary = COMPOSITE_AUXILIARIES[tense.lower()][pronoun_index]
    return f"{auxiliary} {value}"


def get_tense_values(tense, values):
    """Expand one shared composite form for the six pronoun positions."""
    if tense.lower() in COMPOSITE_TENSES and len(values) == 1:
        return values * len(PRONOUNS)
    return values

def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def is_new_format(conjugations):
    """Check if conjugations are in new format (dict with tenses) or old format (list)"""
    return isinstance(conjugations, dict) and not isinstance(conjugations, list)

def clean_verb_dict(data):
    """Clean and standardize verb data dictionary, rejecting invalid keys like '{' or empty"""
    cleaned = {}
    if not isinstance(data, dict):
        return cleaned
    for k, v in data.items():
        if not isinstance(k, str):
            continue
        k_clean = k.strip()
        if not k_clean or k_clean in ('{', '}', '[', ']') or not any(c.isalpha() for c in k_clean):
            continue
        if isinstance(v, list):
            cleaned[k_clean] = {"present": v}
        elif isinstance(v, dict):
            clean_tenses = {}
            for tense, conjs in v.items():
                if isinstance(conjs, list) and all(isinstance(c, str) for c in conjs):
                    clean_tenses[tense] = conjs
            if clean_tenses:
                cleaned[k_clean] = clean_tenses
    return cleaned

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return clean_verb_dict(json.load(f))
        except Exception:
            return {}
    return {}

def load_all_verbs():
    """Load the master verb database with all tenses"""
    if os.path.exists(ALL_VERBS_FILE):
        try:
            with open(ALL_VERBS_FILE, "r", encoding="utf-8") as f:
                return clean_verb_dict(json.load(f))
        except Exception:
            return {}
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_verb_dict(data), f, ensure_ascii=False, indent=4)

def merge_verb_databases(all_verbs, history):
    """Deep-merge all_verbs and history so all tenses are preserved and history overrides where provided"""
    merged = dict(all_verbs)
    for verb, h_data in history.items():
        if verb in merged and isinstance(merged[verb], dict) and isinstance(h_data, dict):
            merged[verb] = {**merged[verb], **h_data}
        else:
            merged[verb] = h_data
    return merged

def get_tenses(verbs_dict):
    """Get all unique available tenses across all verbs in standard order (Past, Present, Future, etc.)"""
    tenses_found = set()
    for verb_data in verbs_dict.values():
        if is_new_format(verb_data):
            tenses_found.update(verb_data.keys())
    
    ordered = [t for t in STANDARD_TENSE_ORDER if t in tenses_found]
    remaining = sorted(list(tenses_found - set(STANDARD_TENSE_ORDER)))
    return ordered + remaining or ["present"]

def parse_verb_input(text):
    """Parse user text input which could be JSON or plain text format (Verb\\nConj1\\nConj2...)"""
    text = text.strip()
    if not text:
        return {}
    
    if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return clean_verb_dict(parsed)
            elif isinstance(parsed, list):
                res = {}
                for item in parsed:
                    if isinstance(item, dict) and "verb" in item:
                        conjs = item.get("conjugations", {})
                        if isinstance(conjs, (dict, list)):
                            res[item["verb"]] = conjs
                return clean_verb_dict(res)
        except Exception:
            pass

    blocks = re.split(r'\n\s*\n', text)
    parsed_data = {}
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
        verb_line = lines[0].strip().strip('"').strip("'")
        if not verb_line or verb_line in ('{', '}', '[', ']') or not any(c.isalpha() for c in verb_line):
            continue
        if len(lines) >= 2:
            parsed_data[verb_line] = {"present": lines[1:]}
            
    return clean_verb_dict(parsed_data)

def check_conjugation_match(user_val, target):
    """Check if user_val matches target, supporting slash-separated alternative options (e.g. 'Ha/Hay')"""
    user_norm = normalize(user_val.strip().lower())
    if not user_norm:
        return False, ""
    
    options = [t.strip() for t in target.split("/") if t.strip()]
    for opt in options:
        if user_norm == normalize(opt.lower()):
            return True, opt
    return False, ""

def play_audio_feedback(text_to_speak):
    """Generate and return audio file path for Spanish conjugation(s)"""
    try:
        # Clean out slash alternatives for smooth TTS
        clean_text = ", ".join([p.split("/")[0].strip() for p in text_to_speak.split(",") if p.strip()])
        audio_path = generate_audio(clean_text, lang=session_state.get("language_code", "es"))
        return audio_path
    except Exception:
        return None

def focus_conjugation_input(input_label):
    """Focus and scroll to a conjugation input after a rerun."""
    input_label = json.dumps(input_label)
    focus_script = f"""
    <script>
    (() => {{
        const inputLabel = {input_label};
        const focusInput = () => {{
            const input = window.parent.document.querySelector(`input[aria-label="${{inputLabel}}"]`);
            if (input) {{
                input.scrollIntoView({{ behavior: "smooth", block: "center" }});
                input.focus();
                return true;
            }}
            return false;
        }};
        if (!focusInput()) setTimeout(focusInput, 100);
    }})();
    </script>
    """
    components.html(focus_script, height=0)

def conjugation_input_label(tense, pronoun):
    return f"{tense.capitalize()} {pronoun} conjugation input"

def get_pdf_bytes():
    """Get or generate the verbs PDF bytes reliably"""
    from conjugation.export_verbs_pdf import generate_verbs_pdf
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(base_dir, "Spanish_Verbs_Conjugations.pdf")
    generate_verbs_pdf(pdf_path)
    with open(pdf_path, "rb") as f:
        return f.read()

def conjugation_view():
    # Initialize Session State
    if "conj_mode" not in session_state:
        session_state.conj_mode = "input"
    if "conj_data" not in session_state:
        session_state.conj_data = []
    if "conj_verb_idx" not in session_state:
        session_state.conj_verb_idx = 0
    if "conj_pronoun_idx" not in session_state:
        session_state.conj_pronoun_idx = 0
    if "conj_selected_tenses" not in session_state:
        session_state.conj_selected_tenses = DEFAULT_TENSES.copy()
    if "conj_verb_completed" not in session_state:
        session_state.conj_verb_completed = False
    if "conj_completed_pronouns" not in session_state:
        session_state.conj_completed_pronouns = []

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
    all_verbs = load_all_verbs()
    combined_verbs = merge_verb_databases(all_verbs, history)
    
    selected_history = []
    available_tenses = get_tenses(combined_verbs)
    
    # Tense selection (defaults to all available tenses)
    col_tense_label, col_tense_select = columns([1, 3], vertical_alignment="center")
    with col_tense_label:
        markdown("#### Select Tense(s):")
    with col_tense_select:
        current_selection = [t for t in session_state.conj_selected_tenses if t in available_tenses]
        if set(current_selection) == {"past", "present", "future"}:
            current_selection = [t for t in DEFAULT_TENSES if t in available_tenses]
        elif not current_selection:
            current_selection = available_tenses
        if set(session_state.get("tense_selector", [])) == {"past", "present", "future"}:
            session_state.tense_selector = current_selection
        selected_tenses = multiselect(
            "Which tenses to practice simultaneously?",
            options=available_tenses,
            default=current_selection,
            key="tense_selector"
        )
        if selected_tenses:
            # Preserve the standard tense order
            sorted_tenses = [t for t in STANDARD_TENSE_ORDER if t in selected_tenses] + [t for t in selected_tenses if t not in STANDARD_TENSE_ORDER]
            session_state.conj_selected_tenses = sorted_tenses
        else:
            session_state.conj_selected_tenses = ["present"]
    
    # Verb Selection from database
    if combined_verbs:
        combined_list = list(combined_verbs.keys())
        display_options = [f"{i}: {verb}" for i, verb in enumerate(combined_list)]
        
        col_sel, col_range = columns([2, 1])
        with col_sel:
            selection = multiselect(
                "Select verbs from database:", 
                options=["All"] + display_options
            )
        
        with col_range:
            range_input = text_input("Or enter range (e.g. 0-5, 22-, 1,2,5):", placeholder="0-?")

        if "All" in selection:
            selected_history = list(combined_list)
        else:
            for item in selection:
                verb_name = item.split(": ", 1)[1]
                selected_history.append(verb_name)
            
            clean_range = range_input.strip()
            if clean_range:
                try:
                    total_verbs = len(combined_list)
                    if clean_range.endswith("-"):
                        start = max(0, min(int(clean_range[:-1]), total_verbs))
                        selected_history.extend(combined_list[start:])
                    elif clean_range.startswith("-"):
                        end = max(0, min(int(clean_range[1:]), total_verbs - 1))
                        selected_history.extend(combined_list[:end + 1])
                    elif "-" in clean_range:
                        parts = clean_range.split("-")
                        start = max(0, min(int(parts[0]), total_verbs))
                        end = max(0, min(int(parts[1]), total_verbs - 1)) if parts[1] else total_verbs - 1
                        if start <= end:
                            selected_history.extend(combined_list[start:end + 1])
                    elif "," in clean_range:
                        idxs = [int(p.strip()) for p in clean_range.split(",") if p.strip().isdigit()]
                        for i in idxs:
                            if 0 <= i < total_verbs:
                                selected_history.append(combined_list[i])
                    elif clean_range.isdigit():
                        idx = int(clean_range)
                        if 0 <= idx < total_verbs:
                            selected_history.append(combined_list[idx])
                except (ValueError, IndexError):
                    warning("⚠️ Invalid range format.")

        selected_history = list(dict.fromkeys(selected_history))

    default_text = session_state.get("conj_raw_text", "")
    text = text_area(
        "Enter new verbs (plain text: Verb\\nConj1\\n... or JSON):", 
        value=default_text,
        height=180, 
        key="conj_input_widget"
    )
    
    col1, col2, col3 = columns(3)
    with col1:
        start_quiz = button("🚀 Start Quiz", type="primary", width="stretch")
    with col2:
        if button("📋 View List", width="stretch"):
            session_state.conj_mode = "list"
            rerun()
    with col3:
        try:
            pdf_data = get_pdf_bytes()
            download_button(
                label="📥 Download PDF",
                data=pdf_data,
                file_name="Spanish_Verbs_Conjugations.pdf",
                mime="application/pdf",
                width="stretch"
            )
        except Exception as e:
            if button("📥 Generate PDF", width="stretch"):
                warning(f"PDF error: {e}")

    if start_quiz:
        parsed_data = parse_verb_input(text)
        if parsed_data:
            history.update(parsed_data)
            save_history(history)
            combined_verbs = merge_verb_databases(all_verbs, history)

        # Build final data
        final_data = []
        selected_verbs = list(dict.fromkeys(selected_history + list(parsed_data.keys())))
        
        for verb in selected_verbs:
            if verb in combined_verbs:
                final_data.append({"verb": verb, "conjugations": combined_verbs[verb]})

        if not final_data:
            warning("⚠️ Please select from database or enter new verbs.")
        else:
            session_state.conj_data = final_data
            session_state.conj_verb_idx = 0
            session_state.conj_pronoun_idx = 0
            session_state.conj_verb_completed = False
            session_state.conj_completed_pronouns = []
            session_state.conj_mode = "quiz"
            session_state.conj_raw_text = text
            for key in ["conj_feedback_html", "conj_audio", "conj_audio_announced", "conj_last_markdown", "conj_tense_errors", "conj_tense_status"]:
                if key in session_state:
                    del session_state[key]
            rerun()

def _quiz_screen():
    data = session_state.conj_data
    if isinstance(data, dict):
        data = [data]

    if not data:
        markdown("⚠️ No verb data available.")
        if button("🔙 Return to Input", type="primary"):
            session_state.conj_mode = "input"
            rerun()
        return

    history = load_history()
    all_verbs = load_all_verbs()
    combined_verbs = merge_verb_databases(all_verbs, history)
    combined_list = list(combined_verbs.keys())

    if "conj_verb_idx" not in session_state:
        session_state.conj_verb_idx = 0
    if "conj_pronoun_idx" not in session_state:
        session_state.conj_pronoun_idx = 0
    if "conj_completed_pronouns" not in session_state:
        session_state.conj_completed_pronouns = []
    
    verb_idx = session_state.conj_verb_idx
    
    # Check if ALL verbs in quiz finished
    if verb_idx >= len(data):
        balloons()
        markdown(f"## 🎉 All {len(data)} conjugation quizzes finished!")
        col1, col2, _ = columns([1, 1, 2])
        with col1:
            if button("🔄 Return to Input", type="primary", width="stretch"):
                session_state.conj_mode = "input"
                rerun()
        with col2:
            if button("🔁 Restart Quiz", width="stretch"):
                session_state.conj_verb_idx = 0
                session_state.conj_pronoun_idx = 0
                session_state.conj_verb_completed = False
                session_state.conj_completed_pronouns = []
                session_state.conj_audio_announced = set()
                rerun()
        return

    current_verb_data = data[verb_idx]
    full_verb_text = current_verb_data["verb"]
    conjugations_dict = current_verb_data["conjugations"]
    selected_tenses = session_state.conj_selected_tenses
    if set(selected_tenses) == {"past", "present", "future"} and is_new_format(conjugations_dict):
        selected_tenses = [t for t in DEFAULT_TENSES if t in conjugations_dict]
        session_state.conj_selected_tenses = selected_tenses
    
    # Determine active tenses for this verb
    active_tenses = []
    for t in selected_tenses:
        if is_new_format(conjugations_dict) and t in conjugations_dict:
            active_tenses.append(t)
        elif not is_new_format(conjugations_dict) and t == "present":
            active_tenses.append(t)

    # Fallback to available tenses if selected tenses aren't in this verb
    if not active_tenses:
        if is_new_format(conjugations_dict):
            active_tenses = list(conjugations_dict.keys())[:3]
        else:
            active_tenses = ["present"]

    # Keep the review table at six pronouns, but quiz them in two groups of three.
    total_pronouns = 6
    if is_new_format(conjugations_dict):
        lens = [
            len(conjugations_dict[t])
            for t in active_tenses
            if isinstance(conjugations_dict.get(t), list) and t not in COMPOSITE_TENSES
        ]
        if lens:
            total_pronouns = min(lens)
    elif isinstance(conjugations_dict, list):
        total_pronouns = len(conjugations_dict)

    if " (" in full_verb_text:
        verb = full_verb_text.split(" (")[0].strip()
        translation = " (" + full_verb_text.split(" (")[1]
    else:
        verb = full_verb_text
        translation = ""

    global_idx = combined_list.index(full_verb_text) if full_verb_text in combined_list else (verb_idx + 1)
    pronoun_idx = session_state.conj_pronoun_idx
    total_pronoun_groups = len(PRONOUN_GROUPS)
    first_input_label = conjugation_input_label(active_tenses[0], PRONOUN_GROUPS[0][0])

    # --- VERB COMPLETED SCREEN ---
    if session_state.get("conj_verb_completed", False) or pronoun_idx >= total_pronoun_groups:
        session_state.conj_verb_completed = True
        markdown(f"## 🎉 Verb #{global_idx}: **{verb}** {translation} — Completed!", unsafe_allow_html=True)
        
        # Audio feedback for the last word/tenses
        if "conj_audio" in session_state:
            audio_path = play_audio_feedback(session_state.conj_audio)
            if audio_path:
                audio(audio_path, format="audio/mp3", autoplay=True)
            del session_state.conj_audio

        # Full 3-Tense Conjugation Table for this verb
        markdown("#### 📖 Conjugation Review (All Tenses)")
        table_rows = []
        for p_i in range(total_pronouns):
            p_name = PRONOUNS[p_i] if p_i < len(PRONOUNS) else f"#{p_i + 1}"
            row = {"Pronoun": p_name}
            for t in active_tenses:
                conj_list = conjugations_dict.get(t, []) if is_new_format(conjugations_dict) else conjugations_dict
                display_values = get_tense_values(t, conj_list)
                if p_i < len(display_values):
                    display_list = [
                        format_tense_value(t, value, value_index)
                        for value_index, value in enumerate(display_values)
                    ]
                    row[t.capitalize()] = colorize_conjugation(verb, display_list[p_i], display_list)
                else:
                    row[t.capitalize()] = "-"
            table_rows.append(row)

        if table_rows:
            df = DataFrame(table_rows)
            custom_css = """<style>
table.dataframe { width: 100% !important; font-size: 17px !important; margin: 10px 0 !important; }
table.dataframe th, table.dataframe td { padding: 10px 14px !important; text-align: left !important; border: 1px solid #444 !important; }
table.dataframe th { background-color: #2b2b2b !important; font-weight: bold !important; }
</style>"""
            markdown(custom_css + df.to_html(escape=False, index=False), unsafe_allow_html=True)

        col_next, col_retry, col_quit = columns([2, 1, 1])
        with col_next:
            is_last_verb = (verb_idx + 1 >= len(data))
            next_label = "🎉 Finish Quiz" if is_last_verb else f"➡️ Next Verb ({verb_idx + 2}/{len(data)})"
            if button(next_label, type="primary", width="stretch"):
                session_state.conj_verb_idx += 1
                session_state.conj_pronoun_idx = 0
                session_state.conj_verb_completed = False
                session_state.conj_completed_pronouns = []
                if not is_last_verb:
                    session_state.conj_audio_announced = set()
                    session_state.conj_focus_tense = first_input_label
                if "conj_last_markdown" in session_state:
                    del session_state.conj_last_markdown
                rerun()
        with col_retry:
            if button("🔄 Practice Again", width="stretch"):
                session_state.conj_pronoun_idx = 0
                session_state.conj_verb_completed = False
                session_state.conj_completed_pronouns = []
                session_state.conj_audio_announced = set()
                session_state.conj_focus_tense = first_input_label
                if "conj_last_markdown" in session_state:
                    del session_state.conj_last_markdown
                rerun()
        with col_quit:
            if button("🛑 Quit", width="stretch"):
                session_state.conj_mode = "input"
                rerun()
        return

    # --- ACTIVE PRONOUN GROUP QUESTION ---
    current_group = PRONOUN_GROUPS[pronoun_idx]
    group_start = pronoun_idx * 3

    # Target values for every pronoun and active tense in this group.
    targets = {}
    target_lists = {}
    for t in active_tenses:
        conj_list = conjugations_dict.get(t, []) if is_new_format(conjugations_dict) else conjugations_dict
        tense_values = get_tense_values(t, conj_list)
        target_lists[t] = [
            format_tense_value(t, value, value_index)
            for value_index, value in enumerate(tense_values)
        ]
        for group_offset in range(len(current_group)):
            pronoun_position = group_start + group_offset
            targets[(group_offset, t)] = (
                tense_values[pronoun_position] if pronoun_position < len(tense_values) else ""
            )

    # Header and Progress
    markdown(f"### Verb #{global_idx}: {translation}")
    markdown(f"# **{verb}**", unsafe_allow_html=True)
    
    col_p_badge, col_prog = columns([1, 3], vertical_alignment="center")
    with col_p_badge:
        markdown(f"## 👥 **{'/'.join(current_group)}**")
    with col_prog:
        progress_val = max(0.0, min(float(pronoun_idx)/float(total_pronoun_groups), 1.0))
        progress(progress_val, text=f"Pronoun group {pronoun_idx + 1}/{total_pronoun_groups} (Verb {verb_idx + 1}/{len(data)})")

    # Audio & Previous Pronoun Success
    if "conj_audio" in session_state:
        audio_path = play_audio_feedback(session_state.conj_audio)
        if audio_path:
            audio(audio_path, format="audio/mp3", autoplay=True)
        del session_state.conj_audio

    if "conj_last_markdown" in session_state:
        markdown(session_state.conj_last_markdown, unsafe_allow_html=True)
        del session_state.conj_last_markdown

    # Multi-Tense Simultaneous Form
    with form(key=f"pronoun_form_{verb_idx}_{pronoun_idx}"):
        user_inputs = {}
        
        tense_title_map = {
            "past": "Pretérito (Past)",
            "imperfecto": "Imperfecto",
            "perfecto": "Perfecto",
            "present": "Presente (Present)",
            "presente progresivo": "Presente Progresivo",
            "future": "Futuro (Future)"
        }
        
        tense_columns = columns(len(active_tenses))
        for column, t in zip(tense_columns, active_tenses):
            with column:
                header_title = tense_title_map.get(t.lower(), t.capitalize())
                markdown(f"**{header_title}**")
                if t in COMPOSITE_TENSES:
                    field_key = t
                    field_label = f"{t.capitalize()} main form input"
                    if session_state.get("conj_tense_status", {}).get(field_key) == "correct":
                        markdown("✅ **Main form**")
                    else:
                        markdown("**Main form**")
                    err_msg = session_state.get("conj_tense_errors", {}).get(field_key, "")
                    if err_msg:
                        markdown(f"<span style='color: #ff5555; font-size: 13px;'>{err_msg}</span>", unsafe_allow_html=True)
                    user_inputs[field_key] = text_input(
                        label=field_label,
                        label_visibility="collapsed",
                        placeholder="Participle only..." if t == "perfecto" else "Gerund only...",
                        key=f"form_input_{verb_idx}_{pronoun_idx}_shared_{t}"
                    )
                else:
                    for group_offset, pronoun in enumerate(current_group):
                        field_key = (group_offset, t)
                        field_label = conjugation_input_label(t, pronoun)
                        if session_state.get("conj_tense_status", {}).get(field_key) == "correct":
                            markdown(f"✅ **{pronoun}**")
                        else:
                            markdown(f"**{pronoun}**")
                        err_msg = session_state.get("conj_tense_errors", {}).get(field_key, "")
                        if err_msg:
                            markdown(f"<span style='color: #ff5555; font-size: 13px;'>{err_msg}</span>", unsafe_allow_html=True)
                        user_inputs[field_key] = text_input(
                            label=field_label,
                            label_visibility="collapsed",
                            placeholder=f"{pronoun} in {t.capitalize()}...",
                            key=f"form_input_{verb_idx}_{pronoun_idx}_{group_offset}_{t}"
                        )

        # Form Submit Row
        btn_c1, btn_c2 = columns([3, 1])
        with btn_c1:
            form_submitted = form_submit_button("✅ Check Answer (Press Enter)", type="primary", width="stretch")

    focus_tense = session_state.get("conj_focus_tense")
    if focus_tense:
        focus_conjugation_input(focus_tense)
        del session_state.conj_focus_tense

    # Form Submission Evaluation
    if form_submitted:
        all_correct = True
        matched_opts = {}
        tense_errors = {}
        tense_status = {}
        
        for t in active_tenses:
            for group_offset, _pronoun in enumerate(current_group):
                field_key = (group_offset, t)
                input_key = t if t in COMPOSITE_TENSES else field_key
                u_val = user_inputs[input_key].strip()
                target = targets[field_key]
                is_match, matched_opt = check_conjugation_match(u_val, target)
                if is_match:
                    matched_opts[field_key] = matched_opt if matched_opt else target
                    tense_status[input_key] = "correct"
                else:
                    all_correct = False
                    tense_errors[input_key] = "Try again"
                    tense_status[input_key] = "incorrect"
        
        if all_correct:
            feedback_parts = []
            for group_offset, pronoun in enumerate(current_group):
                conjugations = [
                    colorize_conjugation(
                        verb,
                        format_tense_value(t, matched_opts[(group_offset, t)], group_start + group_offset),
                        target_lists[t]
                    )
                    for t in active_tenses
                ]
                feedback_parts.append(f"<b>{pronoun}:</b> " + " &ensp;·&ensp; ".join(conjugations))
            session_state.conj_feedback_html = "<br>".join(feedback_parts)
            announced = session_state.get("conj_audio_announced", set())
            new_correct_audio = [
                format_tense_value(t, matched_opts[(group_offset, t)], group_start + group_offset)
                for t in active_tenses
                for group_offset in range(len(current_group))
                if (group_offset, t) not in announced
            ]
            if new_correct_audio:
                session_state.conj_audio = ", ".join(new_correct_audio)
            session_state.conj_audio_announced = announced | set(matched_opts)
            
            # Record completed pronoun row for the live table
            for group_offset, pronoun in enumerate(current_group):
                completed_entry = {"Pronoun": pronoun}
                for t in active_tenses:
                    completed_entry[t.capitalize()] = colorize_conjugation(
                        verb,
                        format_tense_value(t, matched_opts[(group_offset, t)], group_start + group_offset),
                        target_lists[t]
                    )
                session_state.conj_completed_pronouns.append(completed_entry)
            
            session_state.conj_pronoun_idx += 1
            for key in ["conj_tense_errors", "conj_tense_status"]:
                if key in session_state:
                    del session_state[key]
            if "conj_last_markdown" in session_state:
                del session_state.conj_last_markdown
            if session_state.conj_pronoun_idx >= total_pronoun_groups:
                session_state.conj_verb_idx += 1
                session_state.conj_pronoun_idx = 0
                session_state.conj_verb_completed = False
                session_state.conj_completed_pronouns = []
                session_state.conj_audio_announced = set()
                if session_state.conj_verb_idx < len(data):
                    session_state.conj_focus_tense = first_input_label
            else:
                session_state.conj_audio_announced = set()
                session_state.conj_focus_tense = (
                    conjugation_input_label(
                        active_tenses[0],
                        PRONOUN_GROUPS[session_state.conj_pronoun_idx][0]
                    )
                )
            rerun()
        else:
            session_state.conj_tense_errors = tense_errors
            session_state.conj_tense_status = tense_status
            announced = session_state.get("conj_audio_announced", set())
            new_correct_audio = [
                format_tense_value(t, matched_opts[(group_offset, t)], group_start + group_offset)
                for t in active_tenses
                for group_offset in range(len(current_group))
                if (group_offset, t) in matched_opts and (group_offset, t) not in announced
            ]
            if new_correct_audio:
                session_state.conj_audio = ", ".join(new_correct_audio)
                session_state.conj_audio_announced = announced | set(matched_opts)
            session_state.conj_focus_tense = next(
                f"{t.capitalize()} main form input"
                if t in COMPOSITE_TENSES else
                conjugation_input_label(t, current_group[group_offset])
                for t in active_tenses
                for group_offset, _pronoun in enumerate(current_group)
                if tense_status.get(t if t in COMPOSITE_TENSES else (group_offset, t)) == "incorrect"
            )
            session_state.conj_last_markdown = (
                f"❌ Review needed for <b>{'/'.join(current_group)}</b>. "
                "Try the marked fields again."
            )
            rerun()

    # Action Buttons Row (Skip, Prev, Show, Quit)
    btn_prev, btn_skip, btn_skip_verb, btn_show, btn_quit = columns(5)
    
    with btn_prev:
        def go_prev():
            if session_state.conj_pronoun_idx > 0:
                session_state.conj_pronoun_idx -= 1
                for _ in current_group:
                    if session_state.conj_completed_pronouns:
                        session_state.conj_completed_pronouns.pop()
            elif session_state.conj_verb_idx > 0:
                session_state.conj_verb_idx -= 1
                session_state.conj_pronoun_idx = 0
                session_state.conj_completed_pronouns = []
            for k in ["conj_last_markdown", "conj_feedback_html", "conj_audio", "conj_audio_announced", "conj_tense_errors", "conj_tense_status"]:
                if k in session_state:
                    del session_state[k]
        button("⏮️ Prev", width="stretch", on_click=go_prev, disabled=(verb_idx == 0 and pronoun_idx == 0))

    with btn_skip:
        def skip_pronoun():
            feedback_parts = []
            audio_parts = []
            for group_offset, pronoun in enumerate(current_group):
                colorized_parts = [
                    colorize_conjugation(
                        verb,
                        format_tense_value(t, targets[(group_offset, t)], group_start + group_offset),
                        target_lists[t]
                    )
                    for t in active_tenses
                ]
                feedback_parts.append(f"<b>Skipped ({pronoun}):</b> " + " &ensp;·&ensp; ".join(colorized_parts))
                audio_parts.extend(
                    format_tense_value(t, targets[(group_offset, t)], group_start + group_offset)
                    for t in active_tenses
                )
                completed_entry = {"Pronoun": pronoun}
                for t in active_tenses:
                    completed_entry[t.capitalize()] = colorized_parts[active_tenses.index(t)]
                session_state.conj_completed_pronouns.append(completed_entry)
            session_state.conj_feedback_html = "<br>".join(feedback_parts)
            session_state.conj_audio = ", ".join(audio_parts)
            session_state.conj_pronoun_idx += 1
            for k in ["conj_last_markdown", "conj_tense_errors", "conj_tense_status"]:
                if k in session_state:
                    del session_state[k]
            if session_state.conj_pronoun_idx >= total_pronoun_groups:
                session_state.conj_verb_completed = True
            else:
                session_state.conj_audio_announced = set()
                session_state.conj_focus_tense = (
                    conjugation_input_label(
                        active_tenses[0],
                        PRONOUN_GROUPS[session_state.conj_pronoun_idx][0]
                    )
                )
        button("⏭️ Skip", width="stretch", on_click=skip_pronoun)

    with btn_skip_verb:
        def skip_verb():
            session_state.conj_verb_idx += 1
            session_state.conj_pronoun_idx = 0
            session_state.conj_verb_completed = False
            session_state.conj_completed_pronouns = []
            session_state.conj_focus_tense = first_input_label
            for key in ["conj_last_markdown", "conj_audio", "conj_audio_announced", "conj_feedback_html", "conj_tense_errors", "conj_tense_status"]:
                if key in session_state:
                    del session_state[key]
        button("🔀 Skip Verb", width="stretch", on_click=skip_verb)

    with btn_show:
        if button("📖 Show", width="stretch"):
            answer_lines = []
            audio_parts = []
            for group_offset, pronoun in enumerate(current_group):
                answers_str = " &ensp;·&ensp; ".join([
                    f"<b>{t.capitalize()}</b>: {colorize_conjugation(verb, format_tense_value(t, targets[(group_offset, t)], group_start + group_offset), target_lists[t])}"
                    for t in active_tenses
                ])
                answer_lines.append(f"<b>{pronoun}</b>: {answers_str}")
                audio_parts.extend(
                    format_tense_value(t, targets[(group_offset, t)], group_start + group_offset)
                    for t in active_tenses
                )
            session_state.conj_last_markdown = "💡 Expected:<br>" + "<br>".join(answer_lines)
            session_state.conj_audio = ", ".join(audio_parts)
            rerun()

    with btn_quit:
        if button("🛑 Quit", width="stretch"):
            session_state.conj_mode = "input"
            rerun()

    if "conj_feedback_html" in session_state:
        markdown(
            f"<div style='text-align: center; font-size: 24px; padding: 8px; border-radius: 6px; background-color: rgba(0,255,100,0.08); margin-bottom: 12px;'>"
            f"✅ {session_state.conj_feedback_html}</div>",
            unsafe_allow_html=True
        )
        del session_state.conj_feedback_html

    # Live Evolving Pronouns Table for this Verb
    if session_state.conj_completed_pronouns:
        with expander("📋 Completed Pronouns so far", expanded=True):
            df_comp = DataFrame(session_state.conj_completed_pronouns)
            custom_css = """<style>
table.dataframe { width: 100% !important; font-size: 16px !important; }
table.dataframe th, table.dataframe td { padding: 6px 12px !important; text-align: left !important; border: 1px solid #444 !important; }
table.dataframe th { background-color: #2b2b2b !important; }
</style>"""
            markdown(custom_css + df_comp.to_html(escape=False, index=False), unsafe_allow_html=True)

    markdown("#### 📚 Regular Verb Terminations (All Tenses)")
    render_termination_table(markdown, PRONOUNS)

def _list_screen():
    markdown("## 📋 Conjugation Database (Show All)")
    
    col_back, col_toggle, col_pdf = columns([1, 2, 1], vertical_alignment="center")
    with col_back:
        if button("🔙 Back to Input", type="primary", width="stretch"):
            session_state.conj_mode = "input"
            rerun()
    with col_toggle:
        show_tense_tags = toggle("Show tense tags [Pas/Pres/Fut]", value=False, key="list_show_tense_tags")
    with col_pdf:
        try:
            pdf_data = get_pdf_bytes()
            download_button(
                label="📥 Download PDF",
                data=pdf_data,
                file_name="Spanish_Verbs_Conjugations.pdf",
                mime="application/pdf",
                width="stretch"
            )
        except Exception as e:
            markdown(f"⚠️ PDF: {e}")

    history = load_history()
    all_verbs = load_all_verbs()
    combined_verbs = merge_verb_databases(all_verbs, history)
    
    if not combined_verbs:
        markdown("No verbs found in database.")
        return

    search_query = text_input("🔍 Filter verbs:", placeholder="Search by verb or translation...").strip().lower()
    available_tenses = get_tenses(combined_verbs)
    
    markdown(
        f"**Available Tenses:** {', '.join([t.capitalize() for t in available_tenses])} &ensp;|&ensp; "
        f"**Total Verbs:** {len(combined_verbs)}<br>"
        f"<span style='color: #aaa; font-size: 14px;'>ℹ️ Order in each cell: <b>Past</b> &ensp;→&ensp; <b>Present</b> &ensp;→&ensp; <b>Future</b> &ensp;→&ensp; <b>Perfecto</b> &ensp;→&ensp; <b>Imperfecto</b></span>",
        unsafe_allow_html=True
    )

    tense_tag_map = {
        "past": "<span style='color: #888; font-size: 11px;'>[Pas]</span> ",
        "present": "<span style='color: #888; font-size: 11px;'>[Pres]</span> ",
        "future": "<span style='color: #888; font-size: 11px;'>[Fut]</span> ",
        "perfecto": "<span style='color: #888; font-size: 11px;'>[Perf]</span> ",
        "imperfecto": "<span style='color: #888; font-size: 11px;'>[Imperf]</span> "
    }

    # Main Table: All Tenses in the SAME CELL per pronoun!
    rows = []
    for full_verb_text, conjugations in combined_verbs.items():
        if search_query and search_query not in full_verb_text.lower():
            continue

        verb = full_verb_text.split(" (")[0].strip() if " (" in full_verb_text else full_verb_text
        row = {"Verb": full_verb_text}
        
        for p_idx in range(6):
            cell_lines = []
            for t in available_tenses:
                if is_new_format(conjugations) and t in conjugations:
                    conj_list = conjugations[t]
                elif not is_new_format(conjugations) and t == "present":
                    conj_list = conjugations
                else:
                    continue

                display_values = get_tense_values(t, conj_list)
                if isinstance(display_values, list) and p_idx < len(display_values):
                    tag = tense_tag_map.get(t.lower(), f"<span style='color: #888; font-size: 11px;'>[{t[:3]}]</span> ") if show_tense_tags else ""
                    formatted_values = [
                        format_tense_value(t, value, value_index)
                        for value_index, value in enumerate(display_values)
                    ]
                    colored_conj = colorize_conjugation(verb, formatted_values[p_idx], formatted_values)
                    cell_lines.append(f"{tag}{colored_conj}")
            
            row[PRONOUNS[p_idx]] = "<br>".join(cell_lines) if cell_lines else "-"
        
        rows.append(row)

    if rows:
        df_all = DataFrame(rows)
        col_order = ["Verb"] + PRONOUNS
        df_all = df_all[[c for c in col_order if c in df_all.columns]]
        custom_css = """<style>
table.dataframe {
    width: 100% !important;
    font-size: 16px !important;
    border-collapse: collapse !important;
    margin-top: 10px !important;
}
table.dataframe th, table.dataframe td {
    padding: 8px 12px !important;
    text-align: left !important;
    vertical-align: top !important;
    border: 1px solid #444 !important;
    line-height: 1.5 !important;
}
table.dataframe th {
    background-color: #2b2b2b !important;
    font-weight: bold !important;
    font-size: 16px !important;
}
table.dataframe tr:nth-child(even) {
    background-color: rgba(255, 255, 255, 0.02) !important;
}
</style>"""
        markdown(custom_css + df_all.to_html(escape=False, index=False), unsafe_allow_html=True)
        markdown(f"*Showing {len(rows)} verbs*")
    else:
        markdown(f"*No verbs found matching '{search_query}'.*")

    # Optional: Individual Tense Breakdown in expanders below
    with expander("📂 Individual Tense Breakdowns", expanded=False):
        for tense in available_tenses:
            with expander(f"📖 {tense.upper()} Tense Only", expanded=False):
                data = []
                for full_verb_text, conjugations in combined_verbs.items():
                    if search_query and search_query not in full_verb_text.lower():
                        continue

                    verb = full_verb_text.split(" (")[0].strip() if " (" in full_verb_text else full_verb_text
                    
                    if is_new_format(conjugations) and tense in conjugations:
                        conj_list = conjugations[tense]
                    elif not is_new_format(conjugations) and tense == "present":
                        conj_list = conjugations
                    else:
                        continue

                    display_values = get_tense_values(tense, conj_list)
                    if not isinstance(display_values, list) or len(display_values) < 6:
                        continue
                    
                    try:
                        row = {"Verb": full_verb_text}
                        formatted_values = [
                            format_tense_value(tense, value, value_index)
                            for value_index, value in enumerate(display_values)
                        ]
                        for p_idx in range(6):
                            row[PRONOUNS[p_idx]] = colorize_conjugation(
                                verb, formatted_values[p_idx], formatted_values
                            )
                        data.append(row)
                    except Exception:
                        continue
                
                if data:
                    df = DataFrame(data)
                    col_order = ["Verb"] + PRONOUNS
                    df = df[[col for col in col_order if col in df.columns]]
                    markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
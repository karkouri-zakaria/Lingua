from streamlit import cache_data, columns,fragment, markdown, rerun, session_state, text_input, toast, warning, write

from Files.Upload import json_upload_dialog
def save_answers():
    from json import dump
    from pathlib import Path
    Path("History").mkdir(parents=True, exist_ok=True)
    with open(Path(f"./History/Answers_{session_state.uploaded_file_data.name[:-5]}.json"), 'w', newline='', encoding='utf-8-sig') as f:
        dump(session_state.Answers, f, ensure_ascii=False, indent=4)
def load_answers():
    from json import load
    from pathlib import Path
    filepath = Path(f"./History/Answers_{session_state.uploaded_file_data.name[:-5]}.json") 
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = load(f)
            if len(data) == 0:
                json_upload_dialog(msg="Empty `JSON`. take the Quiz or Upload a `JSON` file.")
            else:
                 session_state.Answers = data
                 rerun()
    else:
        json_upload_dialog(msg="No `JSON` found.")
@cache_data
def normalize_german(text):
    return text.translate(str.maketrans({'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'}))

@cache_data
def normalize_spanish(text):
    # Remove diacritics for fair comparison when users omit accents (á, é, í, ó, ú, ü, ñ)
    import unicodedata
    decomposed = unicodedata.normalize('NFD', text)
    return ''.join(ch for ch in decomposed if unicodedata.category(ch) != 'Mn')
@fragment
def check_answer(flashcard, current_index, total_flashcards):    
    from time import sleep
    from Audio_gen.generate_audio import generate_audio
    from Answers.colorize import colorize_noun
    from mutagen.mp3 import MP3
    from pathlib import Path
    from difflib import SequenceMatcher
    from html import escape
    from collections import Counter
    import re
    # Language-aware input hint
    lang = session_state.get("language_code", "de")
    prompt = "Type your answer here :"
    right, left = columns([1, 19], gap="small", width="stretch")
    hint_clicked = right.button("Hint", key=f"hint_button_{current_index}", width="stretch", type="primary")
    answer = left.text_input(label=prompt, label_visibility="collapsed", placeholder=prompt, key=f"answer_input_{current_index}")
    if lang == "de":
        correct_answer = normalize_german(flashcard['Target'])
        user_answer = normalize_german(answer.lower())
    elif lang == "es":
        correct_answer = normalize_spanish(flashcard['Target'])
        user_answer = normalize_spanish(answer.lower())
    else:
        correct_answer = flashcard['Target']
        user_answer = answer.lower()
    for sep in ["·", "\u00B7"]:
        correct_answer = correct_answer.replace(sep, "")
        user_answer = user_answer.replace(sep, "")
    if answer:
        if len(user_answer) > len(correct_answer):
            warning("Answer is longer than needed.")
            return
        feedback = ""
        mistakes_found = False

        matcher = SequenceMatcher(None, user_answer.lower(), correct_answer.lower())
        
        # Pre-calculate missing characters for "misplaced" detection
        missing_chars = Counter()
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ('replace', 'insert'):
                for char in correct_answer[j1:j2]:
                    if char.isalpha():
                        missing_chars[char.lower()] += 1

        matched_indices = set()
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for idx in range(j1, j2):
                    char = correct_answer[idx]
                    feedback += f"<span style='color: green;'>{escape(char)}</span>"
                    if char.isalpha():
                        matched_indices.add(idx)
            elif tag == 'replace':
                mistakes_found = True
                for char in user_answer[i1:i2]:
                    char_lower = char.lower()
                    if char.isalpha() and missing_chars[char_lower] > 0:
                        feedback += f"<span style='color: orange;'>{escape(char)}</span>"
                        missing_chars[char_lower] -= 1
                for char in correct_answer[j1:j2]:
                    if not char.isalpha():
                        feedback += f"<span style='color: yellow;'>{escape(char)}</span>"
                    else:
                        feedback += f"<span style='color: red;'>&ensp;&lowbar;&ensp;</span>"
            elif tag == 'insert':
                if j2 != len(correct_answer):
                    mistakes_found = True
                for char in correct_answer[j1:j2]:
                    if char.isspace():
                        feedback += f"<span style='color: red;'>&ensp;&ensp;&ensp;</span>"
                    elif not char.isalpha():
                        feedback += f"<span style='color: yellow;'>&ensp;{escape(char)}&ensp;</span>"
                    elif not mistakes_found:
                        feedback += f"<span style='color: yellow;'>&ensp;&lowbar;</span>"
                    else:
                        feedback += f"<span style='color: red;'>&ensp;&lowbar;&ensp;</span>"
            elif tag == 'delete':
                mistakes_found = True
                for char in user_answer[i1:i2]:
                    char_lower = char.lower()
                    if char.isalpha() and missing_chars[char_lower] > 0:
                        feedback += f"<span style='color: orange;'>{escape(char)}</span>"
                        missing_chars[char_lower] -= 1

        if user_answer.lower() == correct_answer.lower() and not mistakes_found:
            markdown(f"##### ⇒ {colorize_noun(flashcard)}", unsafe_allow_html=True)
            right, left = columns(2, gap="small")
            right.success("✅ That's 100% correct:")
            try:
                audio_path = Path(f"Audios/{flashcard['Target']}.mp3")
                if not audio_path.exists():
                    audio_path = generate_audio(flashcard["Target"], lang=session_state.get("language_code", "de"))
                if session_state.auto_continue:
                    with open(audio_path, "rb") as audio_file:
                        left.audio(audio_file, format="audio/mp3", autoplay=True)
                    sleep(MP3(audio_path).info.length + 2)
                    if not session_state.show_wrongs:
                        session_state.Answers = [answer for answer in session_state.Answers if answer[2] != flashcard['Target']]
                        session_state.Answers.append([int(current_index)+1, flashcard['Source'], flashcard['Target'], True])
                    session_state.flashcard_index = (current_index + 1) % total_flashcards
                    save_answers()
                    rerun()
            except Exception as e:
                write(f"Error generating audio: {str(e)}")
            save_answers()
        elif mistakes_found:
            articles = {"das", "der", "die", "(das)", "(der)", "(die)","el", "(el)", "los", "(los)", "la", "(la)", "las", "(las)"}
            leftover_counts = []
            for match in re.finditer(r'\S+', correct_answer):
                s, e = match.span()
                if correct_answer[s:e].lower() in articles:
                    continue
                if not any(c.isalpha() for c in correct_answer[s:e]):
                    continue
                leftover_counts.append(sum(1 for i in range(s, e) if correct_answer[i].isalpha() and i not in matched_indices))
            leftover_chars = ", ".join(map(str, leftover_counts))
            markdown(f"##### {feedback}&ensp;&ensp;<span style='font-size:0.7em'>[{leftover_chars}]</span>", unsafe_allow_html=True)
            if articles & set(flashcard['Target'].split()):
                    write("Articles: ", ", ".join(articles & set(flashcard['Target'].split())))
            sleep(1)
        else:
            articles = {"das", "der", "die", "(das)", "(der)", "(die)","el", "(el)", "los", "(los)", "la", "(la)", "las", "(las)"}
            leftover_counts = []
            for match in re.finditer(r'\S+', correct_answer):
                s, e = match.span()
                if correct_answer[s:e].lower() in articles:
                    continue
                if not any(c.isalpha() for c in correct_answer[s:e]):
                    continue
                leftover_counts.append(sum(1 for i in range(s, e) if correct_answer[i].isalpha() and i not in matched_indices))
            leftover_chars = ", ".join(map(str, leftover_counts))
            markdown(f"##### {feedback}&ensp;&ensp;<span style='font-size:0.7em'>[{leftover_chars}]</span>", unsafe_allow_html=True)
            sleep(1)
    if hint_clicked:
        matcher = SequenceMatcher(None, user_answer.lower(), correct_answer.lower())
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                if j1 < len(correct_answer):
                    write(f"##### \"{correct_answer[j1].lower()}\"")
                break
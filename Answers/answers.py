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
            if len(data) == 0: json_upload_dialog()
            else:
                 session_state.Answers = data
                 rerun()
    else:
        json_upload_dialog()
@cache_data
def normalize_german(text):
    return text.translate(str.maketrans({'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'}))
@fragment
def check_answer(flashcard, current_index, total_flashcards):    
    from time import sleep
    from Audio_gen.generate_audio import generate_audio
    from Answers.colorize import colorize_noun
    from mutagen.mp3 import MP3
    answer = text_input(
        "Type your answer here (ä : ae || ö : oe || ü : ue || ß : ss) :",
        key=f"answer_input_{current_index}",
    )
    if answer:
        correct_answer = normalize_german(flashcard['Target'])
        user_answer = normalize_german(answer.lower())
        for sep in ["·", "\u00B7"]:
            correct_answer = correct_answer.replace(sep, "")
            user_answer = user_answer.replace(sep, "")
        feedback = ""
        mistakes_found = False
        if len(user_answer) > len(correct_answer):
                warning("Your answer is too long. Please try again.")
                mistakes_found = True
        else:
            for i in range(len(correct_answer)):            
                if i < len(user_answer):
                    if user_answer[i].lower() == correct_answer[i].lower():
                        feedback += f"<span style='color: green;'>{correct_answer[i]}</span>"
                    elif not correct_answer[i].isalpha():
                        feedback += f"<span style='color: yellow;'>{correct_answer[i]}</span>"
                        mistakes_found = True
                    else:
                        feedback += f"<span style='color: red;'>&ensp;&lowbar;&ensp;</span>"
                        mistakes_found = True
                elif correct_answer[i] in [" ", "\xa0"]:
                    feedback += f"<span style='color: red;'>&#160;</span>"
                elif not correct_answer[i].isalpha():
                        feedback += f"<span style='color: yellow;'>{correct_answer[i]}</span>"
                        mistakes_found = True
                elif not mistakes_found:
                    feedback += f"<span style='color: yellow;'>&ensp;&lowbar;</span>"
                else :
                    feedback += f"<span style='color: red;'>&ensp;&lowbar;</span>"
                    mistakes_found = True
            if user_answer.lower() == correct_answer.lower() and not mistakes_found:
                    markdown(f"# ⇒ {colorize_noun(flashcard)}", unsafe_allow_html=True)
                    right, left = columns(2, gap="small")
                    right.success("✅ That's 100% correct:")
                    try:
                        audio_path = Path(f"cached_audios/{flashcard['Target']}.mp3")
                        if not audio_path.exists():
                            audio_path = generate_audio(flashcard["Target"])
                        with open(audio_path, "rb") as audio_file:
                            left.audio(audio_file, format="audio/mp3", autoplay=True)
                        if session_state.auto_continue:
                            sleep(MP3(audio_path).info.length + 2)
                            if not session_state.show_wrongs:
                                session_state.Answers = [answer for answer in session_state.Answers if answer[2] != flashcard['Target']]
                                session_state.Answers.append([int(current_index)+1, flashcard['Source'], flashcard['Target'], True])
                            session_state.flashcard_index = (current_index + 1) % total_flashcards
                            rerun()
                    except Exception as e:
                        write(f"Error generating audio: {str(e)}")
                    save_answers()
            elif mistakes_found:
                markdown(f"> {feedback}", unsafe_allow_html=True)
                articles = {"das", "der", "die", "(das)", "(der)", "(die)"}
                if articles & set(flashcard['Target'].split()):
                        write("Articles: ", ", ".join(articles & set(flashcard['Target'].split())))
                toast(f"❌ **Wrong try again.**")
                sleep(1)
            else:
                markdown(f"{feedback}", unsafe_allow_html=True)
                toast(f"👍🏼 Correct continue ...")
                sleep(1)
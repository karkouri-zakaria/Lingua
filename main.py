from streamlit import audio, balloons, button, columns, data_editor, expander, markdown, number_input, rerun, session_state, set_page_config, sidebar, toast, write, selectbox, navigation, Page
from Answers.colorize import colorize_noun
from Sidebar.appSidebar import AppSidebar
from Answers.answers import load_answers, save_answers
from Audio_gen.generate_audio import generate_audio, generate_audios
from pathlib import Path
from time import sleep
from mutagen.mp3 import MP3
from Quiz_tab.init import init_session_state
from Quiz_tab.keyboard_handler import keyboard_handler
def main():
    set_page_config(page_title="Lingua", page_icon="🐦", layout="wide", initial_sidebar_state="expanded")
    def reader(text, pause=1):
        audio_path = Path(f"Audios/{text}.mp3")
        if not audio_path.exists():
            audio_path = generate_audio(text)
        with open(audio_path, "rb") as audio_file:
            audio(audio_file, format="audio/mp3", autoplay=True)
        sleep(MP3(audio_path).info.length + pause)
    keyboard_handler()
    init_session_state()
    sidebar_manager = AppSidebar()
    if session_state.uploaded_file_data is None:
        from Files.Upload import file_upload_dialog
        with sidebar:
            lang_display_to_code = {"Spanish": "es", "German": "de"}
            current_lang_name = session_state.get("language_name", "Spanish")
            selected_lang = selectbox(
                "Language",
                options=list(lang_display_to_code.keys()),
                index=list(lang_display_to_code.keys()).index(current_lang_name) if current_lang_name in lang_display_to_code else 0,
                key="language_select_upload_modal",
            )
            # Persist selection
            session_state.language_name = selected_lang
            session_state.language_code = lang_display_to_code[selected_lang]
            if button("Upload", icon="📂", width='stretch'):
                file_upload_dialog()
            if button("Last file", icon="📄", width='stretch', disabled=not Path("temp.xlsx").exists()):
                session_state.uploaded_file_data = open("temp.xlsx", "rb")
                rerun()
    else:
        with sidebar:
            left_button, right_button = columns(2, gap="small")
            if left_button.button("🗑️", width='stretch'):
                    session_state.flashcards_df = None
                    session_state.uploaded_file_data = None
                    session_state.success_value = False
                    session_state.Answers.clear()
                    rerun()
            if right_button.button("🪣", on_click=lambda: session_state.Answers.clear(), width='stretch'):
                    session_state.flashcard_index = 0
                    save_answers()
                    rerun()
            if session_state.flashcards_df is not None and not session_state.Show_all_anwsers and not session_state.show_wrongs:
                with right_button.popover("📋", width='stretch'):
                    from itertools import count, groupby, starmap
                    unanswered = sorted(i+1 for i, flashcard in session_state.flashcards_df.iterrows() if not any(answer[2] == flashcard["Target"] for answer in session_state.Answers))
                    ranges = starmap(lambda _, grp: list(grp), groupby(unanswered, key=lambda x, c=count(): x - next(c)))
                    write(f"Unanswered: ")
                    for range in ranges:
                        label = f"{range[0]}-{range[-1]}" if len(range) > 1 else str(range[0])
                        if button(label, key=f"unanswered_{label}"): session_state.flashcard_index = range[0] - 1
            if left_button.button("♾️", width='stretch'):
                load_answers()
    if "flashcards_df" not in session_state or session_state.flashcards_df is None:
        from Files.Handle_file_upload import Handle_file_upload
        session_state.flashcards_df = Handle_file_upload(session_state.uploaded_file_data, session_state.success_value)
        if session_state.flashcards_df is not None:
            session_state.flashcards_df = session_state.flashcards_df.iloc[::-1].reset_index(drop=True)
            session_state.original_flashcards_df = session_state.flashcards_df.copy()
            try:
                generate_audios(session_state.flashcards_df)
            except Exception as e:
                toast(f"Error generating audio files: {e}", icon="🔊")
    if session_state.flashcards_df is not None:
        with sidebar:
            current_index = session_state.flashcard_index if session_state.flashcard_index < len(session_state.flashcards_df ) else 0
            if not session_state.flashcards_df.empty: flashcard = session_state.flashcards_df.iloc[current_index]
            total_flashcards = len(session_state.flashcards_df)
            if len(session_state.Answers) > 1 or not session_state.show_wrongs:
                def update_flashcard_index():
                    session_state.flashcard_index = session_state.page_input - 1
                try:
                    session_state.page_input = session_state.flashcard_index + 1
                    number_input(f"Card N° ({len(session_state.flashcards_df)} total): ", min_value=1, max_value=len(session_state.flashcards_df), step=1, key="page_input", on_change=update_flashcard_index)
                except:
                    pass
            with left_button:
                if button("✖", key="wrong_button", width='stretch', type="primary" if any(answer[0] == flashcard['Source'] and not answer[2] for answer in session_state.Answers) else "secondary") and not session_state.show_wrongs:
                    session_state.Answers = [answer for answer in session_state.Answers if answer[2] != flashcard['Target']]
                    session_state.Answers.append([int(current_index)+1, flashcard['Source'], flashcard['Target'], False])
                    session_state.flashcard_index = (current_index + 1) % total_flashcards
                    save_answers()
                    markdown(f"{colorize_noun(flashcard)}", unsafe_allow_html=True)
                    reader(flashcard["Target"])
                    rerun()
            with right_button:
                if button("✔", key="correct_button", width='stretch', type="  " if any(answer[0] == flashcard['Source'] and answer[2] for answer in session_state.Answers) else "secondary") and not session_state.show_wrongs:
                    session_state.Answers = [answer for answer in session_state.Answers if answer[2] != flashcard['Target']]
                    session_state.Answers.append([int(current_index)+1, flashcard['Source'], flashcard['Target'], True])
                    session_state.flashcard_index = (current_index + 1) % total_flashcards
                    save_answers()
                    markdown(f"{colorize_noun(flashcard)}", unsafe_allow_html=True)
                    reader(flashcard["Target"])
                    rerun()
            with left_button:
                if button("➖", key="previous_button", width='stretch', type="primary" if any(answer[0] == flashcard['Source'] and not answer[2] for answer in session_state.Answers) else "secondary") and not session_state.show_wrongs:
                    session_state.flashcard_index = (current_index - 1) % total_flashcards
                    rerun()
            with right_button:
                if button("➕", key="next_button", width='stretch', type="  " if any(answer[0] == flashcard['Source'] and answer[2] for answer in session_state.Answers) else "secondary") and not session_state.show_wrongs:
                    session_state.flashcard_index = (current_index + 1) % total_flashcards
                    rerun()
            with expander("Settings", expanded=False, icon="⚙️"):
                left_button, right_button = columns(2, gap="small", vertical_alignment='center')
                session_state.auto_continue = right_button.toggle("⏩", key="auto", value=session_state.auto_continue, help="Auto-continue")
                session_state.Show_all_anwsers = left_button.toggle("🔠", key="show", value=session_state.Show_all_anwsers, help="Learning mode")
                session_state.show_wrongs = left_button.toggle("🔂", key="wrongs", value=session_state.show_wrongs, help="Review mistakes")
                session_state.shuffle = right_button.toggle("🔀", key="shuffling", value=session_state.shuffle, help="Shuffle flashcards")
            sidebar_manager.download_answers()
            if session_state.show_wrongs: session_state.flashcards_df = session_state.original_flashcards_df[session_state.original_flashcards_df["Source"].isin({answer[1] for answer in session_state.Answers if answer[3] == False})]
            if session_state.shuffle: session_state.flashcards_df = session_state.flashcards_df.sample(frac=1)
        if len(session_state.Answers) == total_flashcards and total_flashcards != 0 and not session_state.show_wrongs:
            balloons()
            write("""<br><div style="text-align:center; font-size:50px;"><strong>All the cards are done!🥳🎆</strong><br></div>""", unsafe_allow_html=True)
        else :
            def quiz_page():
                from Quiz_tab.Quiz import Quiz
                Quiz(session_state.flashcards_df)
                with sidebar:
                    if session_state.flashcards_df is not None: 
                        with sidebar.expander("Timer", icon="⏱️"):
                            sidebar_manager.timer()
            def viewer_page():
                from Flashcards.Viewer import viewer_table
                viewer_table(session_state.flashcards_df)
            pg = navigation([
                Page(quiz_page, title=f"🎮 {session_state.language_name} Quiz - {round(100*len(session_state.Answers)/len(session_state.flashcards_df),2)}%"),
                Page(viewer_page, title=f"📓All cards {session_state.uploaded_file_data.name if not session_state.flashcards_df is None else 'All cards'}")
            ])
            pg.run()
        if not session_state.Show_all_anwsers and not session_state.show_wrongs:    
            col1, col2 = columns([20, 1], gap="small")
            if col2.button("🔻all ") and len([r for r in session_state.Answers if r[3] == False]) > 0: col1.data_editor([{f"👍🏼 {((wval := sum(r[3] == True for r in session_state.Answers)) / (l := len(session_state.flashcards_df) or 1) * 100):.1f}% - {wval}       ||       👎🏼 {((wval := sum(r[3] == False for r in session_state.Answers)) / l * 100):.1f}% - {wval}       ||       ✍🏼 {round(100 - 100*len(session_state.Answers) / len(session_state.flashcards_df), 2)}% - {len(session_state.flashcards_df) - len(session_state.Answers)}" : f"{r[0]} - {r[1]} : {r[2]}"} for r in session_state.Answers if r[3] == False][::-1], hide_index=True, width='stretch')
            else: col1.data_editor([{f"👍🏼 {((wval := sum(r[3] == True for r in session_state.Answers)) / (l := len(session_state.flashcards_df) or 1) * 100):.1f}% - {wval}       ||       👎🏼 {((wval := sum(r[3] == False for r in session_state.Answers)) / l * 100):.1f}% - {wval}       ||       ✍🏼 {round(100 - 100*len(session_state.Answers) / len(session_state.flashcards_df), 2)}% - {len(session_state.flashcards_df) - len(session_state.Answers)}" : f"{r[0]} - {r[1]} : {r[2]}"} for r in reversed(session_state.Answers) if not r[3]][:3], hide_index=True, width='stretch')
    else:
        pass
    # Keyboard mapping
    markdown("""
        <style>
            .footer-shortcuts { font-size: 1em; color: gray; text-align: center; margin-top: 15px; font-family: sans-serif; }
            .footer-shortcuts kbd { background-color: #f7f7f7; border: 1px solid #ccc; border-radius: 3px; box-shadow: 0 1px 0 rgba(0,0,0,0.2); color: #333; display: inline-block; font-size: 0.9em; font-weight: bold; line-height: 1.2; padding: 1px 4px; margin: 0 1px; white-space: nowrap; }
            .footer-shortcuts .sep { color: #b0b0b0; margin: 0 4px; }
            @media (prefers-color-scheme: dark) { .footer-shortcuts kbd { background-color: #444; border-color: #666; color: #ddd; } .footer-shortcuts .sep { color: #666; } }
        </style>
        <div class="footer-shortcuts">
            <span style="white-space: nowrap;">
                <kbd>Ctrl</kbd>:  + [ &ensp;
                <kbd>⬆️</kbd>: ✔ <span class="sep">&ensp;|&ensp;</span> <kbd>⬇️</kbd>: ✖ <span class="sep">&ensp;|&ensp;</span> <kbd>➡️</kbd>: ➕ <span class="sep">&ensp;|&ensp;</span> <kbd>⬅️</kbd>: ➖ <span class="sep">&ensp;|&ensp;</span> 
                <kbd>𝐐</kbd>: 🗑️ <span class="sep">&ensp;|&ensp;</span> <kbd>𝐔</kbd>: Upload <span class="sep">&ensp;|&ensp;</span> <kbd>𝐋</kbd>: 📄 <span class="sep">&ensp;|&ensp;</span> <kbd>𝐄</kbd>: 🪣 <span class="sep">&ensp;|&ensp;</span> <kbd>𝐂</kbd>: ♾️ <span class="sep">&ensp;|&ensp;</span> <kbd>𝐌</kbd>: 📋 <span class="sep">&ensp;|&ensp;</span> 
                <kbd>⇧</kbd>: Hint <span class="sep">&ensp;|&ensp;</span> <kbd>␣</kbd>: Show ]
            </span> &ensp;&ensp;&ensp;&ensp;    
            <span style="white-space: nowrap;"><kbd>AltGr</kbd>:  🔉</span> &ensp;
            <span style="white-space: nowrap;"><kbd>Alt</kbd>:  🖊️</span>
        </div>
        """, unsafe_allow_html=True)
if __name__ == "__main__":
    main()
    
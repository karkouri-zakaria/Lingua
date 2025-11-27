from streamlit import audio, cache_data, columns, container, markdown, write
from Answers.colorize import colorize_noun
from Audio_gen.generate_audio import generate_audio
import pandas as pd
cache_data()
def display_flashcard(index, flashcard):
    """Display a single flashcard with its audio."""
    with container(border=True):
        ind, Src, Tar, Aud = columns([1, 6 , 6, 2])
        ind.write(f"> {index + 1}")
        Src.write(f"> {flashcard['Source']}")
        Tar.markdown(f"> {colorize_noun(flashcard)}", unsafe_allow_html=True)
        try:
            # Respect selected language for TTS
            from streamlit import session_state
            audio_file = generate_audio(flashcard['Target'], lang=session_state.get('language_code', 'de'))  
            with open(audio_file, "rb") as audio_data:
                Aud.audio(audio_data, format="audio/mp3", autoplay=False)
        except Exception as e:
            write(f"Error: {str(e)}")

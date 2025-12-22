from hashlib import md5
from os import makedirs, path
import re
from gtts import gTTS
from streamlit import cache_data, session_state

@cache_data
def generate_audio(text, lang=None, cache_dir="Audios"):
    """Generate or return cached path to TTS audio for given text and language.

    Args:
        text (str): The text to synthesize.
        lang (str|None): gTTS language code. Defaults to session_state.language_code or 'de'.
        cache_dir (str): Directory where audio files are stored.

    Returns:
        str: Path to the mp3 file.
    """
    # Filter out non-alphanumeric characters, but keep spaces and letters from all languages.
    cleaned_text = re.sub(r'[^\w\s/]', '', text, flags=re.UNICODE)

    # Resolve language selection
    resolved_lang = lang or session_state.get("language_code", "de")
    makedirs(cache_dir, exist_ok=True)
    # Include language in cache key and filename to prevent cross-language collisions
    cache_key = f"{resolved_lang}:{cleaned_text}".encode()
    audio_file = path.join(cache_dir, f"audio_{resolved_lang}_{md5(cache_key).hexdigest()}.mp3")
    if not path.exists(audio_file):
        try:
            tts = gTTS(text=cleaned_text, lang=resolved_lang)
            tts.save(audio_file)
        except Exception as e:
            raise RuntimeError(f"Error generating audio: {e}") from e
    return audio_file

def generate_audios(flashcards_df, cache_dir="Audios"):
    from pandas import DataFrame
    """Generate audio files for all flashcards."""
    if not session_state.get("audio_generated", False):
        makedirs(cache_dir, exist_ok=True)
        resolved_lang = session_state.get("language_code", "de")
        for index, flashcard in DataFrame(flashcards_df).iterrows():
            flashcards_df.at[index, "audio_path"] = generate_audio(flashcard["Target"], lang=resolved_lang, cache_dir=cache_dir)
        session_state.audio_generated = True

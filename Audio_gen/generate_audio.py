from hashlib import md5
from os import makedirs, path
from gtts import gTTS
from streamlit import cache_data, session_state, toast
@cache_data
def generate_audio(text, lang="de", cache_dir="Audios"):
    makedirs(cache_dir, exist_ok=True)
    audio_file = path.join(cache_dir, f"audio_{md5(text.encode()).hexdigest()}.mp3")
    if not path.exists(audio_file):
        try:
            tts = gTTS(text=text, lang=lang) 
            tts.save(audio_file)
            s=0
        except Exception as e:
            raise RuntimeError(f"Error generating audio: {e}") from e
    return audio_file
def generate_audios(flashcards_df, cache_dir="Audios"):
    from pandas import DataFrame
    """Generate audio files for all flashcards."""
    if not session_state.get("audio_generated", False):
        makedirs(cache_dir, exist_ok=True)
        for index, flashcard in DataFrame(flashcards_df).iterrows():
            flashcards_df.at[index, "audio_path"] = generate_audio(flashcard["Target"], cache_dir=cache_dir)
        session_state.audio_generated = True

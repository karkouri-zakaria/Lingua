def colorize_noun(flashcard, colors={("der", "(der)"): "DeepSkyBlue", ("die", "(die)"): "DeepPink", ("das", "(das)"): "LawnGreen"}): 
    """Colorize target text based on language-specific articles and verbs.

    - German: color the noun following der/die/das if capitalized (keeps current behavior).
    - Spanish: color the noun following el/la/los/las regardless of capitalization.
    - Verbs (when Source starts with 'to '): highlight syllables or the whole word.
    """
    from streamlit import session_state

    lang = session_state.get("language_code", "de")
    words = flashcard["Target"].split()

    # Choose color mapping per language
    if lang == "es":
        es_colors = {
            ("el", "(el)", "los", "(los)"): "DeepSkyBlue",  # masculine
            ("la", "(la)", "las", "(las)"): "DeepPink",     # feminine
        }
        color_map = {a: c for arts, c in es_colors.items() for a in arts}
        # Spanish nouns are not generally capitalized; color next token whenever an article is found
        for i, w in enumerate(words[:-1]):
            wl = w.lower()
            if wl in color_map:
                words[i+1] = f'<span style="color: {color_map[wl]};">{words[i+1]}</span>'
    else:
        # Default (German) behavior using provided colors
        color_map = {a: c for arts, c in colors.items() for a in arts}
        for i, w in enumerate(words[:-1]):
            wl = w.lower()
            if wl in color_map and words[i+1] and words[i+1][0].isupper():
                words[i+1] = f'<span style="color: {color_map[wl]};">{words[i+1]}</span>'

    # Verb highlighting (applies regardless of language when English source starts with 'to ')
    if flashcard.get("Source", "")[:3] == "to ":
        for i, w in enumerate(words):
            if '<span' in w or w.lower() in color_map:
                continue
            if "·" in w:
                left, right = w.split("·", 1)
                words[i] = f'<span style="color: yellow;">{left}</span>·<span style="color: orange;">{right}</span>'
            else:
                words[i] = f'<span style="color: orange;">{w}</span>'

    return " ".join(words)
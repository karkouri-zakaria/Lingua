from streamlit import write, markdown
def colorize_noun(flashcard, colors={("der", "(der)"): "DeepSkyBlue", ("die", "(die)"): "DeepPink", ("das", "(das)"): "LawnGreen"}):
    """Colorize target text based on language-specific articles and verbs.

    - German: color the noun following der/die/das if capitalized. For verbs,
              it highlights separable prefixes or the whole verb.
    - Spanish: color the noun following el/la/los/las. For verbs, it highlights
               -ar, -er, -ir endings or the whole verb.
    - Verbs are only colorized when the Source text starts with 'to '.
    """
    from streamlit import session_state

    lang = session_state.get("language_code", "de")
    words = flashcard["Target"].split()
    color_map = {}

    # --- Noun Highlighting ---
    if lang == "es":
        es_colors = {
            ("el", "(el)", "los", "(los)"): "DeepSkyBlue",  # masculine
            ("la", "(la)", "las", "(las)"): "DeepPink",     # feminine
        }
        color_map = {a: c for arts, c in es_colors.items() for a in arts}
        # For Spanish, color the noun after an article regardless of capitalization.
        for i, w in enumerate(words[:-1]):
            wl = w.lower()
            if wl in color_map:
                words[i+1] = f'<span style="color: {color_map[wl]};">{words[i+1]}</span>'
    else:  # Default to German behavior
        color_map = {a: c for arts, c in colors.items() for a in arts}
        # For German, color the noun after an article only if it is capitalized.
        for i, w in enumerate(words[:-1]):
            wl = w.lower()
            if wl in color_map and words[i+1] and words[i+1][0].isupper():
                words[i+1] = f'<span style="color: {color_map[wl]};">{words[i+1]}</span>'

    # --- Verb Highlighting ---
    if flashcard.get("Source", "")[:3].lower() == "to ":
        # Iterate through words to find verbs to colorize
        for i, w in enumerate(words):
            # Skip words that are already colorized (i.e., nouns) or are articles
            if '<span' in w or w.lower() in color_map:
                continue

            # Language-specific verb logic
            if lang == "es":
                w_clean = w.lower().strip(".,;:!?")
                if w_clean.endswith("ar"):
                    words[i] = f'{w[:-2]}<span style="color: yellow;">{w[-2:]}</span>'  # -ar verbs
                elif w_clean.endswith("arse"):
                    words[i] = f'{w[:-4]}<span style="color: yellow;">{w[-4:-2]}</span>' # -ar reflexive verbs
                    words[i] += f'<span>{w[-2:]}</span>'
                elif w_clean.endswith("er") or w_clean.endswith("erse"):
                    words[i] = f'{w[:-2]}<span style="color: red;">{w[-2:]}</span>'      # -er verbs
                elif w_clean.endswith("erse"):
                    words[i] = f'{w[:-4]}<span style="color: red;">{w[-4:-2]}</span>'   # -er reflexive verbs
                    words[i] += f'<span>{w[-2:]}</span>'
                elif w_clean.endswith("ir") or w_clean.endswith("irse"):
                    words[i] = f'{w[:-2]}<span style="color: orange;">{w[-2:]}</span>' # -ir verbs
                elif w_clean.endswith("irse"):
                    words[i] = f'{w[:-4]}<span style="color: orange;">{w[-4:-2]}</span>'
                    words[i] += f'<span>{w[-2:]}</span>'
                else:
                    # Fallback for other Spanish verbs (e.g., reflexives, irregulars)
                    words[i] = f'<span>{w}</span>'
            else:  # Default (German) verb logic
                if "·" in w: # Separable verbs
                    left, right = w.split("·", 1)
                    words[i] = f'<span style="color: yellow;">{left}</span>·<span style="color: orange;">{right}</span>'
                else: # Inseparable or regular verbs
                    words[i] = f'<span style="color: orange;">{w}</span>'

    return " ".join(words)
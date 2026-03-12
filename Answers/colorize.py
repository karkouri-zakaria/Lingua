from streamlit import write, markdown, session_state
from difflib import SequenceMatcher
def colorize_noun(flashcard, colors={("der", "(der)"): "DeepSkyBlue", ("die", "(die)"): "DeepPink", ("das", "(das)"): "LawnGreen"}):

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
                if w_clean.endswith("ar") or w_clean.endswith("ár"):
                    words[i] = f'{w[:-2]}<span style="color: yellow;">{w[-2:]}</span>'  # -ar verbs
                elif w_clean.endswith("ar·se") or w_clean.endswith("ár·se"):
                    words[i] = f'{w[:-5]}<span style="color: yellow;">{w[-5:-3]}</span>·<span>{w[-2:]}</span>' # -ar separable reflexive verbs
                elif w_clean.endswith("er") or w_clean.endswith("ér"):
                    words[i] = f'{w[:-2]}<span style="color: red;">{w[-2:]}</span>'      # -er verbs
                elif w_clean.endswith("er·se") or w_clean.endswith("ér·se"):
                    words[i] = f'{w[:-5]}<span style="color: red;">{w[-5:-3]}</span>·<span>{w[-2:]}</span>'  # -er separable reflexive verbs
                elif w_clean.endswith("ir") or w_clean.endswith("ír"):
                    words[i] = f'{w[:-2]}<span style="color: orange;">{w[-2:]}</span>' # -ir verbs
                elif w_clean.endswith("ir·se") or w_clean.endswith("ír·se"):
                    words[i] = f'{w[:-5]}<span style="color: orange;">{w[-5:-3]}</span>·<span>{w[-2:]}</span>' # -ir separable reflexive verbs
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

def colorize_conjugation(verb, conjugation):
    # 1. Handle cases where both have slashes (1-to-1 mapping)
    if "/" in verb and "/" in conjugation:
        v_parts = [v.strip() for v in verb.split("/")]
        c_parts = [c.strip() for c in conjugation.split("/")]
        if len(v_parts) == len(c_parts):
            return "/".join([colorize_conjugation(v, c) for v, c in zip(v_parts, c_parts)])

    # 2. Handle cases where ONLY the conjugation has a slash (e.g., Verb="Haber", Conj="Ha/Hay")
    if "/" in conjugation:
        c_parts = [c.strip() for c in conjugation.split("/")]
        return "/".join([colorize_conjugation(verb, c) for c in c_parts])

    # 3. Handle cases where ONLY the verb has a slash
    if "/" in verb:
        v_parts = [v.strip() for v in verb.split("/")]
        return "/".join([colorize_conjugation(v, conjugation) for v in v_parts])

    # 4. Standard Processing
    # Note: Added 'ay' to ensure "Hay" catches the suffix correctly!
    suffixes = [
        "amos", "emos", "imos", "ámos", "émos", "ímos",
        "ais", "eis", "is", "áis", "éis", "ís",
        "an", "en", "on", "as", "es", "oy", "ay", "ey", "o", "a", "e", 
        "án", "én", "ás", "és", "á", "é", "í", "ó"
    ]
    
    verb_lower = verb.lower()
    root = verb_lower[:-2] if verb_lower.endswith(("ar", "er", "ir")) else verb_lower
    
    # Sort suffixes by length descending
    sorted_sfx = sorted(list(set(suffixes)), key=len, reverse=True)
    suffix_match = next((s for s in sorted_sfx if conjugation.lower().endswith(s)), "")
    
    if suffix_match:
        stem_part = conjugation[:-len(suffix_match)]
        suffix_part = conjugation[-len(suffix_match):]
    else:
        stem_part, suffix_part = conjugation, ""

    colored_stem = ""
    for i, char in enumerate(stem_part):
        if i < len(root) and char.lower() == root[i].lower():
            colored_stem += char
        else:
            colored_stem += f'<span style="color: LawnGreen;">{char}</span>'
            
    colored_suffix = f'<span style="color: DeepPink;">{suffix_part}</span>' if suffix_part else ""
    return f"{colored_stem}{colored_suffix}"
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

def _common_prefix(values):
    values = [value.strip() for value in values if value and value.strip()]
    if not values:
        return ""

    prefix = values[0]
    for value in values[1:]:
        length = 0
        for left, right in zip(prefix.casefold(), value.casefold()):
            if left != right:
                break
            length += 1
        prefix = prefix[:length]
        if not prefix:
            break
    return prefix


def colorize_conjugation(verb, conjugation, subject_conjugations=None):
    """Highlight only the part shared by all subject conjugations."""
    if not subject_conjugations:
        return conjugation

    all_forms = []
    for form in subject_conjugations:
        all_forms.extend(part.strip() for part in form.split("/") if part.strip())

    common_part = _common_prefix(all_forms)
    if not common_part:
        return conjugation

    colored_common = f'<span style="color: LawnGreen;">{common_part}</span>'
    parts = [part.strip() for part in conjugation.split("/")]
    return "/".join(
        colored_common + part[len(common_part):]
        if part.casefold().startswith(common_part.casefold())
        else part
        for part in parts
    )
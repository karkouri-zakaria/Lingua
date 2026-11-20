from pandas import DataFrame
from html import escape

PRONOUN_TERMINATIONS = {
    "Presente": {
        "-ar": ["-o", "-as", "-a", "-amos", "-áis", "-an"],
        "-er": ["-o", "-es", "-e", "-emos", "-éis", "-en"],
        "-ir": ["-o", "-es", "-e", "-imos", "-ís", "-en"]
    },
    "Pretérito": {
        "-ar": ["-é", "-aste", "-ó", "-amos", "-asteis", "-aron"],
        "-er/-ir": ["-í", "-iste", "-ió", "-imos", "-isteis", "-ieron"]
    },
    "Imperfecto": {
        "-ar": ["-aba", "-abas", "-aba", "-ábamos", "-abais", "-aban"],
        "-er/-ir": ["-ía", "-ías", "-ía", "-íamos", "-íais", "-ían"]
    },
    "Perfecto": {
        "-ar": ["-ado"] * 6,
        "-er/-ir": ["-ido"] * 6
    },
    "Progresivo": {
        "-ar": ["-ando", "-ando", "-ando", "-ando", "-ando", "-ando"],
        "-er/-ir": ["-iendo", "-iendo", "-iendo", "-iendo", "-iendo", "-iendo"]
    },
    "Futuro": {
        "-ar": ["-é", "-ás", "-á", "-emos", "-éis", "-án"],
        "-er/-ir": ["-é", "-ás", "-á", "-emos", "-éis", "-án"]
    }
}

font_size = 14  


def render_termination_table(markdown, pronouns):
    colors = {
        "-ar": "#ff9999",
        "-er": "#87cefa",
        "-ir": "#90ee90",
        "-er/-ir": "#fde68a",
    }

    def format_variants(verb_types, index):
        values = []
        er_value = verb_types.get("-er", [])[index] if "-er" in verb_types else None
        ir_value = verb_types.get("-ir", [])[index] if "-ir" in verb_types else None
        er_ir_match = er_value is not None and er_value == ir_value

        for verb_type, endings in verb_types.items():
            if verb_type == "-ir" and er_ir_match:
                continue
            if verb_type == "-er" and er_ir_match:
                values.append(("-er/-ir", endings[index].removeprefix("-")))
            else:
                values.append((verb_type, endings[index].removeprefix("-")))

        unique_values = {value for _, value in values}
        if len(unique_values) == 1:
            return escape(values[0][1])

        common_prefix = values[0][1]
        for _, value in values[1:]:
            prefix_length = 0
            for left, right in zip(common_prefix, value):
                if left != right:
                    break
                prefix_length += 1
            common_prefix = common_prefix[:prefix_length]

        common_suffix = values[0][1][len(common_prefix):]
        for _, value in values[1:]:
            suffix_length = 0
            left = values[0][1]
            while (
                suffix_length < len(left) - len(common_prefix)
                and suffix_length < len(value) - len(common_prefix)
                and left[-suffix_length - 1] == value[-suffix_length - 1]
            ):
                suffix_length += 1
            common_suffix = common_suffix[-suffix_length:] if suffix_length else ""

        colored_middle = []
        for verb_type, value in values:
            middle_end = len(value) - len(common_suffix) if common_suffix else len(value)
            middle = value[len(common_prefix):middle_end]
            colored_middle.append(
                f"<span style='color: {colors[verb_type]};'>{escape(middle)}</span>"
            )
        parts = []
        if common_prefix:
            parts.append(escape(common_prefix))
        parts.append("/".join(colored_middle))
        if common_suffix:
            parts.append(escape(common_suffix))
        return " · ".join(parts)

    termination_rows = [
        {
            tense: format_variants(verb_types, index)
            for tense, verb_types in PRONOUN_TERMINATIONS.items()
        }
        for index in range(len(pronouns))
    ]

    tense_names = list(PRONOUN_TERMINATIONS)
    termination_tables = []
    for start in range(0, len(tense_names), 3):
        columns = tense_names[start:start + 3]
        termination_tables.append(
            DataFrame(termination_rows, columns=columns).to_html(
                escape=False,
                index=False,
                classes="termination-table",
            )
        )

    termination_css = f"""<style>
 table.termination-table {{ width: 100% !important; font-size: {font_size}px !important; }}
 table.termination-table th, table.termination-table td {{
     padding: 1px 2px !important;
     text-align: left !important;
     border: 1px solid #444 !important;
     font-weight: bold !important;
 }}
 table.termination-table th {{ background-color: #2b2b2b !important; font-size: {font_size}px !important; }}
 </style>"""
    markdown(
        termination_css
        + "<div class='termination-tables'>"
        + "".join(f"<div>{table}</div>" for table in termination_tables)
        + "</div>",
        unsafe_allow_html=True
    )

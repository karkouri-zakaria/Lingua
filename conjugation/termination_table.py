from pandas import DataFrame

PRONOUN_TERMINATIONS = {
    "Pretérito": {
        "-ar": ["-é", "-aste", "-ó", "-amos", "-asteis", "-aron"],
        "-er/-ir": ["-í", "-iste", "-ió", "-imos", "-isteis", "-ieron"]
    },
    "Imperfecto": {
        "-ar": ["-aba", "-abas", "-aba", "-ábamos", "-abais", "-aban"],
        "-er/-ir": ["-ía", "-ías", "-ía", "-íamos", "-íais", "-ían"]
    },
    "Perfecto": {
        "-ar": ["he -ado", "has -ado", "ha -ado", "hemos -ado", "habéis -ado", "han -ado"],
        "-er": ["he -ido", "has -ido", "ha -ido", "hemos -ido", "habéis -ido", "han -ido"],
        "-ir": ["he -ido", "has -ido", "ha -ido", "hemos -ido", "habéis -ido", "han -ido"]
    },
    "Presente": {
        "-ar": ["-o", "-as", "-a", "-amos", "-áis", "-an"],
        "-er": ["-o", "-es", "-e", "-emos", "-éis", "-en"],
        "-ir": ["-o", "-es", "-e", "-imos", "-ís", "-en"]
    },
    "Presente Progresivo": {
        "-ar": ["-ando", "-ando", "-ando", "-ando", "-ando", "-ando"],
        "-er/-ir": ["-iendo", "-iendo", "-iendo", "-iendo", "-iendo", "-iendo"]
    },
    "Futuro": {
        "-ar": ["-é", "-ás", "-á", "-emos", "-éis", "-án"],
        "-er/-ir": ["-é", "-ás", "-á", "-emos", "-éis", "-án"]
    }
}


def render_termination_table(markdown, pronouns):
    termination_rows = []
    for index, pronoun in enumerate(pronouns):
        row = {"Pronoun": pronoun}
        for tense, verb_types in PRONOUN_TERMINATIONS.items():
            endings = {verb_type: values[index] for verb_type, values in verb_types.items()}
            unique_endings = set(endings.values())
            if len(unique_endings) == 1:
                row[tense] = f"{next(iter(unique_endings))}"
            else:
                differences = []
                if "-ar" in endings:
                    differences.append(
                        f"<span style='color: #ff9999;'>-a</span>: {endings['-ar']}"
                    )
                if "-er/-ir" in endings:
                    differences.append(
                        f"<span style='color: #90ee90;'>-i</span>/"
                        f"<span style='color: #87cefa;'>e</span>: {endings['-er/-ir']}"
                    )
                else:
                    if "-er" in endings and "-ir" in endings and endings["-er"] == endings["-ir"]:
                        differences.append(
                            f"<span style='color: #90ee90;'>-i</span>/"
                            f"<span style='color: #87cefa;'>e</span>: {endings['-er']}"
                        )
                    else:
                        if "-ir" in endings:
                            differences.append(
                                f"<span style='color: #90ee90;'>-i</span>: {endings['-ir']}"
                            )
                        if "-er" in endings:
                            differences.append(
                                f"<span style='color: #87cefa;'>-e</span>: {endings['-er']}"
                            )
                row[tense] = "<br>".join(differences)
        termination_rows.append(row)

    termination_df = DataFrame(termination_rows)
    termination_css = """<style>
 table.termination-table { width: 100% !important; font-size: 25px !important; }
 table.termination-table th, table.termination-table td {
     padding: 3px 6px !important;
     text-align: left !important;
     border: 1px solid #444 !important;
     font-weight: bold !important;
 }
 table.termination-table th { background-color: #2b2b2b !important; font-size: 22px !important; }
 </style>"""
    markdown(
        termination_css
        + termination_df.to_html(escape=False, index=False, classes="termination-table"),
        unsafe_allow_html=True
    )

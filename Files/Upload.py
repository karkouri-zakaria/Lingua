from streamlit import button, columns, dialog, error, file_uploader, info, rerun, session_state, toast, write
@dialog("Upload a File 📂")
def file_upload_dialog():
    from json import load
    write("You can upload a `.xlsx` or `.csv` file here:")
    uploaded_file = file_uploader(
        "Upload your main file",
        type=["xlsx", "csv"],
        key="file_upload_dialog",
    )
    write("You can upload a `.json` file here:")
    uploaded_json = file_uploader("Upload your answers JSON", type=["json"], key="json_upload_dialog")
    info("Please upload a file and then click 'Submit'.")
    if button("**Submit**", icon="💾", use_container_width=True) and uploaded_file is not None:
        if uploaded_json is not None:
            try:
                session_state.Answers = load(uploaded_json)
            except Exception as e:
                error(f"Failed to load JSON: {e}")
        else :
            session_state.Answers = []
        session_state.uploaded_file_data = uploaded_file
        session_state.success_value = True
        rerun()
@dialog("No Answers Found 📃")
def json_upload_dialog():
    from json import load
    uploaded_json = file_uploader("Upload your JSON", type=["json"], key="json_upload_dialog")
    if button("📤 Upload and Submit", use_container_width=True) and uploaded_json is not None:
        try:
            session_state.Answers = load(uploaded_json)
            rerun()
        except Exception as e:
            error(f"Failed to load JSON: {e}")

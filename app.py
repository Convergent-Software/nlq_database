import streamlit as st
from dotenv import load_dotenv
from ui import UI

load_dotenv()


def main():
    ui = UI()

    st.set_page_config(page_title="NLQ Dashboard", layout="wide")

    ui.initialize_session_state()
    ui.handle_sidebar()
    ui.handle_database_connection_tab()

    current_page = st.session_state.get("current_page", "")
    if current_page == "Visualizations" and "connection" in st.session_state:
        ui.setup_pygwalker()
    else:
        ui.handle_query_tab()


if __name__ == "__main__":
    main()

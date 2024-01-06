from dotenv import load_dotenv
from ui import UI

load_dotenv()


def main():
    ui = UI()

    ui.apply_styles()
    ui.initialize_session_state()
    # ui.setup_pygwalker()
    ui.handle_sidebar()
    ui.handle_database_connection_tab()
    ui.handle_query_tab()


if __name__ == "__main__":
    main()

import streamlit as st

class StateManager:
    """Manage cross-page state and filters for the service management app."""
    
    SESSION_KEYS = {
        "selected_object_type": "selected_object_type",
        "selected_object_id": "selected_object_id",
        "text_filter": "text_filter",
        "status_filter": "status_filter",
    }
    
    @staticmethod
    def init_session_state():
        """Initialize session state with default values."""
        defaults = {
            StateManager.SESSION_KEYS["selected_object_type"]: None,
            StateManager.SESSION_KEYS["selected_object_id"]: None,
            StateManager.SESSION_KEYS["text_filter"]: "",
            StateManager.SESSION_KEYS["status_filter"]: "All",
        }
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def set_object_type(object_type):
        """Set the selected object type globally."""
        st.session_state[StateManager.SESSION_KEYS["selected_object_type"]] = object_type
        st.session_state[StateManager.SESSION_KEYS["selected_object_id"]] = None
    
    @staticmethod
    def get_object_type():
        """Get the selected object type."""
        return st.session_state.get(StateManager.SESSION_KEYS["selected_object_type"])
    
    @staticmethod
    def set_object_id(object_id):
        """Set the selected object ID globally."""
        st.session_state[StateManager.SESSION_KEYS["selected_object_id"]] = object_id
    
    @staticmethod
    def get_object_id():
        """Get the selected object ID."""
        return st.session_state.get(StateManager.SESSION_KEYS["selected_object_id"])
    
    @staticmethod
    def set_text_filter(text):
        """Set the text filter globally."""
        st.session_state[StateManager.SESSION_KEYS["text_filter"]] = text
    
    @staticmethod
    def get_text_filter():
        """Get the text filter."""
        return st.session_state.get(StateManager.SESSION_KEYS["text_filter"], "")
    
    @staticmethod
    def set_status_filter(status):
        """Set the status filter globally."""
        st.session_state[StateManager.SESSION_KEYS["status_filter"]] = status
    
    @staticmethod
    def get_status_filter():
        """Get the status filter."""
        return st.session_state.get(StateManager.SESSION_KEYS["status_filter"], "All")
    
    @staticmethod
    def enforce_auth():
        """Stop page execution if the user is not authenticated."""
        if not st.session_state.get('authenticated', False):
            st.error("🔒 Please log in to access this page.")
            st.info("Return to the **Home** page to sign in.")
            st.stop()

    @staticmethod
    def clear_filters():
        """Clear all filters."""
        st.session_state[StateManager.SESSION_KEYS["text_filter"]] = ""
        st.session_state[StateManager.SESSION_KEYS["status_filter"]] = "All"

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
    def init_and_enforce(cm):
        """
        Unified auth setup for every page:
          1. On the very first render give the CookieController JS component one
             render cycle to deliver cookies (st.stop() guarded by a flag so it
             only fires once per browser session).
          2. Try to restore session from the browser cookie if not in session_state.
          3. Enforce authentication — stop if not logged in.
          4. Check inactivity timeout (10 min); logout + stop if exceeded.
          5. Update last_activity and throttle-refresh the cookie.
        """
        import time
        from utils.auth_session import (
            try_restore_session, do_logout,
            refresh_cookie_if_needed, INACTIVITY_TIMEOUT,
        )

        if not st.session_state.get("authenticated"):
            # Guard: give the JS component exactly one render to fire
            if not st.session_state.get("_mml_init_done"):
                st.session_state["_mml_init_done"] = True
                st.stop()
            try_restore_session(cm)

        if not st.session_state.get("authenticated", False):
            if st.session_state.pop("_session_expired", False):
                st.warning("⏰ Session expired due to inactivity. Please log in again.")
            else:
                st.error("🔒 Please log in to access this page.")
                st.info("Return to the **Home** page to sign in.")
            st.stop()

        # Inactivity check
        now = time.time()
        last = st.session_state.get("last_activity", now)
        if now - last > INACTIVITY_TIMEOUT:
            do_logout(cm)
            st.session_state["_session_expired"] = True
            st.warning("⏰ Session expired due to inactivity. Please log in again.")
            st.stop()

        st.session_state["last_activity"] = now
        refresh_cookie_if_needed(cm)

    @staticmethod
    def clear_filters():
        """Clear all filters."""
        st.session_state[StateManager.SESSION_KEYS["text_filter"]] = ""
        st.session_state[StateManager.SESSION_KEYS["status_filter"]] = "All"

    @staticmethod
    def get_widget_instance_key(widget_key_base: str) -> str:
        """Return a stable-per-run, rotatable widget key for safe widget resets."""
        counter_key = f"{widget_key_base}__instance"
        if counter_key not in st.session_state:
            st.session_state[counter_key] = 0
        return f"{widget_key_base}_{st.session_state[counter_key]}"

    @staticmethod
    def reset_widget_instance(widget_key_base: str):
        """Rotate a widget's instance key to reset widget state without mutating widget-bound keys."""
        counter_key = f"{widget_key_base}__instance"
        if counter_key not in st.session_state:
            st.session_state[counter_key] = 0
        st.session_state[counter_key] += 1

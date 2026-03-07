"""
mymaintlog - Main Entry Point

This is a Streamlit-based service management application that helps manage:
- Objects: Equipment (Vehicles, Facilities, Other)
- Services: Scheduled maintenance and service plans
- Reminders: Service reminder notifications
- Reports: Service completion reports

Multi-page navigation with cross-page filters and state management.
Data is stored in CSV files for easy backup and sharing.
"""


import streamlit as st
from utils.state_manager import StateManager
from utils.auth_session import (
    try_restore_session, make_session_cookie, do_logout,
    refresh_cookie_if_needed, COOKIE_NAME, INACTIVITY_TIMEOUT, COOKIE_MAX_AGE,
)
from streamlit_cookies_controller import CookieController
import yaml
from yaml.loader import SafeLoader
import bcrypt
import time


# Set page config
st.set_page_config(
    page_title="MyMaintLog",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Cookie Manager (must be created right after set_page_config) ---
cm = CookieController(key="cookies")

# --- User Authentication ---
# Try to restore session from browser cookie on page refresh.
# CookieController reads cookies via a JS component.  On the very first render
# the component hasn't fired yet (returns empty dict), so we do one mandatory
# st.stop() to give it a chance to send the cookie data back to Python.
if not st.session_state.get("authenticated"):
    if not st.session_state.get("_mml_init_done"):
        st.session_state["_mml_init_done"] = True
        st.stop()   # Wait one render for the JS component to deliver cookies
    try_restore_session(cm)

# Show expiry notice carried over from a sub-page timeout
if st.session_state.pop("_session_expired", False):
    st.session_state["_show_expired_msg"] = True

if not st.session_state.get("authenticated"):
    st.title("🔐 MyMaintLog Login")

    if st.session_state.pop("_show_expired_msg", False):
        st.warning("⏰ Your session expired due to inactivity. Please log in again.")

    # Load users
    with open("users.yaml") as file:
        config = yaml.load(file, Loader=SafeLoader)

    # Login form
    with st.form("login_form"):
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            # Check if user exists
            users = config['credentials']['usernames']
            if username in users:
                user_data = users[username]
                # Verify password
                if bcrypt.checkpw(password.encode(), user_data['password'].encode()):
                    # Successful login
                    st.session_state['authenticated'] = True
                    st.session_state['user_email'] = username
                    st.session_state['user_role'] = user_data['role']
                    st.session_state['user_name'] = user_data['name']
                    # Track news views: increment counter and persist
                    news_views = user_data.get('news_views', 0) + 1
                    config['credentials']['usernames'][username]['news_views'] = news_views
                    st.session_state['news_views'] = news_views
                    with open('users.yaml', 'w') as f:
                        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                    # Persist session in browser cookie
                    cm.set(COOKIE_NAME, make_session_cookie(
                        username, user_data['role'], user_data['name'], news_views
                    ), max_age=COOKIE_MAX_AGE)
                    st.session_state['last_activity'] = time.time()
                    st.success(f"Welcome {user_data['name']}!")
                    st.rerun()
                else:
                    st.error("Incorrect password")
            else:
                st.error("User not found")

    st.stop()

# --- Inactivity timeout check for Home page ---
now = time.time()
last = st.session_state.get("last_activity", now)
if now - last > INACTIVITY_TIMEOUT:
    do_logout(cm)
    st.session_state["_session_expired"] = True
    st.rerun()
st.session_state["last_activity"] = now
refresh_cookie_if_needed(cm)

# Initialize session state
StateManager.init_session_state()

# Add logout button in sidebar
with st.sidebar:
    st.write(f"👤 {st.session_state.get('user_name', 'User')}")
    st.write(f"📧 {st.session_state.get('user_email', '')}")
    if st.session_state.get('user_role') == 'admin':
        st.write("🔑 Admin")
    if st.button("Logout"):
        do_logout(cm)
        st.rerun()

# Add custom styling
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Fault Reports Highlight (shown only for first 2 login sessions per user) ---
if st.session_state.get('news_views', 0) <= 2:
    st.markdown("""
<style>
.news-info {
    background-color: var(--news-bg, #f9f6e7);
    color: var(--news-fg, #222);
    padding: 1em;
    border-radius: 8px;
    margin-bottom: 1em;
}
@media (prefers-color-scheme: dark) {
    .news-info {
        --news-bg: #2a2a2a;
        --news-fg: #ffd580;
    }
}
</style>
<div class="news-info">
<b>New:</b> <span style="color:#d35400;">Fault Reports</span> page now supports multiple photos per report, instant updates, and improved photo viewing!<br>
Easily document faults with images and view all reports in real time.
</div>
""", unsafe_allow_html=True)

# Sidebar information
with st.sidebar:
    st.title("📋 MyMaintLog")
    st.markdown("---")
    st.markdown("""
    ### Features
    - **Equipment Management**: Add and manage equipment
    - **Service Planning**: Schedule maintenance and services
    - **Service Reminders**: Track upcoming services
    - **Service Reports**: Document completed services
    - **Fault Reports**: Log faults with photos and details
    - **Cross-Page Filters**: Seamless data viewing
    - **SQLite Storage**: Reliable single-file data storage
    """)
    
    st.markdown("---")
    st.markdown("""
    ### Navigation
    Use the sidebar menu to navigate between pages.
    
    - **Dashboard**: Overview and alerts
    - **Equipment**: Manage equipment objects
    - **Service Planning**: Schedule and manage services
    - **Service Reminders**: Track service reminders
    - **Service Reports**: View and add reports
    - **Fault Reports**: View and add fault reports
    """)
    
    st.markdown("---")
    st.markdown("""
    ### Data Location
    All data is stored in a single SQLite database (`data/mymaintlog.db`):
    - Equipment, services, reminders, reports, fault reports
    - Fault photos stored as BLOBs (no separate files needed)
    """)

# Main content
st.title("🎯 Welcome to mymaintlog")

st.markdown("""
## Get Started

This application helps you manage services, maintenance, and equipment tracking across 
your organization. Here's how to use it:

### 1️⃣ Add Equipment First
Navigate to the **Equipment** page to add equipment you want to manage.

### 2️⃣ Plan Services
Go to **Service Planning** to schedule regular maintenance services for your objects.

### 3️⃣ Set Reminders
Create **Service Reminders** to get notifications for upcoming services.


### 4️⃣ Track Reports & Faults
Use **Service Reports** to document completed services and maintenance activities.
Use **Fault Reports** to log faults, upload multiple photos, and track issues for any equipment.


### 5️⃣ Monitor Dashboard
The **Dashboard** provides an overview of all objects, services, faults, and alerts.

---

## Features

✅ **Equipment Management** - Manage all your equipment (Vehicles, Facilities, Other)  
✅ **Service Planning** - Schedule maintenance with custom intervals  
✅ **Reminder System** - Track upcoming and overdue services  
✅ **Reporting** - Document all service activities  
✅ **Fault Reporting** - Log faults with multiple photos and instant updates  
✅ **Photo Management** - Attach and view images for faults and reports  
✅ **Cross-Page Filters** - Seamless navigation and filtering  
✅ **SQLite Data Storage** - Single-file database, easy to backup  
✅ **Status Tracking** - Monitor service status (Active, Inactive, Maintenance)  
✅ **Data Export** - Download data from dashboard  

---

## Quick Links

- [View Dashboard](Dashboard) - See overview and alerts
- [Manage Equipment](Equipment) - Add and edit equipment
- [Plan Services](Service%20Planning) - Schedule maintenance
- [Track Reminders](Service%20Reminders) - View upcoming services
- [View Reports](Service%20Reports) - See service history
- [View Fault Reports](Fault%20Reports) - Log and review faults with photos

---

Start by navigating to the Dashboard or adding your first object!
""")

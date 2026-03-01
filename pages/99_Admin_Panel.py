import streamlit as st
import yaml
import bcrypt
from utils.data_handler import DataHandler
from utils.state_manager import StateManager

st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("👤 Admin Panel")
st.markdown("**Administrator Control Panel** - Manage users and view all system data")
st.markdown("---")

StateManager.enforce_auth()

user_email = st.session_state.get('user_email')
is_admin = False
if 'user_role' in st.session_state:
    is_admin = st.session_state['user_role'] == 'admin'

if not is_admin:
    st.error("You do not have permission to view this page.")
    st.stop()

# --- User Management ---
st.header("User Management")
st.info("👥 Manage user accounts and permissions. Add new users, update existing accounts, or remove users along with all their data.")

users_file = "users.yaml"
with open(users_file) as file:
    config = yaml.safe_load(file)
users_dict = config['credentials']['usernames']
users = [
    {'email': email, 'name': info['name'], 'role': info['role']} 
    for email, info in users_dict.items()
]

st.markdown("**Current Users**")
user_table = [
    {"Email": u['email'], "Name": u['name'], "Role": u['role']} for u in users
]
st.dataframe(user_table, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("Add New User")
st.markdown("Create a new user account. **User role** can view and manage only their own data. **Admin role** can view and manage all data and users.")

with st.form("add_user_form"):
    new_email = st.text_input("Email")
    new_name = st.text_input("Name")
    new_password = st.text_input("Password", type="password")
    new_role = st.selectbox("Role", ["user", "admin"])
    add_user_btn = st.form_submit_button("Add User")
    if add_user_btn:
        if not new_email or not new_name or not new_password:
            st.error("All fields are required.")
        elif any(u['email'] == new_email for u in users):
            st.error("A user with this email already exists.")
        else:
            hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            # Add to usernames dict
            users_dict[new_email] = {
                'name': new_name,
                'password': hashed_pw,
                'role': new_role
            }
            config['credentials']['usernames'] = users_dict
            with open(users_file, 'w') as f:
                yaml.safe_dump(config, f)
            st.success(f"User {new_email} added.")
            st.rerun()

st.markdown("---")
st.subheader("Edit or Remove User")
st.markdown("Update user details or remove a user account. ⚠️ **Warning:** Removing a user will permanently delete all their equipment, services, reminders, reports, and fault reports.")

edit_emails = [u['email'] for u in users]
selected_edit_email = st.selectbox("Select user to edit/remove", edit_emails)
selected_user = next((u for u in users if u['email'] == selected_edit_email), None)
if selected_user:
    with st.form("edit_user_form"):
        edit_name = st.text_input("Name", value=selected_user['name'])
        edit_role = st.selectbox("Role", ["user", "admin"], index=["user", "admin"].index(selected_user['role']))
        new_pw = st.text_input("New Password (leave blank to keep current)", type="password")
        update_btn = st.form_submit_button("Update User")
        remove_btn = st.form_submit_button("Remove User", type="secondary")
        if update_btn:
            # Update in usernames dict
            users_dict[selected_edit_email]['name'] = edit_name
            users_dict[selected_edit_email]['role'] = edit_role
            if new_pw:
                users_dict[selected_edit_email]['password'] = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
            config['credentials']['usernames'] = users_dict
            with open(users_file, 'w') as f:
                yaml.safe_dump(config, f)
            st.success(f"User {selected_edit_email} updated.")
            st.rerun()
        if remove_btn:
            confirm = st.checkbox(f"Confirm delete user {selected_edit_email} and all their data?", key="confirm_delete")
            if confirm:
                # Remove from usernames dict
                del users_dict[selected_edit_email]
                config['credentials']['usernames'] = users_dict
                with open(users_file, 'w') as f:
                    yaml.safe_dump(config, f)
                # Remove all user data from app
                handler = DataHandler()
                handler.delete_user_data(selected_edit_email)
                st.success(f"User {selected_edit_email} and all their data removed.")
                st.rerun()

# --- Data Overview ---
st.markdown("---")
st.header("All Data Overview")
st.info("📊 View all data across the entire system. This includes data from all users.")

handler = DataHandler()

st.subheader("All Equipment")
st.caption("View all equipment (vehicles, facilities, and other items) across all users.")
objects_df = handler.get_objects(is_admin=True)
st.dataframe(objects_df, use_container_width=True, hide_index=True)

st.subheader("All Services")
st.caption("View all scheduled service plans across all users.")
services_df = handler.get_services(is_admin=True)
st.dataframe(services_df, use_container_width=True, hide_index=True)

st.subheader("All Reminders")
st.caption("View all service reminders across all users.")
reminders_df = handler.get_reminders(is_admin=True)
st.dataframe(reminders_df, use_container_width=True, hide_index=True)

st.subheader("All Reports")
st.caption("View all completed service reports across all users.")
reports_df = handler.get_reports(is_admin=True)
st.dataframe(reports_df, use_container_width=True, hide_index=True)

st.subheader("All Fault Reports")
st.caption("View all fault reports with photos across all users.")
fault_reports_df = handler.get_fault_reports(is_admin=True)
st.dataframe(fault_reports_df, use_container_width=True, hide_index=True)

import streamlit as st
import pandas as pd
from utils.data_handler import DataHandler
from utils.state_manager import StateManager
from utils.email_notifier import EmailNotifier
from datetime import datetime
import yaml

st.set_page_config(page_title="Service Reminders", layout="wide")


StateManager.init_session_state()
handler = DataHandler()
user_email = st.session_state.get('user_email')
is_admin = st.session_state.get('user_role') == 'admin'

# Check and send pending email notifications
email_notifier = EmailNotifier()
if email_notifier.is_enabled():
    try:
        reminders_df = handler.get_reminders(user_email=user_email, is_admin=is_admin)
        with open("users.yaml") as f:
            users_config = yaml.safe_load(f)
        emails_sent = email_notifier.check_and_send_pending_reminders(reminders_df, users_config, handler)
        if emails_sent > 0:
            st.sidebar.success(f"📧 {emails_sent} reminder email(s) sent")
    except Exception as e:
        st.sidebar.error(f"Email check error: {e}")

st.header("🔔 Service Reminders")

# Sidebar filters
st.sidebar.header("Filters")
object_type_filter = st.sidebar.selectbox(
    "Object Type",
    ["All"] + handler.OBJECT_TYPES,
    key="reminders_object_type"
)

status_filter = st.sidebar.selectbox(
    "Status",
    ["All", "Pending", "Completed"],
    key="reminders_status"
)

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["View Reminders", "Add Reminder", "Edit Reminder"])

with tab1:
    st.subheader("All Reminders")
    
    # Get reminders
    reminders_df = handler.get_reminders(user_email=user_email, is_admin=is_admin)
    
    # Apply filters
    if object_type_filter != "All":
        reminders_df = reminders_df[reminders_df["object_type"] == object_type_filter]
    
    if status_filter != "All":
        reminders_df = reminders_df[reminders_df["status"] == status_filter]
    
    if reminders_df.empty:
        st.info("No reminders found. Add one to get started!")
    else:
        # Add computed columns
        reminders_df = reminders_df.copy()
        reminders_df["days_until"] = pd.to_datetime(
            reminders_df["reminder_date"]
        ) - pd.Timestamp.now()
        reminders_df["days_until"] = reminders_df["days_until"].dt.days
        
        # Sort by days until reminder
        reminders_df = reminders_df.sort_values("days_until")
        
        # Add conditional notification_time display
        # Show notification_time only if email_notification is True, otherwise empty string
        reminders_df["notification_time_display"] = reminders_df.apply(
            lambda row: row.get("notification_time", "") if row.get("email_notification", False) else "",
            axis=1
        )
        
        # Display table
        display_cols = ["reminder_id", "service_id", "object_id", "object_type", 
                       "reminder_date", "days_until", "status", "email_notification", "notification_time_display", "notes"]
        
        # Rename column for display
        display_df = reminders_df[display_cols].copy()
        display_df.rename(columns={"notification_time_display": "notification_time"}, inplace=True)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            overdue = len(reminders_df[(reminders_df["days_until"] < 0) & 
                                      (reminders_df["status"] == "Pending")])
            st.metric("Overdue Reminders", overdue, delta=None, delta_color="inverse")
        with col2:
            due_soon = len(reminders_df[(reminders_df["days_until"] >= 0) & 
                                       (reminders_df["days_until"] <= 7) &
                                       (reminders_df["status"] == "Pending")])
            st.metric("Due in 7 Days", due_soon)
        with col3:
            pending = len(reminders_df[reminders_df["status"] == "Pending"])
            st.metric("Pending", pending)
        with col4:
            completed = len(reminders_df[reminders_df["status"] == "Completed"])
            st.metric("Completed", completed)

with tab2:
    st.subheader("Add New Reminder")
    
    # Get all services
    services_df = handler.get_services()
    
    if services_df.empty:
        st.warning("No services found. Please schedule a service first.")
    else:
        with st.form("add_reminder_form"):
            service_id = st.selectbox(
                "Select Service",
                services_df["service_id"].tolist(),
                format_func=lambda x: f"{x} - {services_df[services_df['service_id']==x]['service_name'].values[0]}"
            )
            
            if service_id:
                selected_service = services_df[services_df["service_id"] == service_id].iloc[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Object Type:** {selected_service['object_type']}")
                    st.write(f"**Object ID:** {selected_service['object_id']}")
                with col2:
                    st.write(f"**Service:** {selected_service['service_name']}")
                    st.write(f"**Interval:** {selected_service['interval_days']} days")
                
                reminder_date = st.date_input("Reminder Date")
                st.write(f"**Expected Meter Reading:** {selected_service.get('expected_meter_reading', '')}")
                st.write(f"**Meter Unit:** {selected_service.get('meter_unit', '')}")
                notes = st.text_area("Notes", max_chars=500)
                
                # Email notification options
                st.markdown("---")
                st.markdown("**📧 Email Notification**")
                email_notification = st.checkbox("Send email reminder", value=False, 
                                                 help="Send an email notification on the reminder date")
                notification_time = st.time_input("Notification time", 
                                                  value=datetime.strptime("09:00", "%H:%M").time(),
                                                  help="Time to send the email notification")
                
                if not email_notifier.is_enabled():
                    st.info("ℹ️ Email notifications are disabled. Configure email_config.yaml to enable.")
                
                submitted = st.form_submit_button("Add Reminder")
                if submitted:
                    reminder_id = handler.add_reminder(
                        service_id=service_id,
                        object_id=selected_service["object_id"],
                        object_type=selected_service["object_type"],
                        reminder_date=str(reminder_date),
                        notes=notes,
                        email_notification=email_notification,
                        notification_time=notification_time.strftime("%H:%M")
                    )
                    st.success(f"✓ Reminder added successfully! ID: {reminder_id}")
                    st.rerun()

with tab3:
    st.subheader("Edit Reminder")
    
    # Get reminders filtered by object type
    if object_type_filter == "All":
        reminders_df = handler.get_reminders()
    else:
        reminders_df = handler.get_reminders(object_type=object_type_filter)
    
    if reminders_df.empty:
        st.info("No reminders to edit.")
    else:
        selected_reminder_id = st.selectbox(
            "Select reminder to edit:",
            reminders_df["reminder_id"].tolist()
        )
        
        if selected_reminder_id:
            reminder = reminders_df[reminders_df["reminder_id"] == selected_reminder_id].iloc[0]
            
            with st.form("edit_reminder_form"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Service ID:** {reminder['service_id']}")
                    st.write(f"**Object ID:** {reminder['object_id']}")
                with col2:
                    st.write(f"**Object Type:** {reminder['object_type']}")
                # Show associated expected meter info when available
                st.write(f"**Expected Meter Reading:** {reminder.get('expected_meter_reading', '')}")
                st.write(f"**Meter Unit:** {reminder.get('meter_unit', '')}")
                
                reminder_date = st.date_input(
                    "Reminder Date",
                    value=pd.to_datetime(reminder["reminder_date"])
                )
                status = st.selectbox(
                    "Status",
                    ["Pending", "Completed"],
                    index=0 if reminder["status"] == "Pending" else 1
                )
                notes = st.text_area("Notes", value=reminder["notes"], max_chars=500)
                
                # Email notification options
                st.markdown("---")
                st.markdown("**📧 Email Notification**")
                email_notification = st.checkbox(
                    "Send email reminder", 
                    value=reminder.get('email_notification', False),
                    help="Send an email notification on the reminder date"
                )
                
                # Parse existing time or use default
                existing_time = reminder.get('notification_time', '09:00')
                try:
                    time_obj = datetime.strptime(existing_time, "%H:%M").time()
                except:
                    time_obj = datetime.strptime("09:00", "%H:%M").time()
                
                notification_time = st.time_input(
                    "Notification time", 
                    value=time_obj,
                    help="Time to send the email notification"
                )
                
                if not email_notifier.is_enabled():
                    st.info("ℹ️ Email notifications are disabled. Configure email_config.yaml to enable.")
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Update Reminder")
                with col2:
                    delete_btn = st.form_submit_button("Delete Reminder", type="secondary")
                
                if submitted:
                    handler.update_reminder(
                        selected_reminder_id,
                        reminder_date=str(reminder_date),
                        status=status,
                        notes=notes,
                        email_notification=email_notification,
                        notification_time=notification_time.strftime("%H:%M"),
                        email_sent=False  # Reset email_sent when updating
                    )
                    st.success("✓ Reminder updated successfully!")
                    st.rerun()
                
                if delete_btn:
                    # Use handler's safe delete to avoid unguarded file writes
                    deleted = handler.delete_reminder(selected_reminder_id)
                    if deleted:
                        st.success("✓ Reminder deleted successfully!")
                    else:
                        st.error("Could not delete reminder (it may have been removed already).")
                    st.rerun()

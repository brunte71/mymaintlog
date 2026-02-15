import streamlit as st
import pandas as pd
from utils.data_handler import DataHandler
from utils.state_manager import StateManager
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard", layout="wide")

StateManager.init_session_state()
handler = DataHandler()

st.title("📌 Service Management Dashboard")

# Overview statistics
col1, col2, col3, col4 = st.columns(4)


objects_df = handler.get_objects()
services_df = handler.get_services()
reminders_df = handler.get_reminders()
reports_df = handler.get_reports()
fault_reports_df = handler.get_fault_reports()


with col1:
    total_objects = len(objects_df)
    st.metric("Total Objects", total_objects)

with col2:
    total_services = len(services_df)
    st.metric("Total Services", total_services)

with col3:
    pending_reminders = len(reminders_df[reminders_df["status"] == "Pending"])
    st.metric("Pending Reminders", pending_reminders, delta=None, delta_color="inverse")

with col4:
    total_faults = len(fault_reports_df)
    st.metric("Fault Reports", total_faults)

equipment = len(objects_df[objects_df["object_type"] == "Vehicle"])

# Objects by type
st.write("---")
st.subheader("Objects Overview")

col1, col2 = st.columns(2)

equipment = len(objects_df[objects_df["object_type"] == "Vehicle"])

with col1:
    st.metric("🛠️ Equipment", equipment)
    if st.button("View Equipment", key="dash_equipment"):
        st.switch_page("pages/1_Equipment.py")

# Fault Reports quick summary
with col2:
    st.metric("🚨 Fault Reports", total_faults)
    if st.button("View Fault Reports", key="dash_fault_reports"):
        st.switch_page("pages/2_Fault_Reports.py")


# Recent services and recent fault reports
st.write("---")
col_recent_services, col_recent_faults = st.columns(2)

with col_recent_services:
    st.subheader("Recent Services")
    if services_df.empty:
        st.info("No services scheduled yet.")
    else:
        services_df = services_df.copy()
        services_df["days_until"] = pd.to_datetime(
            services_df["next_service_date"]
        ) - pd.Timestamp.now()
        services_df["days_until"] = services_df["days_until"].dt.days
        services_df = services_df.sort_values("days_until")
        display_cols = ["service_id", "object_id", "service_name", "object_type", 
                    "next_service_date", "days_until", "status"]
        st.dataframe(
            services_df[display_cols].head(10),
            use_container_width=True,
            hide_index=True
        )

with col_recent_faults:
    st.subheader("Recent Fault Reports")
    if fault_reports_df.empty:
        st.info("No fault reports yet.")
    else:
        # Show most recent 10 fault reports, with photo count
        fault_reports_df = fault_reports_df.copy()
        fault_reports_df["photo_count"] = fault_reports_df["photo_paths"].apply(lambda x: len([p for p in str(x).split(';') if p and p.lower() != 'nan']))
        display_cols = ["fault_id", "object_id", "object_type", "observation_date", "description", "photo_count", "created_date"]
        st.dataframe(
            fault_reports_df[display_cols].sort_values("created_date", ascending=False).head(10),
            use_container_width=True,
            hide_index=True
        )

# Overdue services alert
st.write("---")
st.subheader("⚠️ Alerts")

if services_df.empty:
    st.info("No alerts.")
else:
    overdue_services = services_df[services_df["days_until"] < 0]
    due_soon_services = services_df[(services_df["days_until"] >= 0) & (services_df["days_until"] <= 3)]
    overdue_reminders = reminders_df[(pd.to_datetime(reminders_df["reminder_date"]) < pd.Timestamp.now()) & 
                                     (reminders_df["status"] == "Pending")]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if len(overdue_services) > 0:
            st.error(f"🔴 **{len(overdue_services)} Overdue Services**")
            st.write("Services past their due date:")
            for _, service in overdue_services.head(5).iterrows():
                st.write(f"- {service['service_name']} ({service['object_id']})")
        else:
            st.success("✓ No overdue services")
    
    with col2:
        if len(due_soon_services) > 0:
            st.warning(f"🟡 **{len(due_soon_services)} Services Due Soon** (within 3 days)")
            st.write("Services due within 3 days:")
            for _, service in due_soon_services.head(5).iterrows():
                st.write(f"- {service['service_name']} ({service['object_id']})")
        else:
            st.success("✓ No services due soon")
    
    with col3:
        if len(overdue_reminders) > 0:
            st.error(f"🔴 **{len(overdue_reminders)} Overdue Reminders**")
            st.write("Reminders past their date:")
            for _, reminder in overdue_reminders.head(5).iterrows():
                st.write(f"- Service ID: {reminder['service_id']}")
        else:
            st.success("✓ No overdue reminders")

# Quick actions
st.write("---")
st.subheader("Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("➕ Add Equipment", use_container_width=True):
        st.switch_page("pages/1_Equipment.py")

with col2:
    if st.button("📋 Plan Service", use_container_width=True):
        st.switch_page("pages/4_Service_Planning.py")

with col3:
    if st.button("🔔 Add Reminder", use_container_width=True):
        st.switch_page("pages/5_Service_Reminders.py")

with col4:
    if st.button("📊 View Reports", use_container_width=True):
        st.switch_page("pages/6_Service_Reports.py")

# Data export
st.write("---")
st.subheader("Data Export")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.download_button(
        label="⬇️ Export Objects",
        data=objects_df.to_csv(index=False),
        file_name="objects.csv",
        mime="text/csv"
    ):
        pass

with col2:
    if st.download_button(
        label="⬇️ Export Services",
        data=services_df.to_csv(index=False),
        file_name="services.csv",
        mime="text/csv"
    ):
        pass

with col3:
    if st.download_button(
        label="⬇️ Export Reminders",
        data=reminders_df.to_csv(index=False),
        file_name="reminders.csv",
        mime="text/csv"
    ):
        pass

with col4:
    if st.download_button(
        label="⬇️ Export Reports",
        data=reports_df.to_csv(index=False),
        file_name="reports.csv",
        mime="text/csv"
    ):
        pass

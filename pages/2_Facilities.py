import streamlit as st
import pandas as pd
from utils.data_handler import DataHandler
from utils.state_manager import StateManager
from datetime import datetime

st.set_page_config(page_title="Facilities", layout="wide")

StateManager.init_session_state()
handler = DataHandler()

st.header("🏢 Facilities Management")

# Sidebar filters
st.sidebar.header("Filters")
status_filter = st.sidebar.selectbox(
    "Status Filter",
    ["All", "Active", "Inactive", "Maintenance"],
    key="facilities_status_filter"
)

# Get facilities
facilities_df = handler.get_objects("Facilities")

# Apply filters
if status_filter != "All":
    facilities_df = facilities_df[facilities_df["status"] == status_filter]

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["View Facilities", "Add Facility", "Edit Facility"])

with tab1:
    st.subheader("All Facilities")
    
    if facilities_df.empty:
        st.info("No facilities found. Add one to get started!")
    else:
        # Display facilities in a table
        col1, col2 = st.columns([4, 1])
        with col1:
            selected_facility = st.dataframe(
                facilities_df[["object_id", "name", "description", "status", "created_date"]],
                use_container_width=True
            )
        
        # Click on row to view details
        facility_ids = facilities_df["object_id"].tolist()
        selected_id = st.selectbox("Select a facility to view details:", facility_ids)
        
        if selected_id:
            StateManager.set_object_id(selected_id)
            StateManager.set_object_type("Facilities")
            
            facility = facilities_df[facilities_df["object_id"] == selected_id].iloc[0]
            
            st.write("---")
            st.subheader(f"Details: {facility['name']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**ID:** {facility['object_id']}")
                st.write(f"**Type:** {facility['object_type']}")
                st.write(f"**Status:** {facility['status']}")
            with col2:
                st.write(f"**Description:** {facility['description']}")
                st.write(f"**Created:** {facility['created_date']}")
                st.write(f"**Last Updated:** {facility['last_updated']}")
            
            # Show services for this facility
            st.write("---")
            st.subheader("Services for this Facility")
            services_df = handler.get_services(object_id=selected_id)
            
            if services_df.empty:
                st.info("No services scheduled for this facility.")
            else:
                st.dataframe(
                    services_df[["service_id", "service_name", "interval_days", 
                                 "next_service_date", "status"]],
                    use_container_width=True
                )
            
            # Show reminders
            st.write("---")
            st.subheader("Reminders for this Facility")
            reminders_df = handler.get_reminders(object_id=selected_id)
            
            if reminders_df.empty:
                st.info("No reminders for this facility.")
            else:
                st.dataframe(
                    reminders_df[["reminder_id", "service_id", "reminder_date", "status"]],
                    use_container_width=True
                )

with tab2:
    st.subheader("Add New Facility")
    
    with st.form("add_facility_form"):
        name = st.text_input("Facility Name (e.g., Main Office, Warehouse)")
        description = st.text_area("Description", max_chars=500)
        status = st.selectbox("Status", ["Active", "Inactive", "Maintenance"])
        
        submitted = st.form_submit_button("Add Facility")
        if submitted:
            if name:
                facility_id = handler.add_object(
                    object_type="Facilities",
                    name=name,
                    description=description,
                    status=status
                )
                st.success(f"✓ Facility added successfully! ID: {facility_id}")
                st.rerun()
            else:
                st.error("Please enter a facility name.")

with tab3:
    st.subheader("Edit Facility")
    
    if facilities_df.empty:
        st.info("No facilities to edit.")
    else:
        selected_facility_id = st.selectbox(
            "Select facility to edit:",
            facilities_df["object_id"].tolist(),
            key="edit_facility_select"
        )
        
        if selected_facility_id:
            facility = facilities_df[facilities_df["object_id"] == selected_facility_id].iloc[0]
            
            with st.form("edit_facility_form"):
                name = st.text_input("Facility Name", value=facility["name"])
                description = st.text_area("Description", value=facility["description"], max_chars=500)
                status = st.selectbox("Status", ["Active", "Inactive", "Maintenance"], 
                                     index=["Active", "Inactive", "Maintenance"].index(facility["status"]))
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Update Facility")
                with col2:
                    delete_btn = st.form_submit_button("Delete Facility", type="secondary")
                
                if submitted:
                    handler.update_object(
                        selected_facility_id,
                        name=name,
                        description=description,
                        status=status
                    )
                    st.success("✓ Facility updated successfully!")
                    st.rerun()
                
                if delete_btn:
                    handler.delete_object(selected_facility_id)
                    st.success("✓ Facility deleted successfully!")
                    st.rerun()

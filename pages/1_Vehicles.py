import streamlit as st
import pandas as pd
from utils.data_handler import DataHandler
from utils.state_manager import StateManager
from datetime import datetime

st.set_page_config(page_title="Vehicles", layout="wide")

StateManager.init_session_state()
handler = DataHandler()

st.header("🚗 Vehicles Management")

# Sidebar filters
st.sidebar.header("Filters")
status_filter = st.sidebar.selectbox(
    "Status Filter",
    ["All", "Active", "Inactive", "Maintenance"],
    key="vehicles_status_filter"
)

# Get vehicles
vehicles_df = handler.get_objects("Vehicles")

# Apply filters
if status_filter != "All":
    vehicles_df = vehicles_df[vehicles_df["status"] == status_filter]

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["View Vehicles", "Add Vehicle", "Edit Vehicle"])

with tab1:
    st.subheader("All Vehicles")
    
    if vehicles_df.empty:
        st.info("No vehicles found. Add one to get started!")
    else:
        # Display vehicles in a table
        col1, col2 = st.columns([4, 1])
        with col1:
            selected_vehicle = st.dataframe(
                vehicles_df[["object_id", "name", "description", "status", "created_date"]],
                use_container_width=True
            )
        
        # Click on row to view details
        vehicle_ids = vehicles_df["object_id"].tolist()
        selected_id = st.selectbox("Select a vehicle to view details:", vehicle_ids)
        
        if selected_id:
            StateManager.set_object_id(selected_id)
            StateManager.set_object_type("Vehicles")
            
            vehicle = vehicles_df[vehicles_df["object_id"] == selected_id].iloc[0]
            
            st.write("---")
            st.subheader(f"Details: {vehicle['name']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**ID:** {vehicle['object_id']}")
                st.write(f"**Type:** {vehicle['object_type']}")
                st.write(f"**Status:** {vehicle['status']}")
            with col2:
                st.write(f"**Description:** {vehicle['description']}")
                st.write(f"**Created:** {vehicle['created_date']}")
                st.write(f"**Last Updated:** {vehicle['last_updated']}")
            
            # Show services for this vehicle
            st.write("---")
            st.subheader("Services for this Vehicle")
            services_df = handler.get_services(object_id=selected_id)
            
            if services_df.empty:
                st.info("No services scheduled for this vehicle.")
            else:
                st.dataframe(
                    services_df[["service_id", "service_name", "interval_days", 
                                 "next_service_date", "status"]],
                    use_container_width=True
                )
            
            # Show reminders
            st.write("---")
            st.subheader("Reminders for this Vehicle")
            reminders_df = handler.get_reminders(object_id=selected_id)
            
            if reminders_df.empty:
                st.info("No reminders for this vehicle.")
            else:
                st.dataframe(
                    reminders_df[["reminder_id", "service_id", "reminder_date", "status"]],
                    use_container_width=True
                )

with tab2:
    st.subheader("Add New Vehicle")
    
    with st.form("add_vehicle_form"):
        name = st.text_input("Vehicle Name (e.g., Truck-001)")
        description = st.text_area("Description", max_chars=500)
        status = st.selectbox("Status", ["Active", "Inactive", "Maintenance"])
        
        submitted = st.form_submit_button("Add Vehicle")
        if submitted:
            if name:
                vehicle_id = handler.add_object(
                    object_type="Vehicles",
                    name=name,
                    description=description,
                    status=status
                )
                st.success(f"✓ Vehicle added successfully! ID: {vehicle_id}")
                st.rerun()
            else:
                st.error("Please enter a vehicle name.")

with tab3:
    st.subheader("Edit Vehicle")
    
    if vehicles_df.empty:
        st.info("No vehicles to edit.")
    else:
        selected_vehicle_id = st.selectbox(
            "Select vehicle to edit:",
            vehicles_df["object_id"].tolist(),
            key="edit_vehicle_select"
        )
        
        if selected_vehicle_id:
            vehicle = vehicles_df[vehicles_df["object_id"] == selected_vehicle_id].iloc[0]
            
            with st.form("edit_vehicle_form"):
                name = st.text_input("Vehicle Name", value=vehicle["name"])
                description = st.text_area("Description", value=vehicle["description"], max_chars=500)
                status = st.selectbox("Status", ["Active", "Inactive", "Maintenance"], 
                                     index=["Active", "Inactive", "Maintenance"].index(vehicle["status"]))
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Update Vehicle")
                with col2:
                    delete_btn = st.form_submit_button("Delete Vehicle", type="secondary")
                
                if submitted:
                    handler.update_object(
                        selected_vehicle_id,
                        name=name,
                        description=description,
                        status=status
                    )
                    st.success("✓ Vehicle updated successfully!")
                    st.rerun()
                
                if delete_btn:
                    handler.delete_object(selected_vehicle_id)
                    st.success("✓ Vehicle deleted successfully!")
                    st.rerun()

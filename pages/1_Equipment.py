import streamlit as st
import pandas as pd
from utils.data_handler import DataHandler
from utils.state_manager import StateManager
from datetime import datetime

st.set_page_config(page_title="Equipment", layout="wide")


StateManager.init_session_state()
handler = DataHandler()
user_email = st.session_state.get('user_email')
is_admin = st.session_state.get('user_role') == 'admin'

st.header("🛠️ Equipment Management")

# Sidebar filters
st.sidebar.header("Filters")
object_type_filter = st.sidebar.selectbox(
    "Object Type",
    ["All"] + handler.OBJECT_TYPES,
    key="equipment_object_type"
)

status_filter = st.sidebar.selectbox(
    "Status Filter",
    ["All", "Active", "Inactive", "Maintenance"],
    key="equipment_status_filter"
)

# Get objects and apply filters
vehicles_df = handler.get_objects(user_email=user_email, is_admin=is_admin)
if object_type_filter != "All":
    vehicles_df = vehicles_df[vehicles_df["object_type"] == object_type_filter]
if status_filter != "All":
    vehicles_df = vehicles_df[vehicles_df["status"] == status_filter]

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["View Equipment", "Add Equipment", "Edit Equipment"])

with tab1:
    st.subheader("All Equipment")
    
    if vehicles_df.empty:
        st.info("No equipment found. Add one to get started!")
    else:
        # Display vehicles in a table
        col1, col2 = st.columns([4, 1])
        with col1:
            column_config = {
                "object_type": st.column_config.TextColumn(width="small"),
                "object_id": st.column_config.TextColumn(width="stretch"),
                "name": st.column_config.TextColumn(width="stretch"),
                "description": st.column_config.TextColumn(width="stretch"),
                "status": st.column_config.TextColumn(width="stretch"),
                "created_date": st.column_config.TextColumn(width="stretch"),
            }
            selected_vehicle = st.dataframe(
                vehicles_df[["object_type", "object_id", "name", "description", "status", "created_date"]],
                use_container_width=True,
                column_config=column_config,
                hide_index=True
            )
        
        # Click on row to view details
        vehicle_ids = vehicles_df["object_id"].tolist()
        selected_id = st.selectbox("Select equipment to view details:", vehicle_ids)
        
        if selected_id:
            StateManager.set_object_id(selected_id)
            vehicle = vehicles_df[vehicles_df["object_id"] == selected_id].iloc[0]
            StateManager.set_object_type(vehicle['object_type'])
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
            st.subheader("Services for this Equipment")
            services_df = handler.get_services(object_id=selected_id, user_email=user_email, is_admin=is_admin)
            
            if services_df.empty:
                st.info("No services scheduled for this equipment.")
            else:
                st.dataframe(
                    services_df[["service_id", "service_name", "interval_days", 
                                 "next_service_date", "status"]],
                    use_container_width=True
                )
            
            # Show reminders
            st.write("---")
            st.subheader("Reminders for this Equipment")
            reminders_df = handler.get_reminders(object_id=selected_id, user_email=user_email, is_admin=is_admin)
            
            if reminders_df.empty:
                st.info("No reminders for this equipment.")
            else:
                st.dataframe(
                    reminders_df[["reminder_id", "service_id", "reminder_date", "status"]],
                    use_container_width=True
                )

with tab2:
    st.subheader("Add New Equipment")
    
    with st.form("add_equipment_form"):
        object_type = st.selectbox("Object Type", handler.OBJECT_TYPES)
        name = st.text_input("Equipment Name (e.g., Truck-001)")
        description = st.text_area("Description", max_chars=500)
        status = st.selectbox("Status", ["Active", "Inactive", "Maintenance"])
        
        submitted = st.form_submit_button("Add Equipment")
        if submitted:
            if name:
                vehicle_id = handler.add_object(
                    object_type=object_type,
                    name=name,
                    description=description,
                    status=status,
                    user_email=user_email
                )
                st.success(f"✓ Equipment added successfully! ID: {vehicle_id}")
                st.rerun()
            else:
                st.error("Please enter a name.")

with tab3:
    st.subheader("Edit Equipment")
    
    if vehicles_df.empty:
        st.info("No equipment to edit.")
    else:
        selected_vehicle_id = st.selectbox(
            "Select equipment to edit:",
            vehicles_df["object_id"].tolist(),
            key="edit_equipment_select"
        )
        if selected_vehicle_id:
            vehicle = vehicles_df[vehicles_df["object_id"] == selected_vehicle_id].iloc[0]
            with st.form("edit_equipment_form"):
                object_type_val = st.selectbox("Object Type", handler.OBJECT_TYPES, index=handler.OBJECT_TYPES.index(vehicle["object_type"]) if vehicle["object_type"] in handler.OBJECT_TYPES else 0)
                name = st.text_input("Equipment Name", value=vehicle["name"])
                description = st.text_area("Description", value=vehicle["description"], max_chars=500)
                status = st.selectbox("Status", ["Active", "Inactive", "Maintenance"], 
                                     index=["Active", "Inactive", "Maintenance"].index(vehicle["status"]))
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Update Equipment")
                with col2:
                    delete_btn = st.form_submit_button("Delete Equipment", type="secondary")
                if submitted:
                    handler.update_object(
                        selected_vehicle_id,
                        object_type=object_type_val,
                        name=name,
                        description=description,
                        status=status
                    )
                    st.success("✓ Equipment updated successfully!")
                    st.rerun()
                if delete_btn:
                    handler.delete_object(selected_vehicle_id)
                    st.success("✓ Equipment deleted successfully!")
                    st.rerun()

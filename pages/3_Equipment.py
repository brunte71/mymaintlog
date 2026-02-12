import streamlit as st
import pandas as pd
from utils.data_handler import DataHandler
from utils.state_manager import StateManager
from datetime import datetime

st.set_page_config(page_title="Equipment", layout="wide")

StateManager.init_session_state()
handler = DataHandler()

st.header("⚙️ Equipment Management")

# Sidebar filters
st.sidebar.header("Filters")
status_filter = st.sidebar.selectbox(
    "Status Filter",
    ["All", "Active", "Inactive", "Maintenance"],
    key="equipment_status_filter"
)

# Get equipment
equipment_df = handler.get_objects("Equipment")

# Apply filters
if status_filter != "All":
    equipment_df = equipment_df[equipment_df["status"] == status_filter]

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["View Equipment", "Add Equipment", "Edit Equipment"])

with tab1:
    st.subheader("All Equipment")
    
    if equipment_df.empty:
        st.info("No equipment found. Add one to get started!")
    else:
        # Display equipment in a table
        col1, col2 = st.columns([4, 1])
        with col1:
            selected_equipment = st.dataframe(
                equipment_df[["object_id", "name", "description", "status", "created_date"]],
                use_container_width=True
            )
        
        # Click on row to view details
        equipment_ids = equipment_df["object_id"].tolist()
        selected_id = st.selectbox("Select an equipment to view details:", equipment_ids)
        
        if selected_id:
            StateManager.set_object_id(selected_id)
            StateManager.set_object_type("Equipment")
            
            equip = equipment_df[equipment_df["object_id"] == selected_id].iloc[0]
            
            st.write("---")
            st.subheader(f"Details: {equip['name']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**ID:** {equip['object_id']}")
                st.write(f"**Type:** {equip['object_type']}")
                st.write(f"**Status:** {equip['status']}")
            with col2:
                st.write(f"**Description:** {equip['description']}")
                st.write(f"**Created:** {equip['created_date']}")
                st.write(f"**Last Updated:** {equip['last_updated']}")
            
            # Show services for this equipment
            st.write("---")
            st.subheader("Services for this Equipment")
            services_df = handler.get_services(object_id=selected_id)
            
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
            reminders_df = handler.get_reminders(object_id=selected_id)
            
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
        name = st.text_input("Equipment Name (e.g., Air Compressor, Generator)")
        description = st.text_area("Description", max_chars=500)
        status = st.selectbox("Status", ["Active", "Inactive", "Maintenance"])
        
        submitted = st.form_submit_button("Add Equipment")
        if submitted:
            if name:
                equipment_id = handler.add_object(
                    object_type="Equipment",
                    name=name,
                    description=description,
                    status=status
                )
                st.success(f"✓ Equipment added successfully! ID: {equipment_id}")
                st.rerun()
            else:
                st.error("Please enter an equipment name.")

with tab3:
    st.subheader("Edit Equipment")
    
    if equipment_df.empty:
        st.info("No equipment to edit.")
    else:
        selected_equipment_id = st.selectbox(
            "Select equipment to edit:",
            equipment_df["object_id"].tolist(),
            key="edit_equipment_select"
        )
        
        if selected_equipment_id:
            equip = equipment_df[equipment_df["object_id"] == selected_equipment_id].iloc[0]
            
            with st.form("edit_equipment_form"):
                name = st.text_input("Equipment Name", value=equip["name"])
                description = st.text_area("Description", value=equip["description"], max_chars=500)
                status = st.selectbox("Status", ["Active", "Inactive", "Maintenance"], 
                                     index=["Active", "Inactive", "Maintenance"].index(equip["status"]))
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Update Equipment")
                with col2:
                    delete_btn = st.form_submit_button("Delete Equipment", type="secondary")
                
                if submitted:
                    handler.update_object(
                        selected_equipment_id,
                        name=name,
                        description=description,
                        status=status
                    )
                    st.success("✓ Equipment updated successfully!")
                    st.rerun()
                
                if delete_btn:
                    handler.delete_object(selected_equipment_id)
                    st.success("✓ Equipment deleted successfully!")
                    st.rerun()

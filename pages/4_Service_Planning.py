import streamlit as st
import pandas as pd
from utils.data_handler import DataHandler
from utils.state_manager import StateManager
from datetime import datetime, timedelta

st.set_page_config(page_title="Service Planning", layout="wide")


StateManager.init_session_state()
handler = DataHandler()
user_email = st.session_state.get('user_email')
is_admin = st.session_state.get('user_role') == 'admin'

st.header("📋 Service Planning")

# Sidebar filters
st.sidebar.header("Filters")
object_type_filter = st.sidebar.selectbox(
    "Object Type",
    ["All"] + handler.OBJECT_TYPES
)

# Meter unit management
with st.sidebar.expander("Manage Meter Units"):
    mu_list = handler.get_meter_units()
    st.write("Current units:")
    for u in mu_list:
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(u)
        with col2:
            if st.button(f"Delete {u}", key=f"del_mu_{u}"):
                deleted = handler.delete_meter_unit(u)
                if deleted:
                    st.success(f"Deleted unit {u}")
                    st.experimental_rerun()
                else:
                    st.error("Could not delete unit")

    new_unit = st.text_input("Add Unit", key="add_mu_input")
    if st.button("Add Unit"):
        added = handler.add_meter_unit(new_unit)
        if added:
            st.success(f"Added unit {new_unit}")
            st.experimental_rerun()
        else:
            st.error("Could not add unit (may already exist or be empty)")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["View Services", "Schedule Service", "Edit Service"])

with tab1:
    st.subheader("Service Schedule")
    
    # Get services
    if object_type_filter == "All":
        services_df = handler.get_services(user_email=user_email, is_admin=is_admin)
    else:
        services_df = handler.get_services(object_type=object_type_filter, user_email=user_email, is_admin=is_admin)
    
    if services_df.empty:
        st.info("No services scheduled. Add one to get started!")
    else:
        # Add a computed column for days until service
        services_df = services_df.copy()
        services_df["days_until_service"] = pd.to_datetime(
            services_df["next_service_date"]
        ) - pd.Timestamp.now()
        services_df["days_until_service"] = services_df["days_until_service"].dt.days
        
        # Sort by days until service
        services_df = services_df.sort_values("days_until_service")
        
        # Display table
        display_cols = ["service_id", "object_id", "object_type", "service_name", 
                       "interval_days", "next_service_date", "days_until_service", "status",
                       "expected_meter_reading", "meter_unit"]
        st.dataframe(
            services_df[display_cols],
            use_container_width=True,
            hide_index=True
        )
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            overdue = len(services_df[services_df["days_until_service"] < 0])
            st.metric("Overdue Services", overdue, delta=None, delta_color="inverse")
        with col2:
            due_soon = len(services_df[(services_df["days_until_service"] >= 0) & 
                                      (services_df["days_until_service"] <= 7)])
            st.metric("Due in 7 Days", due_soon)
        with col3:
            scheduled = len(services_df[services_df["status"] == "Scheduled"])
            st.metric("Scheduled", scheduled)
        with col4:
            completed = len(services_df[services_df["status"] == "Completed"])
            st.metric("Completed", completed)

with tab2:
    st.subheader("Schedule New Service")
    
    # Get all objects
    all_objects = handler.get_objects()
    
    if all_objects.empty:
        st.warning("No equipment found. Please add equipment first.")
    else:
        # --- Robust, reactive object type/equipment selection ---
        if "service_object_type" not in st.session_state:
            st.session_state["service_object_type"] = object_type_filter if object_type_filter in handler.OBJECT_TYPES else handler.OBJECT_TYPES[0]
        def set_service_object_type():
            st.session_state["service_object_type"] = st.session_state["service_object_type_select"]

        # Place Object Type selectbox OUTSIDE the form for reactivity
        object_type_tab = st.selectbox(
            "Object Type",
            handler.OBJECT_TYPES,
            index=handler.OBJECT_TYPES.index(st.session_state["service_object_type"]),
            key="service_object_type_select",
            on_change=set_service_object_type
        )
        filter_type = st.session_state["service_object_type"]
        obj_list = all_objects[all_objects["object_type"] == filter_type]
        with st.form("schedule_service_form"):
            if obj_list.empty:
                st.warning(f"No {filter_type.lower()} found. Please add one first.")
                submitted = st.form_submit_button("Schedule Service", disabled=True)
            else:
                object_id = st.selectbox(
                    "Select Equipment",
                    obj_list["object_id"].tolist(),
                    format_func=lambda x: f"{x} - {obj_list[obj_list['object_id']==x]['name'].values[0]}",
                    key="service_equipment_select"
                )
                service_name = st.text_input("Service Name (e.g., Oil Change, Inspection)")
                description = st.text_area("Description", max_chars=500)
                interval_days = st.number_input("Service Interval (days)", min_value=1, value=30)
                expected_meter_reading = st.number_input("Expected Meter Reading", min_value=0, value=0)
                meter_unit = st.selectbox("Meter Unit", handler.get_meter_units())
                status = st.selectbox("Status", ["Scheduled", "Pending", "In Progress", "Completed"])
                notes = st.text_area("Notes", max_chars=500)
                submitted = st.form_submit_button("Schedule Service")
            
            if submitted and not obj_list.empty:
                if service_name:
                    service_id = handler.add_service(
                        object_id=object_id,
                        object_type=st.session_state["service_object_type"],
                        service_name=service_name,
                        interval_days=interval_days,
                        expected_meter_reading=int(expected_meter_reading) if expected_meter_reading is not None else None,
                        meter_unit=meter_unit,
                        description=description,
                        status=status,
                        notes=notes
                    )
                    st.success(f"✓ Service scheduled successfully! ID: {service_id}")
                    st.rerun()
                else:
                    st.error("Please enter a service name.")

with tab3:
    st.subheader("Edit Service")
    
    # Get services filtered by object type
    if object_type_filter == "All":
        services_df = handler.get_services()
    else:
        services_df = handler.get_services(object_type=object_type_filter)
    
    if services_df.empty:
        st.info("No services to edit.")
    else:
        selected_service_id = st.selectbox(
            "Select service to edit:",
            services_df["service_id"].tolist(),
            format_func=lambda x: f"{x} - {services_df[services_df['service_id']==x]['service_name'].values[0]}"
        )
        
        if selected_service_id:
            service = services_df[services_df["service_id"] == selected_service_id].iloc[0]
            
            with st.form("edit_service_form"):
                service_name = st.text_input("Service Name", value=service["service_name"])
                description = st.text_area("Description", value=service["description"], max_chars=500)
                interval_days = st.number_input("Service Interval (days)", value=int(service["interval_days"]))
                expected_meter_reading = st.number_input("Expected Meter Reading", min_value=0, value=int(service.get("expected_meter_reading") if pd.notna(service.get("expected_meter_reading")) and service.get("expected_meter_reading") is not None else 0))
                meter_unit = st.selectbox("Meter Unit", handler.get_meter_units(), index=handler.get_meter_units().index(service.get("meter_unit")) if service.get("meter_unit") in handler.get_meter_units() else 0)
                last_service_date = st.date_input(
                    "Last Service Date",
                    value=pd.to_datetime(service["last_service_date"]) if pd.notna(service["last_service_date"]) else None
                )
                next_service_date = st.date_input(
                    "Next Service Date",
                    value=pd.to_datetime(service["next_service_date"])
                )
                status = st.selectbox(
                    "Status",
                    ["Scheduled", "Pending", "In Progress", "Completed"],
                    index=["Scheduled", "Pending", "In Progress", "Completed"].index(service["status"])
                )
                notes = st.text_area("Notes", value=service["notes"], max_chars=500)
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Update Service")
                with col2:
                    delete_btn = st.form_submit_button("Delete Service", type="secondary")
                
                if submitted:
                    handler.update_service(
                        selected_service_id,
                        service_name=service_name,
                        description=description,
                        interval_days=interval_days,
                        expected_meter_reading=int(expected_meter_reading) if expected_meter_reading is not None else None,
                        meter_unit=meter_unit,
                        last_service_date=str(last_service_date) if last_service_date else None,
                        next_service_date=str(next_service_date),
                        status=status,
                        notes=notes
                    )
                    st.success("✓ Service updated successfully!")
                    st.rerun()
                
                if delete_btn:
                    handler.delete_service(selected_service_id)
                    st.success("✓ Service deleted successfully!")
                    st.rerun()

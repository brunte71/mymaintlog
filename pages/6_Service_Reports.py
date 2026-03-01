import streamlit as st
import pandas as pd
from utils.data_handler import DataHandler
from utils.state_manager import StateManager
from datetime import datetime

st.set_page_config(page_title="Service Reports", layout="wide")


StateManager.init_session_state()
StateManager.enforce_auth()
handler = DataHandler()
user_email = st.session_state.get('user_email')
is_admin = st.session_state.get('user_role') == 'admin'

st.header("📊 Service Reports")

# Sidebar filters
st.sidebar.header("Filters")
object_type_filter = st.sidebar.selectbox(
    "Object Type",
    ["All"] + handler.OBJECT_TYPES,
    key="reports_object_type"
)

report_type_filter = st.sidebar.selectbox(
    "Report Type",
    ["All", "Maintenance", "Inspection", "Repair", "Preventive", "Other"],
    key="reports_type"
)

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["View Reports", "Add Report", "Edit Report"])

with tab1:
    st.subheader("Service Reports")
    
    # Get reports
    reports_df = handler.get_reports(user_email=user_email, is_admin=is_admin)
    
    # Apply filters
    if object_type_filter != "All":
        reports_df = reports_df[reports_df["object_type"] == object_type_filter]
    
    if report_type_filter != "All":
        reports_df = reports_df[reports_df["report_type"] == report_type_filter]
    
    if reports_df.empty:
        st.info("No reports found. Add one to get started!")
    else:
        # Display table
        display_cols = ["report_id", "object_id", "object_type", "report_type", 
                       "title", "completion_date", "notes", "actual_meter_reading", "meter_unit"]
        st.dataframe(
            reports_df[display_cols],
            use_container_width=True,
            hide_index=True
        )
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            total_reports = len(reports_df)
            st.metric("Total Reports", total_reports)
        with col2:
            unique_objects = reports_df["object_id"].nunique()
            st.metric("Objects Reported", unique_objects)
        with col3:
            maintenance_reports = len(reports_df[reports_df["report_type"] == "Maintenance"])
            st.metric("Maintenance Reports", maintenance_reports)
        
        # Detailed view
        st.write("---")
        st.subheader("Report Details")
        
        selected_report_id = st.selectbox(
            "Select report to view details:",
            reports_df["report_id"].tolist(),
            key="view_report_select"
        )
        
        if selected_report_id:
            report = reports_df[reports_df["report_id"] == selected_report_id].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Report ID:** {report['report_id']}")
                st.write(f"**Object ID:** {report['object_id']}")
                st.write(f"**Object Type:** {report['object_type']}")
                st.write(f"**Report Type:** {report['report_type']}")
            with col2:
                st.write(f"**Title:** {report['title']}")
                st.write(f"**Completion Date:** {report['completion_date']}")
                st.write(f"**Created Date:** {report['created_date']}")
            
            st.write("**Description:**")
            st.write(report['description'])
            
            st.write("**Notes:**")
            st.write(report['notes'])

with tab2:
    st.subheader("Add New Report")
    
    # Get all objects
    all_objects = handler.get_objects()
    
    if all_objects.empty:
        st.warning("No equipment found. Please add equipment first.")
    else:
        # --- Robust, reactive object type/equipment selection ---
        if "report_object_type" not in st.session_state:
            st.session_state["report_object_type"] = object_type_filter if object_type_filter in handler.OBJECT_TYPES else handler.OBJECT_TYPES[0]
        def set_report_object_type():
            st.session_state["report_object_type"] = st.session_state["report_object_type_select"]

        # Place Object Type selectbox OUTSIDE the form for reactivity
        object_type_tab = st.selectbox(
            "Object Type",
            handler.OBJECT_TYPES,
            index=handler.OBJECT_TYPES.index(st.session_state["report_object_type"]),
            key="report_object_type_select",
            on_change=set_report_object_type
        )
        filter_type = st.session_state["report_object_type"]
        obj_list = all_objects[all_objects["object_type"] == filter_type]
        with st.form("add_report_form"):
            if obj_list.empty:
                st.warning(f"No {filter_type.lower()} found. Please add one first.")
                submitted = st.form_submit_button("Add Report", disabled=True)
            else:
                object_id = st.selectbox(
                    "Select Equipment",
                    obj_list["object_id"].tolist(),
                    format_func=lambda x: f"{x} - {obj_list[obj_list['object_id']==x]['name'].values[0]}",
                    key="report_equipment_select"
                )
                report_type = st.selectbox(
                    "Report Type",
                    ["Maintenance", "Inspection", "Repair", "Preventive", "Other"]
                )
                actual_meter_reading = st.number_input("Actual Meter Reading", min_value=0, value=0)
                meter_unit = st.selectbox("Meter Unit", handler.get_meter_units())
                title = st.text_input("Report Title")
                description = st.text_area("Description", max_chars=1000)
                completion_date = st.date_input("Completion Date")
                notes = st.text_area("Notes", max_chars=500)
                submitted = st.form_submit_button("Add Report")
            
            if submitted and not obj_list.empty:
                if title:
                    report_id = handler.add_report(
                        object_id=object_id,
                        object_type=st.session_state["report_object_type"],
                        report_type=report_type,
                        title=title,
                        description=description,
                        completion_date=str(completion_date),
                        notes=notes,
                        actual_meter_reading=int(actual_meter_reading) if actual_meter_reading is not None else None,
                        meter_unit=meter_unit,
                        user_email=user_email
                    )
                    st.success(f"✓ Report added successfully! ID: {report_id}")
                    st.rerun()
                else:
                    st.error("Please enter a report title.")

with tab3:
    st.subheader("Edit Report")
    
    # Get reports filtered by object type
    if object_type_filter == "All":
        reports_df = handler.get_reports()
    else:
        reports_df = handler.get_reports(object_type=object_type_filter)
    
    if reports_df.empty:
        st.info("No reports to edit.")
    else:
        selected_report_id = st.selectbox(
            "Select report to edit:",
            reports_df["report_id"].tolist(),
            key="edit_report_select"
        )
        
        if selected_report_id:
            report = reports_df[reports_df["report_id"] == selected_report_id].iloc[0]
            
            with st.form("edit_report_form"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Object ID:** {report['object_id']}")
                    st.write(f"**Object Type:** {report['object_type']}")
                with col2:
                    st.write(f"**Report ID:** {report['report_id']}")
                
                report_type = st.selectbox(
                    "Report Type",
                    ["Maintenance", "Inspection", "Repair", "Preventive", "Other"],
                    index=["Maintenance", "Inspection", "Repair", "Preventive", "Other"].index(report["report_type"])
                )
                title = st.text_input("Report Title", value=report["title"])
                description = st.text_area("Description", value=report["description"], max_chars=1000)
                actual_meter_reading = st.number_input("Actual Meter Reading", min_value=0, value=int(report.get("actual_meter_reading") if pd.notna(report.get("actual_meter_reading")) and report.get("actual_meter_reading") is not None else 0))
                meter_unit = st.selectbox("Meter Unit", handler.get_meter_units(), index=handler.get_meter_units().index(report.get("meter_unit")) if report.get("meter_unit") in handler.get_meter_units() else 0)
                completion_date = st.date_input(
                    "Completion Date",
                    value=pd.to_datetime(report["completion_date"])
                )
                notes = st.text_area("Notes", value=report["notes"], max_chars=500)
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Update Report")
                with col2:
                    delete_btn = st.form_submit_button("Delete Report", type="secondary")
                
                if submitted:
                    handler.update_report(
                        selected_report_id,
                        report_type=report_type,
                        title=title,
                        description=description,
                        completion_date=str(completion_date),
                        notes=notes,
                        actual_meter_reading=int(actual_meter_reading) if actual_meter_reading is not None else None,
                        meter_unit=meter_unit
                    )
                    st.success("✓ Report updated successfully!")
                    st.rerun()
                
                if delete_btn:
                    handler.delete_report(selected_report_id)
                    st.success("✓ Report deleted successfully!")
                    st.rerun()

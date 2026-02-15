import streamlit as st
import pandas as pd
import os
from utils.data_handler import DataHandler
from utils.state_manager import StateManager
from datetime import datetime

st.set_page_config(page_title="Fault Reports", layout="wide")

StateManager.init_session_state()
handler = DataHandler()

st.header("🚨 Fault Reports")

# Sidebar filter
object_type_filter = st.sidebar.selectbox(
    "Object Type",
    ["All"] + handler.OBJECT_TYPES,
    key="fault_object_type"
)

# Tabs
view_tab, add_tab = st.tabs(["View Fault Reports", "Add Fault Report"])

with view_tab:
    st.subheader("All Fault Reports")
    df = handler.get_fault_reports()
    if object_type_filter != "All":
        df = df[df["object_type"] == object_type_filter]
    if df.empty:
        st.info("No fault reports found.")
    else:
        st.dataframe(df[["fault_id", "object_id", "object_type", "observation_date", "actual_meter_reading", "meter_unit", "description", "created_date"]], use_container_width=True, hide_index=True)
        selected_fault_id = st.selectbox(
            "Select fault report to view details:",
            df["fault_id"].tolist(),
            key="view_fault_select"
        )
        if selected_fault_id:
            fault = df[df["fault_id"] == selected_fault_id].iloc[0]
            st.write(f"**Fault ID:** {fault['fault_id']}")
            st.write(f"**Object ID:** {fault['object_id']}")
            st.write(f"**Object Type:** {fault['object_type']}")
            st.write(f"**Observation Date:** {fault['observation_date']}")
            st.write(f"**Actual Meter Reading:** {fault['actual_meter_reading']} {fault['meter_unit']}")
            st.write(f"**Description:** {fault['description']}")
            st.write(f"**Created Date:** {fault['created_date']}")
            # Show photos
            if fault['photo_paths']:
                st.write("**Photos:**")
                for path in fault['photo_paths'].split(';'):
                    if path:
                        st.image(path, width=300)
            # Schedule Service button
            if st.button("Schedule Service for this Fault"):
                StateManager.set_object_id(fault['object_id'])
                StateManager.set_object_type(fault['object_type'])
                st.session_state["service_object_type"] = fault['object_type']
                st.session_state["service_equipment_select"] = fault['object_id']
                st.session_state["service_name"] = f"Service for Fault {fault['fault_id']}"
                st.session_state["expected_meter_reading"] = int(fault['actual_meter_reading']) if pd.notna(fault['actual_meter_reading']) else 0
                st.session_state["meter_unit"] = fault['meter_unit']
                st.switch_page("4_Service_Planning.py")

with add_tab:
    st.subheader("Add New Fault Report")
    all_objects = handler.get_objects()
    if all_objects.empty:
        st.warning("No equipment found. Please add equipment first.")
    else:
        # --- Robust, reactive object type/equipment selection (copied from Add Report) ---
        if "fault_report_object_type" not in st.session_state:
            st.session_state["fault_report_object_type"] = object_type_filter if object_type_filter in handler.OBJECT_TYPES else handler.OBJECT_TYPES[0]
        def set_fault_report_object_type():
            st.session_state["fault_report_object_type"] = st.session_state["fault_report_object_type_select"]

        # Place Object Type selectbox OUTSIDE the form for reactivity
        object_type_tab = st.selectbox(
            "Object Type",
            handler.OBJECT_TYPES,
            index=handler.OBJECT_TYPES.index(st.session_state["fault_report_object_type"]),
            key="fault_report_object_type_select",
            on_change=set_fault_report_object_type
        )
        filter_type = st.session_state["fault_report_object_type"]
        obj_list = all_objects[all_objects["object_type"] == filter_type]
        with st.form("add_fault_form"):
            if obj_list.empty:
                st.warning(f"No {filter_type.lower()} found. Please add one first.")
                submitted = st.form_submit_button("Add Fault Report", disabled=True)
            else:
                object_id = st.selectbox(
                    "Select Equipment",
                    obj_list["object_id"].tolist(),
                    format_func=lambda x: f"{x} - {obj_list[obj_list['object_id']==x]['name'].values[0]}",
                    key="fault_add_equipment_select"
                )
                observation_date = st.date_input("Observation Date", value=datetime.today())
                actual_meter_reading = st.number_input("Actual Meter Reading", min_value=0, value=0)
                meter_unit = st.selectbox("Meter Unit", handler.get_meter_units())
                description = st.text_area("Description", max_chars=1000)
                uploaded_files = st.file_uploader("Upload Photos", accept_multiple_files=True, type=["png", "jpg", "jpeg"], key="fault_photos")
                take_photo = st.checkbox("Take photo with camera", key="take_photo_checkbox")
                camera_image = None
                if take_photo:
                    camera_image = st.camera_input("Camera", key="fault_camera")
                submitted = st.form_submit_button("Add Fault Report")
            if submitted and not obj_list.empty:
                # Save uploaded files and camera photo
                photo_paths = []
                photo_dir = os.path.join("data", "fault_photos")
                os.makedirs(photo_dir, exist_ok=True)
                if uploaded_files:
                    for file in uploaded_files:
                        file_path = os.path.join(photo_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{file.name}")
                        with open(file_path, "wb") as f:
                            f.write(file.read())
                        photo_paths.append(file_path)
                if camera_image is not None:
                    cam_file_path = os.path.join(photo_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_camera.jpg")
                    with open(cam_file_path, "wb") as f:
                        f.write(camera_image.getvalue())
                    photo_paths.append(cam_file_path)
                fault_id = handler.add_fault_report(
                    object_id=object_id,
                    object_type=filter_type,
                    observation_date=str(observation_date),
                    actual_meter_reading=int(actual_meter_reading),
                    meter_unit=meter_unit,
                    description=description,
                    photo_paths=photo_paths
                )
                st.success(f"✓ Fault report added successfully! ID: {fault_id}")
                st.rerun()

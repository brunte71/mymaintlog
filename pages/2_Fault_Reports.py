import streamlit as st
import pandas as pd
import os
from utils.data_handler import DataHandler
from utils.state_manager import StateManager
from datetime import datetime

st.set_page_config(page_title="Fault Reports", layout="wide")


StateManager.init_session_state()
handler = DataHandler()
user_email = st.session_state.get('user_email')
is_admin = st.session_state.get('user_role') == 'admin'

st.header("🚨 Fault Reports")

# Sidebar filter
object_type_filter = st.sidebar.selectbox(
    "Object Type",
    ["All"] + handler.OBJECT_TYPES,
    key="fault_object_type"
)


# Tabs
view_tab, add_tab, edit_tab = st.tabs(["View Fault Reports", "Add Fault Report", "Edit Fault Report"])
with edit_tab:
    st.subheader("Edit Fault Report")
    df = handler.get_fault_reports(user_email=user_email, is_admin=is_admin)
    if df.empty:
        st.info("No fault reports to edit.")
    else:
        selected_fault_id = st.selectbox(
            "Select fault report to edit:",
            df["fault_id"].tolist(),
            key="edit_fault_select"
        )
        if selected_fault_id:
            fault = df[df["fault_id"] == selected_fault_id].iloc[0]
            with st.form("edit_fault_form"):
                object_id = st.text_input("Object ID", value=fault["object_id"])
                object_type = st.selectbox("Object Type", handler.OBJECT_TYPES, index=handler.OBJECT_TYPES.index(fault["object_type"]))
                observation_date = st.date_input("Observation Date", value=pd.to_datetime(fault["observation_date"]))
                actual_meter_reading = st.number_input("Actual Meter Reading", min_value=0, value=int(fault["actual_meter_reading"]))
                meter_unit = st.selectbox("Meter Unit", handler.get_meter_units(), index=handler.get_meter_units().index(fault["meter_unit"]) if fault["meter_unit"] in handler.get_meter_units() else 0)
                description = st.text_area("Description", value=fault["description"] if pd.notna(fault["description"]) else "", max_chars=1000)
                # Photo management
                photo_paths_val = str(fault['photo_paths']) if pd.notna(fault['photo_paths']) else ''
                photo_list = [p for p in photo_paths_val.split(';') if p and p.lower() != 'nan']
                st.write("**Photos for this Fault Report:**")
                remove_photos = []
                for idx, path in enumerate(photo_list):
                    st.image(path, width=120, caption=f"Photo {idx+1}")
                    if st.checkbox(f"Remove Photo {idx+1}", key=f"remove_photo_{selected_fault_id}_{idx}"):
                        remove_photos.append(path)
                new_photos = st.file_uploader("Add new photos", accept_multiple_files=True, type=["png", "jpg", "jpeg"], key=f"edit_fault_photos_{selected_fault_id}")
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Save Changes")
                with col2:
                    delete_btn = st.form_submit_button("Delete Fault Report", type="secondary")
                # Handle photo changes
                updated_photo_list = [p for p in photo_list if p not in remove_photos]
                photo_dir = os.path.join("data", "fault_photos")
                os.makedirs(photo_dir, exist_ok=True)
                if new_photos:
                    for file in new_photos:
                        file_path = os.path.join(photo_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{file.name}")
                        with open(file_path, "wb") as f:
                            f.write(file.read())
                        updated_photo_list.append(file_path)
                updated_photo_paths = ";".join(updated_photo_list)
            if submitted:
                handler.update_fault_report(
                    fault_id=selected_fault_id,
                    object_id=object_id,
                    object_type=object_type,
                    observation_date=str(observation_date),
                    actual_meter_reading=int(actual_meter_reading),
                    meter_unit=meter_unit,
                    description=description,
                    photo_paths=updated_photo_paths
                )
                st.success("✓ Fault report updated.")
                st.rerun()
            if delete_btn:
                df = handler.get_fault_reports()
                df = df[df["fault_id"] != selected_fault_id]
                handler._write_df_atomic(handler.fault_reports_file, df)
                st.success("✓ Fault report deleted.")
                st.rerun()

with view_tab:
    st.subheader("All Fault Reports")
    df = handler.get_fault_reports(user_email=user_email, is_admin=is_admin)
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
            # Show preview image and photo viewer
            photo_paths_val = str(fault['photo_paths']) if pd.notna(fault['photo_paths']) else ''
            photo_list = [p for p in photo_paths_val.split(';') if p and p.lower() != 'nan']
            if photo_list:
                st.write("**Photo Preview:**")
                # Show first photo as preview, clickable
                if 'show_photo_viewer' not in st.session_state:
                    st.session_state['show_photo_viewer'] = False
                if st.session_state['show_photo_viewer']:
                    st.write("**Photos Viewer**")
                    for path in photo_list:
                        st.image(path, width=400)
                    if st.button("Close Viewer", key="close_photo_viewer_btn"):
                        st.session_state['show_photo_viewer'] = False
                        st.rerun()
                else:
                    col_show, col_count = st.columns([2,1])
                    with col_show:
                        if st.button("Show All Photos", key="open_photo_viewer_btn"):
                            st.session_state['show_photo_viewer'] = True
                            st.rerun()
                    with col_count:
                        st.markdown(f"**{len(photo_list)} photo{'s' if len(photo_list)!=1 else ''}**")
                    st.image(photo_list[0], width=120, caption="Click 'Show All Photos' to view")
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
    all_objects = handler.get_objects(user_email=user_email, is_admin=is_admin)
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
        # Camera checkbox and input outside the form for reactivity
        take_photo = st.checkbox("Take photo with camera", key="take_photo_checkbox")
        # Initialize session state for multiple camera images
        if "fault_camera_images" not in st.session_state:
            st.session_state["fault_camera_images"] = []
        if take_photo:
            st.write("You can take multiple photos. After each photo, click 'Add this photo'.")
            camera_image = st.camera_input("Camera", key="fault_camera")
            if camera_image is not None:
                if st.button("Add this photo", key="add_camera_photo_btn"):
                    st.session_state["fault_camera_images"].append(camera_image)
                    st.rerun()
            # Show thumbnails of added camera images
            if st.session_state["fault_camera_images"]:
                st.write("**Camera Photos Added:**")
                for idx, img in enumerate(st.session_state["fault_camera_images"]):
                    st.image(img, width=100, caption=f"Photo {idx+1}")
                if st.button("Clear all camera photos", key="clear_camera_photos_btn"):
                    st.session_state["fault_camera_images"] = []
                    st.rerun()
        else:
            st.session_state["fault_camera_images"] = []

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
                submitted = st.form_submit_button("Add Fault Report")
            if submitted and not obj_list.empty:
                # Save uploaded files and camera photos
                photo_paths = []
                photo_dir = os.path.join("data", "fault_photos")
                os.makedirs(photo_dir, exist_ok=True)
                if uploaded_files:
                    for file in uploaded_files:
                        file_path = os.path.join(photo_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{file.name}")
                        with open(file_path, "wb") as f:
                            f.write(file.read())
                        photo_paths.append(file_path)
                # Save all camera images
                for idx, camera_image in enumerate(st.session_state.get("fault_camera_images", [])):
                    cam_file_path = os.path.join(photo_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_camera_{idx+1}.jpg")
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
                    photo_paths=photo_paths,
                    user_email=user_email
                )
                st.success(f"✓ Fault report added successfully! ID: {fault_id}")
                # Reset only non-widget session state to avoid StreamlitAPIException
                st.session_state["fault_camera_images"] = []
                st.session_state["fault_photos"] = None
                st.session_state["fault_report_object_type"] = handler.OBJECT_TYPES[0]
                st.rerun()

"""
Service Management App - Main Entry Point

This is a Streamlit-based service management application that helps manage:
- Objects: Equipment (Vehicles, Facilities, Other)
- Services: Scheduled maintenance and service plans
- Reminders: Service reminder notifications
- Reports: Service completion reports

Multi-page navigation with cross-page filters and state management.
Data is stored in CSV files for easy backup and sharing.
"""

import streamlit as st
from utils.state_manager import StateManager

# Set page config
st.set_page_config(
    page_title="Service Manager",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
StateManager.init_session_state()

# Add custom styling
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Fault Reports Highlight ---
st.markdown("""
<div style='background-color:#f9f6e7;padding:1em;border-radius:8px;margin-bottom:1em;'>
<b>New:</b> <span style='color:#d35400;'>Fault Reports</span> page now supports multiple photos per report, instant updates, and improved photo viewing!<br>
Easily document faults with images and view all reports in real time.
</div>
""", unsafe_allow_html=True)

# Sidebar information
with st.sidebar:
    st.title("📋 Service Manager")
    st.markdown("---")
    st.markdown("""
    ### Features
    - **Equipment Management**: Add and manage equipment
    - **Service Planning**: Schedule maintenance and services
    - **Service Reminders**: Track upcoming services
    - **Service Reports**: Document completed services
    - **Fault Reports**: Log faults with photos and details
    - **Cross-Page Filters**: Seamless data viewing
    - **CSV Storage**: Easy data backup and export
    """)
    
    st.markdown("---")
    st.markdown("""
    ### Navigation
    Use the sidebar menu to navigate between pages.
    
    - **Dashboard**: Overview and alerts
    - **Equipment**: Manage equipment objects
    - **Service Planning**: Schedule and manage services
    - **Service Reminders**: Track service reminders
    - **Service Reports**: View and add reports
    - **Fault Reports**: View and add fault reports
    """)
    
    st.markdown("---")
    st.markdown("""
    ### Data Location
    All data is stored in CSV files in the `data/` folder:
    - `objects.csv`: All equipment objects
    - `services.csv`: Scheduled services
    - `reminders.csv`: Service reminders
    - `reports.csv`: Service reports
    """)

# Main content
st.title("🎯 Welcome to Service Manager")

st.markdown("""
## Get Started

This application helps you manage services, maintenance, and equipment tracking across 
your organization. Here's how to use it:

### 1️⃣ Add Equipment First
Navigate to the **Equipment** page to add equipment you want to manage.

### 2️⃣ Plan Services
Go to **Service Planning** to schedule regular maintenance services for your objects.

### 3️⃣ Set Reminders
Create **Service Reminders** to get notifications for upcoming services.


### 4️⃣ Track Reports & Faults
Use **Service Reports** to document completed services and maintenance activities.
Use **Fault Reports** to log faults, upload multiple photos, and track issues for any equipment.


### 5️⃣ Monitor Dashboard
The **Dashboard** provides an overview of all objects, services, faults, and alerts.

---

## Features

✅ **Equipment Management** - Manage all your equipment (Vehicles, Facilities, Other)  
✅ **Service Planning** - Schedule maintenance with custom intervals  
✅ **Reminder System** - Track upcoming and overdue services  
✅ **Reporting** - Document all service activities  
✅ **Fault Reporting** - Log faults with multiple photos and instant updates  
✅ **Photo Management** - Attach and view images for faults and reports  
✅ **Cross-Page Filters** - Seamless navigation and filtering  
✅ **CSV Data Storage** - Portable, easy-to-backup data format  
✅ **Status Tracking** - Monitor service status (Active, Inactive, Maintenance)  
✅ **Data Export** - Download data from dashboard  

---

## Quick Links

- [View Dashboard](Dashboard) - See overview and alerts
- [Manage Equipment](Equipment) - Add and edit equipment
- [Plan Services](Service%20Planning) - Schedule maintenance
- [Track Reminders](Service%20Reminders) - View upcoming services
- [View Reports](Service%20Reports) - See service history
- [View Fault Reports](Fault%20Reports) - Log and review faults with photos

---

Start by navigating to the Dashboard or adding your first object!
""")

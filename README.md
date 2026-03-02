# MyMaintLog

A Streamlit-based application for managing vehicle services, fault reports, maintenance, and tracking.

## Features

✅ **Vehicle Management**
- Manage Vehicles
- Per-vehicle management and history

✅ **Service Planning**
- Schedule maintenance services with custom intervals
- Track service dates and status
- Plan upcoming maintenance

✅ **Service Reminders**
- Track upcoming service reminders
- Receive alerts for overdue services
- Status tracking (Pending, Completed)

✅ **Service Reporting**
- Document completed services
- Multiple report types (Maintenance, Inspection, Repair, Preventive)
- Comprehensive notes and descriptions

✅ **Cross-Page Filtering**
- Filter by object type across all pages
- Status filters (Active, Inactive, Maintenance)
- Text-based search capabilities
- Seamless state management between pages

✅ **Dashboard & Analytics**
- Real-time overview of all objects and services
- Alert system for overdue services and reminders
- Statistics and metrics
- Quick action buttons

## Project Structure

```
mymaintlog/
├── Home.py                     # Main entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── pages/                      # Multi-page app pages
│   ├── 0_Dashboard.py         # Dashboard with analytics
│   ├── 1_Equipment.py        # Equipment management
│   ├── 4_Service_Planning.py  # Service scheduling
│   ├── 5_Service_Reminders.py # Reminder management
│   └── 6_Service_Reports.py   # Report management
├── utils/                      # Utility modules
│   ├── data_handler.py        # SQLite data operations
│   └── state_manager.py       # Cross-page state management
└── data/                       # Runtime data storage
   ├── mymaintlog.db          # SQLite database
   ├── fault_photos/          # Uploaded fault photos (if file-based)
   └── *.bak-*                # Optional migration backups
```

## SQLite Storage Overview

The app stores operational data in `data/mymaintlog.db` (SQLite, WAL mode).

Main tables:
- `objects`: equipment/facilities/other tracked objects
- `services`: planned and scheduled services
- `reminders`: due-date reminders and notification flags
- `reports`: completed service reports
- `fault_reports`: fault observations and metadata
- `meter_units`: allowed unit values
- `fault_photos`: image blobs for fault reports

## Local Setup

### Prerequisites

- [Git](https://git-scm.com/)
- Python 3.8 or higher ([python.org](https://www.python.org/downloads/))

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/brunte71/mymaintlog.git
   cd mymaintlog
   ```

2. **Create and activate a virtual environment** *(recommended)*
   ```bash
   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows (Command Prompt)
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create the data directory** *(required on first run)*

   macOS / Linux:
   ```bash
   mkdir -p data
   ```
   Windows (Command Prompt):
   ```cmd
   mkdir data
   ```
   The SQLite database (`data/mymaintlog.db`) is created automatically when the app first starts.

5. **Run the application**
   ```bash
   streamlit run Home.py
   ```
   The app opens in your default browser at `http://localhost:8501`.

### Default Login Credentials

The `users.yaml` file ships with two example accounts you can use straight away:

| Email | Password | Role |
|---|---|---|
| `brunte71@example.com` | `admin123` | admin |
| `user1@example.com` | `user123` | user |

> ⚠️ **Security notice:** Change these passwords before exposing the app on any shared network
> or the internet. Replace the bcrypt hashes in `users.yaml` using the helper below.

> **Tip:** Generate a bcrypt hash for a new password with:
> ```python
> import bcrypt
> print(bcrypt.hashpw(b"yourpassword", bcrypt.gensalt()).decode())
> ```

## Usage Guide

### Adding Objects

1. Navigate to the **Equipment** page
2. Fill in the required information
3. Click **"Add"** button

### Planning Services

1. Go to **Service Planning** page
2. Click **"Schedule Service"** tab
3. Select the object type and specific object
4. Enter service name, interval, and other details
5. Click **"Schedule Service"** button

### Creating Reminders

1. Navigate to **Service Reminders** page
2. Click **"Add Reminder"** tab
3. Select a service to create a reminder for
4. Set the reminder date and notes
5. Click **"Add Reminder"** button

### Adding Reports

1. Go to **Service Reports** page
2. Click **"Add Report"** tab
3. Select the object and report type
4. Enter report details
5. Click **"Add Report"** button

### Filtering and Viewing Data

- Use filters in the sidebar on each page to narrow down results
- Click on objects to view detailed information
- Use the Dashboard for an overall view of all data
- Apply status filters to see Active, Inactive, or Maintenance items

### Exporting Data

On the Dashboard page:
- Use the **"Export"** buttons to download CSV files
- Import these files into Excel, databases, or other tools

## Cross-Page Features

The application includes a state management system that enables:
- Persistent object selection across pages
- Filter preservation when navigating
- Quick navigation from object details to services and reminders
- Seamless user experience across the entire application

### Customization

### Adding New Object Types

Edit `utils/data_handler.py`:
```python
OBJECT_TYPES = ["Vehicle", "Facility", "Other"]
```

Then create a new page file: `pages/X_YourNewType.py`

### Modifying Service Intervals

Service intervals are customizable per service. Set any number of days when creating/editing a service.

### Report Types

Current report types are: Maintenance, Inspection, Repair, Preventive, Other

To add more types, modify the selectbox options in `pages/6_Service_Reports.py`

## Data Backup

Your data is stored in the SQLite database in the `data/` folder. To backup:

1. Copy the entire `data/` folder to a safe location
2. Or use the export buttons on the Dashboard
3. Or manually backup `data/mymaintlog.db`

## Troubleshooting

**Problem**: SQLite database file not created automatically
- **Solution**: Create the `data/` folder manually if it doesn't exist and verify write permissions

**Problem**: Data not persisting
- **Solution**: Ensure the `data/` folder has write permissions

**Problem**: Filters not working
- **Solution**: Make sure you have data in the system first

## Requirements

- Python 3.8 or higher
- Streamlit 1.28+
- Pandas 2.1+

## License

Free to use and modify for your organization.

## Support

For issues or questions:
1. Check the sidebar information for feature explanations
2. Review the records in `data/mymaintlog.db` for data integrity
3. Ensure all dependencies are installed with `pip install -r requirements.txt`

---

**Happy Service Management! 📋**

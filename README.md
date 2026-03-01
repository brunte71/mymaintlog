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
├── app.py                      # Main entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── pages/                      # Multi-page app pages
│   ├── 0_Dashboard.py         # Dashboard with analytics
│   ├── 1_Equipment.py        # Equipment management
│   ├── 4_Service_Planning.py  # Service scheduling
│   ├── 5_Service_Reminders.py # Reminder management
│   └── 6_Service_Reports.py   # Report management
├── utils/                      # Utility modules
│   ├── data_handler.py        # CSV data operations
│   └── state_manager.py       # Cross-page state management
└── data/                       # CSV data storage
   ├── objects.csv            # Equipment objects
    ├── services.csv           # Scheduled services
    ├── reminders.csv          # Service reminders
    └── reports.csv            # Service reports
```

## CSV File Structure

### objects.csv
- `object_id`: Unique identifier (e.g., VEH-0001, FAC-0001, EQU-0001)
- `object_type`: Type of object (Vehicle, Facility, Other)
- `name`: Name of the object
- `description`: Object description
- `status`: Status (Active, Inactive, Maintenance)
- `created_date`: Creation timestamp
- `last_updated`: Last update timestamp

### services.csv
- `service_id`: Unique service identifier (SVC-00001)
- `object_id`: Associated object ID
- `object_type`: Type of object
- `service_name`: Service name
- `description`: Service description
- `interval_days`: Service interval in days
- `last_service_date`: Date of last service
- `next_service_date`: Next scheduled service date
- `status`: Status (Scheduled, Pending, In Progress, Completed)
- `notes`: Service notes
- `created_date`: Creation timestamp

### reminders.csv
- `reminder_id`: Unique reminder ID (REM-00001)
- `service_id`: Associated service ID
- `object_id`: Associated object ID
- `object_type`: Type of object
- `reminder_date`: Reminder date
- `status`: Status (Pending, Completed)
- `notes`: Reminder notes
- `created_date`: Creation timestamp

### reports.csv
- `report_id`: Unique report ID (REP-00001)
- `object_id`: Associated object ID
- `object_type`: Type of object
- `report_type`: Type of report (Maintenance, Inspection, Repair, Preventive, Other)
- `title`: Report title
- `description`: Report description
- `completion_date`: Date of completion
- `notes`: Report notes
- `created_date`: Creation timestamp

## Installation

1. **Clone or download the project**

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

The app will open in your default browser at `http://localhost:8501`

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

Your data is stored in CSV files in the `data/` folder. To backup:

1. Copy the entire `data/` folder to a safe location
2. Or use the export buttons on the Dashboard
3. Or manually backup the CSV files

## Troubleshooting

**Problem**: CSV files not created automatically
- **Solution**: Create the `data/` folder manually if it doesn't exist

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
2. Review the CSV files in the `data/` folder for data integrity
3. Ensure all dependencies are installed with `pip install -r requirements.txt`

---

**Happy Service Management! 📋**

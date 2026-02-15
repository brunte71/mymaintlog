# Email Notifications for Service Reminders

This feature allows users to receive email notifications for their service reminders on the specified date and time.

## Setup Instructions

### 1. Configure Email Settings

Edit the `email_config.yaml` file in the root directory:

```yaml
smtp:
  enabled: true  # Set to true to enable email notifications
  server: smtp.gmail.com  # Your SMTP server
  port: 587  # SMTP port (587 for TLS, 465 for SSL)
  use_tls: true  # Use TLS encryption
  username: "your-email@gmail.com"  # Your email address
  password: "your-app-password"  # Your email password or app-specific password
  from_email: "your-email@gmail.com"  # Email address to send from
  from_name: "ServiceMgr"  # Display name for the sender
```

### 2. Gmail Setup (If using Gmail)

If you're using Gmail, you need to create an **App Password**:

1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. Scroll down to "App passwords"
4. Generate a new app password for "Mail"
5. Use this app password in the `email_config.yaml` file

**Note:** Regular Gmail passwords won't work with SMTP. You must use an app-specific password.

### 3. Other Email Providers

For other email providers, update the SMTP settings accordingly:

- **Outlook/Office365:**
  - Server: `smtp-mail.outlook.com` or `smtp.office365.com`
  - Port: `587`
  - TLS: `true`

- **Yahoo:**
  - Server: `smtp.mail.yahoo.com`
  - Port: `587` or `465`
  - TLS: `true`

- **Custom SMTP:**
  - Contact your email provider for SMTP settings

## Using Email Notifications

### Adding a Reminder with Email Notification

1. Go to **Service Reminders** page
2. Click the **Add Reminder** tab
3. Fill in the reminder details
4. Check the "**Send email reminder**" checkbox
5. Set the **Notification time** (default is 9:00 AM)
6. Click **Add Reminder**

### Email Notification Behavior

- Emails are sent when the  page loads and checks for pending notifications
- Notifications are sent on or after the reminder date
- Each reminder email is only sent once (tracked by `email_sent` flag)
- If email configuration is disabled, reminders will still work but no emails will be sent

### Editing Email Settings for Existing Reminders

1. Go to **Service Reminders** page
2. Click the **Edit Reminder** tab
3. Select the reminder you want to modify
4. Update the email notification checkbox and time as needed
5. Click **Update Reminder**

## Email Template

The email template can be customized in `email_config.yaml`:

```yaml
template:
  subject: "Service Reminder: {object_name}"
  body: |
    Hello {user_name},
    
    This is a reminder for the following service:
    
    Object: {object_name} ({object_type})
    Service: {service_name}
    Reminder Date: {reminder_date}
    
    Notes: {notes}
    
    Please log in to ServiceMgr to view more details and complete the service.
    
    Best regards,
    ServiceMgr
```

Available template variables:
- `{user_name}` - Name of the user
- `{object_name}` - Equipment ID
- `{object_type}` - Type of object (Vehicle, Facility, etc.)
- `{service_name}` - Service ID
- `{reminder_date}` - Date of the reminder
- `{notes}` - Notes from the reminder

## Troubleshooting

### Emails not being sent

1. Check that `enabled: true` in `email_config.yaml`
2. Verify SMTP credentials are correct
3. For Gmail, make sure you're using an app password, not your regular password
4. Check the terminal/logs for error messages
5. Ensure your firewall allows outbound connections on the SMTP port

### Testing Email Configuration

You can test your email setup by:
1. Creating a test reminder with today's date
2. Enabling email notification
3. Reloading the Service Reminders page
4. Check if the email was sent (you should see a success message in the sidebar)

## Security Notes

- Never commit `email_config.yaml` with real credentials to version control
- Use app-specific passwords instead of your main email password
- Consider using environment variables for sensitive credentials in production
- The email password is stored in plain text in the config file - ensure file permissions are restricted

## Disabling Email Notifications

To disable email notifications:

1. Set `enabled: false` in `email_config.yaml`
2. Existing reminders will keep their email settings but no emails will be sent
3. The email notification options will still appear in the UI with an info message

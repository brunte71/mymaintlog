"""
Email utility for sending service reminder notifications
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yaml
from datetime import datetime, date
import os

class EmailNotifier:
    def __init__(self):
        self.config_file = "email_config.yaml"
        self.config = self._load_config()
    
    def _load_config(self):
        """Load email configuration from YAML file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f)
            return None
        except Exception as e:
            print(f"Error loading email config: {e}")
            return None
    
    def is_enabled(self):
        """Check if email notifications are enabled"""
        if not self.config:
            return False
        return self.config.get('smtp', {}).get('enabled', False)
    
    def send_reminder_email(self, to_email, user_name, reminder_data):
        """
        Send a reminder email
        
        Args:
            to_email: Recipient email address
            user_name: Name of the user
            reminder_data: Dict with reminder details (object_name, object_type, service_name, etc.)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.is_enabled():
            print("Email notifications are disabled")
            return False
        
        try:
            smtp_config = self.config['smtp']
            template = self.config['template']
            
            # Format email subject and body
            subject = template['subject'].format(**reminder_data)
            body = template['body'].format(
                user_name=user_name,
                **reminder_data
            )
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{smtp_config.get('from_name', 'ServiceMgr')} <{smtp_config['from_email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                if smtp_config.get('use_tls', True):
                    server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
            
            print(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def check_and_send_pending_reminders(self, reminders_df, users_config, data_handler=None):
        """
        Check for reminders that need email notifications and send them
        
        Args:
            reminders_df: DataFrame of reminders
            users_config: User configuration to get user names
            data_handler: DataHandler instance to update email_sent status
        
        Returns:
            int: Number of emails sent
        """
        if not self.is_enabled() or reminders_df.empty:
            return 0
        
        import pandas as pd
        from datetime import date
        
        emails_sent = 0
        today = date.today()
        
        for _, reminder in reminders_df.iterrows():
            # Check if email notification is enabled for this reminder
            if not reminder.get('email_notification', False):
                continue
            
            # Check if reminder is pending
            if reminder.get('status', '') != 'Pending':
                continue
            
            # Check if email was already sent
            if reminder.get('email_sent', False):
                continue
            
            # Parse reminder date and time
            try:
                reminder_date = pd.to_datetime(reminder['reminder_date']).date()
                notification_time = reminder.get('notification_time', '09:00')
                
                # Check if today is the reminder date or after
                if today >= reminder_date:
                    # Get user details
                    user_email = reminder.get('user_email', '')
                    users_dict = users_config.get('credentials', {}).get('usernames', {})
                    user_data = users_dict.get(user_email, {})
                    user_name = user_data.get('name', 'User')
                    
                    # Prepare reminder data for email
                    reminder_data = {
                        'object_name': reminder.get('object_id', 'N/A'),
                        'object_type': reminder.get('object_type', 'N/A'),
                        'service_name': reminder.get('service_id', 'N/A'),
                        'reminder_date': reminder.get('reminder_date', 'N/A'),
                        'notes': reminder.get('notes', 'No additional notes')
                    }
                    
                    # Send email
                    if self.send_reminder_email(user_email, user_name, reminder_data):
                        emails_sent += 1
                        # Mark as sent in CSV
                        if data_handler:
                            try:
                                data_handler.update_reminder(
                                    reminder.get('reminder_id'), 
                                    email_sent=True
                                )
                            except Exception as e:
                                print(f"Error updating email_sent status: {e}")
            
            except Exception as e:
                print(f"Error processing reminder {reminder.get('reminder_id', 'unknown')}: {e}")
                continue
        
        return emails_sent

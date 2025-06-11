from flask import current_app
from app.models import SystemSettings
from app.extensions import mail
from flask_mail import Message
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import smtplib
from functools import lru_cache
import time

# Add a base NotificationError class
class NotificationError(Exception):
    pass

class SlackNotificationError(NotificationError):
    pass

class EmailNotificationError(NotificationError):
    pass

def send_slack_notification(email, guest):
    # Get token from database
    slack_token = SystemSettings.get_setting('slack_api_key')
    current_app.logger.info(f"Attempting Slack notification to {email} for guest {guest.name}")
    
    if not slack_token:
        current_app.logger.error("Slack API token not found in settings")
        return False
    
    current_app.logger.info("Found Slack token, initializing client")
    client = WebClient(token=slack_token)
    
    try:
        # First, look up the user by email
        current_app.logger.info(f"Looking up Slack user by email: {email}")
        try:
            user_response = client.users_lookupByEmail(email=email)
            current_app.logger.info(f"User lookup response: {user_response}")
        except SlackApiError as e:
            if e.response['error'] == 'users_not_found':
                current_app.logger.error(f"No Slack user found with email: {email}")
                return False
            raise  # Re-raise other Slack API errors
            
        if not user_response.get('ok'):
            current_app.logger.error(f"Error finding Slack user by email: {email}")
            current_app.logger.error(f"Slack response: {user_response}")
            return False
        
        slack_id = user_response['user']['id']
        current_app.logger.info(f"Found Slack user ID: {slack_id}")
        
        # Then send the message
        message = (
            f"👋 Hello! Your guest has arrived!\n\n"
            f"*Guest Details:*\n"
            f"• Name: {guest.name}\n"
            f"• Company: {guest.company or 'Not provided'}"
        )
        
        current_app.logger.info(f"Sending message to {slack_id}: {message}")
        
        try:
            response = client.chat_postMessage(
                channel=slack_id,
                text=message,
                parse='full'  # Enable parsing of markup
            )
            current_app.logger.info(f"Message send response: {response}")
            
            if not response.get('ok'):
                current_app.logger.error(f"Error sending message: {response.get('error')}")
                return False
                
            current_app.logger.info("Message sent successfully")
            return True
            
        except SlackApiError as e:
            if e.response['error'] == 'not_in_channel':
                # Try to open a DM channel first
                try:
                    open_response = client.conversations_open(users=[slack_id])
                    if open_response['ok']:
                        channel_id = open_response['channel']['id']
                        # Try sending the message again
                        response = client.chat_postMessage(
                            channel=channel_id,
                            text=message,
                            parse='full'
                        )
                        return response['ok']
                except SlackApiError as e2:
                    current_app.logger.error(f"Error opening DM channel: {e2.response['error']}")
                    return False
            else:
                current_app.logger.error(f"Error sending message: {e.response['error']}")
                return False
            
    except SlackApiError as e:
        current_app.logger.error(f"Slack API Error: {str(e)}")
        current_app.logger.error(f"Error details: {e.response['error']}")
        return False
    except Exception as e:
        current_app.logger.error(f"Unexpected error in send_slack_notification: {str(e)}")
        return False

def send_email_notification(email, guest):
    try:
        # Get SMTP settings from database
        smtp_settings = {
            'server': SystemSettings.get_setting('smtp_server'),
            'port': int(SystemSettings.get_setting('smtp_port')),
            'username': SystemSettings.get_setting('smtp_username'),
            'password': SystemSettings.get_setting('smtp_password'),
            'use_tls': SystemSettings.get_setting('smtp_use_tls', 'true').lower() == 'true',
            'use_ssl': SystemSettings.get_setting('smtp_use_ssl', 'false').lower() == 'true',
            'sender': SystemSettings.get_setting('smtp_sender', 'NRSC Lobby <noreply@nrsc.org>')
        }

        current_app.logger.info(f"Sending notification email to {email} for guest {guest.name}")

        # Create SMTP connection
        if smtp_settings['use_ssl']:
            smtp = smtplib.SMTP_SSL(smtp_settings['server'], smtp_settings['port'], timeout=10)
        else:
            smtp = smtplib.SMTP(smtp_settings['server'], smtp_settings['port'], timeout=10)
            if smtp_settings['use_tls']:
                smtp.starttls()

        smtp.ehlo()

        # Login if credentials provided
        if smtp_settings['username'] and smtp_settings['password']:
            smtp.login(smtp_settings['username'], smtp_settings['password'])

        # Create message
        msg = f"""From: {smtp_settings['sender']}
To: {email}
Subject: Guest Arrival: {guest.name}
Content-Type: text/html

<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #2c3e50;">Guest Arrival Notification</h2>
    <p>Hello,</p>
    <p>Your guest has arrived at the NRSC:</p>
    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p style="margin: 5px 0;"><strong>Name:</strong> {guest.name}</p>
        <p style="margin: 5px 0;"><strong>Company:</strong> {guest.company or 'Not provided'}</p>
        <p style="margin: 5px 0;"><strong>Additional Guests:</strong> {
            ', '.join(json.loads(guest.additional_guests)) if guest.additional_guests else 'None'
        }</p>
    </div>
    <p>Please proceed to the reception area.</p>
    <p style="color: #666; font-size: 0.9em; margin-top: 20px;">
        This is an automated message from the NRSC Guest Management System.
    </p>
</div>
"""
        # Send email
        smtp.sendmail(smtp_settings['sender'], [email], msg)
        smtp.quit()

        current_app.logger.info(f"Email notification sent to {email}")
        return True

    except smtplib.SMTPAuthenticationError:
        current_app.logger.error("SMTP authentication failed")
        return False
    except smtplib.SMTPException as e:
        current_app.logger.error(f"SMTP error: {str(e)}")
        return False
    except Exception as e:
        current_app.logger.error(f"Error sending email notification: {str(e)}")
        return False 

def get_email_template(template_name):
    return SystemSettings.get_setting(f'email_template_{template_name}')

def get_slack_template(template_name):
    return SystemSettings.get_setting(f'slack_template_{template_name}')

# Consider adding async versions of notification functions
async def send_slack_notification_async(email, guest):
    # Async implementation
    pass

async def send_email_notification_async(email, guest):
    # Async implementation
    pass 

@lru_cache(maxsize=100)
def get_rate_limit(notification_type, recipient):
    return SystemSettings.get_setting(f'{notification_type}_rate_limit')

def check_rate_limit(notification_type, recipient):
    # Implement rate limiting logic
    pass 

# Add a test mode flag
def send_notification(email, guest, test_mode=False):
    if test_mode:
        return simulate_notification(email, guest)
    # Regular notification logic 
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, Response, current_app, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Guest, Admin, TeamMember, SystemSettings, SessionLog
from app.forms import GuestRegistrationForm, LoginForm
from app import db
import csv
from io import StringIO, BytesIO
from datetime import datetime, timedelta
import json
import pytz
from functools import wraps
from app.utils.notifications import send_slack_notification, send_email_notification
from app.utils.name_matching import find_matching_team_members
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask_mail import Message
from app.extensions import mail
import socket
import ssl
import smtplib
import os
from flask_wtf.csrf import generate_csrf


main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
ac = Blueprint('ac', __name__, url_prefix='/ac')


# Import functions from traneweb.py                                                                                                        
from traneweb import (                                                                                                                     
    get_individual_data,                                                                                                                   
    get_point_value,                                                                                                                       
    set_hvac_parameter,                                                                                                                    
    authenticate                                                                                                                           
)   


eastern = pytz.timezone('US/Eastern')

def get_eastern_time():
    # Return timezone-aware datetime in Eastern time
    return datetime.now(eastern)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Admin):
            flash('You must be an admin to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@main.route('/', methods=['GET', 'POST'])
def register():
    # Initialize session start time if not present
    if 'session_start' not in session:
        session['session_start'] = datetime.now(pytz.UTC)  # Store as UTC
        session.permanent = True  # Make session permanent
    
    form = GuestRegistrationForm(request.form)
    
    # Generate a session ID if one doesn't exist
    if 'session_id' not in session:
        session['session_id'] = os.urandom(16).hex()
        session.permanent = True  # Make session permanent
        # Log new session
        new_session = SessionLog(
            session_id=session['session_id'],
            user_agent=request.user_agent.string,
            ip_address=request.remote_addr
        )
        db.session.add(new_session)
        db.session.commit()
    
    # Update last seen time
    session_log = SessionLog.query.filter_by(session_id=session['session_id']).first()
    if session_log:
        session_log.last_seen = datetime.now(pytz.UTC)
        if request.method == 'POST':
            session_log.submission_attempts += 1
            if not form.validate():
                session_log.errors = str(form.errors)
        db.session.commit()

    # Always refresh the session
    session['session_start'] = datetime.now(pytz.UTC)
    session.permanent = True

    if request.method == 'POST' and form.validate():
        try:
            # Store timestamp in UTC but capture it now
            eastern_time = get_eastern_time()
            utc_time = eastern_time.astimezone(pytz.UTC)
            
            additional_guests = []
            if form.additional_guests.data:
                additional_guests = [
                    name.strip() 
                    for name in form.additional_guests.data.split('\n') 
                    if name.strip()
                ]

            guest = Guest(
                name=form.name.data,
                company=form.company.data,
                host=form.host.data,
                additional_guests=json.dumps(additional_guests) if additional_guests else None,
                timestamp=utc_time  # Explicitly set UTC timestamp
            )
            db.session.add(guest)
            db.session.commit()

            # Update session log on successful submission
            if session_log:
                session_log.form_interactions += 1
                db.session.commit()

            return '', 204
        except Exception as e:
            if session_log:
                session_log.errors = str(e)
                db.session.commit()
            current_app.logger.error(f"Form submission error: {str(e)}")
            return 'Error submitting form', 500

    return render_template('register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.admin'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Admin.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.admin'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.register'))

def count_total_guests(guests):
    total = len(guests)  # Primary guests
    for guest in guests:
        if guest.additional_guests:
            try:
                # Parse JSON array of additional guests
                additional = len(json.loads(guest.additional_guests))
                total += additional
            except (json.JSONDecodeError, TypeError):
                # Handle any existing records with old format
                pass
    return total

@main.route('/admin')
@login_required
def admin():
    # Get the current date in Eastern time
    eastern_now = get_eastern_time()
    eastern_today = eastern_now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Query using timezone-aware datetime range
    guests = Guest.query.filter(
        Guest.timestamp >= eastern_today,
        Guest.timestamp < eastern_today + timedelta(days=1)
    ).order_by(Guest.timestamp.desc()).all()
    
    # Get all team members and create a preferences dictionary
    team_members = TeamMember.query.all()
    host_preferences = {}
    
    # First, create the full preferences dictionary
    for member in team_members:
        host_preferences[member.name] = {
            'preferences': [],
            'email': member.email,
            'full_name': member.name  # Store the full name
        }
        if member.email_notifications:
            host_preferences[member.name]['preferences'].append('email')
        if member.slack_notifications:
            host_preferences[member.name]['preferences'].append('slack')
    
    # For each guest, find the best matching team member
    guest_host_matches = {}
    for guest in guests:
        matches = find_matching_team_members(guest.host)
        if matches:
            best_match = matches[0][0]  # Get the best matching team member
            guest_host_matches[guest.host] = host_preferences[best_match.name]
    
    # Combine both dictionaries
    combined_preferences = {**host_preferences, **guest_host_matches}
    
    # Debug logging
    current_app.logger.info("Host Preferences:")
    for name, prefs in combined_preferences.items():
        current_app.logger.info(f"  {name}: {prefs}")
    
    current_app.logger.info("Guests:")
    for guest in guests:
        current_app.logger.info(f"  {guest.host}: {combined_preferences.get(guest.host)}")
    
    primary_count = len(guests)
    total_count = count_total_guests(guests)
    
    return render_template('admin.html', 
                         guests=guests, 
                         primary_count=primary_count,
                         total_count=total_count,
                         host_preferences=combined_preferences)

@main.route('/export')
@main.route('/export/<date>')
@login_required
def export(date=None):
    if date:
        try:
            export_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            export_date = get_eastern_time().date()
    else:
        export_date = get_eastern_time().date()

    guests = Guest.query.filter(
        db.func.date(Guest.timestamp) == export_date
    ).order_by(Guest.timestamp.desc()).all()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Name', 'Company', 'Host', 'Additional Guests', 'Time'])
    
    for guest in guests:
        # Parse additional guests from JSON
        try:
            additional_guests = json.loads(guest.additional_guests) if guest.additional_guests else []
            additional_guests_str = ', '.join(additional_guests)
        except (json.JSONDecodeError, TypeError):
            additional_guests_str = ''

        # Convert timestamp to Eastern time
        eastern_time = pytz.UTC.localize(guest.timestamp).astimezone(eastern)
        
        cw.writerow([
            guest.name,
            guest.company,
            guest.host,
            additional_guests_str,
            eastern_time.strftime('%I:%M %p')
        ])
    
    output = si.getvalue()
    si.close()

    # Convert to BytesIO
    bio = BytesIO()
    bio.write(output.encode('utf-8-sig'))  # Use UTF-8 with BOM for Excel compatibility
    bio.seek(0)
    
    return send_file(
        bio,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'guests_{export_date.strftime("%Y-%m-%d")}.csv'
    )

@main.route('/delete/<int:id>')
@login_required
def delete(id):
    guest = Guest.query.get_or_404(id)
    db.session.delete(guest)
    db.session.commit()
    flash('Record deleted successfully!')
    return redirect(url_for('main.admin'))

@main.route('/check-new-guests/<int:last_id>')
@login_required
def check_new_guests(last_id):
    # Get the current date in Eastern time
    eastern_now = get_eastern_time()
    eastern_today = eastern_now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Query using timezone-aware datetime range for today's guests
    new_guests = Guest.query.filter(
        Guest.id > last_id,
        Guest.timestamp >= eastern_today,
        Guest.timestamp < eastern_today + timedelta(days=1)
    ).order_by(Guest.id.asc()).all()
    
    # Get all today's guests for total count
    all_guests = Guest.query.filter(
        Guest.timestamp >= eastern_today,
        Guest.timestamp < eastern_today + timedelta(days=1)
    ).all()
    
    total_count = count_total_guests(all_guests)
    
    # Get team member preferences
    team_members = TeamMember.query.all()
    host_preferences = {}
    
    # Create full preferences dictionary
    for member in team_members:
        host_preferences[member.name] = {
            'preferences': [],
            'email': member.email,
            'full_name': member.name
        }
        if member.email_notifications:
            host_preferences[member.name]['preferences'].append('email')
        if member.slack_notifications:
            host_preferences[member.name]['preferences'].append('slack')
    
    # For each new guest, find the best matching team member
    guest_host_matches = {}
    for guest in new_guests:
        matches = find_matching_team_members(guest.host)
        if matches:
            best_match = matches[0][0]
            guest_host_matches[guest.host] = host_preferences[best_match.name]
    
    # Combine both dictionaries
    combined_preferences = {**host_preferences, **guest_host_matches}
    
    guests_data = []
    for guest in new_guests:
        try:
            additional_guests = json.loads(guest.additional_guests) if guest.additional_guests else []
        except (json.JSONDecodeError, TypeError):
            additional_guests = []
            
        eastern_timestamp = guest.timestamp.astimezone(eastern)
        
        guests_data.append({
            'id': guest.id,
            'name': guest.name,
            'company': guest.company,
            'host': guest.host,
            'additional_guests': additional_guests,
            'timestamp': eastern_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({
        'guests': guests_data,
        'total_count': total_count,
        'host_preferences': combined_preferences
    })

@main.route('/archive')
@main.route('/archive/<date>')
@login_required
def archive(date=None):
    if date:
        try:
            selected_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = get_eastern_time().date()
    else:
        selected_date = get_eastern_time().date()

    guests = Guest.query.filter(
        db.func.date(Guest.timestamp) == selected_date
    ).order_by(Guest.timestamp.desc()).all()
    
    primary_count = len(guests)
    total_count = count_total_guests(guests)

    return render_template('archive.html', 
                         guests=guests, 
                         selected_date=selected_date,
                         datetime=get_eastern_time,
                         primary_count=primary_count,
                         total_count=total_count)

@main.route('/archive/delete-day/<date>')
@login_required
def delete_day(date):
    try:
        delete_date = datetime.strptime(date, '%Y-%m-%d').date()
        Guest.query.filter(
            db.func.date(Guest.timestamp) == delete_date
        ).delete()
        db.session.commit()
        flash(f'All records for {delete_date.strftime("%B %d, %Y")} have been deleted.')
    except Exception as e:
        flash('Error deleting records.', 'error')
    
    return redirect(url_for('main.archive', date=date))

@main.route('/users')
@login_required
def users():
    users = Admin.query.all()
    return render_template('users.html', users=users)

@main.route('/users/add', methods=['POST'])
@login_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Username and password are required.', 'error')
        return redirect(url_for('main.users'))
        
    if Admin.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('main.users'))
    
    user = Admin(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash('User added successfully.')
    return redirect(url_for('main.users'))

@main.route('/users/update/<int:id>', methods=['POST'])
@login_required
def update_user(id):
    user = Admin.query.get_or_404(id)
    password = request.form.get('password')
    
    if not password:
        flash('Password is required.', 'error')
        return redirect(url_for('main.users'))
    
    user.set_password(password)
    db.session.commit()
    
    flash('Password updated successfully.')
    return redirect(url_for('main.users'))

@main.route('/users/delete/<int:id>')
@login_required
def delete_user(id):
    if Admin.query.count() <= 1:
        flash('Cannot delete the last admin user.', 'error')
        return redirect(url_for('main.users'))
        
    user = Admin.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('Cannot delete your own account.', 'error')
        return redirect(url_for('main.users'))
        
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully.')
    return redirect(url_for('main.users'))

@main.app_template_filter('from_json')
def from_json(value):
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

@main.app_template_filter('eastern_time')
def eastern_time(dt):
    """Convert UTC datetime to Eastern time"""
    if dt.tzinfo is None:  # If datetime is naive, assume it's UTC
        dt = pytz.UTC.localize(dt)
    eastern_dt = dt.astimezone(eastern)
    return eastern_dt.strftime('%I:%M %p')  # Format as "HH:MM AM/PM"

@main.app_template_filter('from_isoformat')
def from_isoformat(dt_str):
    """Convert ISO format string to datetime object"""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None

@main.route('/team-notifications')
@login_required
def team_notifications():
    members = TeamMember.query.all()
    return render_template('team_notifications.html', members=members)

@main.route('/api/team-members', methods=['POST'])
@login_required
def add_team_member():
    data = request.json
    member = TeamMember(
        name=data['name'],
        email=data['email'],
        slack_notifications=data.get('slack_notifications', False),
        email_notifications=data.get('email_notifications', False)
    )
    db.session.add(member)
    db.session.commit()
    return jsonify({'success': True})

@main.route('/api/team-members/<int:id>', methods=['DELETE'])
@login_required
def delete_team_member(id):
    member = TeamMember.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({'success': True})

@main.route('/api/team-members/<int:id>/notifications', methods=['PATCH'])
@login_required
def update_notifications(id):
    member = TeamMember.query.get_or_404(id)
    data = request.json
    
    if data['type'] == 'slack':
        member.slack_notifications = data['enabled']
    elif data['type'] == 'email':
        member.email_notifications = data['enabled']
        
    db.session.commit()
    return jsonify({'success': True})

@main.route('/api/team-members/import', methods=['POST'])
@login_required
def import_team_members():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'Please upload a CSV file'})
    
    default_slack = request.form.get('default_slack') == 'true'
    default_email = request.form.get('default_email') == 'true'
    
    try:
        # Read CSV file
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_data = csv.DictReader(stream)
        
        # Validate headers
        required_fields = {'Name', 'Email'}
        headers = set(csv_data.fieldnames)
        if not required_fields.issubset(headers):
            return jsonify({
                'success': False, 
                'error': 'CSV must contain Name and Email columns'
            })
        
        # Process each row
        for row in csv_data:
            # Check if member already exists
            existing_member = TeamMember.query.filter_by(email=row['Email']).first()
            if not existing_member:
                member = TeamMember(
                    name=row['Name'],
                    email=row['Email'],
                    slack_notifications=default_slack,
                    email_notifications=default_email
                )
                db.session.add(member)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Error processing CSV: {str(e)}'
        })

@main.route('/settings')
@login_required
@admin_required
def settings():
    # Fetch all settings
    settings_dict = {
        'slack_api_key': SystemSettings.get_setting('slack_api_key'),
        'slack_channel': SystemSettings.get_setting('slack_channel'),
        'smtp_server': SystemSettings.get_setting('smtp_server'),
        'smtp_port': SystemSettings.get_setting('smtp_port'),
        'smtp_username': SystemSettings.get_setting('smtp_username'),
        'smtp_password': SystemSettings.get_setting('smtp_password'),
        'smtp_sender': SystemSettings.get_setting('smtp_sender'),
        'smtp_use_tls': SystemSettings.get_setting('smtp_use_tls', 'true').lower() == 'true',
        'smtp_use_ssl': SystemSettings.get_setting('smtp_use_ssl', 'false').lower() == 'true'
    }
    return render_template('settings.html', active_page='settings', **settings_dict)

@main.route('/settings/slack', methods=['POST'])
@login_required
@admin_required
def update_slack_settings():
    SystemSettings.set_setting('slack_api_key', request.form.get('slack_api_key'))
    SystemSettings.set_setting('slack_channel', request.form.get('slack_channel'))
    flash('Slack settings updated successfully', 'success')
    return redirect(url_for('main.settings'))

@main.route('/update_email_settings', methods=['POST'])
@login_required
@admin_required
def update_email_settings():
    try:
        # Log the incoming form data for debugging
        current_app.logger.info(f"Updating email settings with data: {request.form}")
        
        # Update all SMTP settings
        settings_to_update = {
            'smtp_server': request.form.get('smtp_server'),
            'smtp_port': request.form.get('smtp_port'),
            'smtp_username': request.form.get('smtp_username'),
            'smtp_sender': request.form.get('smtp_sender'),
            'smtp_use_tls': 'true' if request.form.get('smtp_use_tls') else 'false',
            'smtp_use_ssl': 'true' if request.form.get('smtp_use_ssl') else 'false'
        }
        
        # Only update password if provided
        if request.form.get('smtp_password'):
            settings_to_update['smtp_password'] = request.form.get('smtp_password')

        # Update each setting
        for key, value in settings_to_update.items():
            current_app.logger.info(f"Setting {key} to {value}")
            SystemSettings.set_setting(key, value)
        
        flash('Email settings updated successfully', 'success')
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"Error updating email settings: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@main.route('/notify-host', methods=['POST'])
@login_required
def notify_host():
    data = request.get_json()
    method = data.get('method')
    guest_id = data.get('guest_id')
    host_name = data.get('host_name')
    selected_email = data.get('selected_email')
    
    current_app.logger.info(f"Notification request: method={method}, guest_id={guest_id}, host={host_name}, selected_email={selected_email}")
    
    guest = Guest.query.get_or_404(guest_id)
    current_app.logger.info(f"Found guest: {guest.name}")
    
    # If we have a selected email, use that directly
    if selected_email:
        team_member = TeamMember.query.filter_by(email=selected_email).first()
        current_app.logger.info(f"Using selected email, found team member: {team_member.name if team_member else 'None'}")
        if not team_member:
            return jsonify({'success': False, 'message': 'Selected team member not found'})
    else:
        # Find matching team members
        matches = find_matching_team_members(host_name)
        
        # Log matching results for debugging
        current_app.logger.info(f"Matching results for '{host_name}':")
        for member, score in matches:
            current_app.logger.info(f"  - {member.name}: {score}")
        
        if not matches:
            return jsonify({'success': False, 'message': 'No matching team members found'})
        
        # If multiple matches found, return them to the frontend
        if len(matches) > 1:
            current_app.logger.info("Multiple matches found, returning to frontend for selection")
            return jsonify({
                'success': False,
                'multiple_matches': True,
                'matches': [
                    {
                        'name': member.name,
                        'email': member.email,
                        'score': score
                    }
                    for member, score in matches
                ]
            })
        
        team_member = matches[0][0]
    
    try:
        success = False
        if method == 'slack':
            success = send_slack_notification(team_member.email, guest)
        else:
            success = send_email_notification(team_member.email, guest)
            
        if success:
            guest.add_notification(method)
            db.session.commit()
            
            # Get the latest notification for the response
            notifications = guest.get_notifications()
            latest = notifications[-1] if notifications else None
            
            if latest:
                # Convert ISO format time string to datetime
                notification_time = datetime.fromisoformat(latest['time'])
                eastern_time = notification_time.astimezone(eastern)
                formatted_time = eastern_time.strftime('%I:%M %p')
            else:
                formatted_time = None
            
            return jsonify({
                'success': True,
                'notification_time': formatted_time,
                'notification_type': method,
                'all_notifications': notifications
            })
            
    except Exception as e:
        current_app.logger.error(f"Error sending notification: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Error sending notification: {str(e)}'
        })

@main.route('/test-slack')
@login_required
@admin_required
def test_slack():
    slack_token = SystemSettings.get_setting('slack_api_key')
    if not slack_token:
        return jsonify({
            'success': False,
            'message': 'No Slack token found in settings'
        })
    
    try:
        client = WebClient(token=slack_token)
        response = client.auth_test()
        
        if response['ok']:
            return jsonify({
                'success': True,
                'message': f"Connected as {response['user']} to workspace {response['team']}",
                'details': {
                    'user': response['user'],
                    'team': response['team'],
                    'url': response['url'],
                    'bot_id': response.get('bot_id')
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Slack connection test failed',
                'details': {
                    'error': response.get('error', 'Unknown error')
                }
            })
            
    except SlackApiError as e:
        error_details = e.response['error'] if isinstance(e.response['error'], str) else str(e.response['error'])
        return jsonify({
            'success': False,
            'message': f"Slack API Error: {str(e)}",
            'error_details': error_details
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Unexpected error: {str(e)}"
        })

def test_smtp_connection(host, port, use_tls=False, use_ssl=False):
    try:
        current_app.logger.info(f"Attempting to connect to {host}:{port} (TLS: {use_tls}, SSL: {use_ssl})")
        
        if use_ssl:
            smtp = smtplib.SMTP_SSL(host, int(port), timeout=10)
            current_app.logger.info("SSL connection successful")
        else:
            smtp = smtplib.SMTP(host, int(port), timeout=10)
            current_app.logger.info("Basic connection successful")
            if use_tls:
                smtp.starttls()
                current_app.logger.info("STARTTLS successful")
            
        # Try to say HELLO
        smtp.ehlo()
        current_app.logger.info("EHLO successful")
        
        # Try to authenticate
        username = SystemSettings.get_setting('smtp_username')
        password = SystemSettings.get_setting('smtp_password')
        if username and password:
            current_app.logger.info(f"Attempting authentication as {username}")
            smtp.login(username, password)
            current_app.logger.info("Authentication successful")
        
        smtp.quit()
        return True, "Connection successful"
        
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Please check your username and password."
    except smtplib.SMTPConnectError as e:
        return False, f"Connection failed: {str(e)}"
    except smtplib.SMTPServerDisconnected as e:
        return False, "Server disconnected unexpectedly"
    except ssl.SSLError as e:
        return False, f"SSL/TLS error: {str(e)}"
    except socket.timeout:
        return False, "Connection timed out"
    except socket.gaierror:
        return False, "DNS lookup failed"
    except ConnectionRefusedError:
        return False, "Connection refused"
    except Exception as e:
        current_app.logger.error(f"Unexpected error testing SMTP: {str(e)}")
        return False, str(e)

@main.route('/test-email', methods=['POST'])
@login_required
@admin_required
def test_email():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({
            'success': False,
            'message': 'Email address is required'
        })
    
    try:
        smtp_settings = {
            'server': SystemSettings.get_setting('smtp_server'),
            'port': SystemSettings.get_setting('smtp_port'),
            'username': SystemSettings.get_setting('smtp_username'),
            'use_tls': SystemSettings.get_setting('smtp_use_tls', 'true').lower() == 'true',
            'use_ssl': SystemSettings.get_setting('smtp_use_ssl', 'false').lower() == 'true',
            'sender': SystemSettings.get_setting('smtp_sender', 'NRSC Lobby <noreply@nrsc.org>')
        }
        
        current_app.logger.info(f"Testing connection to SMTP server...")
        success, message = test_smtp_connection(
            smtp_settings['server'], 
            smtp_settings['port'],
            smtp_settings['use_tls'],
            smtp_settings['use_ssl']
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': f"Connection test failed: {message}"
            })
            
        current_app.logger.info(f"Connection test successful, attempting to send email using settings: {smtp_settings}")
        
        # Update mail settings and reinitialize
        app = current_app._get_current_object()
        app.config.update(
            MAIL_SERVER=smtp_settings['server'],
            MAIL_PORT=int(smtp_settings['port']),
            MAIL_USE_TLS=smtp_settings['use_tls'],
            MAIL_USE_SSL=smtp_settings['use_ssl'],
            MAIL_USERNAME=smtp_settings['username'],
            MAIL_PASSWORD=SystemSettings.get_setting('smtp_password'),
            MAIL_DEFAULT_SENDER=smtp_settings['sender']
        )
        
        # Reinitialize mail with new settings
        mail.init_app(app)

        msg = Message(
            subject="Test Email from NRSC Guest Management",
            recipients=[email],
            html="""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Test Email</h2>
                <p>Hello,</p>
                <p>This is a test email from the NRSC Guest Management System.</p>
                <p>If you received this email, your email settings are configured correctly.</p>
                <p style="color: #666; font-size: 0.9em; margin-top: 20px;">
                    This is an automated message from the NRSC Guest Management System.
                </p>
            </div>
            """
        )
        
        current_app.logger.info("Attempting to send email...")
        with app.app_context():
            mail.send(msg)
        current_app.logger.info("Email sent successfully")
        
        return jsonify({
            'success': True,
            'message': 'Test email sent successfully'
        })
    except ConnectionRefusedError as e:
        error_msg = (
            f"Could not connect to SMTP server {smtp_settings['server']}:{smtp_settings['port']}. "
            "Please verify the server address and port are correct and the server is accessible."
        )
        current_app.logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        })
    except Exception as e:
        current_app.logger.error(f"Error sending test email: {str(e)}")
        error_msg = f"Failed to send email: {str(e)}"
        if "authentication failed" in str(e).lower():
            error_msg = "SMTP authentication failed. Please check your username and password."
        elif "ssl" in str(e).lower():
            error_msg = "SSL/TLS error. Please check your SSL/TLS settings."
        
        return jsonify({
            'success': False,
            'message': error_msg
        })

@main.route('/find-team-members', methods=['POST'])
@login_required
def find_team_members():
    try:
        data = request.get_json()
        host_name = data.get('host_name')
        
        if not host_name:
            return jsonify({
                'success': False,
                'message': 'Host name is required'
            })
            
        # Use the existing name matching function
        matches = find_matching_team_members(host_name)
        
        if not matches:
            return jsonify({
                'success': False,
                'message': 'No matching team members found'
            })
            
        # Convert matches to a list of dictionaries
        matches_data = [
            {
                'name': match[0].name,
                'email': match[0].email,
                'score': match[1]
            }
            for match in matches
        ]
        
        return jsonify({
            'success': True,
            'matches': matches_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error finding team members: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error finding team members: {str(e)}'
        })

@main.route('/debug-guests/<int:last_id>')
def debug_guests(last_id):
    # Get the same data as check-new-guests but return it formatted
    data = {
        'last_id_received': last_id,
        'current_time': datetime.now().isoformat(),
        'guests': [
            {
                'id': g.id,
                'name': g.name,
                'timestamp': g.timestamp.isoformat()
            } for g in Guest.query.filter(Guest.id > last_id).all()
        ],
        'total_count': Guest.query.filter(Guest.timestamp >= datetime.now().date()).count(),
        'host_preferences': get_host_preferences()  # Your existing function
    }
    return jsonify(data)

@main.route('/check-session')
def check_session():
    if 'session_start' not in session:
        session['session_start'] = datetime.now(pytz.UTC)  # Store as UTC
        # Make session permanent
        session.permanent = True
        return jsonify({
            'valid': True,
            'expires_in': int(current_app.config.get('PERMANENT_SESSION_LIFETIME').total_seconds())
        })
    
    # Refresh the session start time to keep it alive
    session['session_start'] = datetime.now(pytz.UTC)
    session.permanent = True
    
    # Always return valid with a long expiration time
    return jsonify({
        'valid': True,
        'expires_in': int(current_app.config.get('PERMANENT_SESSION_LIFETIME').total_seconds())
    })

@main.route('/admin/sessions')
@login_required
@admin_required
def view_sessions():
    sessions = SessionLog.query.order_by(SessionLog.last_seen.desc()).limit(100).all()
    return render_template('sessions.html', sessions=sessions)

@main.route('/update-session', methods=['POST'])
def update_session():
    session_id = session.get('session_id')
    if not session_id:
        # Create a new session if one doesn't exist
        session['session_id'] = os.urandom(16).hex()
        session['session_start'] = datetime.now(pytz.UTC)
        session.permanent = True
        
        # Log new session
        new_session = SessionLog(
            session_id=session['session_id'],
            user_agent=request.user_agent.string,
            ip_address=request.remote_addr
        )
        db.session.add(new_session)
        db.session.commit()
        
        return jsonify({'success': True})
    
    # Refresh the session start time
    session['session_start'] = datetime.now(pytz.UTC)
    session.permanent = True
    
    session_log = SessionLog.query.filter_by(session_id=session_id).first()
    if session_log:
        session_log.form_interactions += 1
        session_log.last_seen = datetime.now(pytz.UTC)
        db.session.commit()
    
    return jsonify({'success': True})



############ TRANE AC ROUTING ##############
@ac.route('/')                                                                                                                             
def ac_home():                                                                                                                             
    return render_template('trane.html')                                                                                                   
                                                                                                                                           
@ac.route('/api/status', methods=['GET'])                                                                                                  
def api_status():                                                                                                                          
    data = get_individual_data()                                                                                                           
    return jsonify(data)                                                                                                                   
                                                                                                                                           
@ac.route('/evox/point/<point_type>/<point_id>/value', methods=['GET'])                                                                    
def point_value(point_type, point_id):                                                                                                     
    # Make sure we're authenticated                                                                                                        
    if not authenticate():                                                                                                                 
        return "Authentication failed", 401                                                                                                
                                                                                                                                           
    # Get the value using the function from traneweb.py                                                                                    
    result = get_point_value(point_type, point_id)                                                                                         
                                                                                                                                           
    if 'error' in result:                                                                                                                  
        return result['error'], 500                                                                                                        
                                                                                                                                           
    # Return the result                                                                                                                    
    return jsonify(result)                                                                                                                 
                                                                                                                                           
@ac.route('/api/set', methods=['POST'])                                                                                                    
def api_set():                                                                                                                             
    data = request.json                                                                                                                    
    if not data or 'keyName' not in data or 'value' not in data:                                                                           
        return jsonify({"error": "Missing parameter or value"}), 400                                                                       
                                                                                                                                           
    result = set_hvac_parameter(data['keyName'], data['value'])                                                                            
    return jsonify(result)                                                                                                                 
                                                                                                                                           
@ac.route('/api/point', methods=['GET'])                                                                                                   
def api_point():                                                                                                                           
    point_type = request.args.get('type')                                                                                                  
    point_id = request.args.get('id')                                                                                                      
                                                                                                                                           
    if not point_type or not point_id:                                                                                                     
        return jsonify({"error": "Missing point type or ID"}), 400                                                                         
                                                                                                                                           
    result = get_point_value(point_type, point_id)                                                                                         
    return jsonify(result)                                                                                                                 
                                                                                                                                           
@ac.route('/debug')                                                                                                                        
def ac_debug():                                                                                                                            
    result = get_individual_data()                                                                                                         
    return jsonify(result) 

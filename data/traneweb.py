import os
import requests
import xml.etree.ElementTree as ET
import warnings
import base64
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

# Suppress InsecureRequestWarning
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

app = Flask(__name__)

# Configuration from environment variables
TRACER_SC_URL = os.getenv('TRACER_SC_URL', 'http://trane.nrsc.org')  # Changed to http if your example works with that
USERNAME = os.getenv('TRACER_USERNAME')
PASSWORD = os.getenv('TRACER_PASSWORD')

# Map of keyNames to human-readable parameter names and paths
PARAMETER_MAP = {
    # Essential parameters for the main dashboard
    'SpaceTempActive': {'name': 'Space Temperature Active', 'path': '/evox/equipment/scc/wshp/2/SpaceTempActive/value'},
    'OutdoorAirTemp': {'name': 'Outdoor Air Temperature', 'path': '/evox/point/ai/1/value'},
    'OutdoorHumidity': {'name': 'Outdoor Humidity', 'path': '/evox/point/ai/2/value'},
    'ReversingValve': {'name': 'Reversing Valve', 'path': '/evox/equipment/scc/wshp/2/ReversingValve/value'},
    'UCMDiagnosticPresent': {'name': 'Diagnostic Present', 'path': '/evox/equipment/scc/wshp/2/UCMDiagnosticPresent/value'},
    'aV6_wJ8BLYdd': {'name': 'Occupied Heat Setpoint', 'path': '/evox/equipment/scc/wshp/2/aV6_wJ8BLYdd/value', 'editable': True},
    'aV6_wJ8BLYdc': {'name': 'Occupied Cool Setpoint', 'path': '/evox/equipment/scc/wshp/2/aV6_wJ8BLYdc/value', 'editable': True},
    'aV6_wkNKKotN': {'name': 'Comfort Mode', 'path': '/evox/equipment/scc/wshp/2/aV6_wkNKKotN/value'},
    'aV6_wkNKKotV': {'name': 'PI Heating Demand', 'path': '/evox/equipment/scc/wshp/2/aV6_wkNKKotV/value'},
    'aV6_wkNKKotU': {'name': 'PI Cooling Demand', 'path': '/evox/equipment/scc/wshp/2/aV6_wkNKKotU/value'},
    
    # Status Info Tab
    'CommunicationStatus': {'name': 'Communication Status', 'path': '/evox/equipment/scc/wshp/2/CommunicationStatus/value'},
    'OccupancyStatus': {'name': 'Occupancy Status', 'path': '/evox/equipment/scc/wshp/2/OccupancyStatus/value'},
    
    # We'll keep these few additional parameters for the All Parameters tab
    'DischargeAirTemp': {'name': 'Discharge Air Temperature', 'path': '/evox/equipment/scc/wshp/2/DischargeAirTemp/value'},
    'InDefrost': {'name': 'In Defrost', 'path': '/evox/equipment/scc/wshp/2/InDefrost/value'},
}

# Map of known path prefixes to data types
DATA_TYPE_MAP = {
    'SpaceTempActive': 'Analog',
    'OutdoorAirTemp': 'Analog',
    'OutdoorHumidity': 'Analog',
    'OccupancyStatus': 'Multistate',
    'CommunicationStatus': 'Multistate',
    'ReversingValve': 'Binary',
    'UCMDiagnosticPresent': 'Binary',
    'InDefrost': 'Binary',
    'aV6_wJ8BLYdd': 'Analog',  # Occupied Heat Setpoint
    'aV6_wJ8BLYdc': 'Analog',  # Occupied Cool Setpoint
    'aV6_wkNKKotV': 'Analog',  # PI Heating Demand
    'aV6_wkNKKotU': 'Analog',  # PI Cooling Demand
    'aV6_wkNKKotN': 'Binary',  # Comfort Mode
    'DischargeAirTemp': 'Analog',
}

# State text mappings for multistate and binary values
STATE_TEXT_MAP = {
    'ReversingValve': ['Heating', 'Cooling'],  # false = Heating, true = Cooling
    'UCMDiagnosticPresent': ['Normal', 'In Alarm'],  # false = Normal, true = In Alarm
    'InDefrost': ['Not in Defrost', 'Defrost'],
    'OccupancyStatus': ['---', 'Occupied', 'Unoccupied', 'Occupied Bypass', 'Occupied Standby', 'Auto'],
    'CommunicationStatus': ['---', 'Not Communicating', 'Unresolved', 'Communicating', 'Startup'],
    'aV6_wkNKKotN': ['Comfort', 'Economy'],  # Comfort Mode
}

# Session to maintain cookies and authentication
session = requests.Session()
session.verify = False  # Skip SSL verification


def authenticate():
    """Authenticate with the Tracer SC system and set up session cookies"""
    try:
        auth_url = f"{TRACER_SC_URL}/hui/hui.html"

        # Use HTTP Digest Auth
        session.auth = requests.auth.HTTPDigestAuth(USERNAME, PASSWORD)

        # Make the authentication request
        response = session.get(auth_url)

        print(f"Authentication response: {response.status_code}")
        print(f"Cookies: {session.cookies.get_dict()}")

        return response.status_code == 200
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return False


def format_temperature(value):
    """Format temperature value to show 1 decimal place and °F"""
    try:
        temp = float(value)
        return f"{temp:.1f} °F"
    except (ValueError, TypeError):
        return value


# And format percentage values
def format_percentage(value):
    """Format percentage value to show 1 decimal place and %"""
    try:
        percent = float(value)
        return f"{percent:.1f}%"
    except (ValueError, TypeError):
        return value


# Format humidity values
def format_humidity(value):
    """Format humidity value to show whole number and %"""
    try:
        humidity = float(value)
        return f"{int(humidity)}%"
    except (ValueError, TypeError):
        # Ensure we always return with a % sign
        if not str(value).endswith('%'):
            return f"{value}%"
        return value


# Then modify the get_parameter_value function to format temperatures
def get_parameter_value(path):
    """Get the value of a single parameter from its path"""
    try:
        url = f"{TRACER_SC_URL}{path}"

        response = session.get(url)

        if response.status_code == 200:
            # Parse XML response
            try:
                root = ET.fromstring(response.text)

                # Get the value from the val attribute
                if 'val' in root.attrib:
                    value = root.get('val')

                    # Check if it's a scientific notation and convert if needed
                    if 'E' in value:
                        try:
                            value = str(float(value))
                        except ValueError:
                            pass

                    result = {
                        'value': value
                    }

                    # Also get the unit if present
                    if 'unit' in root.attrib:
                        result['unit'] = root.get('unit')

                        # Format temperature values
                        if 'degF' in root.get('unit'):
                            result['displayValue'] = format_temperature(value)
                        elif 'percent' in root.get('unit'):
                            result['displayValue'] = format_humidity(value)
                        else:
                            result['displayValue'] = value
                    else:
                        result['displayValue'] = value

                    return result
                else:
                    return {"error": f"No value found in response for {path}"}
            except ET.ParseError:
                return {"error": f"Invalid XML response for {path}"}
        else:
            return {"error": f"Failed to retrieve data: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error retrieving data: {str(e)}"}


def get_point_value(point_type, point_id):
    """Get a point value by its type and ID"""
    # Make sure we're authenticated
    if not authenticate():
        return {"error": "Authentication failed"}
    
    # Construct the path to the point
    path = f"/evox/point/{point_type}/{point_id}/value"
    
    # Get the value using the existing function
    return get_parameter_value(path)


# And update the get_individual_data function for better interpretation of true/false
def get_individual_data():
    """Retrieve data for each parameter in parallel"""
    import concurrent.futures
    
    auth_success = authenticate()

    if not auth_success:
        return {"error": "Authentication failed"}

    result = {}
    
    # Create a function to process a single parameter
    def process_parameter(key_name, param_info):
        value_data = get_parameter_value(param_info['path'])
        if value_data and 'error' not in value_data:
            # Get human-readable name
            param_name = param_info['name']

            # Determine data type
            data_type = DATA_TYPE_MAP.get(key_name, 'Analog')

            # Process the raw value
            value = value_data.get('value', '')

            # Special handling for Communication Status
            if key_name == 'CommunicationStatus':
                # Force it to be treated as multistate
                data_type = 'Multistate'
                # Print debug info
                print(f"Communication Status raw value: {value}")

            # Convert true/false strings to indices for binary values
            if data_type == 'Binary' and isinstance(value, str):
                if value.lower() == 'true':
                    value = '1'
                elif value.lower() == 'false':
                    value = '0'

            # Process multistate and binary values to get display value
            display_value = value
            if data_type in ['Multistate', 'Binary']:
                try:
                    index = int(float(value))
                    if key_name in STATE_TEXT_MAP and index < len(STATE_TEXT_MAP[key_name]):
                        display_value = STATE_TEXT_MAP[key_name][index]
                    else:
                        # Fall back to numeric value if not in map
                        display_value = str(index)
                except (ValueError, IndexError):
                    # Keep original if can't convert
                    pass

            # Format special value types
            if 'unit' in value_data and 'degF' in value_data.get('unit', ''):
                display_value = format_temperature(value)
            elif key_name in ['aV6_wkNKKotV', 'aV6_wkNKKotU']:  # PI Heating/Cooling Demand
                display_value = format_percentage(value)

            # Return the processed data
            return param_name, {
                'value': value,
                'displayValue': display_value,
                'keyName': key_name,
                'dataType': data_type,
                'path': param_info['path'],
                'editable': param_info.get('editable', False),  # Use editable flag from parameter map
                'stateText': STATE_TEXT_MAP.get(key_name, []),
                'unit': value_data.get('unit', '')
            }
        return None, None
    
    # Process all parameters in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Create a dictionary of futures to parameter keys
        future_to_param = {executor.submit(process_parameter, key, info): key 
                          for key, info in PARAMETER_MAP.items()}
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_param):
            param_name, param_data = future.result()
            if param_name and param_data:
                result[param_name] = param_data
    
    return result


def set_hvac_parameter(key_name, value):
    """Set a parameter on the HVAC system"""
    # Determine the path for this parameter
    if key_name not in PARAMETER_MAP:
        return {"error": f"Unknown parameter key: {key_name}"}

    param_path = PARAMETER_MAP[key_name]['path']

    # Make sure we're authenticated
    if not authenticate():
        return {"error": "Authentication failed"}

    try:
        url = f"{TRACER_SC_URL}{param_path}"

        # Prepare the XML content for the PUT request
        if key_name in DATA_TYPE_MAP and DATA_TYPE_MAP[key_name] == 'Analog':
            xml_content = f'<real val="{value}" />'
        elif key_name in DATA_TYPE_MAP and DATA_TYPE_MAP[key_name] == 'Binary':
            xml_content = f'<bool val="{value}" />'
        elif key_name in DATA_TYPE_MAP and DATA_TYPE_MAP[key_name] == 'Multistate':
            xml_content = f'<enum val="{value}" />'
        else:
            xml_content = f'<str val="{value}" />'

        headers = {
            'Content-Type': 'application/xml',
            'Referer': f'{TRACER_SC_URL}/hui/hui.html'
        }

        # Make the PUT request to update the value
        response = session.put(url, headers=headers, data=xml_content)

        if response.status_code == 200:
            return {"success": True, "message": f"Set {key_name} to {value}"}
        else:
            return {"error": f"Failed to set parameter: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error setting parameter: {str(e)}"}


# Flask Routes
@app.route('/')
def home():
    return render_template('trane.html')


@app.route('/api/status', methods=['GET'])
def api_status():
    data = get_individual_data()
    return jsonify(data)


@app.route('/evox/point/<point_type>/<point_id>/value', methods=['GET'])
def point_value(point_type, point_id):
    """Direct access to point values using the Tracer SC URL format"""
    # Make sure we're authenticated
    if not authenticate():
        return "Authentication failed", 401
    
    # Construct the path to the point
    path = f"/evox/point/{point_type}/{point_id}/value"
    
    # Get the value from the Tracer SC
    try:
        url = f"{TRACER_SC_URL}{path}"
        response = session.get(url)
        
        if response.status_code == 200:
            # Return the raw XML response
            return response.text, 200, {'Content-Type': 'application/xml'}
        else:
            return f"Failed to retrieve data: {response.status_code}", response.status_code
    except Exception as e:
        return f"Error retrieving data: {str(e)}", 500


@app.route('/api/set', methods=['POST'])
def api_set():
    data = request.json
    if not data or 'keyName' not in data or 'value' not in data:
        return jsonify({"error": "Missing parameter or value"}), 400

    result = set_hvac_parameter(data['keyName'], data['value'])
    return jsonify(result)


@app.route('/api/point', methods=['GET'])
def api_point():
    """API endpoint to get a point value by type and ID"""
    point_type = request.args.get('type')
    point_id = request.args.get('id')
    
    if not point_type or not point_id:
        return jsonify({"error": "Missing point type or ID"}), 400
    
    result = get_point_value(point_type, point_id)
    return jsonify(result)


@app.route('/debug')
def debug():
    result = get_individual_data()
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=5000)

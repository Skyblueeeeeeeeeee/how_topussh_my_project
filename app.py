from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
socketio = SocketIO(app)
CORS(app, resources={r"/socket.io/*": {"origins": "*"}})

tenant_username = "gpstrackingoto@gmail.com"
tenant_password = "12345678"
thingsboard_base_url = "https://thingsboard.cloud/"
device_id = "72fd9950-8f67-11ee-9774-a38683104857"
device_access_token = "dU0p1fYdDKR4kL3kqYNS"
telemetry_keys = "latitude,longitude"  # Updated keys

longitude, latitude = None, None  # Khởi tạo giá trị mặc định

def get_access_token(username, password):
    url = thingsboard_base_url + "api/auth/login"
    payload = {"username": username, "password": password}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        token = response.json().get('token', None)
        return token
    except requests.exceptions.RequestException as e:
        print(f"Error during access token retrieval: {e}")
        return None

def get_device_telemetry(device_token, keys):
    url = f"{thingsboard_base_url}api/plugins/telemetry/DEVICE/{device_id}/values/timeseries?keys={keys}&useStrictDataTypes=true"
    headers = {'Content-Type': 'application/json', 'X-Authorization': f'Bearer {device_token}'}

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()

        telemetry_data = response.json()
        return telemetry_data
    except requests.exceptions.RequestException as e:
        print(f"Error during telemetry data retrieval: {e}")
        return None

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit_telemetry_data()  # Gửi dữ liệu ngay khi kết nối

@socketio.on('telemetry_update')
def send_telemetry_data():
    emit_telemetry_data()  # Gửi dữ liệu khi có yêu cầu cập nhật

@app.route('/')
def display_telemetry():
    return render_template('index.html')

def emit_telemetry_data():
    global longitude, latitude  # Sử dụng biến toàn cục
    device_access_token = get_access_token(tenant_username, tenant_password)

    if device_access_token:
        telemetry_data = get_device_telemetry(device_access_token, telemetry_keys)

        if telemetry_data:
            longitude = telemetry_data.get('longitude', [{}])[0].get('value', None)
            latitude = telemetry_data.get('latitude', [{}])[0].get('value', None)
        else:
            longitude, latitude = None, None
    else:
        longitude, latitude = None, None

    print(f"Sending telemetry data - Longitude: {longitude}, Latitude: {latitude}")
    socketio.emit('telemetry_data', {'longitude': longitude, 'latitude': latitude}, namespace='/')

def update_telemetry_periodically():
    global longitude, latitude  # Sử dụng biến toàn cục
    while True:
        emit_telemetry_data()
        socketio.sleep(3)

# Thêm tham số `longitude` và `latitude` khi gọi hàm `update_telemetry_periodically`
if __name__ == '__main__':
    socketio.start_background_task(target=update_telemetry_periodically)
    socketio.run(app, host='0.0.0.0', port=3000, debug=True)

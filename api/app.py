from flask import Flask, jsonify, render_template, request
import requests
from datetime import datetime, timedelta
import os

from supabase_client import insert_order, get_all_orders, update_order, delete_order

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
BASE_URL = 'https://smshub.org/stubs/handler_api.php'

SERVICES = {
    "go": "Google",
    "ni": "Gojek",
    "wa": "WhatsApp",
    "bnu": "Qpon",
    "tg": "Telegram",
    "eh": "Telegram 2.0"
}

COUNTRIES = {
    "6": "Indonesia",
    "0": "Russia",
    "3": "China"
}

def get_smshub_data(action, params=None):
    try:
        params = params or {}
        params.update({'api_key': API_KEY, 'action': action})
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"API Error: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/services')
def get_services():
    return jsonify(SERVICES)

@app.route('/api/countries')
def get_countries():
    return jsonify(COUNTRIES)

@app.route('/api/balance')
def get_balance():
    response = get_smshub_data('getBalance')
    if response and response.startswith('ACCESS_BALANCE:'):
        return jsonify({'success': True, 'balance': response.split(':')[1]})
    return jsonify({'success': False, 'error': 'Failed to get balance'})

@app.route('/api/orders')
def get_orders():
    orders = get_all_orders()
    result = []
    for o in orders:
        expires_at = datetime.fromisoformat(o['expires_at']) if o.get('expires_at') else None
        remaining = (expires_at - datetime.utcnow()).total_seconds() if expires_at else None
        result.append({
            **o,
            'service': SERVICES.get(o['service'], o['service']),
            'country': COUNTRIES.get(o['country'], o['country']),
            'expires_in': max(int(remaining), 0) if remaining else None
        })
    return jsonify({'success': True, 'orders': result})

@app.route('/api/create', methods=['POST'])
def create_order():
    data = request.json
    service = data.get('service')
    country = data.get('country')
    if service not in SERVICES or country not in COUNTRIES:
        return jsonify({'success': False, 'error': 'Invalid service or country'})

    response = get_smshub_data('getNumber', {'service': service, 'country': country})
    if response and response.startswith('ACCESS_NUMBER:'):
        _, order_id, number = response.split(':')
        now = datetime.utcnow()
        order = {
            'id': order_id,
            'number': number,
            'service': service,
            'country': country,
            'status': 'WAITING',
            'created_at': now.isoformat(),
            'expires_at': (now + timedelta(minutes=20)).isoformat()
        }
        insert_order(order)
        return jsonify({'success': True, 'order': order})
    return jsonify({'success': False, 'error': response or 'Failed to create order'})

@app.route('/api/status/<order_id>')
def get_status(order_id):
    response = get_smshub_data('getStatus', {'id': order_id})
    if response:
        if response.startswith('STATUS_OK:'):
            update_order(order_id, {'status': 'COMPLETED'})
            return jsonify({'status': 'COMPLETED', 'sms': response.split(':', 1)[1]})
        elif response.startswith('STATUS_WAIT_CODE'):
            return jsonify({'status': 'WAITING'})
        elif response.startswith('STATUS_CANCEL'):
            update_order(order_id, {'status': 'CANCELED'})
            return jsonify({'status': 'CANCELED'})
        return jsonify({'status': response})
    return jsonify({'status': 'UNKNOWN'})

@app.route('/api/cancel/<order_id>', methods=['POST'])
def cancel_order(order_id):
    response = get_smshub_data('setStatus', {'status': 8, 'id': order_id})
    if response == 'ACCESS_CANCEL':
        delete_order(order_id)
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/request_again/<order_id>', methods=['POST'])
def request_again(order_id):
    response = get_smshub_data('setStatus', {'status': 3, 'id': order_id})
    if response == 'ACCESS_READY':
        now = datetime.utcnow()
        update_order(order_id, {
            'status': 'WAITING',
            'created_at': now.isoformat(),
            'expires_at': (now + timedelta(minutes=20)).isoformat()
        })
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': response})

@app.route('/api/remove_order/<order_id>', methods=['POST'])
def remove_order(order_id):
    try:
        delete_order(order_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

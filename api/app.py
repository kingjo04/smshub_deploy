import os
from flask import Flask, jsonify, render_template, request
from datetime import datetime
import requests
import sys

# Tambahkan path untuk import file supabase_client.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from supabase_client import (
    insert_order, get_all_orders, update_order,
    delete_order, get_order_by_id
)

app = Flask(
    __name__,
    template_folder='../templates',
    static_folder='../static'
)

API_KEY = os.environ.get('API_KEY')
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
    for order in orders:
        order["service"] = SERVICES.get(order["service"], order["service"])
        order["country"] = COUNTRIES.get(order["country"], order["country"])
    return jsonify({'success': True, 'orders': orders})

@app.route('/api/create', methods=['POST'])
def create_order():
    data = request.json
    service = data.get('service')
    country = data.get('country')

    if service not in SERVICES:
        return jsonify({'success': False, 'error': 'Invalid service'})

    if country not in COUNTRIES:
        return jsonify({'success': False, 'error': 'Invalid country'})

    response = get_smshub_data('getNumber', {'service': service, 'country': country})

    if response and response.startswith('ACCESS_NUMBER:'):
        _, order_id, number = response.split(':')
        order = {
            'id': order_id,
            'number': number,
            'service': service,
            'country': country,
            'status': 'WAITING',
            'created_at': datetime.now().isoformat()
        }
        insert_order(order)
        return jsonify({'success': True, 'order': order})

    return jsonify({'success': False, 'error': response or 'Failed to create order'})

@app.route('/api/status/<order_id>')
def get_status(order_id):
    response = get_smshub_data('getStatus', {'id': order_id})
    if response:
        if response.startswith('STATUS_OK:'):
            sms = response.split(':', 1)[1]
            update_order(order_id, {'status': 'COMPLETED'})
            return jsonify({'status': 'COMPLETED', 'sms': sms})
        elif response.startswith('STATUS_WAIT_CODE'):
            return jsonify({'status': 'WAITING'})
        elif response.startswith('STATUS_CANCEL'):
            update_order(order_id, {'status': 'CANCELED'})
            return jsonify({'status': 'CANCELED'})
        elif response.startswith('STATUS_USED'):
            update_order(order_id, {'status': 'USED'})
            return jsonify({'status': 'USED'})
    return jsonify({'status': 'UNKNOWN'})

@app.route('/api/cancel/<order_id>', methods=['POST'])
def cancel_order(order_id):
    response = get_smshub_data('setStatus', {'status': 8, 'id': order_id})
    if response == 'ACCESS_CANCEL':
        delete_order(order_id)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': response})

@app.route('/api/request_again/<order_id>', methods=['POST'])
def request_again(order_id):
    response = get_smshub_data('setStatus', {'status': 3, 'id': order_id})
    if response == 'ACCESS_READY':
        update_order(order_id, {
            'status': 'WAITING',
            'created_at': datetime.now().isoformat()
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

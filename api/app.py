from flask import Flask, jsonify, render_template, request
import requests
import configparser
import ast
from datetime import datetime
import os

app = Flask(__name__)
config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config['DEFAULT']['API_KEY']
BASE_URL = 'https://smshub.org/stubs/handler_api.php'
ORDERS_FILE = 'orders.txt'

# Daftar layanan dan negara yang didukung
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

def save_order_to_file(order):
    """Simpan order ke file orders.txt"""
    with open(ORDERS_FILE, 'a') as file:
        file.write(f"{order['id']},{order['number']},{order['service']},{order['country']},{order['status']},{order['created_at']}\n")

def load_orders_from_file():
    """Baca semua order dari file orders.txt"""
    if not os.path.exists(ORDERS_FILE):
        return []
    
    orders = []
    with open(ORDERS_FILE, 'r') as file:
        for line in file:
            order_id, number, service, country, status, created_at = line.strip().split(',')
            orders.append({
                'id': order_id,
                'number': number,
                'service': service,
                'country': country,
                'status': status,
                'created_at': created_at
            })
    return orders

def update_order_in_file(order_id, updates):
    """Update order di file orders.txt"""
    orders = load_orders_from_file()
    updated_orders = []
    for order in orders:
        if order['id'] == order_id:
            order.update(updates)
        updated_orders.append(order)
    
    with open(ORDERS_FILE, 'w') as file:
        for order in updated_orders:
            file.write(f"{order['id']},{order['number']},{order['service']},{order['country']},{order['status']},{order['created_at']}\n")

def remove_order_from_file(order_id):
    """Hapus order dari file orders.txt"""
    orders = load_orders_from_file()
    updated_orders = [order for order in orders if order['id'] != order_id]
    
    with open(ORDERS_FILE, 'w') as file:
        for order in updated_orders:
            file.write(f"{order['id']},{order['number']},{order['service']},{order['country']},{order['status']},{order['created_at']}\n")

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
    orders = load_orders_from_file()
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
        save_order_to_file(order)  # Simpan order ke
        return jsonify({'success': True, 'order': order})
    
    return jsonify({'success': False, 'error': response or 'Failed to create order'})

@app.route('/api/status/<order_id>')
def get_status(order_id):
    response = get_smshub_data('getStatus', {'id': order_id})
    if response:
        if response.startswith('STATUS_OK:'):
            return jsonify({
                'status': 'COMPLETED',
                'sms': response.split(':', 1)[1]
            })
        return jsonify({'status': response})
    return jsonify({'status': 'UNKNOWN'})

@app.route('/api/cancel/<order_id>', methods=['POST'])
def cancel_order(order_id):
    response = get_smshub_data('setStatus', {'status': 8, 'id': order_id})
    if response == 'ACCESS_CANCEL':
        remove_order_from_file(order_id)  # Hapus order dari file
        return jsonify({'success': True})
    return jsonify({'success': False})

# ... (Kode backend sebelumnya tetap sama)
@app.route('/api/request_again/<order_id>', methods=['POST'])
def request_again(order_id):
    """Fitur untuk meminta ulang SMS"""
    response = get_smshub_data('setStatus', {'status': 3, 'id': order_id})
    if response == 'ACCESS_READY':
        update_order_in_file(order_id, {
            'status': 'WAITING',
            'created_at': datetime.now().isoformat()  # Reset waktu
        })
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': response})

@app.route('/api/remove_order/<order_id>', methods=['POST'])
def remove_order(order_id):
    try:
        remove_order_from_file(order_id)  # Fungsi yang sudah ada
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
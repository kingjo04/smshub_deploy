from flask import Flask, render_template, request, jsonify
from .supabase_client import (
    insert_order,
    get_all_orders,
    get_order_by_id,
    update_order,
    delete_order
)
import requests
import os
from datetime import datetime

app = Flask(__name__, template_folder="../templates", static_folder="../static")

API_KEY = os.getenv("API_KEY")
BASE_URL = 'https://smshub.org/stubs/handler_api.php'

# Favorite layanan dan negara
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/services")
def get_services():
    return jsonify(SERVICES)

@app.route("/api/countries")
def get_countries():
    return jsonify(COUNTRIES)

@app.route("/api/all_services")
def get_all_services():
    response = get_smshub_data('getServices')
    if not response:
        return jsonify({'success': False, 'error': 'Failed to load services'})
    try:
        services = eval(response)
        return jsonify({'success': True, 'services': services})
    except:
        return jsonify({'success': False, 'error': 'Failed to parse services'})

@app.route("/api/all_countries")
def get_all_countries():
    response = get_smshub_data('getCountries')
    if not response:
        return jsonify({'success': False, 'error': 'Failed to load countries'})
    try:
        countries = eval(response)
        return jsonify({'success': True, 'countries': countries})
    except:
        return jsonify({'success': False, 'error': 'Failed to parse countries'})

@app.route("/api/balance")
def get_balance():
    response = get_smshub_data('getBalance')
    if response and response.startswith('ACCESS_BALANCE:'):
        return jsonify({'success': True, 'balance': response.split(':')[1]})
    return jsonify({'success': False, 'error': 'Failed to get balance'})

@app.route("/api/orders")
def get_orders():
    orders = get_all_orders()
    return jsonify({'success': True, 'orders': orders})

@app.route("/api/create", methods=["POST"])
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

@app.route("/api/status/<order_id>")
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

@app.route("/api/cancel/<order_id>", methods=['POST'])
def cancel_order(order_id):
    response = get_smshub_data('setStatus', {'status': 8, 'id': order_id})
    if response == 'ACCESS_CANCEL':
        delete_order(order_id)
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == "__main__":
    app.run(debug=True)

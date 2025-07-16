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
from datetime import datetime, timedelta, timezone

app = Flask(__name__, template_folder="../templates", static_folder="../static")

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

@app.route("/")
def index():
    orders = get_all_orders()
    now = datetime.now(timezone.utc)
    active_orders = []
    history_orders = []

    for order in orders:
        try:
            created_time = datetime.fromisoformat(order['created_at'])
            if created_time.tzinfo is None:
                created_time = created_time.replace(tzinfo=timezone.utc)
            expires_time = datetime.fromisoformat(order['expires_at']) if order['expires_at'] else created_time + timedelta(minutes=20)
        except:
            created_time = now
            expires_time = now + timedelta(minutes=20)

        if order['status'] == 'WAITING' and (now - created_time) < timedelta(minutes=20):
            active_orders.append(order)
        else:
            history_orders.append(order)

    return render_template("index.html", active_orders=active_orders, history_orders=history_orders)

@app.route("/order", methods=["POST"])
def create_order():
    data = request.json
    if not data.get('expires_at'):
        data['expires_at'] = (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat()
    response = insert_order(data)
    return jsonify(response)

@app.route("/order/<order_id>", methods=["GET"])
def get_order(order_id):
    order = get_order_by_id(order_id)
    return jsonify(order)

@app.route("/order/<order_id>", methods=["PUT"])
def update(order_id):
    data = request.json
    if 'sms_code' in data and not data.get('expires_at'):
        data['expires_at'] = (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat()
    result = update_order(order_id, data)
    return jsonify(result)

@app.route("/order/<order_id>", methods=["DELETE"])
def delete(order_id):
    result = delete_order(order_id)
    return jsonify(result)

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
def api_orders():
    orders = get_all_orders()
    now = datetime.now(timezone.utc)
    active_orders = []
    history_orders = []

    for order in orders:
        try:
            created_time = datetime.fromisoformat(order['created_at'])
            if created_time.tzinfo is None:
                created_time = created_time.replace(tzinfo=timezone.utc)
            expires_time = datetime.fromisoformat(order['expires_at']) if order['expires_at'] else created_time + timedelta(minutes=20)
        except:
            created_time = now
            expires_time = now + timedelta(minutes=20)

        if order['status'] == 'WAITING' and (now - created_time) < timedelta(minutes=20):
            active_orders.append(order)
        else:
            history_orders.append(order)

    return jsonify({
        'active_orders': active_orders,
        'history_orders': history_orders
    })

@app.route("/api/create", methods=["POST"])
def create_sms_order():
    data = request.json
    service = data.get('service')
    country = data.get('country')
    if not service or not country:
        return jsonify({'success': False, 'error': 'Service and country are required'})

    response = get_smshub_data('getNumber', {'service': service, 'country': country})
    if response and response.startswith('ACCESS_NUMBER:'):
        _, order_id, number = response.split(':')
        order = {
            'id': order_id,
            'number': number,
            'service': SERVICES.get(service, service),
            'country': COUNTRIES.get(country, country),
            'status': 'WAITING',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat(),
            'sms_code': None
        }
        insert_order(order)
        return jsonify({'success': True, 'order': order})
    return jsonify({'success': False, 'error': response or 'Failed to create order'})

@app.route("/api/status/<order_id>")
def get_status(order_id):
    response = get_smshub_data('getStatus', {'id': order_id})
    if response:
        if response.startswith('STATUS_OK:'):
            sms_code = response.split(':', 1)[1]
            update_order(order_id, {'status': 'COMPLETED', 'sms_code': sms_code})
            return jsonify({
                'status': 'COMPLETED',
                'sms_code': sms_code
            })
        return jsonify({'status': response})
    return jsonify({'status': 'UNKNOWN'})

@app.route("/api/cancel/<order_id>", methods=['POST'])
def cancel_order(order_id):
    response = get_smshub_data('setStatus', {'status': 8, 'id': order_id})
    if response == 'ACCESS_CANCEL':
        update_order(order_id, {'status': 'CANCELED'})
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == "__main__":
    app.run(debug=True)

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

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Ambil API_KEY dari environment variable
API_KEY = os.getenv("API_KEY")
BASE_URL = 'https://smshub.org/stubs/handler_api.php'

# Daftar layanan dan negara yang sering digunakan
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
    return render_template("index.html", orders=orders)

@app.route("/order", methods=["POST"])
def create_order():
    data = request.json
    response = insert_order(data)
    return jsonify(response)

@app.route("/order/<order_id>", methods=["GET"])
def get_order(order_id):
    order = get_order_by_id(order_id)
    return jsonify(order)

@app.route("/order/<order_id>", methods=["PUT"])
def update(order_id):
    data = request.json
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

if __name__ == "__main__":
    app.run(debug=True)

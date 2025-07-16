from flask import Flask, render_template, request, jsonify
from .supabase_client import (
    insert_order,
    get_all_orders,
    get_order_by_id,
    update_order,
    delete_order
)


app = Flask(__name__, template_folder="../templates", static_folder="../static")

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

if __name__ == "__main__":
    app.run(debug=True)

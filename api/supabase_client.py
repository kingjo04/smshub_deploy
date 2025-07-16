import os
from supabase import create_client, Client
from datetime import datetime, timedelta

# Ambil ENV dari Railway
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Inisialisasi client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fungsi: Ambil semua data order
def get_all_orders():
    response = supabase.table("orders").select("*").order("created_at", desc=True).execute()
    return response.data if response.data else []

# Fungsi: Tambah order baru
def insert_order(service, phone, status, code, price, time_limit):
    created_at = datetime.utcnow()
    expired_at = created_at + timedelta(minutes=int(time_limit))  # waktu habis otomatis
    response = supabase.table("orders").insert({
        "service": service,
        "phone": phone,
        "status": status,
        "code": code,
        "price": price,
        "created_at": created_at.isoformat(),
        "expired_at": expired_at.isoformat()
    }).execute()
    return response.data

# Fungsi: Update order
def update_order(order_id, data: dict):
    response = supabase.table("orders").update(data).eq("id", order_id).execute()
    return response.data

# Fungsi: Hapus order
def delete_order(order_id):
    response = supabase.table("orders").delete().eq("id", order_id).execute()
    return response.data

# Fungsi: Ambil saldo (misal hanya 1 baris di tabel balances)
def get_balance():
    response = supabase.table("balance").select("*").limit(1).execute()
    return response.data[0] if response.data else {"amount": 0}

# Fungsi: Ambil order by ID (untuk detail misalnya)
def get_order_by_id(order_id):
    response = supabase.table("orders").select("*").eq("id", order_id).limit(1).execute()
    return response.data[0] if response.data else None

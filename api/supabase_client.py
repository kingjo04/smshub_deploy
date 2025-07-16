
from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_order(order):
    return supabase.table("orders").insert(order).execute()

def get_all_orders():
    return supabase.table("orders").select("*").order("created_at", desc=True).execute().data

def update_order(order_id, updates):
    return supabase.table("orders").update(updates).eq("id", order_id).execute()

def delete_order(order_id):
    return supabase.table("orders").delete().eq("id", order_id).execute()


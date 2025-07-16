from supabase import create_client, Client
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def insert_order(order):
    return supabase.table("orders").insert(order).execute()

def get_all_orders():
    res = supabase.table("orders").select("*").execute()
    return res.data

def get_order_by_id(order_id):
    res = supabase.table("orders").select("*").eq("id", order_id).single().execute()
    return res.data

def update_order(order_id, updates):
    return supabase.table("orders").update(updates).eq("id", order_id).execute()

def delete_order(order_id):
    return supabase.table("orders").delete().eq("id", order_id).execute()

from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_order(order):
    supabase.table("orders").insert(order).execute()

def get_all_orders():
    data = supabase.table("orders").select("*").order("created_at", desc=True).execute()
    return data.data

def get_order_by_id(order_id):
    data = supabase.table("orders").select("*").eq("id", order_id).single().execute()
    return data.data

def update_order(order_id, updates):
    supabase.table("orders").update(updates).eq("id", order_id).execute()
    return {"success": True}

def delete_order(order_id):
    supabase.table("orders").delete().eq("id", order_id).execute()
    return {"success": True}

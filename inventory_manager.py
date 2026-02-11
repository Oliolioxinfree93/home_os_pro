import streamlit as st
from st_supabase_connection import SupabaseConnection

class InventoryManager:
    def __init__(self):
        # Connect to the cloud database using the secrets you just saved
        try:
            self.conn = st.connection("supabase", type=SupabaseConnection)
        except Exception as e:
            st.error(f"Failed to connect to Supabase: {e}")

    def add_item(self, name, quantity=1, category="Other", unit="unit", storage="fresh", price=0.0, store="None"):
        """Adds a new item to your Cloud Fridge."""
        item_data = {
            "item_name": name.lower(),
            "quantity": quantity,
            "category": category,
            "unit": unit,
            "storage": storage,
            "price": price,
            "store": store,
            "status": "In Stock"
        }
        # Insert into the 'inventory' table in Supabase
        return self.conn.table("inventory").insert(item_data).execute()

    def get_inventory(self):
        """Fetches all items currently in stock."""
        response = self.conn.table("inventory").select("*").eq("status", "In Stock").execute()
        return response.data

    def delete_item(self, item_id):
        """Deletes an item from the cloud."""
        return self.conn.table("inventory").delete().eq("id", item_id).execute()

    def add_to_shopping_list(self, name, estimated_price=0.0):
        """Adds an item to the shopping list table."""
        # Note: Ensure you have a 'shopping_list' table in Supabase as well
        item_data = {
            "item_name": name.lower(),
            "estimated_price": estimated_price
        }
        return self.conn.table("shopping_list").insert(item_data).execute()

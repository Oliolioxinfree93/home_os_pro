import sqlite3
from datetime import datetime, timedelta

DB_NAME = 'home.db'

# --- THIS IS THE FUNCTION APP.PY IS LOOKING FOR ---
def load_demo():
    print("🎬 Populating Home OS with demo data...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Clear old data to prevent duplicates
    cursor.execute("DELETE FROM inventory")
    cursor.execute("DELETE FROM price_history")
    
    # 2. Add Sample Inventory
    today = datetime.now().date()
    inventory_items = [
        ('milk', 'Dairy', 1, 'gallon', 'fresh', 4, 4.99, 'Kroger'),
        ('eggs', 'Dairy', 1, 'carton', 'fresh', 18, 3.49, 'Walmart'),
        ('chicken', 'Meat', 2, 'lb', 'frozen', 120, 8.99, 'Costco'),
        ('spinach', 'Produce', 1, 'bag', 'fresh', 3, 2.99, 'Whole Foods'),
        ('rice', 'Pantry', 1, 'bag', 'pantry', 300, 12.99, 'Amazon')
    ]

    for item in inventory_items:
        name, category, qty, unit, storage, days_exp, price, store = item
        expiry = today + timedelta(days=days_exp)
        
        cursor.execute('''
        INSERT INTO inventory 
        (item_name, category, quantity, unit, storage, date_added, expiry_date, 
         status, decision_reason, price, store)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, category, qty, unit, storage, today, expiry, 'In Stock',
              f'Demo data: {storage} storage', price, store))

    # 3. Add Price History (For "Impact" Dashboard)
    price_history_items = [
        ('milk', 4.99, 'Kroger'),
        ('eggs', 3.49, 'Walmart'),
        ('chicken', 8.99, 'Costco')
    ]
    for name, price, store in price_history_items:
        cursor.execute('''
        INSERT INTO price_history (item_name, price, store, quantity, unit, date_recorded)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, price, store, 1, 'unit', today))

    # 4. Set Budget
    cursor.execute('UPDATE budget_settings SET current_spent = 150.50 WHERE id = 1')

    conn.commit()
    conn.close()
    print("✅ Demo data loaded successfully!")

if __name__ == "__main__":
    load_demo()

import sqlite3
import datetime
from datetime import timedelta
from inventory_logic import InventoryLogic

class InventoryManager:
    def __init__(self, db_name='home.db'):
        self.db_name = db_name
        self.logic = InventoryLogic()

    def add_item(self, raw_item_name, quantity=1, price=None, store=None, barcode=None):
        analysis = self.logic.normalize_item(raw_item_name)
        today = datetime.date.today()
        expiry_date = today + timedelta(days=analysis['expiry_days'])
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO inventory (item_name, category, quantity, unit, storage, date_added, 
                              expiry_date, status, decision_reason, price, store, barcode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis['clean_name'], 
            analysis['category'], 
            quantity, 
            analysis['unit'],      
            analysis['storage'],   
            today, 
            expiry_date, 
            'In Stock',
            analysis['reason'],
            price,
            store,
            barcode
        ))
        
        conn.commit()
        conn.close()
        print(f"Added '{analysis['clean_name']}' ({analysis['storage']})")

    def add_to_shopping_list(self, item_name, estimated_price=None, barcode=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM shopping_list WHERE item_name = ?", (item_name,))
        if not cursor.fetchone():
            cursor.execute('''
            INSERT INTO shopping_list (item_name, is_urgent, estimated_price, barcode) 
            VALUES (?, 0, ?, ?)
            ''', (item_name, estimated_price, barcode))
            print(f"🛒 Added '{item_name}' to shopping list.")
        conn.commit()
        conn.close()

    def consume_ingredients(self, ingredient_names):
        """
        Smart Consumption: 
        - Decrements quantity if > 1
        - Marks 'Consumed' if = 1
        - Returns (report_text, list_of_depleted_items)
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        report = [] 
        depleted_items = []
        
        for ingredient in ingredient_names:
            search_term = ingredient.lower().replace("frozen", "").strip()

            # FIFO: Find OLDEST 'In Stock' item
            cursor.execute("""
                SELECT id, item_name, quantity, storage, unit 
                FROM inventory 
                WHERE item_name LIKE ? 
                AND status='In Stock'
                ORDER BY expiry_date ASC
                LIMIT 1
            """, (f'%{search_term}%',))
            
            match = cursor.fetchone()
            
            if match:
                item_id, db_name, qty, storage, unit = match
                
                if qty > 1:
                    new_qty = qty - 1
                    cursor.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_qty, item_id))
                    report.append(f"Used 1 {unit} of '{db_name}'. Remaining: {new_qty}")
                else:
                    # Item is GONE
                    cursor.execute("UPDATE inventory SET status='Consumed' WHERE id=?", (item_id,))
                    report.append(f"Finished '{db_name}' ({storage})")
                    depleted_items.append(db_name)
            else:
                report.append(f"⚠️ '{ingredient}' not found in fridge")
        
        conn.commit()
        conn.close()
        return report, depleted_items
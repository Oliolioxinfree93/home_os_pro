import sqlite3

def create_database():
    conn = sqlite3.connect('home.db')
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS inventory')
    cursor.execute('DROP TABLE IF EXISTS shopping_list')

    # 1. NEW INVENTORY SCHEMA (Added 'decision_reason')
    cursor.execute('''
    CREATE TABLE inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        category TEXT,
        quantity REAL,
        unit TEXT,          
        storage TEXT,       
        date_added DATE,
        expiry_date DATE,
        status TEXT DEFAULT 'In Stock',
        decision_reason TEXT  -- The "Why" Column
    )
    ''')

    cursor.execute('''
    CREATE TABLE shopping_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        is_urgent BOOLEAN DEFAULT 0
    )
    ''')

    print("✅ Database V1 Ready: Added 'decision_reason' column.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
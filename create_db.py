import sqlite3

def create_database():
    conn = sqlite3.connect('home.db')
    cursor = conn.cursor()

    # Drop old tables to ensure clean schema
    cursor.execute('DROP TABLE IF EXISTS inventory')
    cursor.execute('DROP TABLE IF EXISTS shopping_list')
    cursor.execute('DROP TABLE IF EXISTS meal_plan')
    cursor.execute('DROP TABLE IF EXISTS price_history')
    cursor.execute('DROP TABLE IF EXISTS nutrition_data')
    cursor.execute('DROP TABLE IF EXISTS budget_settings')

    # 1. INVENTORY TABLE (Enhanced with price tracking)
    cursor.execute('''
    CREATE TABLE inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        category TEXT,
        quantity REAL,
        unit TEXT,          
        storage TEXT,       -- 'fresh', 'frozen', 'pantry'
        date_added DATE,
        expiry_date DATE,
        status TEXT DEFAULT 'In Stock',
        decision_reason TEXT,
        price REAL,         -- NEW: Price per unit
        barcode TEXT,       -- NEW: UPC/EAN barcode
        store TEXT          -- NEW: Where purchased
    )
    ''')

    # 2. SHOPPING LIST TABLE (Enhanced with price estimates)
    cursor.execute('''
    CREATE TABLE shopping_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        is_urgent BOOLEAN DEFAULT 0,
        estimated_price REAL,
        barcode TEXT
    )
    ''')

    # 3. MEAL PLAN TABLE (NEW)
    cursor.execute('''
    CREATE TABLE meal_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        meal_type TEXT,     -- 'breakfast', 'lunch', 'dinner', 'snack'
        recipe_id INTEGER,  -- Spoonacular recipe ID
        recipe_name TEXT,
        recipe_image TEXT,
        servings INTEGER DEFAULT 1,
        calories INTEGER,
        prep_time INTEGER,  -- minutes
        ingredients TEXT,   -- JSON array of ingredient names
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 4. PRICE HISTORY TABLE (NEW)
    cursor.execute('''
    CREATE TABLE price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        price REAL NOT NULL,
        store TEXT,
        quantity REAL,
        unit TEXT,
        date_recorded DATE,
        barcode TEXT
    )
    ''')

    # 5. NUTRITION DATA TABLE (NEW)
    cursor.execute('''
    CREATE TABLE nutrition_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        serving_size TEXT,
        calories REAL,
        protein REAL,       -- grams
        carbs REAL,         -- grams
        fat REAL,           -- grams
        fiber REAL,         -- grams
        sugar REAL,         -- grams
        sodium REAL,        -- mg
        source TEXT,        -- 'api', 'manual', 'barcode'
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 6. BUDGET SETTINGS TABLE (NEW)
    cursor.execute('''
    CREATE TABLE budget_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period TEXT DEFAULT 'monthly',  -- 'weekly', 'monthly'
        budget_limit REAL,
        alert_threshold REAL DEFAULT 0.8,  -- Alert at 80% of budget
        start_date DATE,
        current_spent REAL DEFAULT 0
    )
    ''')

    # Insert default budget settings
    cursor.execute('''
    INSERT INTO budget_settings (period, budget_limit, start_date, current_spent)
    VALUES ('monthly', 500.00, date('now'), 0)
    ''')

    print("✅ Database V2 Created Successfully with Enhanced Features!")
    print("   - Meal Planning")
    print("   - Price Tracking")
    print("   - Nutrition Data")
    print("   - Budget Management")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
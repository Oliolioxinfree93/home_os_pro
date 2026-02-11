#!/usr/bin/env python3
"""
Demo script to populate the Home OS database with sample data
Run this after create_db.py to see the system in action
"""

import sqlite3
from datetime import datetime, timedelta
import random

DB_NAME = 'home.db'

def populate_demo_data():
    print("🎬 Populating Home OS with demo data...\n")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Sample inventory items
    today = datetime.now().date()
    
    inventory_items = [
        # (name, category, qty, unit, storage, days_until_expiry, price, store)
        ('milk', 'Dairy', 1, 'gallon', 'fresh', 4, 4.99, 'Kroger'),
        ('eggs', 'Dairy', 1, 'carton', 'fresh', 18, 3.49, 'Walmart'),
        ('chicken', 'Meat', 2, 'lb', 'frozen', 120, 8.99, 'Costco'),
        ('spinach', 'Produce', 1, 'bag', 'fresh', 3, 2.99, 'Whole Foods'),
        ('rice', 'Pantry', 1, 'bag', 'pantry', 300, 12.99, 'Amazon'),
        ('bread', 'Bakery', 1, 'loaf', 'fresh', 5, 2.49, 'Kroger'),
        ('cheese', 'Dairy', 1, 'block', 'fresh', 10, 5.99, 'Trader Joes'),
        ('pasta', 'Pantry', 2, 'box', 'pantry', 200, 1.99, 'Walmart'),
        ('frozen spinach', 'Produce', 1, 'bag', 'frozen', 200, 2.49, 'Kroger'),
        ('chicken breast', 'Meat', 1.5, 'lb', 'fresh', 2, 7.99, 'Whole Foods'),
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
    
    print(f"✅ Added {len(inventory_items)} items to inventory")
    
    # Sample shopping list
    shopping_items = [
        ('apples', 3.99),
        ('orange juice', 4.49),
        ('yogurt', 2.99),
        ('carrots', 1.99),
        ('ground beef', 6.99),
    ]
    
    for item, price in shopping_items:
        cursor.execute('''
        INSERT INTO shopping_list (item_name, is_urgent, estimated_price)
        VALUES (?, ?, ?)
        ''', (item, 0, price))
    
    print(f"✅ Added {len(shopping_items)} items to shopping list")
    
    # Sample price history (last 30 days)
    price_history_items = [
        ('milk', [(4.99, 'Kroger'), (5.29, 'Walmart'), (4.79, 'Costco')]),
        ('eggs', [(3.49, 'Walmart'), (3.99, 'Kroger'), (3.29, 'Costco')]),
        ('chicken', [(8.99, 'Costco'), (9.49, 'Kroger'), (10.99, 'Whole Foods')]),
    ]
    
    for item_name, prices in price_history_items:
        for price, store in prices:
            days_ago = random.randint(1, 30)
            date = today - timedelta(days=days_ago)
            
            cursor.execute('''
            INSERT INTO price_history (item_name, price, store, quantity, unit, date_recorded)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (item_name, price, store, 1, 'unit', date))
    
    print("✅ Added price history data")
    
    # Sample meal plan (this week)
    meal_plan = [
        # (days_from_today, meal_type, recipe_name)
        (0, 'dinner', 'Grilled Chicken with Rice'),
        (0, 'lunch', 'Spinach Salad'),
        (1, 'breakfast', 'Scrambled Eggs'),
        (1, 'dinner', 'Pasta with Cheese'),
        (2, 'dinner', 'Chicken Stir Fry'),
        (3, 'lunch', 'Chicken Sandwich'),
        (4, 'dinner', 'Baked Chicken'),
    ]
    
    for days, meal_type, recipe in meal_plan:
        meal_date = today + timedelta(days=days)
        
        cursor.execute('''
        INSERT INTO meal_plan (date, meal_type, recipe_name, servings, calories, prep_time)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (meal_date, meal_type, recipe, 2, 500, 30))
    
    print(f"✅ Added {len(meal_plan)} meals to meal plan")
    
    # Sample nutrition data
    nutrition_data = [
        ('chicken breast', '100g', 165, 31, 0, 3.6, 0, 0, 74),
        ('rice', '100g', 130, 2.7, 28, 0.3, 0.4, 0, 1),
        ('spinach', '100g', 23, 2.9, 3.6, 0.4, 2.2, 0.4, 79),
        ('eggs', '1 large', 72, 6.3, 0.4, 5, 0, 0.2, 71),
        ('milk', '1 cup', 149, 7.7, 11.7, 7.9, 0, 12.3, 105),
    ]
    
    for item in nutrition_data:
        name, serving, cal, protein, carbs, fat, fiber, sugar, sodium = item
        
        cursor.execute('''
        INSERT INTO nutrition_data 
        (item_name, serving_size, calories, protein, carbs, fat, fiber, sugar, sodium, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, serving, cal, protein, carbs, fat, fiber, sugar, sodium, 'demo'))
    
    print(f"✅ Added nutrition data for {len(nutrition_data)} items")
    
    # Update budget with some spending
    cursor.execute('''
    UPDATE budget_settings
    SET current_spent = 150.50
    WHERE id = 1
    ''')
    
    print("✅ Set demo budget spending: $150.50 / $500.00")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("🎉 Demo data loaded successfully!")
    print("="*60)
    print("\n📋 What's in your demo system:")
    print(f"  • {len(inventory_items)} items in fridge")
    print(f"  • {len(shopping_items)} items on shopping list")
    print(f"  • {len(meal_plan)} meals planned")
    print(f"  • Price history for 3 items")
    print(f"  • Nutrition data for 5 items")
    print(f"  • Budget: $150.50 spent of $500.00 (30%)")
    print("\n🚀 Run 'streamlit run app.py' to see it in action!")
    print("="*60)

if __name__ == "__main__":
    populate_demo_data()
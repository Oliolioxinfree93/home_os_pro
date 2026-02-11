import json
import datetime
from datetime import timedelta
import requests
import sqlite3

API_KEY = "YOUR_API_KEY_HERE"  # <--- PASTE SPOONACULAR KEY HERE
DB_NAME = 'home.db'

def get_expiring_ingredients(days=7):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    today = datetime.date.today()
    limit_date = today + timedelta(days=days)
    
    # Logic: Get Fresh items expiring soon
    cursor.execute("""
        SELECT item_name FROM inventory 
        WHERE status='In Stock' 
        AND expiry_date <= ?
        AND storage != 'frozen' 
        AND storage != 'pantry'
    """, (limit_date,))
    
    rows = cursor.fetchall()
    conn.close()
    return list(set([row[0] for row in rows]))

def suggest_recipes():
    ingredients = get_expiring_ingredients()
    
    if not ingredients:
        return {"error": "No fresh food is expiring soon! Good job."}
    
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "apiKey": API_KEY,
        "ingredients": ",".join(ingredients),
        "number": 3,
        "ranking": 1,
        "ignorePantry": True
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {e}"}
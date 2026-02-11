import requests
import datetime
from datetime import timedelta

API_KEY = "YOUR_SPOONACULAR_KEY_HERE"

def suggest_recipes_from_list(ingredients):
    """Takes a list of ingredient names and returns recipe suggestions"""
    if not ingredients:
        return {"error": "No expiring ingredients found."}

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
            return {"error": f"API Error: {response.status_code}. Add Spoonacular API key to recipe_manager.py"}
    except Exception as e:
        return {"error": f"Connection Error: {e}"}

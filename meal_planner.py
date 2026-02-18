import sqlite3
import json
import requests
from datetime import datetime, timedelta

class MealPlanner:
    def __init__(self, db_name='home.db', api_key=None):
        self.db_name = db_name
        self.api_key = api_key  # Spoonacular API key
    
    def add_meal(self, date, meal_type, recipe_id=None, recipe_name=None, 
                 recipe_image=None, servings=1, ingredients=None):
        """
        Add a meal to the calendar
        meal_type: 'breakfast', 'lunch', 'dinner', 'snack'
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # If recipe_id provided, fetch details from API
        calories = None
        prep_time = None
        if recipe_id and self.api_key:
            recipe_details = self._fetch_recipe_details(recipe_id)
            if recipe_details:
                recipe_name = recipe_details['title']
                recipe_image = recipe_details['image']
                ingredients = json.dumps(recipe_details['ingredients'])
                calories = recipe_details.get('calories')
                prep_time = recipe_details.get('readyInMinutes')

        cursor.execute('''
        INSERT INTO meal_plan (date, meal_type, recipe_id, recipe_name,
                               recipe_image, servings, ingredients, calories, prep_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, meal_type, recipe_id, recipe_name, recipe_image,
              servings, ingredients, calories, prep_time))
        
        conn.commit()
        conn.close()
        print(f"✅ Added {recipe_name} to {meal_type} on {date}")
    
    def get_week_plan(self, start_date=None):
        """
        Get meal plan for a week starting from start_date
        """
        if not start_date:
            start_date = datetime.now().date()
        
        end_date = start_date + timedelta(days=6)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT date, meal_type, recipe_name, recipe_image, servings, 
               ingredients, calories, prep_time
        FROM meal_plan
        WHERE date BETWEEN ? AND ?
        ORDER BY date, 
                 CASE meal_type 
                     WHEN 'breakfast' THEN 1 
                     WHEN 'lunch' THEN 2 
                     WHEN 'dinner' THEN 3 
                     WHEN 'snack' THEN 4 
                 END
        ''', (start_date, end_date))
        
        meals = cursor.fetchall()
        conn.close()
        
        # Organize by day
        week_plan = {}
        for meal in meals:
            date = meal[0]
            if date not in week_plan:
                week_plan[date] = []
            
            week_plan[date].append({
                'meal_type': meal[1],
                'recipe_name': meal[2],
                'recipe_image': meal[3],
                'servings': meal[4],
                'ingredients': json.loads(meal[5]) if meal[5] else [],
                'calories': meal[6],
                'prep_time': meal[7]
            })
        
        return week_plan
    
    def generate_shopping_list_from_plan(self, start_date=None, days=7):
        """
        Generate shopping list from meal plan
        Checks what's already in inventory
        """
        if not start_date:
            start_date = datetime.now().date()
        
        end_date = start_date + timedelta(days=days-1)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Get all ingredients from planned meals
        cursor.execute('''
        SELECT ingredients FROM meal_plan
        WHERE date BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        all_ingredients = []
        for row in cursor.fetchall():
            if row[0]:
                ingredients = json.loads(row[0])
                all_ingredients.extend(ingredients)
        
        # Check what's in inventory
        cursor.execute('''
        SELECT item_name, quantity FROM inventory
        WHERE status = 'In Stock'
        ''')
        
        inventory_items = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Determine what needs to be bought
        shopping_needed = {}
        for ingredient in all_ingredients:
            ingredient_lower = ingredient.lower()
            
            # Check if we have it in inventory
            found_in_inventory = False
            for item_name, qty in inventory_items.items():
                if item_name in ingredient_lower or ingredient_lower in item_name:
                    if qty > 0:
                        found_in_inventory = True
                        break
            
            if not found_in_inventory:
                # Add to shopping list
                shopping_needed[ingredient] = shopping_needed.get(ingredient, 0) + 1
        
        # Add to shopping_list table
        for item, count in shopping_needed.items():
            # Check if already in shopping list
            cursor.execute("SELECT id FROM shopping_list WHERE item_name = ?", (item,))
            if not cursor.fetchone():
                cursor.execute('''
                INSERT INTO shopping_list (item_name, is_urgent)
                VALUES (?, 0)
                ''', (item,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Added {len(shopping_needed)} items to shopping list")
        return list(shopping_needed.keys())
    
    def _fetch_recipe_details(self, recipe_id):
        """
        Fetch recipe details from Spoonacular API
        """
        if not self.api_key:
            return None
        
        try:
            url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
            params = {
                'apiKey': self.api_key,
                'includeNutrition': True
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                
                # Extract ingredient names
                ingredients = [ing['name'] for ing in data.get('extendedIngredients', [])]
                
                # Get nutrition info
                calories = None
                if 'nutrition' in data and 'nutrients' in data['nutrition']:
                    for nutrient in data['nutrition']['nutrients']:
                        if nutrient['name'] == 'Calories':
                            calories = nutrient['amount']
                            break
                
                return {
                    'title': data.get('title'),
                    'image': data.get('image'),
                    'ingredients': ingredients,
                    'calories': calories,
                    'readyInMinutes': data.get('readyInMinutes')
                }
        except Exception as e:
            print(f"Error fetching recipe details: {e}")
        
        return None
    
    def delete_meal(self, meal_id):
        """Remove a meal from the plan"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM meal_plan WHERE id = ?", (meal_id,))
        conn.commit()
        conn.close()
    
    def get_nutrition_summary(self, date):
        """
        Get total nutrition for a specific day
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT SUM(calories) FROM meal_plan
        WHERE date = ?
        ''', (date,))
        
        total_calories = cursor.fetchone()[0] or 0
        conn.close()
        
        return {'total_calories': total_calories}


# Example usage
if __name__ == "__main__":
    planner = MealPlanner()
    
    # Add a meal
    today = datetime.now().date()
    planner.add_meal(
        date=today,
        meal_type='dinner',
        recipe_name='Chicken Stir Fry',
        servings=2,
        ingredients=json.dumps(['chicken', 'broccoli', 'soy sauce', 'rice'])
    )
    
    # Get week plan
    week = planner.get_week_plan()
    print(f"\nMeal plan: {week}")
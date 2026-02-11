import sqlite3
import requests
from datetime import datetime, timedelta

class NutritionTracker:
    def __init__(self, db_name='home.db', api_key=None):
        self.db_name = db_name
        self.api_key = api_key  # Spoonacular API key for nutrition lookup
    
    def add_nutrition_data(self, item_name, serving_size, calories, protein=0, 
                          carbs=0, fat=0, fiber=0, sugar=0, sodium=0, source='manual'):
        """
        Add or update nutrition information for an item
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT id FROM nutrition_data WHERE item_name = ?", (item_name,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute('''
            UPDATE nutrition_data
            SET serving_size=?, calories=?, protein=?, carbs=?, fat=?, 
                fiber=?, sugar=?, sodium=?, source=?, last_updated=CURRENT_TIMESTAMP
            WHERE item_name=?
            ''', (serving_size, calories, protein, carbs, fat, fiber, sugar, sodium, source, item_name))
        else:
            # Insert new
            cursor.execute('''
            INSERT INTO nutrition_data 
            (item_name, serving_size, calories, protein, carbs, fat, fiber, sugar, sodium, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item_name, serving_size, calories, protein, carbs, fat, fiber, sugar, sodium, source))
        
        conn.commit()
        conn.close()
        print(f"✅ Nutrition data saved for {item_name}")
    
    def lookup_nutrition_api(self, item_name):
        """
        Fetch nutrition data from Spoonacular API
        """
        if not self.api_key:
            return None
        
        try:
            url = "https://api.spoonacular.com/food/ingredients/search"
            params = {
                'apiKey': self.api_key,
                'query': item_name,
                'number': 1
            }
            
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get('results'):
                return None
            
            ingredient_id = data['results'][0]['id']
            
            # Get nutrition info
            url2 = f"https://api.spoonacular.com/food/ingredients/{ingredient_id}/information"
            params2 = {
                'apiKey': self.api_key,
                'amount': 100,
                'unit': 'grams'
            }
            
            response2 = requests.get(url2, params=params2)
            if response2.status_code != 200:
                return None
            
            nutrition_data = response2.json()
            nutrients = nutrition_data.get('nutrition', {}).get('nutrients', [])
            
            # Extract key nutrients
            nutrient_dict = {}
            for nutrient in nutrients:
                nutrient_dict[nutrient['name']] = nutrient['amount']
            
            result = {
                'item_name': item_name,
                'serving_size': '100g',
                'calories': nutrient_dict.get('Calories', 0),
                'protein': nutrient_dict.get('Protein', 0),
                'carbs': nutrient_dict.get('Carbohydrates', 0),
                'fat': nutrient_dict.get('Fat', 0),
                'fiber': nutrient_dict.get('Fiber', 0),
                'sugar': nutrient_dict.get('Sugar', 0),
                'sodium': nutrient_dict.get('Sodium', 0)
            }
            
            # Save to database
            self.add_nutrition_data(**result, source='api')
            
            return result
            
        except Exception as e:
            print(f"Error fetching nutrition data: {e}")
            return None
    
    def get_nutrition_info(self, item_name):
        """
        Get nutrition info from database, fetch from API if not found
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT serving_size, calories, protein, carbs, fat, fiber, sugar, sodium, source
        FROM nutrition_data
        WHERE item_name LIKE ?
        ORDER BY last_updated DESC
        LIMIT 1
        ''', (f'%{item_name}%',))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'item_name': item_name,
                'serving_size': result[0],
                'calories': result[1],
                'protein': result[2],
                'carbs': result[3],
                'fat': result[4],
                'fiber': result[5],
                'sugar': result[6],
                'sodium': result[7],
                'source': result[8]
            }
        else:
            # Try to fetch from API
            return self.lookup_nutrition_api(item_name)
    
    def calculate_meal_nutrition(self, ingredients):
        """
        Calculate total nutrition for a meal from ingredient list
        ingredients: list of dicts with 'name' and 'amount' (in grams)
        """
        total = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0,
            'sugar': 0,
            'sodium': 0
        }
        
        for ingredient in ingredients:
            name = ingredient['name']
            amount = ingredient.get('amount', 100)  # default 100g
            
            nutrition = self.get_nutrition_info(name)
            if nutrition:
                # Scale nutrition based on amount (assuming nutrition is per 100g)
                scale_factor = amount / 100
                
                total['calories'] += nutrition['calories'] * scale_factor
                total['protein'] += nutrition['protein'] * scale_factor
                total['carbs'] += nutrition['carbs'] * scale_factor
                total['fat'] += nutrition['fat'] * scale_factor
                total['fiber'] += nutrition['fiber'] * scale_factor
                total['sugar'] += nutrition['sugar'] * scale_factor
                total['sodium'] += nutrition['sodium'] * scale_factor
        
        return total
    
    def get_daily_nutrition(self, date=None):
        """
        Get total nutrition consumed for a specific day based on meal plan
        """
        if not date:
            date = datetime.now().date()
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Get meals for the day
        cursor.execute('''
        SELECT ingredients, servings FROM meal_plan
        WHERE date = ?
        ''', (date,))
        
        meals = cursor.fetchall()
        conn.close()
        
        total = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0,
            'sugar': 0,
            'sodium': 0
        }
        
        for meal in meals:
            if meal[0]:  # if ingredients exist
                import json
                ingredients = json.loads(meal[0])
                servings = meal[1] or 1
                
                # Calculate nutrition for each ingredient
                ingredient_list = [{'name': ing, 'amount': 100} for ing in ingredients]
                meal_nutrition = self.calculate_meal_nutrition(ingredient_list)
                
                # Add to total (multiplied by servings)
                for key in total.keys():
                    total[key] += meal_nutrition[key] * servings
        
        return total
    
    def set_nutrition_goals(self, calories=2000, protein=50, carbs=250, fat=70, fiber=25):
        """
        Set daily nutrition goals (could be expanded to user preferences table)
        """
        return {
            'calories': calories,
            'protein': protein,
            'carbs': carbs,
            'fat': fat,
            'fiber': fiber
        }
    
    def check_nutrition_goals(self, date=None):
        """
        Compare actual nutrition vs goals
        """
        daily_nutrition = self.get_daily_nutrition(date)
        goals = self.set_nutrition_goals()
        
        comparison = {}
        for key in ['calories', 'protein', 'carbs', 'fat', 'fiber']:
            actual = daily_nutrition[key]
            goal = goals[key]
            percentage = (actual / goal * 100) if goal > 0 else 0
            
            comparison[key] = {
                'actual': actual,
                'goal': goal,
                'percentage': percentage,
                'status': 'over' if percentage > 110 else 
                         'under' if percentage < 90 else 'good'
            }
        
        return comparison
    
    def get_macro_breakdown(self, date=None):
        """
        Get percentage breakdown of macronutrients (protein/carbs/fat)
        """
        daily = self.get_daily_nutrition(date)
        
        # Calories per gram: Protein=4, Carbs=4, Fat=9
        protein_cal = daily['protein'] * 4
        carbs_cal = daily['carbs'] * 4
        fat_cal = daily['fat'] * 9
        
        total_cal = protein_cal + carbs_cal + fat_cal
        
        if total_cal == 0:
            return {'protein': 0, 'carbs': 0, 'fat': 0}
        
        return {
            'protein': round(protein_cal / total_cal * 100, 1),
            'carbs': round(carbs_cal / total_cal * 100, 1),
            'fat': round(fat_cal / total_cal * 100, 1)
        }


# Example usage
if __name__ == "__main__":
    tracker = NutritionTracker()
    
    # Add nutrition data manually
    tracker.add_nutrition_data(
        item_name='chicken breast',
        serving_size='100g',
        calories=165,
        protein=31,
        carbs=0,
        fat=3.6
    )
    
    # Get nutrition info
    info = tracker.get_nutrition_info('chicken')
    print(f"Nutrition for chicken: {info}")
    
    # Calculate meal
    meal = [
        {'name': 'chicken', 'amount': 150},
        {'name': 'rice', 'amount': 200}
    ]
    total = tracker.calculate_meal_nutrition(meal)
    print(f"\nMeal nutrition: {total}")
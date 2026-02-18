import sqlite3
from datetime import datetime, timedelta
import json

class SavingsTracker:
    def __init__(self, db_name='home.db'):
        self.db_name = db_name
        
        # Economic values (customize these)
        self.RESTAURANT_MEAL_COST = 35.00  # Average cost per person eating out
        self.MEAL_PLANNER_RATE = 15.00     # Per hour
        self.BOOKKEEPER_RATE = 25.00       # Per hour
        self.GROCERY_DELIVERY_FEE = 10.00  # Saved by shopping yourself
    
    def calculate_monthly_savings(self, start_date=None):
        """
        Calculate total savings for the month
        """
        if not start_date:
            start_date = datetime.now().date().replace(day=1)
        
        # Calculate end of month
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1)
        
        savings = {
            'meal_planning_savings': self._calculate_meal_planning_savings(start_date, end_date),
            'smart_shopping_savings': self._calculate_smart_shopping_savings(start_date, end_date),
            'food_waste_prevention': self._calculate_food_waste_prevention(start_date, end_date),
            'price_comparison_savings': self._calculate_price_comparison_savings(start_date, end_date),
            'bulk_buying_savings': self._calculate_bulk_savings(start_date, end_date),
        }
        
        savings['total_monthly_savings'] = sum(savings.values())
        savings['annual_projection'] = savings['total_monthly_savings'] * 12
        savings['equivalent_salary'] = savings['annual_projection'] * 1.25  # Add 25% for after-tax equivalent
        
        return savings
    
    def _calculate_meal_planning_savings(self, start_date, end_date):
        """
        Calculate savings from meal planning vs eating out
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Count meals planned this month
        cursor.execute('''
        SELECT COUNT(*) FROM meal_plan
        WHERE date BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        meals_planned = cursor.fetchone()[0]
        conn.close()
        
        # Assume 80% of planned meals were actually cooked
        meals_cooked = int(meals_planned * 0.8)
        
        # Calculate savings vs eating out
        savings = meals_cooked * self.RESTAURANT_MEAL_COST
        
        return savings
    
    def _calculate_smart_shopping_savings(self, start_date, end_date):
        """
        Calculate savings from finding deals and lower prices
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Count shopping trips (saved delivery fees)
        cursor.execute('''
        SELECT COUNT(DISTINCT date_recorded) 
        FROM price_history
        WHERE date_recorded BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        shopping_trips = cursor.fetchone()[0]
        delivery_savings = shopping_trips * self.GROCERY_DELIVERY_FEE
        
        # Calculate price comparison savings
        # (Compare current prices vs previous higher prices)
        cursor.execute('''
        SELECT item_name, price FROM price_history
        WHERE date_recorded BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        recent_purchases = cursor.fetchall()
        comparison_savings = 0
        
        for item_name, price in recent_purchases:
            # Get average price from past 6 months
            cursor.execute('''
            SELECT AVG(price) FROM price_history
            WHERE item_name = ? 
            AND date_recorded < ?
            AND date_recorded > ?
            ''', (item_name, start_date, start_date - timedelta(days=180)))
            
            avg_past_price = cursor.fetchone()[0]
            if avg_past_price and avg_past_price > price:
                comparison_savings += (avg_past_price - price)
        
        conn.close()
        
        return delivery_savings + comparison_savings
    
    def _calculate_food_waste_prevention(self, start_date, end_date):
        """
        Calculate value of food that was saved from expiring
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Items that were consumed before expiring
        cursor.execute('''
        SELECT SUM(price) FROM inventory
        WHERE status = 'Consumed'
        AND date_added BETWEEN ? AND ?
        AND expiry_date >= date_added
        ''', (start_date, end_date))
        
        result = cursor.fetchone()[0]
        prevented_waste = result if result else 0
        
        conn.close()
        
        return prevented_waste
    
    def _calculate_price_comparison_savings(self, start_date, end_date):
        """
        Savings from choosing cheaper stores
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Get all items bought this month
        cursor.execute('''
        SELECT DISTINCT item_name FROM price_history
        WHERE date_recorded BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        items = cursor.fetchall()
        total_savings = 0
        
        for item in items:
            item_name = item[0]
            
            # Get price paid
            cursor.execute('''
            SELECT price, store FROM price_history
            WHERE item_name = ?
            AND date_recorded BETWEEN ? AND ?
            ORDER BY date_recorded DESC
            LIMIT 1
            ''', (item_name, start_date, end_date))
            
            current = cursor.fetchone()
            if not current:
                continue
            
            price_paid, store_used = current
            
            # Get highest price from other stores (last 90 days)
            if store_used:
                cursor.execute('''
                SELECT MAX(price) FROM price_history
                WHERE item_name = ?
                AND store != ?
                AND date_recorded > ?
                ''', (item_name, store_used, start_date - timedelta(days=90)))
            else:
                cursor.execute('''
                SELECT MAX(price) FROM price_history
                WHERE item_name = ?
                AND date_recorded > ?
                ''', (item_name, start_date - timedelta(days=90)))
            
            max_other_price = cursor.fetchone()[0]
            if max_other_price and max_other_price > price_paid:
                total_savings += (max_other_price - price_paid)
        
        conn.close()
        return total_savings
    
    def _calculate_bulk_savings(self, start_date, end_date):
        """
        Estimate savings from bulk buying
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Look for bulk purchases (quantity > 1 or from stores like Costco)
        cursor.execute('''
        SELECT SUM(price * 0.15) FROM price_history
        WHERE date_recorded BETWEEN ? AND ?
        AND (quantity > 1 OR store LIKE '%Costco%' OR store LIKE '%Sam%')
        ''', (start_date, end_date))
        
        result = cursor.fetchone()[0]
        bulk_savings = result if result else 0
        
        conn.close()
        
        # Estimate 15% savings on bulk items
        return bulk_savings
    
    def get_contribution_value(self, start_date=None):
        """
        Calculate the economic value of household management work
        """
        if not start_date:
            start_date = datetime.now().date().replace(day=1)
        
        end_date = start_date + timedelta(days=30)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Count meals prepared
        cursor.execute('''
        SELECT COUNT(*) FROM meal_plan
        WHERE date BETWEEN ? AND ?
        ''', (start_date, end_date))
        meals_planned = cursor.fetchone()[0]
        meals_cooked = int(meals_planned * 0.8)
        
        # Count shopping trips
        cursor.execute('''
        SELECT COUNT(DISTINCT date_recorded) FROM price_history
        WHERE date_recorded BETWEEN ? AND ?
        ''', (start_date, end_date))
        shopping_trips = cursor.fetchone()[0]
        
        conn.close()
        
        # Calculate economic value
        contributions = {
            'meals_prepared': {
                'count': meals_cooked,
                'value': meals_cooked * self.RESTAURANT_MEAL_COST,
                'description': 'Saved vs. eating out'
            },
            'meal_planning_hours': {
                'hours': meals_planned / 7 * 1,  # ~1 hour per week of planning
                'value': (meals_planned / 7) * self.MEAL_PLANNER_RATE,
                'description': 'Professional meal planner rate'
            },
            'shopping_trips': {
                'count': shopping_trips,
                'value': shopping_trips * self.GROCERY_DELIVERY_FEE,
                'description': 'Saved delivery fees'
            },
            'budget_management_hours': {
                'hours': 4,  # Estimated hours per month
                'value': 4 * self.BOOKKEEPER_RATE,
                'description': 'Bookkeeper rate'
            }
        }
        
        total_value = sum(item['value'] for item in contributions.values())
        contributions['total_value'] = total_value
        
        return contributions
    
    def get_achievements(self, start_date=None):
        """
        Get achievements earned this month
        """
        if not start_date:
            start_date = datetime.now().date().replace(day=1)
        
        savings = self.calculate_monthly_savings(start_date)
        achievements = []
        
        # Define achievement thresholds
        if savings['food_waste_prevention'] >= 50:
            achievements.append({
                'title': '🏆 Waste Warrior',
                'description': f'Prevented ${savings["food_waste_prevention"]:.2f} in food waste!',
                'icon': '♻️'
            })
        
        if savings['smart_shopping_savings'] >= 75:
            achievements.append({
                'title': '🏆 Deal Hunter',
                'description': f'Found ${savings["smart_shopping_savings"]:.2f} in savings!',
                'icon': '🎯'
            })
        
        if savings['meal_planning_savings'] >= 300:
            achievements.append({
                'title': '🏆 Meal Prep Master',
                'description': f'Saved ${savings["meal_planning_savings"]:.2f} by cooking at home!',
                'icon': '👨‍🍳'
            })
        
        if savings['total_monthly_savings'] >= 300:
            achievements.append({
                'title': '🏆 Budget Hero',
                'description': f'Total savings: ${savings["total_monthly_savings"]:.2f}!',
                'icon': '💪'
            })
        
        return achievements
    
    def generate_monthly_report(self, start_date=None):
        """
        Generate a comprehensive monthly savings report
        """
        if not start_date:
            start_date = datetime.now().date().replace(day=1)
        
        savings = self.calculate_monthly_savings(start_date)
        contributions = self.get_contribution_value(start_date)
        achievements = self.get_achievements(start_date)
        
        report = {
            'month': start_date.strftime('%B %Y'),
            'savings': savings,
            'contributions': contributions,
            'achievements': achievements,
            'summary': f"This month, you added ${contributions['total_value']:.2f} in economic value to your household!"
        }
        
        return report


# Example usage
if __name__ == "__main__":
    tracker = SavingsTracker()
    
    # Get monthly savings
    savings = tracker.calculate_monthly_savings()
    print(f"Total Monthly Savings: ${savings['total_monthly_savings']:.2f}")
    print(f"Annual Projection: ${savings['annual_projection']:.2f}")
    print(f"Equivalent Salary: ${savings['equivalent_salary']:.2f}")
    
    # Get contributions
    contributions = tracker.get_contribution_value()
    print(f"\nTotal Household Value Added: ${contributions['total_value']:.2f}")
    
    # Get achievements
    achievements = tracker.get_achievements()
    print(f"\nAchievements Earned: {len(achievements)}")
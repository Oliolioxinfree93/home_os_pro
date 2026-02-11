import sqlite3
from datetime import datetime, timedelta
import statistics

class BudgetManager:
    def __init__(self, db_name='home.db'):
        self.db_name = db_name
    
    def record_purchase(self, item_name, price, quantity=1, unit='unit', store=None, barcode=None):
        """
        Record a purchase in price history
        Returns: alert_message if budget threshold exceeded
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Add to price history
        cursor.execute('''
        INSERT INTO price_history (item_name, price, store, quantity, unit, date_recorded, barcode)
        VALUES (?, ?, ?, ?, ?, date('now'), ?)
        ''', (item_name, price, store, quantity, unit, barcode))
        
        # Update budget spending - FIXED: Added the parameter
        cursor.execute('''
        UPDATE budget_settings
        SET current_spent = current_spent + ?
        WHERE id = 1
        ''', (price,))
        
        # Check if alert needed
        cursor.execute('''
        SELECT budget_limit, alert_threshold, current_spent
        FROM budget_settings WHERE id = 1
        ''')
        
        budget_data = cursor.fetchone()
        conn.commit()
        conn.close()
        
        if budget_data:
            limit, threshold, spent = budget_data
            percentage = (spent / limit) if limit > 0 else 0
            
            if percentage >= threshold:
                return {
                    'alert': True,
                    'message': f'⚠️ Budget Alert: ${spent:.2f} / ${limit:.2f} ({percentage*100:.1f}%)',
                    'spent': spent,
                    'limit': limit,
                    'percentage': percentage
                }
        
        return None
    
    def get_budget_status(self):
        """
        Get current budget status
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT period, budget_limit, current_spent, alert_threshold, start_date
        FROM budget_settings WHERE id = 1
        ''')
        
        data = cursor.fetchone()
        conn.close()
        
        if data:
            period, limit, spent, threshold, start_date = data
            percentage = (spent / limit * 100) if limit > 0 else 0
            remaining = limit - spent
            
            return {
                'period': period,
                'limit': limit,
                'spent': spent,
                'remaining': remaining,
                'percentage': percentage,
                'threshold': threshold * 100,
                'start_date': start_date,
                'status': 'over_budget' if spent > limit else 
                         'warning' if percentage >= threshold * 100 else 'good'
            }
        
        return None
    
    def set_budget(self, amount, period='monthly'):
        """
        Set or update budget limit
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE budget_settings
        SET budget_limit = ?, period = ?, start_date = date('now'), current_spent = 0
        WHERE id = 1
        ''', (amount, period))
        
        conn.commit()
        conn.close()
        print(f"✅ Budget set to ${amount:.2f} per {period}")
    
    def reset_budget_period(self):
        """
        Reset spending for new budget period
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE budget_settings
        SET current_spent = 0, start_date = date('now')
        WHERE id = 1
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Budget period reset")
    
    def get_price_trends(self, item_name, days=90):
        """
        Get price history and trends for an item
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        date_limit = datetime.now().date() - timedelta(days=days)
        
        cursor.execute('''
        SELECT price, store, date_recorded
        FROM price_history
        WHERE item_name LIKE ? AND date_recorded >= ?
        ORDER BY date_recorded DESC
        ''', (f'%{item_name}%', date_limit))
        
        records = cursor.fetchall()
        conn.close()
        
        if not records:
            return None
        
        prices = [r[0] for r in records]
        
        return {
            'item_name': item_name,
            'current_price': prices[0],
            'average_price': statistics.mean(prices),
            'min_price': min(prices),
            'max_price': max(prices),
            'price_change': ((prices[0] - prices[-1]) / prices[-1] * 100) if len(prices) > 1 else 0,
            'stores': list(set([r[1] for r in records if r[1]])),
            'history': [{'price': r[0], 'store': r[1], 'date': r[2]} for r in records]
        }
    
    def get_cheapest_store(self, item_name):
        """
        Find which store has the best price for an item
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT store, AVG(price) as avg_price
        FROM price_history
        WHERE item_name LIKE ? AND store IS NOT NULL
        GROUP BY store
        ORDER BY avg_price ASC
        LIMIT 1
        ''', (f'%{item_name}%',))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {'store': result[0], 'avg_price': result[1]}
        
        return None
    
    def get_spending_by_category(self, days=30):
        """
        Get spending breakdown by category
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        date_limit = datetime.now().date() - timedelta(days=days)
        
        cursor.execute('''
        SELECT i.category, SUM(ph.price) as total
        FROM price_history ph
        LEFT JOIN inventory i ON ph.item_name = i.item_name
        WHERE ph.date_recorded >= ?
        GROUP BY i.category
        ORDER BY total DESC
        ''', (date_limit,))
        
        categories = cursor.fetchall()
        conn.close()
        
        return [{'category': c[0] if c[0] else 'Other', 'spent': c[1]} for c in categories]
    
    def estimate_shopping_list_cost(self):
        """
        Estimate total cost of current shopping list based on price history
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_name FROM shopping_list")
        items = cursor.fetchall()
        
        total_estimate = 0
        item_estimates = []
        
        for item in items:
            item_name = item[0]
            
            # Get average price from history
            cursor.execute('''
            SELECT AVG(price) FROM price_history
            WHERE item_name LIKE ?
            ''', (f'%{item_name}%',))
            
            avg_price = cursor.fetchone()[0]
            
            if avg_price:
                total_estimate += avg_price
                item_estimates.append({
                    'item': item_name,
                    'estimated_price': avg_price
                })
            else:
                # No history, use default estimate
                item_estimates.append({
                    'item': item_name,
                    'estimated_price': 5.00  # Default estimate
                })
                total_estimate += 5.00
        
        conn.close()
        
        return {
            'total_estimate': total_estimate,
            'item_count': len(items),
            'items': item_estimates
        }


# Example usage
if __name__ == "__main__":
    budget = BudgetManager()
    
    # Set budget
    budget.set_budget(500.00, 'monthly')
    
    # Record a purchase
    alert = budget.record_purchase('milk', 4.99, store='Kroger')
    if alert:
        print(alert['message'])
    
    # Get status
    status = budget.get_budget_status()
    print(f"\nBudget Status: ${status['spent']:.2f} / ${status['limit']:.2f}")
    print(f"Remaining: ${status['remaining']:.2f}")
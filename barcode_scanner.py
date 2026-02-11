import requests
import json

class BarcodeScanner:
    """
    Uses Open Food Facts API (free, no key required) to lookup product info by barcode
    """
    
    def __init__(self):
        self.api_url = "https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    
    def lookup_barcode(self, barcode):
        """
        Lookup product by barcode (UPC/EAN)
        Returns: dict with product info or None if not found
        """
        try:
            url = self.api_url.format(barcode=barcode)
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 1:  # Product found
                    product = data['product']
                    
                    # Extract relevant data
                    result = {
                        'barcode': barcode,
                        'name': product.get('product_name', 'Unknown Product'),
                        'brand': product.get('brands', ''),
                        'categories': product.get('categories', ''),
                        'quantity': product.get('quantity', ''),
                        'image_url': product.get('image_url', ''),
                        
                        # Nutrition data (per 100g usually)
                        'nutrition': {
                            'calories': product.get('nutriments', {}).get('energy-kcal_100g'),
                            'protein': product.get('nutriments', {}).get('proteins_100g'),
                            'carbs': product.get('nutriments', {}).get('carbohydrates_100g'),
                            'fat': product.get('nutriments', {}).get('fat_100g'),
                            'fiber': product.get('nutriments', {}).get('fiber_100g'),
                            'sugar': product.get('nutriments', {}).get('sugars_100g'),
                            'sodium': product.get('nutriments', {}).get('sodium_100g')
                        }
                    }
                    
                    # Determine category from Open Food Facts categories
                    category = self._categorize(product.get('categories', ''))
                    result['category'] = category
                    
                    return result
                else:
                    return None
                    
        except Exception as e:
            print(f"Error looking up barcode: {e}")
            return None
    
    def _categorize(self, categories_string):
        """
        Map Open Food Facts categories to our internal categories
        """
        categories_lower = categories_string.lower()
        
        if any(word in categories_lower for word in ['milk', 'dairy', 'cheese', 'yogurt', 'cream']):
            return 'Dairy'
        elif any(word in categories_lower for word in ['meat', 'chicken', 'beef', 'pork', 'poultry']):
            return 'Meat'
        elif any(word in categories_lower for word in ['vegetable', 'fruit', 'produce']):
            return 'Produce'
        elif any(word in categories_lower for word in ['bread', 'bakery', 'pastries']):
            return 'Bakery'
        elif any(word in categories_lower for word in ['canned', 'pasta', 'rice', 'grain', 'cereal']):
            return 'Pantry'
        elif any(word in categories_lower for word in ['frozen']):
            return 'Frozen'
        elif any(word in categories_lower for word in ['beverage', 'drink', 'juice', 'soda']):
            return 'Beverages'
        elif any(word in categories_lower for word in ['snack', 'chips', 'cookies']):
            return 'Snacks'
        else:
            return 'Other'
    
    def search_product(self, search_term):
        """
        Search for products by name (useful for finding barcodes)
        """
        try:
            url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={search_term}&json=1&page_size=5"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                products = []
                
                for product in data.get('products', [])[:5]:
                    products.append({
                        'name': product.get('product_name', 'Unknown'),
                        'brand': product.get('brands', ''),
                        'barcode': product.get('code', ''),
                        'image': product.get('image_url', '')
                    })
                
                return products
            return []
            
        except Exception as e:
            print(f"Error searching products: {e}")
            return []


# Example usage and testing
if __name__ == "__main__":
    scanner = BarcodeScanner()
    
    # Test with a real barcode (Coca-Cola example)
    print("Testing barcode scanner...")
    result = scanner.lookup_barcode("5449000000996")
    
    if result:
        print(f"\n✅ Found: {result['name']}")
        print(f"Brand: {result['brand']}")
        print(f"Category: {result['category']}")
        print(f"Nutrition: {result['nutrition']}")
    else:
        print("❌ Product not found")
    
    # Test search
    print("\nSearching for 'organic milk'...")
    results = scanner.search_product("organic milk")
    for i, product in enumerate(results, 1):
        print(f"{i}. {product['name']} - {product['brand']} (Barcode: {product['barcode']})")
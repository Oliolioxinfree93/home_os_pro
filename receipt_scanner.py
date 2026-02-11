import google.generativeai as genai
import json
import PIL.Image
from datetime import datetime

# Configure your API Key (Get one at aistudio.google.com)
# It's free for personal rate limits
GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY"

class ReceiptScanner:
    def __init__(self):
        if GOOGLE_API_KEY != "YOUR_GEMINI_API_KEY":
            genai.configure(api_key=GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.active = True
        else:
            self.active = False

    def scan_receipt(self, image_file):
        """
        Takes a Streamlit uploaded file (image), sends to AI, 
        returns a list of items found.
        """
        if not self.active:
            return {"error": "API Key missing. Please configure receipt_scanner.py"}

        try:
            # 1. Prepare Image
            img = PIL.Image.open(image_file)

            # 2. The Prompt (The "Brain" instructions)
            prompt = """
            Analyze this receipt image. Extract all purchased grocery items.
            Return ONLY a valid JSON array of objects.
            Each object must have:
            - "item": (string) Clean name of the item (e.g., "Milk", "Eggs")
            - "price": (float) Price of the item
            - "qty": (int) Quantity (default to 1 if not specified)
            - "category": (string) Guess the category (Dairy, Produce, Meat, Pantry, Other)
            
            Do not include subtotal, tax, or payment info. 
            If the image is not a receipt, return {"error": "Not a receipt"}.
            JSON:
            """

            # 3. Call AI
            response = self.model.generate_content([prompt, img])
            
            # 4. Clean & Parse JSON
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw_text)
            
            return data

        except Exception as e:
            return {"error": f"Scan failed: {str(e)}"}

# Mock function for testing without API
    def mock_scan(self):
        return [
            {"item": "Organic Bananas", "price": 1.29, "qty": 1, "category": "Produce"},
            {"item": "Sourdough Bread", "price": 4.50, "qty": 1, "category": "Bakery"},
            {"item": "Almond Milk", "price": 3.99, "qty": 1, "category": "Dairy"},
            {"item": "Chicken Breast", "price": 12.45, "qty": 1, "category": "Meat"}
        ]
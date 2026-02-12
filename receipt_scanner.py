import google.generativeai as genai
import json
import PIL.Image
import streamlit as st

class ReceiptScanner:
    def __init__(self):
        try:
            self.api_key = st.secrets["GOOGLE_API_KEY"]
            genai.configure(api_key=self.api_key)
            # Use the correct current model name
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            self.active = True
        except Exception as e:
            self.active = False
            print(f"Scanner Init Error: {e}")

    def scan_receipt(self, image_file):
        if not self.active:
            return {"error": "API Key missing. Add GOOGLE_API_KEY to Streamlit Secrets."}

        try:
            img = PIL.Image.open(image_file)
            prompt = """
            Analyze this receipt image. Extract all grocery/food items only.
            Ignore taxes, totals, subtotals, fees, and store info lines.
            Return ONLY a valid JSON array of objects.
            Format:
            [
              {"item": "Milk", "price": 4.99, "qty": 1, "category": "Dairy"},
              {"item": "Chicken Breast", "price": 8.99, "qty": 1, "category": "Meat"}
            ]
            Categories must be one of: Dairy, Meat, Produce, Bakery, Pantry, Frozen, Beverages, Snacks, Other
            Return ONLY the JSON array. No markdown, no explanation, no extra text.
            """
            response = self.model.generate_content([prompt, img])
            raw_text = response.text.strip()
            # Clean up any markdown formatting
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            raw_text = raw_text.strip()
            return json.loads(raw_text)

        except json.JSONDecodeError:
            return {"error": "Could not read receipt. Try a clearer photo with better lighting."}
        except Exception as e:
            return {"error": f"Scan failed: {str(e)}"}

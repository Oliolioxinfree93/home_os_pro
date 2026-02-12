import json
import PIL.Image
import streamlit as st
import base64
import requests
import io

class ReceiptScanner:
    def __init__(self):
        try:
            self.api_key = st.secrets["GOOGLE_API_KEY"]
            self.active = True
        except Exception as e:
            self.active = False
            print(f"Scanner Init Error: {e}")

    def scan_receipt(self, image_file):
        if not self.active:
            return {"error": "API Key missing. Add GOOGLE_API_KEY to Streamlit Secrets."}

        try:
            # Convert image to base64
            img = PIL.Image.open(image_file)
            img.thumbnail((1024, 1024))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            prompt = """You are reading a grocery store receipt. Many receipts (especially Walmart) 
use abbreviated or coded product names. Your job is to decode them into real food names.

Examples of Walmart abbreviations to decode:
- "GV WHL MLK 1G" → "Whole Milk 1 Gallon"
- "FZ CHKN BRST" → "Frozen Chicken Breast"  
- "BNLS SKNLS CKN" → "Boneless Skinless Chicken"
- "GV SLCD WHT BRD" → "White Bread"
- "LG EGGS 18CT" → "Eggs 18 count"
- "BTRMLK PNCKE MX" → "Buttermilk Pancake Mix"
- "GV" or "SE" or "MM" at start = store brand, ignore the prefix
- Numbers at end like "1G" "2L" "32OZ" = size, include it

Rules:
1. Extract ONLY food and grocery items
2. Skip: taxes, fees, totals, subtotals, rewards, store name, cashier info
3. Decode abbreviations into plain English product names
4. If you cannot decode something, make your best guess based on context
5. Include the price for each item

Return ONLY a valid JSON array:
[{"item": "Whole Milk 1 Gallon", "price": 3.98, "qty": 1, "category": "Dairy"}]

Categories: Dairy, Meat, Produce, Bakery, Pantry, Frozen, Beverages, Snacks, Other

Return ONLY the JSON array. No markdown, no explanation, no extra text."""

            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={self.api_key}"

            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": img_base64
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1  # Low temperature = more precise, less creative
                }
            }

            response = requests.post(url, json=payload)

            if response.status_code != 200:
                return {"error": f"API Error {response.status_code}: {response.text[:200]}"}

            result = response.json()
            raw_text = result['candidates'][0]['content']['parts'][0]['text'].strip()

            # Clean markdown if present
            if "```" in raw_text:
                parts = raw_text.split("```")
                raw_text = parts[1] if len(parts) > 1 else parts[0]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            raw_text = raw_text.strip()

            items = json.loads(raw_text)
            
            # Clean up item names — remove common store brand prefixes
            prefixes_to_remove = ["GV ", "SE ", "MM ", "EQ ", "MV ", "PL "]
            for item in items:
                name = item['item']
                for prefix in prefixes_to_remove:
                    if name.upper().startswith(prefix):
                        name = name[len(prefix):]
                item['item'] = name.title().strip()
            
            return items

        except json.JSONDecodeError:
            return {"error": "Could not read receipt. Try a clearer, well-lit photo."}
        except Exception as e:
            return {"error": f"Scan failed: {str(e)}"}

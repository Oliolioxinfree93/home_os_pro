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
            self.model = "models/gemini-2.0-flash"
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

            prompt = """Analyze this receipt image. Extract all grocery/food items only.
Ignore taxes, totals, subtotals, fees, and store info lines.
Return ONLY a valid JSON array of objects like this:
[{"item": "Milk", "price": 4.99, "qty": 1, "category": "Dairy"}]
Categories: Dairy, Meat, Produce, Bakery, Pantry, Frozen, Beverages, Snacks, Other
Return ONLY the JSON array. No markdown, no explanation."""

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
                }]
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

            return json.loads(raw_text)

        except json.JSONDecodeError:
            return {"error": "Could not read receipt. Try a clearer photo with better lighting."}
        except Exception as e:
            return {"error": f"Scan failed: {str(e)}"}

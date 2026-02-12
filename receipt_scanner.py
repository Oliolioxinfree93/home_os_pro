import google.generativeai as genai
import json
import PIL.Image
import streamlit as st

class ReceiptScanner:
    def __init__(self):
        try:
            self.api_key = st.secrets["GOOGLE_API_KEY"]
            genai.configure(api_key=self.api_key)
            # FIXED: Using correct model name
            self.model = genai.GenerativeModel('gemini-1.5-flash')
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
            Analyze this receipt image. Extract all grocery items.
            Return ONLY a valid JSON array of objects.
            Format:
            [
              {"item": "Milk", "price": 4.99, "qty": 1, "category": "Dairy"},
              ...
            ]
            Return ONLY the JSON. No markdown formatting. No explanation.
            """
            response = self.model.generate_content([prompt, img])
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(raw_text)

        except Exception as e:
            return {"error": f"Scan failed: {str(e)}"}

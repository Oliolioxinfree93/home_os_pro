import google.generativeai as genai
import json
import PIL.Image
import streamlit as st

class ReceiptScanner:
    def __init__(self):
        try:
            # 1. Get Key from Secrets
            self.api_key = st.secrets["GOOGLE_API_KEY"]
            genai.configure(api_key=self.api_key)
            
            # 2. Use the exact model name from your list
            # Using Gemini 3 Flash for maximum speed and accuracy
            self.model = genai.GenerativeModel('models/gemini-3-flash-preview')
            self.active = True
        except Exception as e:
            self.active = False
            print(f"Scanner Init Error: {e}")

    def scan_receipt(self, image_file):
        if not self.active:
            return {"error": "API Key missing. Check Streamlit Secrets."}

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
            Return ONLY the JSON. No markdown formatting.
            """

            # Call the AI
            response = self.model.generate_content([prompt, img])
            
            # Clean up the response
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            
            return json.loads(raw_text)

        except Exception as e:
            return {"error": f"Scan failed: {str(e)}"}

import google.generativeai as genai
import json
import PIL.Image
import streamlit as st

class ReceiptScanner:
    def __init__(self):
        try:
            self.api_key = st.secrets["GOOGLE_API_KEY"]
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.active = True
        except Exception as e:
            self.active = False
            print(f"Scanner Init Error: {e}")

    def list_available_models(self):
        """Helper to debug what models the server sees"""
        try:
            models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models.append(m.name)
            return models
        except Exception as e:
            return [f"Error listing models: {str(e)}"]

    def scan_receipt(self, image_file):
        if not self.active:
            return {"error": "API Key missing. Check Streamlit Secrets."}

        try:
            img = PIL.Image.open(image_file)

            prompt = """
            Analyze this receipt image. Extract all purchased grocery items.
            Return ONLY a valid JSON array of objects.
            Each object must have:
            - "item": (string) Clean name (e.g., "Milk")
            - "price": (float) Price
            - "qty": (int) Quantity (default 1)
            - "category": (string) Guess category (Dairy, Produce, Meat, Pantry, Other)
            
            Return ONLY the JSON. No markdown formatting.
            """

            response = self.model.generate_content([prompt, img])
            
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)

        except Exception as e:
            # --- DEBUG BLOCK ---
            # If scan fails, tell the user what models ARE available
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg:
                available = self.list_available_models()
                return {"error": f"Model 1.5-Flash not found. Available models: {', '.join(available)}"}
            
            return {"error": f"Scan failed: {error_msg}"}

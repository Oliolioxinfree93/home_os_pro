import google.generativeai as genai
import json
import PIL.Image
import streamlit as st

class ReceiptScanner:
    def __init__(self):
        try:
            self.api_key = st.secrets["GOOGLE_API_KEY"]
            genai.configure(api_key=self.api_key)
            self.active = True
        except Exception as e:
            self.active = False
            print(f"Scanner Init Error: {e}")

    def get_available_models(self):
        """
        DIAGNOSTIC: Asks Google 'What models can I use?'
        """
        try:
            valid_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    valid_models.append(m.name)
            return valid_models
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

            # 1. Try the most stable model first
            # Note: We use the full path 'models/gemini-1.5-flash'
            try:
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                response = model.generate_content([prompt, img])
            except Exception as e:
                # 2. IF FAILED: Run Diagnostic
                available = self.get_available_models()
                return {"error": f"❌ Model Failed. \n\nYOUR AVAILABLE MODELS:\n" + "\n".join(available)}

            # 3. Clean and Parse
            text = response.text.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(text)
            except:
                return {"error": "AI response was not valid JSON."}

        except Exception as e:
            return {"error": f"Critical Error: {str(e)}"}

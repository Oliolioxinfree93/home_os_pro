import google.generativeai as genai
import json
import PIL.Image
import streamlit as st

class ReceiptScanner:
    def __init__(self):
        try:
            # 1. Get API Key securely from Streamlit Cloud
            self.api_key = st.secrets["GOOGLE_API_KEY"]
            genai.configure(api_key=self.api_key)
            self.active = True
        except Exception as e:
            self.active = False
            print(f"Scanner Init Error: {e}")

    def scan_receipt(self, image_file):
        """
        Scans a receipt image using Google Gemini Vision.
        Returns a JSON list of items found.
        """
        if not self.active:
            return {"error": "API Key missing. Please add GOOGLE_API_KEY to Streamlit Secrets."}

        try:
            # 1. Load the image
            img = PIL.Image.open(image_file)

            # 2. The Prompt for the AI
            prompt = """
            You are a receipt scanner for a home inventory app.
            Analyze this image. Extract all purchased grocery items.
            
            Return ONLY a raw JSON array. Do not use Markdown code blocks.
            
            Each object in the array must have:
            - "item": (string) The clean name of the product (e.g., "Organic Bananas").
            - "price": (float) The price of the item. If unknown, use 0.0.
            - "qty": (int) The quantity found. Default to 1.
            - "category": (string) One of: [Dairy, Produce, Meat, Pantry, Bakery, Frozen, Other].
            
            Ignore tax, subtotal, and payment details.
            """

            # 3. Model Fallback Logic (The "Safety Net")
            # We try the fastest model first. If it fails (404/Not Found), we try the next one.
            models_to_try = [
                'gemini-1.5-flash',  # Fast & Cheap (Best for receipts)
                'gemini-1.5-pro',    # Smarter but slower
                'gemini-pro-vision', # Older vision model
                'gemini-pro'         # Standard text/multimodal
            ]

            response = None
            last_error = None

            for model_name in models_to_try:
                try:
                    # Initialize the specific model
                    model = genai.GenerativeModel(model_name)
                    
                    # Attempt to generate content
                    response = model.generate_content([prompt, img])
                    
                    # If we get here, it worked! Break the loop.
                    break
                except Exception as e:
                    # If this model failed, save the error and try the next one
                    last_error = e
                    continue

            # 4. If all models failed, return the error
            if not response:
                return {"error": f"All AI models failed. Last error: {str(last_error)}"}

            # 5. Clean and Parse the JSON
            # AI sometimes wraps the response in ```json ... ```. We strip that out.
            raw_text = response.text
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(clean_text)
                return data
            except json.JSONDecodeError:
                return {"error": "AI response was not valid JSON. Try again."}

        except Exception as e:
            return {"error": f"Critical Scan Error: {str(e)}"}

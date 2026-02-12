import requests
import json
import streamlit as st

def suggest_recipes_from_list(ingredients, lang='en'):
    """
    Uses Gemini to suggest recipes based on expiring ingredients.
    Returns list of recipe dicts compatible with existing app UI.
    """
    if not ingredients:
        return {"error": "No expiring ingredients found."}

    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except Exception:
        return {"error": "GOOGLE_API_KEY missing from Streamlit Secrets."}

    # Language-specific instructions
    if lang == 'es':
        language_instruction = "Responde en español. Sugiere comidas latinoamericanas o mexicanas cuando sea apropiado."
        cuisine_note = "Prioriza recetas latinoamericanas, mexicanas, o familiares para hogares hispanohablantes."
    else:
        language_instruction = "Respond in English."
        cuisine_note = "Suggest practical home-cooking recipes, not overly fancy dishes."

    ingredients_str = ", ".join(ingredients)

    prompt = f"""You are a helpful home cooking assistant. {language_instruction}

A home cook has these ingredients that need to be used soon:
{ingredients_str}

{cuisine_note}

Suggest exactly 3 recipes that use as many of these ingredients as possible.

Return ONLY a valid JSON array with exactly this structure:
[
  {{
    "id": 1,
    "title": "Recipe Name",
    "image": "https://via.placeholder.com/150x100/FF6B6B/white?text=Recipe",
    "usedIngredients": [
      {{"name": "ingredient1"}},
      {{"name": "ingredient2"}}
    ],
    "missedIngredients": [
      {{"name": "ingredient3"}}
    ],
    "instructions": "Brief 2-3 sentence description of how to make it.",
    "time": "30 minutes",
    "difficulty": "Easy"
  }}
]

Rules:
- usedIngredients = ingredients from the list above that this recipe uses
- missedIngredients = common ingredients the recipe needs that aren't in the list
- Keep missedIngredients to pantry staples only (salt, oil, garlic etc.)
- Make the recipes realistic and practical for a home cook
- Return ONLY the JSON array, no markdown, no explanation"""

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7
        }
    }

    try:
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

        recipes = json.loads(raw_text)

        # Generate placeholder images with recipe name
        for i, recipe in enumerate(recipes):
            colors = ["FF6B6B", "4ECDC4", "45B7D1"]
            color = colors[i % len(colors)]
            name_encoded = recipe['title'].replace(' ', '+')[:20]
            recipe['image'] = f"https://via.placeholder.com/150x100/{color}/white?text={name_encoded}"

        return recipes

    except json.JSONDecodeError:
        return {"error": "Could not parse recipe response. Try again."}
    except Exception as e:
        return {"error": f"Recipe lookup failed: {str(e)}"}


def get_recipe_details(recipe_title, ingredients, lang='en'):
    """
    Gets detailed instructions for a specific recipe.
    Called when user wants to actually cook something.
    """
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except Exception:
        return {"error": "API key missing."}

    if lang == 'es':
        language_instruction = "Responde completamente en español."
    else:
        language_instruction = "Respond in English."

    ingredients_str = ", ".join(ingredients)

    prompt = f"""{language_instruction}

Give me a complete recipe for "{recipe_title}" using these available ingredients: {ingredients_str}

Return ONLY valid JSON:
{{
  "title": "{recipe_title}",
  "servings": 4,
  "time": "30 minutes",
  "ingredients": [
    {{"item": "chicken breast", "amount": "1 lb"}},
    {{"item": "salt", "amount": "1 tsp"}}
  ],
  "steps": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "tips": "One helpful cooking tip."
}}

Return ONLY the JSON, no markdown."""

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3}
    }

    try:
        response = requests.post(url, json=payload)
        result = response.json()
        raw_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
        if "```" in raw_text:
            parts = raw_text.split("```")
            raw_text = parts[1] if len(parts) > 1 else parts[0]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        return json.loads(raw_text.strip())
    except Exception as e:
        return {"error": f"Could not get recipe details: {str(e)}"}

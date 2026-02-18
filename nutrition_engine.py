# nutrition_engine.py
# Gemini-powered nutrition lookup and meal suggestions
import requests
import json
import streamlit as st

def get_nutrition_for_items(item_names, lang='en'):
    """
    Ask Gemini for nutrition estimates for a list of items.
    Returns dict: {item_name: {calories, protein, carbs, fat, fiber}}
    """
    if not item_names:
        return {}

    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        return {}

    items_str = ", ".join(item_names[:20])  # cap at 20

    prompt = f"""Give nutrition estimates per 100g (or per unit if that's more natural) for these common grocery items:
{items_str}

Return ONLY a valid JSON object like this:
{{
  "milk": {{"calories": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3, "fiber": 0, "unit": "100ml", "emoji": "🥛"}},
  "chicken breast": {{"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0, "unit": "100g", "emoji": "🍗"}},
  "rice": {{"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4, "unit": "100g cooked", "emoji": "🍚"}}
}}

Rules:
- Use the exact item names from the input as keys (lowercase)
- Estimate for realistic serving/unit if 100g doesn't make sense (e.g. eggs = per egg)
- emoji should match the food
- Return ONLY JSON, no markdown, no explanation"""

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1}
    }

    try:
        r = requests.post(url, json=payload, timeout=15)
        candidates = r.json().get('candidates')
        if not candidates:
            return {}
        raw = candidates[0]['content']['parts'][0]['text'].strip()
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return {}


def suggest_portions_for_goals(inventory_items, goals, lang='en'):
    """
    Given nutrition goals and available items, suggest what to eat and how much.
    goals: {calories, protein, carbs, fat}
    Returns a meal suggestion with portions.
    """
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        return {"error": "API key missing"}

    items_str = ", ".join([i['item_name'].replace('*','').strip() for i in inventory_items[:20]])

    if lang == 'es':
        lang_instruction = "Responde completamente en español."
        goal_words = {
            'calories': 'calorías', 'protein': 'proteína',
            'carbs': 'carbohidratos', 'fat': 'grasa'
        }
    else:
        lang_instruction = "Respond in English."
        goal_words = {
            'calories': 'calories', 'protein': 'protein',
            'carbs': 'carbs', 'fat': 'fat'
        }

    goals_str = " | ".join([
        f"{goals.get(k,0)}{'' if k=='calories' else 'g'} {goal_words[k]}"
        for k in ['calories','protein','carbs','fat']
        if goals.get(k, 0) > 0
    ])

    prompt = f"""{lang_instruction}

A person has these food items available at home:
{items_str}

Their nutrition goal for this meal is: {goals_str}

Suggest the best combination of items from that list to hit those goals, with exact portions.
Return ONLY valid JSON:
{{
  "meal_name": "High Protein Lunch",
  "total_nutrition": {{"calories": 480, "protein": 38, "carbs": 45, "fat": 12}},
  "items": [
    {{"name": "chicken breast", "amount": "150g", "calories": 248, "protein": 47, "carbs": 0, "fat": 5, "emoji": "🍗"}},
    {{"name": "rice", "amount": "1 cup cooked", "calories": 206, "protein": 4, "carbs": 45, "fat": 0, "emoji": "🍚"}}
  ],
  "tip": "Brief cooking or portioning tip"
}}

Only use items from the list provided. Return ONLY JSON."""

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4}
    }

    try:
        r = requests.post(url, json=payload, timeout=20)
        candidates = r.json().get('candidates')
        if not candidates:
            return {"error": "No response from AI service."}
        raw = candidates[0]['content']['parts'][0]['text'].strip()
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        return {"error": str(e)}

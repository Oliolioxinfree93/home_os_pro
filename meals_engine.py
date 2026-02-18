# meals_engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime


def build_generation_prompt(
    family_meals: bool,
    liked_ingredients: List[str],
    disliked_ingredients: List[str],
    pantry_items: List[str],
    fridge_items: List[str],
    child_names: List[str],
    constraints: Optional[Dict[str, Any]] = None,
) -> str:
    constraints = constraints or {}

    mode = "FAMILY MEALS" if family_meals else "INDIVIDUAL MEALS"
    kids = ", ".join(child_names) if child_names else "N/A"
    liked = ", ".join(liked_ingredients) if liked_ingredients else "N/A"
    disliked = ", ".join(disliked_ingredients) if disliked_ingredients else "N/A"
    pantry = ", ".join(pantry_items) if pantry_items else "N/A"
    fridge = ", ".join(fridge_items) if fridge_items else "N/A"

    notes = []
    if constraints.get("minutes"):
        notes.append(f"Max time: {constraints['minutes']} minutes")
    if constraints.get("diet"):
        notes.append(f"Diet: {constraints['diet']}")
    if constraints.get("budget"):
        notes.append(f"Budget: {constraints['budget']}")
    note_str = " | ".join(notes) if notes else "None"

    return f"""
You are a helpful meal planner for busy parents.

MODE: {mode}
CHILDREN: {kids}

LIKED INGREDIENTS: {liked}
DISLIKED INGREDIENTS: {disliked}

FRIDGE ITEMS: {fridge}
PANTRY ITEMS: {pantry}

CONSTRAINTS: {note_str}

Return 6 meal suggestions as JSON ONLY in this schema:
{{
  "meals": [
    {{
      "title": "string",
      "type": "family|individual",
      "for_child": "string|null",
      "ingredients": ["string", ...],
      "steps": ["string", ...],
      "time_minutes": number,
      "why_it_matches": "string"
    }}
  ]
}}
""".strip()


@dataclass
class MealsEngine:
    supabase: Any
    user_id: str

    # ---------- Tables ----------
    def ensure_tables_exist(self) -> None:
        # No-op here (tables are created via SQL in Supabase)
        return

    def get_children(self) -> List[Dict[str, Any]]:
        r = self.supabase.table("children").select("*").eq("user_id", self.user_id).order("created_at").execute()
        return r.data or []

    def add_child(self, name: str, age_years: Optional[int] = None) -> None:
        self.supabase.table("children").insert({
            "user_id": self.user_id,
            "name": name.strip(),
            "age_years": age_years,
        }).execute()

    def save_meal_feedback(
        self,
        child_id: str,
        meal_name: str,
        liked: bool,
        notes: str = "",
        ingredients: Optional[List[str]] = None,
    ) -> None:
        self.supabase.table("meal_feedback").insert({
            "user_id": self.user_id,
            "child_id": child_id,
            "meal_name": meal_name.strip(),
            "liked": liked,
            "notes": notes.strip(),
            "ingredients": ingredients or [],
            "created_at": datetime.utcnow().isoformat(),
        }).execute()

    def fetch_feedback(self) -> List[Dict[str, Any]]:
        r = self.supabase.table("meal_feedback").select("*").eq("user_id", self.user_id).order("created_at", desc=True).execute()
        return r.data or []

    def build_preferences(self) -> Dict[str, Any]:
        """
        Aggregates likes/dislikes based on feedback ingredients.
        Returns:
          {
            "liked_ingredients": [...],
            "disliked_ingredients": [...],
            "per_child": { child_id: {"liked":[...], "disliked":[...]} }
          }
        """
        data = self.fetch_feedback()
        liked_counts: Dict[str, int] = {}
        disliked_counts: Dict[str, int] = {}
        per_child: Dict[str, Dict[str, Dict[str, int]]] = {}

        for row in data:
            child = row.get("child_id")
            ingredients = row.get("ingredients") or []
            is_liked = bool(row.get("liked"))

            if child not in per_child:
                per_child[child] = {"liked": {}, "disliked": {}}

            for ing in ingredients:
                key = (ing or "").strip().lower()
                if not key:
                    continue
                if is_liked:
                    liked_counts[key] = liked_counts.get(key, 0) + 1
                    per_child[child]["liked"][key] = per_child[child]["liked"].get(key, 0) + 1
                else:
                    disliked_counts[key] = disliked_counts.get(key, 0) + 1
                    per_child[child]["disliked"][key] = per_child[child]["disliked"].get(key, 0) + 1

        def top_keys(d: Dict[str, int], n=20):
            return [k for k, _ in sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:n]]

        return {
            "liked_ingredients": top_keys(liked_counts),
            "disliked_ingredients": top_keys(disliked_counts),
            "per_child": {
                cid: {
                    "liked": top_keys(v["liked"], 15),
                    "disliked": top_keys(v["disliked"], 15)
                }
                for cid, v in per_child.items()
            }
        }

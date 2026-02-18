# meals_engine.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict, Any, List


@dataclass
class MealsEngine:
    supabase: Any
    user_id: str

    # ---------- Tables ----------
    # meal_feedback columns (recommended):
    # id (auto), user_id (text), child (text), meal (text),
    # rating (text), notes (text), created_at (timestamp)
    #
    # Optional: ingredients (text[] or json), meal_type (text), etc.

    def save_meal_feedback(
        self,
        child: str,
        meal: str,
        rating: str,
        notes: str = "",
    ) -> None:
        payload = {
            "user_id": self.user_id,
            "child": (child or "").strip(),
            "meal": (meal or "").strip(),
            "rating": rating,
            "notes": (notes or "").strip(),
            "date": str(date.today()),
        }
        self.supabase.table("meal_feedback").insert(payload).execute()

    def get_feedback(self) -> List[Dict[str, Any]]:
        r = self.supabase.table("meal_feedback").select("*").eq("user_id", self.user_id).execute()
        return r.data or []

    def get_favorites(self, child: Optional[str] = None) -> List[Dict[str, Any]]:
        q = self.supabase.table("meal_feedback").select("*").eq("user_id", self.user_id).eq("rating", "Loved it")
        if child:
            q = q.eq("child", child)
        r = q.execute()
        return r.data or []


def build_generation_prompt(
    child: Optional[str],
    liked_ingredients: List[str],
    disliked_ingredients: List[str],
    mode: str = "family",  # "family" or "individual"
) -> str:
    child_line = f"Child: {child}\n" if child else ""
    liked = ", ".join([x.strip() for x in liked_ingredients if x.strip()]) or "None provided"
    disliked = ", ".join([x.strip() for x in disliked_ingredients if x.strip()]) or "None provided"

    return f"""
You are a helpful meal planner for busy parents.

MODE: {mode.upper()}
{child_line}
LIKED INGREDIENTS: {liked}
DISLIKED INGREDIENTS: {disliked}

Return:
1) 5 meal ideas (short names)
2) For each: 3-6 ingredients + quick steps
3) If MODE is INDIVIDUAL, tailor portions + kid-friendly notes
Keep it simple, affordable, and low-prep.
""".strip()

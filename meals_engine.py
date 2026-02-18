# meals_engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import re
import pandas as pd


def _safe_execute(fn):
    """Run a Supabase query builder .execute() safely."""
    try:
        res = fn()
        return res, None
    except Exception as e:
        return None, e


def _norm_token(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9\s\-]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _to_list(v) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if str(x).strip()]
    if isinstance(v, str):
        # allow comma-separated input
        parts = [p.strip() for p in v.split(",")]
        return [p for p in parts if p]
    return [str(v)]


@dataclass
class ChildPref:
    likes: Dict[str, int]
    dislikes: Dict[str, int]


class MealsEngine:
    """
    Server-side helper for:
    - child list
    - recording picky eater feedback
    - building meal generation prompts (family or individual)
    """

    def __init__(self, supabase, user_id: str):
        self.supabase = supabase
        self.user_id = user_id

    # -------------------------
    # Children
    # -------------------------
    def get_children_df(self) -> pd.DataFrame:
        if not self.supabase:
            return pd.DataFrame()
        res, err = _safe_execute(
            lambda: self.supabase.table("children")
            .select("*")
            .eq("user_id", self.user_id)
            .order("created_at", desc=False)
            .execute()
        )
        if err or not res or not getattr(res, "data", None):
            return pd.DataFrame()
        return pd.DataFrame(res.data)

    def add_child(self, child_name: str, birthdate: Optional[str] = None, notes: str = "") -> Tuple[bool, str]:
        if not self.supabase:
            return False, "No database connection."
        child_name = (child_name or "").strip()
        if not child_name:
            return False, "Child name required."
        payload = {
            "user_id": self.user_id,
            "child_name": child_name,
            "birthdate": birthdate,
            "notes": notes or "",
        }
        res, err = _safe_execute(lambda: self.supabase.table("children").insert(payload).execute())
        if err:
            return False, f"DB error: {err}"
        return True, "Child added."

    # -------------------------
    # Feedback
    # -------------------------
    def record_feedback(
        self,
        child_id: int,
        meal_name: str,
        ingredients: List[str],
        ate: bool,
        liked: bool,
        rating: Optional[int] = None,
        notes: str = "",
    ) -> Tuple[bool, str]:
        if not self.supabase:
            return False, "No database connection."

        meal_name = (meal_name or "").strip()
        if not meal_name:
            return False, "Meal name required."

        ing = [_norm_token(x) for x in _to_list(ingredients)]
        ing = [x for x in ing if x]

        payload = {
            "user_id": self.user_id,
            "child_id": int(child_id),
            "meal_name": meal_name,
            "ingredients": ing,
            "ate": bool(ate),
            "liked": bool(liked),
            "rating": int(rating) if rating is not None and str(rating).strip() != "" else None,
            "notes": notes or "",
        }
        res, err = _safe_execute(lambda: self.supabase.table("meal_feedback").insert(payload).execute())
        if err:
            return False, f"DB error: {err}"
        return True, "Saved."

    def get_feedback_df(self, child_id: Optional[int] = None) -> pd.DataFrame:
        if not self.supabase:
            return pd.DataFrame()

        q = (
            self.supabase.table("meal_feedback")
            .select("*")
            .eq("user_id", self.user_id)
            .order("created_at", desc=True)
        )
        if child_id:
            q = q.eq("child_id", int(child_id))

        res, err = _safe_execute(lambda: q.execute())
        if err or not res or not getattr(res, "data", None):
            return pd.DataFrame()
        return pd.DataFrame(res.data)

    # -------------------------
    # Preference modeling
    # -------------------------
    def _prefs_from_feedback(self, df: pd.DataFrame) -> ChildPref:
        likes: Dict[str, int] = {}
        dislikes: Dict[str, int] = {}

        if df is None or df.empty:
            return ChildPref(likes=likes, dislikes=dislikes)

        for _, row in df.iterrows():
            ing = row.get("ingredients") or []
            ing = _to_list(ing)
            ing = [_norm_token(x) for x in ing]
            ing = [x for x in ing if x]

            liked = bool(row.get("liked", True))
            ate = bool(row.get("ate", True))

            # If they didn't eat it, treat as strong negative signal
            weight = 2 if not ate else 1

            for token in ing:
                if liked and ate:
                    likes[token] = likes.get(token, 0) + 1
                else:
                    dislikes[token] = dislikes.get(token, 0) + weight

        return ChildPref(likes=likes, dislikes=dislikes)

    def get_child_prefs(self, child_id: int) -> ChildPref:
        df = self.get_feedback_df(child_id=child_id)
        return self._prefs_from_feedback(df)

    def get_family_prefs(self) -> ChildPref:
        df = self.get_feedback_df(child_id=None)

        # aggregate across kids
        prefs = self._prefs_from_feedback(df)
        return prefs

    # -------------------------
    # Inventory helpers
    # -------------------------
    def get_inventory_ingredients(self) -> List[str]:
        """
        Pull your inventory items and turn them into 'available ingredients'.
        This assumes you already store items in `inventory` table.
        """
        if not self.supabase:
            return []
        res, err = _safe_execute(
            lambda: self.supabase.table("inventory")
            .select("item_name,category,storage,expiry_date,status")
            .eq("user_id", self.user_id)
            .eq("status", "In Stock")
            .execute()
        )
        if err or not res or not getattr(res, "data", None):
            return []

        items = []
        for r in res.data:
            name = _norm_token(r.get("item_name", ""))
            if name:
                items.append(name)

        # de-dupe while preserving order
        seen = set()
        out = []
        for x in items:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out


def build_generation_prompt(
    available_ingredients: List[str],
    likes: Dict[str, int],
    dislikes: Dict[str, int],
    *,
    scope: str,
    child_name: Optional[str] = None,
    meal_count: int = 5,
    style: str = "simple family-friendly",
    constraints: Optional[List[str]] = None,
) -> str:
    """
    Build a strong, structured prompt for Gemini (or any LLM).
    """
    constraints = constraints or []
    likes_sorted = sorted(likes.items(), key=lambda x: x[1], reverse=True)[:25]
    dislikes_sorted = sorted(dislikes.items(), key=lambda x: x[1], reverse=True)[:25]

    likes_str = ", ".join([f"{k} (+{v})" for k, v in likes_sorted]) if likes_sorted else "none yet"
    dislikes_str = ", ".join([f"{k} (-{v})" for k, v in dislikes_sorted]) if dislikes_sorted else "none yet"
    inv_str = ", ".join(available_ingredients[:80]) if available_ingredients else "unknown / not provided"

    who = "the whole family" if scope == "family" else f"child '{child_name or 'this child'}'"

    rules = [
        f"Generate {meal_count} meals for {who}.",
        f"Style: {style}.",
        "Prioritize liked ingredients; avoid disliked ingredients when possible.",
        "If you must include a disliked ingredient, use it subtly or offer a swap.",
        "Keep meals realistic for busy parents (minimal steps, common ingredients).",
        "Return results as a clean numbered list.",
        "For each meal include: Title, Ingredients (bullet list), Quick Steps (3-6 bullets), and a 'Swap idea' line.",
    ]
    if constraints:
        rules.append("Constraints: " + "; ".join(constraints))

    prompt = f"""
You are a helpful meal planner for a busy household.

AVAILABLE INGREDIENTS (from fridge/pantry):
{inv_str}

LIKED INGREDIENT SIGNALS:
{likes_str}

DISLIKED INGREDIENT SIGNALS:
{dislikes_str}

RULES:
- """ + "\n- ".join(rules).strip() + "\n"

    return prompt.strip()

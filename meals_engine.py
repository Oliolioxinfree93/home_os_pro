from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import re
import pandas as pd


@dataclass
class ChildPref:
    likes: Dict[str, int]
    dislikes: Dict[str, int]


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
        return [p.strip() for p in v.split(",") if p.strip()]
    return [str(v)]


class MealsEngine:
    def __init__(self, supabase, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
        self.last_error: Optional[str] = None

    def _set_error(self, err: Optional[Exception | str]):
        self.last_error = str(err) if err else None

    def _execute(self, query_fn):
        try:
            res = query_fn()
            self._set_error(None)
            return res
        except Exception as e:
            self._set_error(e)
            return None

    def get_children_df(self) -> pd.DataFrame:
        if not self.supabase:
            return pd.DataFrame()
        res = self._execute(
            lambda: self.supabase.table("children")
            .select("*")
            .eq("user_id", self.user_id)
            .order("created_at", desc=False)
            .execute()
        )
        if not res or not getattr(res, "data", None):
            return pd.DataFrame()
        return pd.DataFrame(res.data)

    def add_child(self, name: str, birthdate_iso: Optional[str], notes: str) -> Tuple[bool, str]:
        if not self.supabase:
            return False, "No database connection."
        name = (name or "").strip()
        if not name:
            return False, "Child name required."
        payload = {
            "user_id": self.user_id,
            "child_name": name,
            "birthdate": birthdate_iso,
            "notes": notes or "",
        }
        res = self._execute(lambda: self.supabase.table("children").insert(payload).execute())
        if not res:
            return False, "Could not add child. Meals tables may not be set up yet."
        return True, "Child added."

    def get_inventory_ingredients(self) -> List[str]:
        if not self.supabase:
            return []
        res = self._execute(
            lambda: self.supabase.table("inventory")
            .select("item_name,status")
            .eq("user_id", self.user_id)
            .eq("status", "In Stock")
            .execute()
        )
        if not res or not getattr(res, "data", None):
            return []

        seen, items = set(), []
        for row in res.data:
            token = _norm_token(row.get("item_name", ""))
            if token and token not in seen:
                seen.add(token)
                items.append(token)
        return items

    def record_feedback(
        self,
        child_id,
        meal_name,
        ingredients,
        ate,
        liked,
        rating,
        notes,
    ) -> Tuple[bool, str]:
        if not self.supabase:
            return False, "No database connection."

        meal_name = (meal_name or "").strip()
        if not meal_name:
            return False, "Meal name required."

        safe_ingredients = [_norm_token(x) for x in _to_list(ingredients)]
        safe_ingredients = [x for x in safe_ingredients if x]

        payload = {
            "user_id": self.user_id,
            "child_id": int(child_id),
            "meal_name": meal_name,
            "ingredients": safe_ingredients,
            "ate": bool(ate),
            "liked": bool(liked),
            "rating": int(rating) if rating is not None else None,
            "notes": notes or "",
        }
        res = self._execute(lambda: self.supabase.table("meal_feedback").insert(payload).execute())
        if not res:
            return False, "Could not save feedback. Meals tables may not be set up yet."
        return True, "Saved."

    def get_feedback_df(self) -> pd.DataFrame:
        if not self.supabase:
            return pd.DataFrame()
        res = self._execute(
            lambda: self.supabase.table("meal_feedback")
            .select("*")
            .eq("user_id", self.user_id)
            .order("created_at", desc=True)
            .execute()
        )
        if not res or not getattr(res, "data", None):
            return pd.DataFrame()
        return pd.DataFrame(res.data)

    def _prefs_from_feedback(self, df: pd.DataFrame) -> ChildPref:
        likes, dislikes = {}, {}
        if df is None or df.empty:
            return ChildPref(likes=likes, dislikes=dislikes)

        for _, row in df.iterrows():
            ing = [_norm_token(x) for x in _to_list(row.get("ingredients") or [])]
            ing = [x for x in ing if x]
            liked = bool(row.get("liked", True))
            ate = bool(row.get("ate", True))
            weight = 2 if not ate else 1

            for token in ing:
                if liked and ate:
                    likes[token] = likes.get(token, 0) + 1
                else:
                    dislikes[token] = dislikes.get(token, 0) + weight
        return ChildPref(likes=likes, dislikes=dislikes)

    def get_family_prefs(self) -> ChildPref:
        return self._prefs_from_feedback(self.get_feedback_df())

    def get_child_prefs(self, child_id) -> ChildPref:
        df = self.get_feedback_df()
        if df.empty or "child_id" not in df.columns:
            return ChildPref(likes={}, dislikes={})
        child_df = df[df["child_id"].astype(str) == str(child_id)]
        return self._prefs_from_feedback(child_df)


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

    return f"""
You are a helpful meal planner for a busy household.

AVAILABLE INGREDIENTS (from fridge/pantry):
{inv_str}

LIKED INGREDIENT SIGNALS:
{likes_str}

DISLIKED INGREDIENT SIGNALS:
{dislikes_str}

RULES:
- """ + "\n- ".join(rules).strip()

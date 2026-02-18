# -----------------------------
# MEALS TAB (Family + Individual)
# -----------------------------
engine = MealsEngine(supabase, user_id)

def inventory_item_names_for_prompt():
    # Pull from your existing DB fetchers
    inv = db_get_inventory()
    if inv is None or inv.empty:
        return []
    # item_name column exists in your inventory table
    return inv["item_name"].astype(str).tolist()

def call_gemini_for_meals(prompt: str) -> dict:
    """
    Replace this with your existing Gemini call pattern.
    Keep it strict: ask for JSON only, then json.loads.
    """
    import google.generativeai as genai
    import json as _json

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")  # or whatever you use

    resp = model.generate_content(prompt)
    text = (resp.text or "").strip()

    # Very common: model wraps in ```json ... ```
    text = text.replace("```json", "```").strip()
    if text.startswith("```") and text.endswith("```"):
        text = text.strip("`").strip()

    return _json.loads(text)

# ---- UI ----
st.markdown("## 🍽️ Meals")
st.caption("Log what each person actually eats, then generate meals that fit your household.")

# People manager
ui_section("People", "Add Child X / Parent Y once. Then log food feedback and generate meals.")

c1, c2, c3 = st.columns([2, 1, 2])
with c1:
    new_name = st.text_input("Name", placeholder="e.g., Mateo")
with c2:
    new_role = st.selectbox("Role", ["child", "adult"], index=0)
with c3:
    new_notes = st.text_input("Notes (optional)", placeholder="picky eater, no spice, etc.")

add_col1, add_col2 = st.columns([1, 5])
with add_col1:
    if st.button("➕ Add", type="primary", use_container_width=True):
        ok = engine.add_person(new_name, role=new_role, notes=new_notes)
        if ok:
            toast_saved()
            st.rerun()
        else:
            st.warning("Add a name first.")

people_df = engine.get_people()
if people_df.empty:
    st.info("Add at least one person to start logging and generating meals.")
    st.stop()

# Select person
person_map = {f"{row['name']} ({row.get('role','child')})": int(row["id"]) for _, row in people_df.iterrows()}
person_label = st.selectbox("Select person", list(person_map.keys()))
person_id = person_map[person_label]

# Feedback logger
ui_section("Food feedback", "Quick logging: did they eat it, and did they like it? Track ingredients or meals.")

f1, f2, f3, f4 = st.columns([2, 1, 1, 2])
with f1:
    food_item = st.text_input("Food / Ingredient", placeholder="e.g., chicken, broccoli, spaghetti")
with f2:
    ate = st.selectbox("Ate it?", ["(skip)", "Yes", "No"], index=0)
with f3:
    reaction = st.selectbox("Reaction", ["like", "neutral", "dislike"], index=0)
with f4:
    context = st.selectbox("Context", ["meal", "ingredient", "snack"], index=0)

notes = st.text_input("Notes (optional)", placeholder="Only ate it with ketchup…")

ate_val = None
if ate == "Yes":
    ate_val = True
elif ate == "No":
    ate_val = False

if st.button("✅ Save feedback", type="primary", use_container_width=True):
    ok = engine.log_feedback(person_id=person_id, item_name=food_item, reaction=reaction, ate=ate_val, context=context, notes=notes)
    if ok:
        toast_saved()
        st.rerun()
    else:
        st.warning("Type a food/ingredient name first.")

# Show top preferences
profile = engine.get_profile(person_id)
likes = sorted(profile["likes"].items(), key=lambda x: -x[1])[:10]
dislikes = sorted(profile["dislikes"].items(), key=lambda x: x[1])[:10]  # most negative

p1, p2 = st.columns(2)
with p1:
    ui_card("Top likes", "<br>".join([f"• {k}" for k, _ in likes]) if likes else "No likes yet.")
with p2:
    ui_card("Top dislikes", "<br>".join([f"• {k}" for k, _ in dislikes]) if dislikes else "No dislikes yet.")

st.divider()

# Generator
ui_section("Generate meals", "Family or Individual mode. Uses your inventory + preferences.")

g1, g2, g3 = st.columns([1, 1, 2])
with g1:
    mode = st.radio("Mode", ["family", "individual"], horizontal=True)
with g2:
    goal = st.selectbox("Goal", ["balanced", "quick", "healthy", "budget", "high-protein", "kid-friendly"], index=0)
with g3:
    max_meals = st.slider("How many suggestions?", 3, 8, 5)

target_person_id = person_id if mode == "individual" else None

if st.button("✨ Generate meals", type="primary", use_container_width=True):
    with st.spinner("Generating…"):
        inventory_list = inventory_item_names_for_prompt()
        people_list = people_df.to_dict("records")
        profiles_by_id = engine.get_family_profiles()

        prompt = build_generation_prompt(
            mode=mode,
            people=people_list,
            profiles_by_person_id=profiles_by_id,
            inventory_items=inventory_list,
            goal=goal,
            person_id=target_person_id,
            max_meals=max_meals,
        )

        try:
            data = call_gemini_for_meals(prompt)
            meals = data.get("meals", [])
        except Exception as e:
            st.error(f"Generator error: {e}")
            meals = []

    if not meals:
        st.warning("No meals returned. Try again or reduce constraints.")
    else:
        st.success(f"Generated {len(meals)} meals.")
        for i, m in enumerate(meals, start=1):
            title = m.get("title", f"Meal {i}")
            ingredients = m.get("ingredients", [])
            shopping = m.get("shopping", [])
            instructions = m.get("instructions", "")
            tags = m.get("tags", [])

            with st.expander(f"🍽️ {title}", expanded=(i == 1)):
                if tags:
                    st.caption(" • ".join(tags))

                if ingredients:
                    st.markdown("**Ingredients**")
                    for ing in ingredients:
                        st.write(f"- {ing.get('item','')} — {ing.get('qty','')}".strip(" —"))

                if shopping:
                    st.markdown("**Shopping (new items)**")
                    for s in shopping:
                        st.write(f"- {s}")

                if instructions:
                    st.markdown("**Instructions**")
                    st.write(instructions)

                # Optional: quick scoring (rough)
                # Score using ingredient item names only
                ing_names = [ing.get("item", "") for ing in ingredients if isinstance(ing, dict)]
                score = engine.score_meal_family(engine.get_family_profiles(), ing_names) if mode == "family" else engine.score_meal_for_person(profile, ing_names)

                s1, s2 = st.columns([1, 2])
                with s1:
                    st.metric("Fit score", f"{score:.1f}")
                with s2:
                    if st.button(f"💾 Save '{title}'", key=f"save_meal_{i}", use_container_width=True):
                        ok = engine.save_meal(
                            title=title,
                            ingredients=ingredients,
                            instructions=instructions,
                            mode=mode,
                            person_id=target_person_id,
                            score=score,
                        )
                        if ok:
                            toast_saved()
                        else:
                            st.error("Could not save meal.")

st.divider()

# Saved meals
ui_section("Saved meals", "Your favorites and past suggestions.")

saved_mode = st.selectbox("Filter", ["all", "family", "individual"], index=0)
saved_df = engine.get_saved_meals(
    mode=None if saved_mode == "all" else saved_mode,
    person_id=person_id if saved_mode == "individual" else None,
    limit=50
)

if saved_df.empty:
    st.caption("No saved meals yet.")
else:
    for _, row in saved_df.iterrows():
        title = row.get("title", "Meal")
        with st.expander(f"⭐ {title}", expanded=False):
            st.caption(f"Mode: {row.get('mode','')} | Score: {row.get('score','')}")
            ings = row.get("ingredients", [])
            if isinstance(ings, list) and ings:
                st.markdown("**Ingredients**")
                for ing in ings:
                    if isinstance(ing, dict):
                        st.write(f"- {ing.get('item','')} — {ing.get('qty','')}".strip(" —"))
                    else:
                        st.write(f"- {ing}")
            inst = row.get("instructions", "")
            if inst:
                st.markdown("**Instructions**")
                st.write(inst)

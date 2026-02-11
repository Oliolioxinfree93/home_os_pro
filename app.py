import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta
import json

# --- IMPORT MODULES ---
from inventory_manager import InventoryManager
from inventory_logic import InventoryLogic
from barcode_scanner import BarcodeScanner
from meal_planner import MealPlanner
from budget_manager import BudgetManager
from nutrition_tracker import NutritionTracker
from savings_tracker import SavingsTracker
from receipt_scanner import ReceiptScanner

# --- 1. APP CONFIGURATION ---
DB_NAME = 'home.db'
st.set_page_config(page_title="Home OS Pro", page_icon="🏠", layout="wide")

# --- 2. INITIALIZE MANAGERS ---
@st.cache_resource
def get_managers():
    return {
        'inventory': InventoryManager(DB_NAME),
        'scanner': BarcodeScanner(),
        'planner': MealPlanner(DB_NAME),
        'budget': BudgetManager(DB_NAME),
        'nutrition': NutritionTracker(DB_NAME),
        'savings': SavingsTracker(DB_NAME),
        'receipt': ReceiptScanner() # The AI Vision Scanner
    }

managers = get_managers()

# --- 3. DATABASE HELPER FUNCTIONS ---
def get_inventory():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT id, item_name, category, quantity, unit, storage, expiry_date, 
               decision_reason, price, store 
        FROM inventory 
        WHERE status='In Stock'
    """, conn)
    conn.close()
    return df

def get_shopping_list():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT id, item_name, is_urgent, estimated_price, barcode 
        FROM shopping_list
    """, conn)
    conn.close()
    
    logic = InventoryLogic()
    if not df.empty:
        df['category'] = df['item_name'].apply(lambda x: logic.normalize_item(x)['category'])
    return df

def delete_item(item_id, table="inventory"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def move_to_fridge(item_name, price=None, store=None, barcode=None):
    mgr = managers['inventory']
    mgr.add_item(item_name)
    
    if price:
        managers['budget'].record_purchase(item_name, price, store=store, barcode=barcode)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM shopping_list WHERE item_name=?", (item_name,))
    conn.commit()
    conn.close()

# --- 4. SIDEBAR DASHBOARD ---
st.sidebar.title("🏠 Home OS Pro")
st.sidebar.markdown("---")

# === POSITIVE IMPACT TRACKER ===
# Calculate savings data
savings_data = managers['savings'].calculate_monthly_savings()
savings_this_month = savings_data['total_monthly_savings']

# Set a dynamic goal (e.g., Monthly avg of projected annual savings)
monthly_savings_goal = savings_data['annual_projection'] / 12 if savings_data['annual_projection'] > 0 else 500.00

st.sidebar.subheader("💪 Monthly Impact")
st.sidebar.success(f"🎉 Saved: ${savings_this_month:.2f}")
st.sidebar.caption(f"Goal: ${monthly_savings_goal:.2f}")

if monthly_savings_goal > 0:
    progress = min(savings_this_month / monthly_savings_goal, 1.0)
    st.sidebar.progress(progress)

st.sidebar.markdown("---")

# === QUICK ADD / SCANNER ===
with st.sidebar.expander("➕ Quick Add / Scan", expanded=True):
    # Three Tabs: Manual, Barcode, Receipt Image
    qa_tab1, qa_tab2, qa_tab3 = st.tabs(["⌨️ Type", "📱 Barcode", "📸 Receipt"])
    
    # TAB 1: MANUAL ENTRY
    with qa_tab1:
        with st.form("add_form"):
            new_item = st.text_input("Item Name")
            qty = st.number_input("Quantity", 1, 100, 1)
            price_input = st.number_input("Price ($)", 0.0, 1000.0, 0.0, step=0.01)
            store_input = st.text_input("Store (optional)")
            dest = st.radio("Add to:", ["Fridge", "Shopping List"])
            
            if st.form_submit_button("Add Item"):
                if dest == "Fridge":
                    managers['inventory'].add_item(new_item, qty)
                    if price_input > 0:
                        managers['budget'].record_purchase(
                            new_item, price_input, quantity=qty, store=store_input
                        )
                    st.toast(f"✅ Added {new_item} to Fridge")
                else:
                    managers['inventory'].add_to_shopping_list(new_item)
                    st.toast(f"✅ Added {new_item} to Shopping List")
                st.rerun()

    # TAB 2: BARCODE SCANNER
    with qa_tab2:
        barcode_input = st.text_input("Enter UPC/EAN")
        if st.button("🔍 Lookup"):
            if barcode_input:
                with st.spinner("Scanning..."):
                    product = managers['scanner'].lookup_barcode(barcode_input)
                    if product:
                        st.success(f"Found: **{product['name']}**")
                        if st.button(f"Add {product['name']}"):
                            managers['inventory'].add_item(product['name'])
                            st.toast("Added to fridge!")
                            st.rerun()
                    else:
                        st.error("Not found")

    # TAB 3: RECEIPT SNAPSHOT (AI)
    with qa_tab3:
        st.caption("Snap a photo to auto-add items.")
        img_file = st.camera_input("Take Photo")
        if not img_file:
            img_file = st.file_uploader("Or Upload", type=['jpg','png','jpeg'])

        if img_file:
            if st.button("🚀 Process Receipt"):
                with st.spinner("AI is reading receipt..."):
                    results = managers['receipt'].scan_receipt(img_file)
                    st.session_state['scan_results'] = results
        
        # Review AI Results
        if 'scan_results' in st.session_state:
            results = st.session_state['scan_results']
            if "error" in results:
                st.error(results['error'])
            else:
                st.success(f"Found {len(results)} items!")
                with st.form("receipt_review"):
                    selected_items = []
                    for i, item in enumerate(results):
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"**{item['item']}** (${item['price']})")
                        if c2.checkbox("Add", value=True, key=f"scan_{i}"):
                            selected_items.append(item)
                    
                    store_name = st.text_input("Store Name", "Grocery Store")
                    
                    if st.form_submit_button("✅ Save Selected"):
                        count = 0
                        total_cost = 0
                        for item in selected_items:
                            managers['inventory'].add_item(
                                item['item'], quantity=item['qty'], 
                                price=item['price'], store=store_name
                            )
                            managers['budget'].record_purchase(
                                item['item'], item['price'], 
                                quantity=item['qty'], store=store_name
                            )
                            count += 1
                            total_cost += item['price']
                        
                        st.toast(f"Saved {count} items (${total_cost:.2f})!")
                        del st.session_state['scan_results']
                        st.rerun()

# --- 5. MAIN TABS ---
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💪 My Impact",
    "🧊 Fridge", 
    "🛒 Shopping List", 
    "📅 Meal Planner",
    "👨‍🍳 Recipe Rescue",
    "📊 Analytics"
])

# === TAB 0: MY IMPACT (DOMESTIC CEO DASHBOARD) ===
with tab0:
    st.title("💪 Your Household Savings Impact")
    st.caption("See the real economic value you're bringing to your family")
    
    contributions = managers['savings'].get_contribution_value()
    achievements = managers['savings'].get_achievements()
    
    # Hero Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 This Month Saved", f"${savings_data['total_monthly_savings']:.2f}", delta="Direct cash retained")
    with col2:
        st.metric("👨‍🍳 Meals Cooked", f"{contributions['meals_prepared']['count']} meals", delta=f"${contributions['meals_prepared']['value']:.2f} labor value")
    with col3:
        st.metric("💼 Annual Projection", f"${savings_data['annual_projection']:.2f}", delta="Est. yearly impact")
    
    st.markdown("---")
    
    # Achievements
    if achievements:
        st.subheader("🏆 Recent Achievements")
        cols = st.columns(len(achievements))
        for i, achievement in enumerate(achievements):
            with cols[i]:
                st.success(f"{achievement['icon']} **{achievement['title']}**")
                st.caption(achievement['description'])
    else:
        st.info("Start cooking and saving to earn badges!")

    st.markdown("---")

    # Value Breakdown
    st.subheader("💰 Where You're Making a Difference")
    c_a, c_b = st.columns(2)
    with c_a:
        st.markdown("**💸 Direct Savings (Cash kept in bank)**")
        st.write(f"- 🍳 Meal Planning: **${savings_data['meal_planning_savings']:.2f}**")
        st.write(f"- 🛒 Smart Shopping: **${savings_data['smart_shopping_savings']:.2f}**")
        st.write(f"- ♻️ Waste Prevention: **${savings_data['food_waste_prevention']:.2f}**")
    with c_b:
        st.markdown("**💼 Labor Value (If you hired this out)**")
        st.write(f"- 👨‍🍳 Chef Services: **${contributions['meals_prepared']['value']:.2f}**")
        st.write(f"- 🛒 Personal Shopper: **${contributions['shopping_trips']['value']:.2f}**")
        st.write(f"- 🧮 Admin/CFO Work: **${contributions['budget_management_hours']['value']:.2f}**")

# === TAB 1: FRIDGE ===
with tab1:
    st.header("Refrigerator Inventory")
    df = get_inventory()
    if not df.empty:
        df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
        today = date.today()
        df['days_left'] = (df['expiry_date'] - today).apply(lambda x: x.days)
        df = df.sort_values(by=['days_left'])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Items in Stock", len(df))
        col2.metric("Expiring Soon", len(df[df['days_left'] < 4]), delta_color="inverse")
        col3.metric("Total Value", f"${df['price'].sum():.2f}" if 'price' in df.columns else "$0.00")
        col4.metric("Frozen Items", len(df[df['storage'] == 'frozen']))

        # Filter Options
        c_a, c_b = st.columns(2)
        cat_filter = c_a.multiselect("Filter Category", options=df['category'].unique(), default=df['category'].unique())
        store_filter = c_b.multiselect("Filter Storage", options=df['storage'].unique(), default=df['storage'].unique())
        
        filtered_df = df[(df['category'].isin(cat_filter)) & (df['storage'].isin(store_filter))]

        for index, row in filtered_df.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 2, 1.5, 1.5, 1])
                c1.markdown(f"**{row['item_name'].title()}**")
                if row['decision_reason']: c1.caption(f"ℹ️ {row['decision_reason']}")
                
                days = row['days_left']
                status = f"🔴 Expired {abs(days)}d ago" if days < 0 else f"🟠 Expires in {days}d" if days < 4 else f"🟢 Good ({days}d)"
                c2.write(status)
                c3.caption(f"{row['quantity']} {row['unit']} ({row['storage']})")
                if row['price']: c4.write(f"${row['price']:.2f}")
                if c5.button("🗑️", key=f"del_{row['id']}"):
                    delete_item(row['id'])
                    st.rerun()
    else:
        st.info("Fridge is empty. Use the sidebar to add items!")

# === TAB 2: SHOPPING LIST ===
with tab2:
    st.header("Shopping List")
    shopping_df = get_shopping_list()
    
    if not shopping_df.empty:
        estimate = managers['budget'].estimate_shopping_list_cost()
        c1, c2 = st.columns(2)
        c1.metric("Items to Buy", len(shopping_df))
        c2.metric("Estimated Cost", f"${estimate['total_estimate']:.2f}")
        
        st.subheader("🏪 Aisle View")
        categories = sorted(shopping_df['category'].unique())
        for category in categories:
            st.markdown(f"### {category}")
            items = shopping_df[shopping_df['category'] == category]
            for index, row in items.iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 1.5, 1, 1])
                    c1.write(f"**{row['item_name'].title()}**")
                    if row['estimated_price']: c1.caption(f"Est. ${row['estimated_price']:.2f}")
                    
                    price = c2.number_input("Price", 0.0, 1000.0, row['estimated_price'] or 0.0, step=0.01, key=f"p_{row['id']}")
                    
                    if c3.button("✅ Got it", key=f"buy_{row['id']}"):
                        move_to_fridge(row['item_name'], price=price if price > 0 else None)
                        st.toast(f"Bought {row['item_name']}!")
                        st.rerun()
                    if c4.button("❌", key=f"rem_{row['id']}"):
                        delete_item(row['id'], "shopping_list")
                        st.rerun()
    else:
        st.success("Shopping list is empty!")

# === TAB 3: MEAL PLANNER ===
with tab3:
    st.header("📅 Weekly Meal Planner")
    c1, c2 = st.columns([2,1])
    start_date = c1.date_input("Week Starting", value=date.today() - timedelta(days=date.today().weekday()))
    if c2.button("🔄 Generate Shopping List"):
        items = managers['planner'].generate_shopping_list_from_plan(start_date)
        st.toast(f"Added {len(items)} items to list!")
        st.rerun()
    
    week_plan = managers['planner'].get_week_plan(start_date)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for i, day_name in enumerate(days):
        current_date = start_date + timedelta(days=i)
        st.subheader(f"{day_name} - {current_date.strftime('%b %d')}")
        
        # Add Meal Logic
        with st.expander(f"➕ Add Meal for {day_name}"):
            with st.form(f"add_meal_{i}"):
                m_type = st.selectbox("Type", ['breakfast', 'lunch', 'dinner', 'snack'])
                r_name = st.text_input("Meal Name")
                if st.form_submit_button("Save"):
                    managers['planner'].add_meal(current_date, m_type, recipe_name=r_name)
                    st.toast("Meal added!")
                    st.rerun()
        
        # Show Meals
        if str(current_date) in week_plan:
            for meal in week_plan[str(current_date)]:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    c1.write(f"**{meal['meal_type'].title()}**")
                    c2.write(meal['recipe_name'])

# === TAB 4: RECIPE RESCUE ===
with tab4:
    st.header("👨‍🍳 Recipe Rescue")
    if st.button("🆘 Find Recipes (Uses Expiring Food)", type="primary"):
        from recipe_manager import suggest_recipes
        with st.spinner("Chef is thinking..."):
            st.session_state['recipes'] = suggest_recipes()
            
    if 'recipes' in st.session_state:
        recipes = st.session_state['recipes']
        if isinstance(recipes, list):
            for r in recipes:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 3])
                    c1.image(r['image'], width=150)
                    with c2:
                        st.subheader(r['title'])
                        used = [i['name'] for i in r['usedIngredients']]
                        missed = [i['name'] for i in r['missedIngredients']]
                        st.caption(f"✨ Uses: {', '.join(used)}")
                        if missed: st.caption(f"🛒 Needs: {', '.join(missed)}")
                        
                        b1, b2, b3 = st.columns(3)
                        if missed and b1.button("Add Missing to List", key=f"s_{r['id']}"):
                            for m in missed: managers['inventory'].add_to_shopping_list(m)
                            st.toast("Added!")
                        
                        if b3.button("🔥 Cook This", key=f"c_{r['id']}"):
                            report, depleted = managers['inventory'].consume_ingredients(used)
                            st.balloons()
                            st.success("Inventory Updated! Savings Recorded.")
        else:
            st.warning(recipes.get('error', 'No recipes found.'))

# === TAB 5: ANALYTICS ===
with tab5:
    st.header("📊 Analytics")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Spending by Category")
        spending = managers['budget'].get_spending_by_category()
        if spending:
            import plotly.express as px
            df_spend = pd.DataFrame(spending)
            fig = px.pie(df_spend, values='spent', names='category', title="Expenses")
            st.plotly_chart(fig)
        else:
            st.info("No spending data yet.")
            
    with c2:
        st.subheader("Nutrition Goals")
        nutri_date = st.date_input("Date", date.today())
        goals = managers['nutrition'].check_nutrition_goals(nutri_date)
        for nutrient, data in goals.items():
            st.write(f"**{nutrient.title()}**")
            st.progress(min(data['percentage']/100, 1.0))
            st.caption(f"{data['actual']:.0f} / {data['goal']:.0f}")

st.markdown("---")
st.caption("Home OS Pro v2.0 | Built with ❤️")
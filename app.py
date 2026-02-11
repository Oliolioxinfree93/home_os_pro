import streamlit as st
import pandas as pd
from datetime import date, timedelta
import json
import os
from supabase import create_client

# --- APP CONFIG ---
st.set_page_config(page_title="Home OS Pro", page_icon="🏠", layout="wide")

# --- SUPABASE CONNECTION ---
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# --- GOOGLE LOGIN (FIXED TO READ FROM [auth]) ---
def show_login():
    st.markdown("""
    <style>
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 80px 20px;
    }
    .login-title {
        font-size: 3em;
        font-weight: bold;
        margin-bottom: 10px;
        text-align: center;
    }
    .login-subtitle {
        font-size: 1.2em;
        color: #666;
        margin-bottom: 40px;
        text-align: center;
    }
    .login-features {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 40px;
        max-width: 500px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🏠 Home OS Pro")
        st.markdown("### See the real value you bring to your family")
        st.markdown("---")

        st.markdown("""
        **What you'll track:**
        
        💰 Money saved through smart shopping  
        🍳 Meals cooked vs. eating out  
        ♻️ Food waste prevented  
        💼 Your monthly household impact  
        """)

        st.markdown("---")
        st.markdown("#### Sign in to get your personal fridge")

        try:
            from streamlit_google_auth import Authenticate
            
            # --- UPDATED: Look inside st.secrets['auth'] ---
            authenticator = Authenticate(
                secret_credentials_path='auth', # Looks for [auth] in secrets.toml
                cookie_name='home_os_auth',
                cookie_key='home_os_secret_key_2024',
                redirect_uri=st.secrets['auth']['redirect_uri']
            )

            authenticator.check_authentification()

            if not st.session_state.get('connected'):
                authorization_url = authenticator.get_authorization_url()
                st.link_button("🔑 Sign in with Google", authorization_url, use_container_width=True)
                st.caption("Your data is private. Only you can see your fridge.")
            else:
                st.rerun()

        except Exception as e:
            st.error(f"Login error: {e}")
            st.info("Check that your secrets.toml has the [auth] section set up correctly.")

# --- CHECK AUTH (FIXED) ---
def get_current_user():
    if 'user_id' in st.session_state and st.session_state['user_id']:
        return st.session_state['user_id']

    try:
        from streamlit_google_auth import Authenticate
        # --- UPDATED: Look inside st.secrets['auth'] ---
        authenticator = Authenticate(
            secret_credentials_path='auth',
            cookie_name='home_os_auth',
            cookie_key='home_os_secret_key_2024',
            redirect_uri=st.secrets['auth']['redirect_uri']
        )
        authenticator.check_authentification()

        if st.session_state.get('connected'):
            user_info = st.session_state.get('user_info', {})
            user_id = user_info.get('email', '')
            st.session_state['user_id'] = user_id
            st.session_state['user_name'] = user_info.get('name', 'Friend')
            st.session_state['user_picture'] = user_info.get('picture', '')
            return user_id
    except:
        pass

    return None

# --- MAIN APP ---
user_id = get_current_user()

if not user_id:
    show_login()
    st.stop()

# --- USER IS LOGGED IN ---
user_name = st.session_state.get('user_name', 'Friend')
user_picture = st.session_state.get('user_picture', '')

# --- IMPORT MANAGERS (pass user_id to all) ---
# NOTE: Ensure you have these files (inventory_logic.py, etc.) in your GitHub
from inventory_logic import InventoryLogic
from barcode_scanner import BarcodeScanner
from receipt_scanner import ReceiptScanner

# --- SUPABASE HELPERS ---
def db_get_inventory():
    try:
        response = supabase.table("inventory")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "In Stock")\
            .execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading inventory: {e}")
        return pd.DataFrame()

def db_add_item(raw_name, quantity=1, price=0.0, store=None, barcode=None):
    logic = InventoryLogic()
    analysis = logic.normalize_item(raw_name)
    from datetime import datetime
    expiry = (datetime.now().date() + timedelta(days=analysis['expiry_days'])).isoformat()

    supabase.table("inventory").insert({
        "user_id": user_id,
        "item_name": analysis['clean_name'],
        "category": analysis['category'],
        "quantity": quantity,
        "unit": analysis['unit'],
        "storage": analysis['storage'],
        "date_added": date.today().isoformat(),
        "expiry_date": expiry,
        "status": "In Stock",
        "decision_reason": analysis['reason'],
        "price": price or 0,
        "store": store or "",
        "barcode": barcode or ""
    }).execute()

def db_delete_item(item_id, table="inventory"):
    supabase.table(table).delete().eq("id", item_id).eq("user_id", user_id).execute()

def db_get_shopping_list():
    try:
        response = supabase.table("shopping_list")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        if not df.empty:
            logic = InventoryLogic()
            df['category'] = df['item_name'].apply(lambda x: logic.normalize_item(x)['category'])
        return df
    except Exception as e:
        st.error(f"Error loading shopping list: {e}")
        return pd.DataFrame()

def db_add_to_shopping_list(item_name, estimated_price=0.0):
    existing = supabase.table("shopping_list")\
        .select("id")\
        .eq("user_id", user_id)\
        .eq("item_name", item_name.lower())\
        .execute()
    if not existing.data:
        supabase.table("shopping_list").insert({
            "user_id": user_id,
            "item_name": item_name.lower(),
            "is_urgent": False,
            "estimated_price": estimated_price or 0
        }).execute()

def db_move_to_fridge(item_name, price=0.0, store=None):
    db_add_item(item_name, price=price, store=store)
    supabase.table("shopping_list")\
        .delete()\
        .eq("user_id", user_id)\
        .eq("item_name", item_name)\
        .execute()
    if price and price > 0:
        db_record_purchase(item_name, price, store=store)

def db_record_purchase(item_name, price, store=None):
    supabase.table("price_history").insert({
        "user_id": user_id,
        "item_name": item_name,
        "price": price,
        "store": store or "",
        "quantity": 1,
        "unit": "unit",
        "date_recorded": date.today().isoformat()
    }).execute()
    # Update budget
    existing = supabase.table("budget_settings")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    if existing.data:
        current = existing.data[0]
        supabase.table("budget_settings")\
            .update({"current_spent": current['current_spent'] + price})\
            .eq("user_id", user_id)\
            .execute()
    else:
        supabase.table("budget_settings").insert({
            "user_id": user_id,
            "period": "monthly",
            "budget_limit": 500.0,
            "alert_threshold": 0.8,
            "start_date": date.today().isoformat(),
            "current_spent": price
        }).execute()

def db_get_budget():
    try:
        response = supabase.table("budget_settings")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        if response.data:
            return response.data[0]
        else:
            # Create default budget for new user
            supabase.table("budget_settings").insert({
                "user_id": user_id,
                "period": "monthly",
                "budget_limit": 500.0,
                "alert_threshold": 0.8,
                "start_date": date.today().isoformat(),
                "current_spent": 0
            }).execute()
            return {"budget_limit": 500.0, "current_spent": 0, "period": "monthly"}
    except:
        return {"budget_limit": 500.0, "current_spent": 0, "period": "monthly"}

def db_calculate_savings():
    try:
        start_of_month = date.today().replace(day=1).isoformat()

        # Meals planned this month
        meals = supabase.table("meal_plan")\
            .select("id")\
            .eq("user_id", user_id)\
            .gte("date", start_of_month)\
            .execute()
        meals_count = len(meals.data) if meals.data else 0
        meal_savings = int(meals_count * 0.8) * 35.00

        # Shopping trips this month
        trips = supabase.table("price_history")\
            .select("date_recorded")\
            .eq("user_id", user_id)\
            .gte("date_recorded", start_of_month)\
            .execute()
        unique_days = len(set([r['date_recorded'] for r in trips.data])) if trips.data else 0
        shopping_savings = unique_days * 10.00

        # Food waste prevention (consumed items with price)
        consumed = supabase.table("inventory")\
            .select("price")\
            .eq("user_id", user_id)\
            .eq("status", "Consumed")\
            .gte("date_added", start_of_month)\
            .execute()
        waste_prevention = sum([r['price'] for r in consumed.data if r['price']]) if consumed.data else 0

        total = meal_savings + shopping_savings + waste_prevention

        return {
            'meal_planning_savings': meal_savings,
            'smart_shopping_savings': shopping_savings,
            'food_waste_prevention': waste_prevention,
            'total_monthly_savings': total,
            'annual_projection': total * 12,
            'meals_cooked': int(meals_count * 0.8),
            'shopping_trips': unique_days
        }
    except Exception as e:
        return {
            'meal_planning_savings': 0, 'smart_shopping_savings': 0,
            'food_waste_prevention': 0, 'total_monthly_savings': 0,
            'annual_projection': 0, 'meals_cooked': 0, 'shopping_trips': 0
        }

def db_get_meal_plan(start_date):
    try:
        end_date = start_date + timedelta(days=6)
        response = supabase.table("meal_plan")\
            .select("*")\
            .eq("user_id", user_id)\
            .gte("date", start_date.isoformat())\
            .lte("date", end_date.isoformat())\
            .execute()
        week_plan = {}
        for meal in (response.data or []):
            d = meal['date']
            if d not in week_plan:
                week_plan[d] = []
            week_plan[d].append(meal)
        return week_plan
    except:
        return {}

def db_add_meal(meal_date, meal_type, recipe_name, servings=1):
    supabase.table("meal_plan").insert({
        "user_id": user_id,
        "date": meal_date.isoformat(),
        "meal_type": meal_type,
        "recipe_name": recipe_name,
        "servings": servings
    }).execute()

def db_consume_ingredients(ingredient_names):
    report = []
    depleted = []
    for ingredient in ingredient_names:
        response = supabase.table("inventory")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "In Stock")\
            .ilike("item_name", f"%{ingredient}%")\
            .order("expiry_date")\
            .limit(1)\
            .execute()
        if response.data:
            item = response.data[0]
            if item['quantity'] > 1:
                supabase.table("inventory")\
                    .update({"quantity": item['quantity'] - 1})\
                    .eq("id", item['id'])\
                    .execute()
                report.append(f"Used 1 of '{item['item_name']}'. Remaining: {item['quantity']-1}")
            else:
                supabase.table("inventory")\
                    .update({"status": "Consumed"})\
                    .eq("id", item['id'])\
                    .execute()
                report.append(f"Finished '{item['item_name']}'")
                depleted.append(item['item_name'])
        else:
            report.append(f"⚠️ '{ingredient}' not found")
    return report, depleted

# --- SIDEBAR ---
st.sidebar.title("🏠 Home OS Pro")

# User profile
if user_picture:
    st.sidebar.image(user_picture, width=40)
st.sidebar.markdown(f"**Welcome, {user_name.split()[0]}!** 👋")

# Logout
if st.sidebar.button("🚪 Sign Out", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.markdown("---")

# Monthly Impact in sidebar
savings = db_calculate_savings()
st.sidebar.subheader("💪 Monthly Impact")
if savings['total_monthly_savings'] > 0:
    st.sidebar.success(f"🎉 Saved: ${savings['total_monthly_savings']:.2f}")
    goal = max(savings['total_monthly_savings'], 100)
    st.sidebar.progress(min(savings['total_monthly_savings'] / goal, 1.0))
else:
    st.sidebar.info("💡 Add groceries to see your impact!")

st.sidebar.markdown("---")

# Quick Add
scanner = BarcodeScanner()
receipt_scanner = ReceiptScanner()

with st.sidebar.expander("➕ Quick Add / Scan", expanded=True):
    qa_tab1, qa_tab2, qa_tab3 = st.tabs(["⌨️ Type", "📱 Barcode", "📸 Receipt"])

    with qa_tab1:
        with st.form("add_form"):
            new_item = st.text_input("Item Name")
            qty = st.number_input("Quantity", 1, 100, 1)
            price_input = st.number_input("Price ($)", 0.0, 1000.0, 0.0, step=0.01)
            store_input = st.text_input("Store (optional)")
            dest = st.radio("Add to:", ["Fridge", "Shopping List"])
            if st.form_submit_button("Add Item"):
                if new_item:
                    if dest == "Fridge":
                        db_add_item(new_item, qty, price_input, store_input)
                        if price_input > 0:
                            db_record_purchase(new_item, price_input, store_input)
                        st.toast(f"✅ Added {new_item}!")
                    else:
                        db_add_to_shopping_list(new_item, price_input)
                        st.toast(f"✅ Added to list!")
                    st.rerun()

    with qa_tab2:
        barcode_input = st.text_input("Enter UPC/EAN")
        if st.button("🔍 Lookup"):
            if barcode_input:
                with st.spinner("Scanning..."):
                    product = scanner.lookup_barcode(barcode_input)
                    if product:
                        st.success(f"Found: **{product['name']}**")
                        if product.get('image_url'):
                            st.image(product['image_url'], width=80)
                        st.caption(f"Brand: {product['brand']}")
                        if st.button(f"Add to Fridge"):
                            db_add_item(product['name'])
                            st.toast("Added!")
                            st.rerun()
                    else:
                        st.error("Not found")

    with qa_tab3:
        img_file = st.camera_input("Take Photo")
        if not img_file:
            img_file = st.file_uploader("Or Upload", type=['jpg','png','jpeg'])
        if img_file:
            if st.button("🚀 Process Receipt"):
                with st.spinner("AI reading receipt..."):
                    results = receipt_scanner.scan_receipt(img_file)
                    st.session_state['scan_results'] = results
        if 'scan_results' in st.session_state:
            results = st.session_state['scan_results']
            if "error" in results:
                st.info(results['error'])
            else:
                st.success(f"Found {len(results)} items!")
                with st.form("receipt_review"):
                    selected = []
                    for i, item in enumerate(results):
                        c1, c2 = st.columns([3,1])
                        c1.write(f"**{item['item']}** (${item['price']})")
                        if c2.checkbox("Add", value=True, key=f"scan_{i}"):
                            selected.append(item)
                    store_name = st.text_input("Store", "Grocery Store")
                    if st.form_submit_button("✅ Save Selected"):
                        for item in selected:
                            db_add_item(item['item'], quantity=item.get('qty',1), price=item['price'], store=store_name)
                            db_record_purchase(item['item'], item['price'], store=store_name)
                        st.toast(f"Saved {len(selected)} items!")
                        del st.session_state['scan_results']
                        st.rerun()

# --- MAIN TABS ---
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💪 My Impact", "🧊 Fridge", "🛒 Shopping List",
    "📅 Meal Planner", "👨‍🍳 Recipe Rescue", "📊 Analytics"
])

# === TAB 0: MY IMPACT ===
with tab0:
    st.title(f"💪 {user_name.split()[0]}'s Household Impact")
    st.caption("The real economic value you bring to your family every month")

    st.info("""
    💡 **How we calculate:** **Direct Savings** = Actual money kept vs. eating out / delivery fees  
    **Labor Value** = What you'd pay to hire these services at market rates
    """)

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 This Month Saved", f"${savings['total_monthly_savings']:.2f}", "Direct cash retained")
    col2.metric("🍳 Meals Cooked", f"{savings['meals_cooked']} meals", f"${savings['meals_cooked'] * 35:.2f} vs. eating out")
    col3.metric("📈 Annual Projection", f"${savings['annual_projection']:.2f}", "Estimated yearly impact")

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**💸 Direct Savings (Cash in your pocket)**")
        st.write(f"🍳 Meal planning: **${savings['meal_planning_savings']:.2f}**")
        st.caption("Cooked meals vs. $35/meal restaurant average")
        st.write(f"🛒 Smart shopping: **${savings['smart_shopping_savings']:.2f}**")
        st.caption("Saved on delivery fees by shopping yourself")
        st.write(f"♻️ Waste prevention: **${savings['food_waste_prevention']:.2f}**")
        st.caption("Value of food saved from expiring")

    with c2:
        st.markdown("**💼 Labor Value (If you hired this out)**")
        chef_value = savings['meals_cooked'] * 35
        shopper_value = savings['shopping_trips'] * 10
        admin_value = 100.0
        st.write(f"👨‍🍳 Chef services: **${chef_value:.2f}**")
        st.caption("Professional meal prep rate")
        st.write(f"🛒 Personal shopper: **${shopper_value:.2f}**")
        st.caption("$10/trip market rate")
        st.write(f"🧮 Admin/CFO work: **${admin_value:.2f}**")
        st.caption("Household bookkeeper rate: $25/hr")

    total_value = chef_value + shopper_value + admin_value
    st.markdown("---")
    st.success(f"""
    ### 🌟 This Month's Bottom Line
    You added **${total_value:.2f}** in economic value to your household.  
    Annual projection: **${total_value * 12:,.2f}**
    """)

    # Achievements
    achievements = []
    if savings['food_waste_prevention'] >= 25:
        achievements.append(("♻️", "Waste Warrior", f"Prevented ${savings['food_waste_prevention']:.2f} in food waste!"))
    if savings['smart_shopping_savings'] >= 30:
        achievements.append(("🎯", "Deal Hunter", f"Saved ${savings['smart_shopping_savings']:.2f} shopping smart!"))
    if savings['meals_cooked'] >= 10:
        achievements.append(("👨‍🍳", "Meal Prep Master", f"Cooked {savings['meals_cooked']} meals at home!"))
    if savings['total_monthly_savings'] >= 100:
        achievements.append(("💪", "Budget Hero", f"Total savings: ${savings['total_monthly_savings']:.2f}!"))

    if achievements:
        st.markdown("---")
        st.subheader("🏆 This Month's Achievements")
        cols = st.columns(len(achievements))
        for i, (icon, title, desc) in enumerate(achievements):
            with cols[i]:
                st.success(f"{icon} **{title}**")
                st.caption(desc)

    # Monthly Report
    st.markdown("---")
    if st.button("📊 Generate Monthly Report"):
        st.markdown(f"""
        ### 📄 Monthly Household Report — {date.today().strftime('%B %Y')}
        **Prepared by:** {user_name}

        ---

        **💰 Total Savings: ${savings['total_monthly_savings']:.2f}**
        - Meal Planning: ${savings['meal_planning_savings']:.2f}
        - Smart Shopping: ${savings['smart_shopping_savings']:.2f}
        - Food Waste Prevention: ${savings['food_waste_prevention']:.2f}

        **💼 Household Value Added: ${total_value:.2f}**
        - {savings['meals_cooked']} meals prepared (${chef_value:.2f})
        - {savings['shopping_trips']} shopping trips (${shopper_value:.2f})
        - Budget management (${admin_value:.2f})

        **📈 Annual Projection: ${total_value * 12:,.2f}**

        ---
        *All calculations based on actual activity and local market rates.*
        """)

# === TAB 1: FRIDGE ===
with tab1:
    st.header("🧊 Your Fridge")
    df = db_get_inventory()

    if not df.empty:
        df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
        today = date.today()
        df['days_left'] = (df['expiry_date'] - today).apply(lambda x: x.days)
        df = df.sort_values('days_left')

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Items in Stock", len(df))
        c2.metric("Expiring Soon", len(df[df['days_left'] < 4]), delta_color="inverse")
        c3.metric("Total Value", f"${df['price'].sum():.2f}")
        c4.metric("Frozen Items", len(df[df['storage'] == 'frozen']))

        c_a, c_b = st.columns(2)
        cat_filter = c_a.multiselect("Category", options=df['category'].unique(), default=df['category'].unique())
        store_filter = c_b.multiselect("Storage", options=df['storage'].unique(), default=df['storage'].unique())
        filtered = df[df['category'].isin(cat_filter) & df['storage'].isin(store_filter)]

        for _, row in filtered.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 2, 1.5, 1.5, 1])
                c1.markdown(f"**{row['item_name'].title()}**")
                if row.get('decision_reason'):
                    c1.caption(f"ℹ️ {row['decision_reason']}")
                days = row['days_left']
                status = f"🔴 Expired {abs(days)}d ago" if days < 0 else f"🟠 Expires in {days}d" if days < 4 else f"🟢 Good ({days}d)"
                c2.write(status)
                c3.caption(f"{row['quantity']} {row['unit']} ({row['storage']})")
                if row.get('price'): c4.write(f"${row['price']:.2f}")
                if c5.button("🗑️", key=f"del_{row['id']}"):
                    db_delete_item(row['id'])
                    st.rerun()
    else:
        st.info("Your fridge is empty! Add items using the sidebar.")

# === TAB 2: SHOPPING LIST ===
with tab2:
    st.header("🛒 Shopping List")
    shop_df = db_get_shopping_list()

    if not shop_df.empty:
        c1, c2 = st.columns(2)
        c1.metric("Items to Buy", len(shop_df))

        categories = sorted(shop_df['category'].unique())
        for category in categories:
            st.markdown(f"### {category}")
            items = shop_df[shop_df['category'] == category]
            for _, row in items.iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 1.5, 1, 1])
                    c1.write(f"**{row['item_name'].title()}**")
                    if row.get('estimated_price'):
                        c1.caption(f"Est. ${row['estimated_price']:.2f}")
                    price = c2.number_input("Price", 0.0, 1000.0,
                        float(row['estimated_price']) if row.get('estimated_price') else 0.0,
                        step=0.01, key=f"p_{row['id']}")
                    if c3.button("✅ Got it", key=f"buy_{row['id']}"):
                        db_move_to_fridge(row['item_name'], price=price)
                        st.toast(f"✅ Bought {row['item_name']}!")
                        st.rerun()
                    if c4.button("❌", key=f"rem_{row['id']}"):
                        db_delete_item(row['id'], "shopping_list")
                        st.rerun()
    else:
        st.success("✅ Shopping list is empty!")

# === TAB 3: MEAL PLANNER ===
with tab3:
    st.header("📅 Weekly Meal Planner")
    c1, c2 = st.columns([2, 1])
    start_date = c1.date_input("Week Starting",
        value=date.today() - timedelta(days=date.today().weekday()))

    week_plan = db_get_meal_plan(start_date)
    days_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    for i, day_name in enumerate(days_names):
        current_date = start_date + timedelta(days=i)
        st.subheader(f"{day_name} — {current_date.strftime('%b %d')}")

        with st.expander(f"➕ Add meal"):
            with st.form(f"meal_{i}"):
                m_type = st.selectbox("Type", ['breakfast', 'lunch', 'dinner', 'snack'])
                r_name = st.text_input("Meal Name")
                if st.form_submit_button("Save"):
                    if r_name:
                        db_add_meal(current_date, m_type, r_name)
                        st.toast("Meal added!")
                        st.rerun()

        if current_date.isoformat() in week_plan:
            for meal in week_plan[current_date.isoformat()]:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    c1.write(f"**{meal['meal_type'].title()}**")
                    c2.write(meal['recipe_name'])

# === TAB 4: RECIPE RESCUE ===
with tab4:
    st.header("👨‍🍳 Recipe Rescue")
    st.caption("Finds recipes using ingredients expiring soon")

    if st.button("🆘 Find Recipes", type="primary"):
        try:
            expiring = supabase.table("inventory")\
                .select("item_name")\
                .eq("user_id", user_id)\
                .eq("status", "In Stock")\
                .lte("expiry_date", (date.today() + timedelta(days=7)).isoformat())\
                .execute()

            if expiring.data:
                ingredients = list(set([r['item_name'] for r in expiring.data]))
                from recipe_manager import suggest_recipes_from_list
                st.session_state['recipes'] = suggest_recipes_from_list(ingredients)
            else:
                st.info("No food expiring soon! Your fridge is well managed. 🎉")
        except Exception as e:
            st.error(f"Error: {e}")

    if 'recipes' in st.session_state:
        recipes = st.session_state['recipes']
        if isinstance(recipes, list):
            for r in recipes:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 3])
                    c1.image(r['image'], width=120)
                    with c2:
                        st.subheader(r['title'])
                        used = [i['name'] for i in r['usedIngredients']]
                        missed = [i['name'] for i in r['missedIngredients']]
                        st.caption(f"✨ Uses: {', '.join(used)}")
                        if missed:
                            st.caption(f"🛒 Needs: {', '.join(missed)}")
                        b1, b2 = st.columns(2)
                        if missed and b1.button("Add Missing to List", key=f"s_{r['id']}"):
                            for m in missed:
                                db_add_to_shopping_list(m)
                            st.toast("Added to list!")
                        if b2.button("🔥 Cook This", key=f"c_{r['id']}"):
                            report, depleted = db_consume_ingredients(used)
                            st.balloons()
                            with st.expander("✅ Inventory Updated", expanded=True):
                                for line in report:
                                    st.write(f"• {line}")
                                if depleted:
                                    st.write("🚫 Ran out of:")
                                    for item in depleted:
                                        st.write(f"- {item}")
                                    if st.button("🛒 Add to Shopping List"):
                                        for item in depleted:
                                            db_add_to_shopping_list(item)
                                        st.toast("Restocked list!")
                                        st.rerun()
        else:
            st.warning(recipes.get('error', 'No recipes found.'))

# === TAB 5: ANALYTICS ===
with tab5:
    st.header("📊 Analytics")
    budget = db_get_budget()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("💰 Budget")
        limit = budget.get('budget_limit', 500)
        spent = budget.get('current_spent', 0)
        remaining = limit - spent
        pct = (spent / limit * 100) if limit > 0 else 0

        st.metric("Monthly Budget", f"${limit:.2f}")
        st.metric("Spent", f"${spent:.2f}", delta=f"${remaining:.2f} remaining")
        st.progress(min(pct / 100, 1.0))

        with st.expander("⚙️ Update Budget"):
            with st.form("budget_form"):
                new_budget = st.number_input("Monthly Budget ($)", 0.0, 10000.0, float(limit))
                if st.form_submit_button("Update"):
                    supabase.table("budget_settings")\
                        .update({"budget_limit": new_budget, "current_spent": 0})\
                        .eq("user_id", user_id)\
                        .execute()
                    st.toast("Budget updated!")
                    st.rerun()

    with c2:
        st.subheader("📈 Spending by Category")
        try:
            ph = supabase.table("price_history")\
                .select("item_name, price")\
                .eq("user_id", user_id)\
                .execute()
            if ph.data:
                logic = InventoryLogic()
                df_ph = pd.DataFrame(ph.data)
                df_ph['category'] = df_ph['item_name'].apply(
                    lambda x: logic.normalize_item(x)['category']
                )
                category_spend = df_ph.groupby('category')['price'].sum().reset_index()
                import plotly.express as px
                fig = px.pie(category_spend, values='price', names='category')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No spending data yet. Add items with prices to see breakdown.")
        except Exception as e:
            st.info("Add purchases to see spending analytics.")

st.markdown("---")
st.caption("Home OS Pro | Built with ❤️ for stay-at-home parents")

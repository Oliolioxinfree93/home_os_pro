import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from supabase import create_client
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import json

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# --- APP CONFIG ---
st.set_page_config(page_title="Home OS Pro", page_icon="🏠", layout="wide")

# --- SUPABASE ---
@st.cache_resource
def get_supabase():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

supabase = get_supabase()

# --- AUTH ---
def get_flow():
    CLIENT_ID = st.secrets["auth"]["client_id"]
    CLIENT_SECRET = st.secrets["auth"]["client_secret"]
    REDIRECT_URI = st.secrets["auth"]["redirect_uri"]
    return Flow.from_client_config(
        {"web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }},
        scopes=["openid", "email", "profile"],
        redirect_uri=REDIRECT_URI
    )

def check_login():
    # Dev mode
    if st.session_state.get('dev_mode'):
        return st.session_state.get('user_id', 'dev@example.com')

    # Already logged in
    if st.session_state.get('user_id'):
        return st.session_state['user_id']

    # Google redirected back with code
    query_params = st.query_params
    if "code" in query_params:
        try:
            flow = get_flow()
            flow.fetch_token(code=query_params["code"])
            credentials = flow.credentials
            user_info = id_token.verify_oauth2_token(
                credentials.id_token,
                google_requests.Request(),
                st.secrets["auth"]["client_id"]
            )
            st.session_state['user_id'] = user_info['email']
            st.session_state['user_name'] = user_info.get('name', 'Friend')
            st.session_state['user_picture'] = user_info.get('picture', '')
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")
            if st.button("🔄 Try Again"):
                st.query_params.clear()
                st.rerun()
            st.stop()

    # Show login screen
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("# 🏠 Home OS Pro")
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

        try:
            flow = get_flow()
            auth_url, _ = flow.authorization_url(
                prompt="select_account",
                access_type="offline"
            )
            st.link_button("🔑 Continue with Google", auth_url, use_container_width=True)
            st.caption("Your data is private. Only you can see your fridge.")
        except Exception as e:
            st.error(f"Auth setup error: {e}")

        st.markdown("---")
        if st.button("🛠️ Dev Mode", use_container_width=True):
            st.session_state['dev_mode'] = True
            st.session_state['user_id'] = 'dev@example.com'
            st.session_state['user_name'] = 'Developer'
            st.session_state['user_picture'] = ''
            st.rerun()

    st.stop()

# --- INIT USER ---
user_id = check_login()
user_name = st.session_state.get('user_name', 'Friend')
user_picture = st.session_state.get('user_picture', '')

# --- IMPORTS ---
from inventory_logic import InventoryLogic
from barcode_scanner import BarcodeScanner
from receipt_scanner import ReceiptScanner

# --- DB FUNCTIONS ---
def db_get_inventory():
    try:
        r = supabase.table("inventory").select("*").eq("user_id", user_id).eq("status", "In Stock").execute()
        return pd.DataFrame(r.data) if r.data else pd.DataFrame()
    except: return pd.DataFrame()

def db_add_item(raw_name, quantity=1, price=0.0, store=None, barcode=None):
    try:
        logic = InventoryLogic()
        a = logic.normalize_item(raw_name)
        expiry = (datetime.now().date() + timedelta(days=a['expiry_days'])).isoformat()
        supabase.table("inventory").insert({
            "user_id": user_id, "item_name": a['clean_name'], "category": a['category'],
            "quantity": quantity, "unit": a['unit'], "storage": a['storage'],
            "date_added": date.today().isoformat(), "expiry_date": expiry,
            "status": "In Stock", "decision_reason": a['reason'],
            "price": price or 0, "store": store or "", "barcode": barcode or ""
        }).execute()
    except Exception as e:
        st.error(f"Error adding item: {e}")

def db_delete_item(item_id, table="inventory"):
    try:
        supabase.table(table).delete().eq("id", item_id).eq("user_id", user_id).execute()
    except: pass

def db_get_shopping_list():
    try:
        r = supabase.table("shopping_list").select("*").eq("user_id", user_id).execute()
        df = pd.DataFrame(r.data) if r.data else pd.DataFrame()
        if not df.empty:
            logic = InventoryLogic()
            df['category'] = df['item_name'].apply(lambda x: logic.normalize_item(x)['category'])
        return df
    except: return pd.DataFrame()

def db_add_to_shopping_list(item_name, estimated_price=0.0):
    try:
        existing = supabase.table("shopping_list").select("id").eq("user_id", user_id).eq("item_name", item_name.lower()).execute()
        if not existing.data:
            supabase.table("shopping_list").insert({
                "user_id": user_id, "item_name": item_name.lower(),
                "is_urgent": False, "estimated_price": estimated_price or 0
            }).execute()
    except: pass

def db_record_purchase(item_name, price, store=None):
    try:
        supabase.table("price_history").insert({
            "user_id": user_id, "item_name": item_name, "price": price,
            "store": store or "", "quantity": 1, "unit": "unit",
            "date_recorded": date.today().isoformat()
        }).execute()
        existing = supabase.table("budget_settings").select("*").eq("user_id", user_id).execute()
        if existing.data:
            supabase.table("budget_settings").update({
                "current_spent": existing.data[0]['current_spent'] + price
            }).eq("user_id", user_id).execute()
        else:
            supabase.table("budget_settings").insert({
                "user_id": user_id, "period": "monthly", "budget_limit": 500.0,
                "current_spent": price, "start_date": date.today().isoformat()
            }).execute()
    except: pass

def db_move_to_fridge(item_name, price=0.0, store=None):
    db_add_item(item_name, price=price, store=store)
    try:
        supabase.table("shopping_list").delete().eq("user_id", user_id).eq("item_name", item_name).execute()
    except: pass
    if price and price > 0:
        db_record_purchase(item_name, price, store)

def db_get_budget():
    try:
        r = supabase.table("budget_settings").select("*").eq("user_id", user_id).execute()
        if r.data: return r.data[0]
        supabase.table("budget_settings").insert({
            "user_id": user_id, "period": "monthly", "budget_limit": 500.0,
            "current_spent": 0, "start_date": date.today().isoformat()
        }).execute()
        return {"budget_limit": 500.0, "current_spent": 0}
    except: return {"budget_limit": 500.0, "current_spent": 0}

def db_calculate_savings():
    try:
        som = date.today().replace(day=1).isoformat()
        meals = supabase.table("meal_plan").select("id").eq("user_id", user_id).gte("date", som).execute()
        mc = len(meals.data) if meals.data else 0
        trips = supabase.table("price_history").select("date_recorded").eq("user_id", user_id).gte("date_recorded", som).execute()
        ud = len(set([r['date_recorded'] for r in trips.data])) if trips.data else 0
        consumed = supabase.table("inventory").select("price").eq("user_id", user_id).eq("status", "Consumed").gte("date_added", som).execute()
        wp = sum([r['price'] for r in consumed.data if r.get('price')]) if consumed.data else 0
        ms = int(mc * 0.8) * 35.0
        ss = ud * 10.0
        total = ms + ss + wp
        return {'meal_planning_savings': ms, 'smart_shopping_savings': ss,
                'food_waste_prevention': wp, 'total_monthly_savings': total,
                'annual_projection': total * 12, 'meals_cooked': int(mc * 0.8), 'shopping_trips': ud}
    except:
        return {'meal_planning_savings': 0, 'smart_shopping_savings': 0, 'food_waste_prevention': 0,
                'total_monthly_savings': 0, 'annual_projection': 0, 'meals_cooked': 0, 'shopping_trips': 0}

def db_get_meal_plan(start_date):
    try:
        r = supabase.table("meal_plan").select("*").eq("user_id", user_id).gte("date", start_date.isoformat()).lte("date", (start_date + timedelta(days=6)).isoformat()).execute()
        wp = {}
        for meal in (r.data or []):
            d = meal['date']
            if d not in wp: wp[d] = []
            wp[d].append(meal)
        return wp
    except: return {}

def db_add_meal(meal_date, meal_type, recipe_name):
    try:
        supabase.table("meal_plan").insert({
            "user_id": user_id, "date": meal_date.isoformat(),
            "meal_type": meal_type, "recipe_name": recipe_name, "servings": 1
        }).execute()
    except: pass

def db_consume_ingredients(ingredient_names):
    report, depleted = [], []
    for ing in ingredient_names:
        try:
            r = supabase.table("inventory").select("*").eq("user_id", user_id).eq("status", "In Stock").ilike("item_name", f"%{ing}%").order("expiry_date").limit(1).execute()
            if r.data:
                item = r.data[0]
                if item['quantity'] > 1:
                    supabase.table("inventory").update({"quantity": item['quantity'] - 1}).eq("id", item['id']).execute()
                    report.append(f"Used 1 of '{item['item_name']}'")
                else:
                    supabase.table("inventory").update({"status": "Consumed"}).eq("id", item['id']).execute()
                    report.append(f"Finished '{item['item_name']}'")
                    depleted.append(item['item_name'])
            else:
                report.append(f"⚠️ '{ing}' not found")
        except: pass
    return report, depleted

# --- SIDEBAR ---
st.sidebar.title("🏠 Home OS Pro")
if user_picture:
    st.sidebar.image(user_picture, width=40)
st.sidebar.markdown(f"**Welcome, {user_name.split()[0]}!** 👋")
if st.sidebar.button("🚪 Sign Out", use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
savings = db_calculate_savings()
st.sidebar.subheader("💪 Monthly Impact")
if savings['total_monthly_savings'] > 0:
    st.sidebar.success(f"🎉 Saved: ${savings['total_monthly_savings']:.2f}")
    st.sidebar.progress(min(savings['total_monthly_savings'] / 500, 1.0))
else:
    st.sidebar.info("💡 Add groceries to see your impact!")

st.sidebar.markdown("---")
scanner = BarcodeScanner()
receipt_scanner_obj = ReceiptScanner()

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
                        if price_input > 0: db_record_purchase(new_item, price_input, store_input)
                        st.toast(f"✅ Added {new_item}!")
                    else:
                        db_add_to_shopping_list(new_item, price_input)
                        st.toast("✅ Added to list!")
                    st.rerun()
    with qa_tab2:
        barcode_input = st.text_input("Enter UPC/EAN")
        if st.button("🔍 Lookup"):
            if barcode_input:
                with st.spinner("Scanning..."):
                    product = scanner.lookup_barcode(barcode_input)
                    if product:
                        st.success(f"Found: **{product['name']}**")
                        if st.button("Add to Fridge"):
                            db_add_item(product['name'])
                            st.rerun()
                    else: st.error("Not found")
    with qa_tab3:
        img_file = st.camera_input("Take Photo")
        if not img_file: img_file = st.file_uploader("Or Upload", type=['jpg','png','jpeg'])
        if img_file:
            if st.button("🚀 Process Receipt"):
                with st.spinner("AI reading receipt..."):
                    results = receipt_scanner_obj.scan_receipt(img_file)
                    st.session_state['scan_results'] = results
        if 'scan_results' in st.session_state:
            results = st.session_state['scan_results']
            if "error" in results: st.info(results['error'])
            else:
                st.success(f"Found {len(results)} items!")
                with st.form("receipt_review"):
                    selected = []
                    for i, item in enumerate(results):
                        c1, c2 = st.columns([3,1])
                        c1.write(f"**{item['item']}** (${item['price']})")
                        if c2.checkbox("Add", value=True, key=f"scan_{i}"): selected.append(item)
                    store_name = st.text_input("Store", "Grocery Store")
                    if st.form_submit_button("✅ Save Selected"):
                        for item in selected:
                            db_add_item(item['item'], quantity=item.get('qty',1), price=item['price'], store=store_name)
                            db_record_purchase(item['item'], item['price'], store=store_name)
                        st.toast(f"Saved {len(selected)} items!")
                        del st.session_state['scan_results']
                        st.rerun()

# --- TABS ---
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💪 My Impact", "🧊 Fridge", "🛒 Shopping List",
    "📅 Meal Planner", "👨‍🍳 Recipe Rescue", "📊 Analytics"
])

with tab0:
    st.title(f"💪 {user_name.split()[0]}'s Household Impact")
    st.caption("The real economic value you bring to your family every month")
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 This Month Saved", f"${savings['total_monthly_savings']:.2f}", "Direct cash retained")
    col2.metric("🍳 Meals Cooked", f"{savings['meals_cooked']} meals", f"${savings['meals_cooked'] * 35:.2f} vs. eating out")
    col3.metric("📈 Annual Projection", f"${savings['annual_projection']:.2f}")
    st.markdown("---")
    c1, c2 = st.columns(2)
    chef_value = savings['meals_cooked'] * 35
    shopper_value = savings['shopping_trips'] * 10
    admin_value = 100.0
    total_value = chef_value + shopper_value + admin_value
    with c1:
        st.markdown("**💸 Direct Savings**")
        st.write(f"🍳 Meal planning: **${savings['meal_planning_savings']:.2f}**")
        st.write(f"🛒 Smart shopping: **${savings['smart_shopping_savings']:.2f}**")
        st.write(f"♻️ Waste prevention: **${savings['food_waste_prevention']:.2f}**")
    with c2:
        st.markdown("**💼 Labor Value**")
        st.write(f"👨‍🍳 Chef services: **${chef_value:.2f}**")
        st.write(f"🛒 Personal shopper: **${shopper_value:.2f}**")
        st.write(f"🧮 Admin work: **${admin_value:.2f}**")
    st.markdown("---")
    st.success(f"### 🌟 You added **${total_value:.2f}** in value this month. Annual: **${total_value*12:,.2f}**")
    achievements = []
    if savings['food_waste_prevention'] >= 25: achievements.append(("♻️", "Waste Warrior", f"Prevented ${savings['food_waste_prevention']:.2f}!"))
    if savings['smart_shopping_savings'] >= 30: achievements.append(("🎯", "Deal Hunter", f"Saved ${savings['smart_shopping_savings']:.2f}!"))
    if savings['meals_cooked'] >= 10: achievements.append(("👨‍🍳", "Meal Prep Master", f"{savings['meals_cooked']} meals cooked!"))
    if savings['total_monthly_savings'] >= 100: achievements.append(("💪", "Budget Hero", f"${savings['total_monthly_savings']:.2f} saved!"))
    if achievements:
        st.markdown("---")
        st.subheader("🏆 Achievements")
        cols = st.columns(len(achievements))
        for i, (icon, title, desc) in enumerate(achievements):
            with cols[i]:
                st.success(f"{icon} **{title}**")
                st.caption(desc)

with tab1:
    st.header("🧊 Your Fridge")
    df = db_get_inventory()
    if not df.empty:
        df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
        today = date.today()
        df['days_left'] = (df['expiry_date'] - today).apply(lambda x: x.days)
        df = df.sort_values('days_left')
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("In Stock", len(df))
        c2.metric("Expiring Soon", len(df[df['days_left'] < 4]), delta_color="inverse")
        c3.metric("Total Value", f"${df['price'].sum():.2f}")
        c4.metric("Frozen", len(df[df['storage'] == 'frozen']))
        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 2, 1.5, 1.5, 1])
                c1.markdown(f"**{row['item_name'].title()}**")
                if row.get('decision_reason'): c1.caption(f"ℹ️ {row['decision_reason']}")
                days = row['days_left']
                c2.write(f"🔴 Expired {abs(days)}d ago" if days < 0 else f"🟠 Expires in {days}d" if days < 4 else f"🟢 Good ({days}d)")
                c3.caption(f"{row['quantity']} {row['unit']} ({row['storage']})")
                if row.get('price'): c4.write(f"${row['price']:.2f}")
                if c5.button("🗑️", key=f"del_{row['id']}"): db_delete_item(row['id']); st.rerun()
    else:
        st.info("Your fridge is empty! Add items using the sidebar.")

with tab2:
    st.header("🛒 Shopping List")
    shop_df = db_get_shopping_list()
    if not shop_df.empty:
        st.metric("Items to Buy", len(shop_df))
        for cat in sorted(shop_df['category'].unique()):
            st.markdown(f"### {cat}")
            for _, row in shop_df[shop_df['category'] == cat].iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 1.5, 1, 1])
                    c1.write(f"**{row['item_name'].title()}**")
                    if row.get('estimated_price'): c1.caption(f"Est. ${row['estimated_price']:.2f}")
                    price = c2.number_input("Price", 0.0, 1000.0, float(row['estimated_price']) if row.get('estimated_price') else 0.0, step=0.01, key=f"p_{row['id']}")
                    if c3.button("✅", key=f"buy_{row['id']}"): db_move_to_fridge(row['item_name'], price=price); st.toast(f"✅ Bought!"); st.rerun()
                    if c4.button("❌", key=f"rem_{row['id']}"): db_delete_item(row['id'], "shopping_list"); st.rerun()
    else:
        st.success("✅ Shopping list is empty!")

with tab3:
    st.header("📅 Weekly Meal Planner")
    start_date = st.date_input("Week Starting", value=date.today() - timedelta(days=date.today().weekday()))
    week_plan = db_get_meal_plan(start_date)
    for i, day_name in enumerate(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']):
        current_date = start_date + timedelta(days=i)
        st.subheader(f"{day_name} — {current_date.strftime('%b %d')}")
        with st.expander("➕ Add meal"):
            with st.form(f"meal_{i}"):
                m_type = st.selectbox("Type", ['breakfast','lunch','dinner','snack'])
                r_name = st.text_input("Meal Name")
                if st.form_submit_button("Save"):
                    if r_name: db_add_meal(current_date, m_type, r_name); st.toast("Added!"); st.rerun()
        if current_date.isoformat() in week_plan:
            for meal in week_plan[current_date.isoformat()]:
                with st.container(border=True):
                    c1, c2 = st.columns([1,4])
                    c1.write(f"**{meal['meal_type'].title()}**")
                    c2.write(meal['recipe_name'])

with tab4:
    st.header("👨‍🍳 Recipe Rescue")
    if st.button("🆘 Find Recipes Using Expiring Food", type="primary"):
        try:
            expiring = supabase.table("inventory").select("item_name").eq("user_id", user_id).eq("status", "In Stock").lte("expiry_date", (date.today() + timedelta(days=7)).isoformat()).execute()
            if expiring.data:
                from recipe_manager import suggest_recipes_from_list
                st.session_state['recipes'] = suggest_recipes_from_list(list(set([r['item_name'] for r in expiring.data])))
            else:
                st.info("No food expiring soon! 🎉")
        except Exception as e:
            st.error(f"Error: {e}")
    if 'recipes' in st.session_state:
        recipes = st.session_state['recipes']
        if isinstance(recipes, list):
            for r in recipes:
                with st.container(border=True):
                    c1, c2 = st.columns([1,3])
                    c1.image(r['image'], width=120)
                    with c2:
                        st.subheader(r['title'])
                        used = [i['name'] for i in r['usedIngredients']]
                        missed = [i['name'] for i in r['missedIngredients']]
                        st.caption(f"✨ Uses: {', '.join(used)}")
                        if missed: st.caption(f"🛒 Needs: {', '.join(missed)}")
                        b1, b2 = st.columns(2)
                        if missed and b1.button("Add Missing", key=f"s_{r['id']}"):
                            for m in missed: db_add_to_shopping_list(m)
                            st.toast("Added!")
                        if b2.button("🔥 Cook This", key=f"c_{r['id']}"):
                            report, _ = db_consume_ingredients(used)
                            st.balloons()
                            for line in report: st.write(f"• {line}")
        else:
            st.warning(recipes.get('error', 'No recipes found.'))

with tab5:
    st.header("📊 Analytics")
    budget = db_get_budget()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("💰 Budget")
        limit = float(budget.get('budget_limit', 500))
        spent = float(budget.get('current_spent', 0))
        st.metric("Monthly Budget", f"${limit:.2f}")
        st.metric("Spent", f"${spent:.2f}", delta=f"${limit-spent:.2f} remaining")
        st.progress(min(spent/limit, 1.0) if limit > 0 else 0)
        with st.expander("⚙️ Update Budget"):
            with st.form("budget_form"):
                new_b = st.number_input("New Budget ($)", 0.0, 10000.0, limit)
                if st.form_submit_button("Update"):
                    supabase.table("budget_settings").update({"budget_limit": new_b, "current_spent": 0}).eq("user_id", user_id).execute()
                    st.toast("Updated!")
                    st.rerun()
    with c2:
        st.subheader("📈 Spending by Category")
        try:
            ph = supabase.table("price_history").select("item_name, price").eq("user_id", user_id).execute()
            if ph.data:
                logic = InventoryLogic()
                df_ph = pd.DataFrame(ph.data)
                df_ph['category'] = df_ph['item_name'].apply(lambda x: logic.normalize_item(x)['category'])
                import plotly.express as px
                fig = px.pie(df_ph.groupby('category')['price'].sum().reset_index(), values='price', names='category')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Add purchases to see breakdown.")
        except:
            st.info("Add purchases to see analytics.")

st.markdown("---")
st.caption("Home OS Pro | Built with ❤️ for stay-at-home parents")

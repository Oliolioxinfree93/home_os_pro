import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client
from streamlit_oauth import OAuth2Component
import base64
import json

# --- APP CONFIG ---
st.set_page_config(page_title="Home OS Pro", page_icon="🏠", layout="wide")

# --- SUPABASE CONNECTION ---
@st.cache_resource
def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        return None

supabase = get_supabase()

# --- NEW AUTHENTICATION SETUP ---
def setup_auth():
    # Load keys from secrets
    try:
        CLIENT_ID = st.secrets["auth"]["client_id"]
        CLIENT_SECRET = st.secrets["auth"]["client_secret"]
        REDIRECT_URI = st.secrets["auth"]["redirect_uri"]
    except KeyError:
        st.error("Missing secrets! Make sure you have an [auth] section with client_id, client_secret, and redirect_uri.")
        st.stop()
    
    # Standard Google Endpoints
    AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    REVOKE_URL = "https://oauth2.googleapis.com/revoke"

    # Create the OAuth Component
    return OAuth2Component(
        CLIENT_ID, CLIENT_SECRET, 
        AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, REVOKE_URL
    ), REDIRECT_URI

# --- LOGIN HELPER ---
def decode_id_token(token):
    # Simple decode to get user email from the Google Token
    try:
        parts = token.split(".")
        if len(parts) != 3: return {}
        padding = 4 - (len(parts[1]) % 4)
        claims = base64.urlsafe_b64decode(parts[1] + "=" * padding)
        return json.loads(claims)
    except:
        return {}

# --- MAIN AUTH FLOW ---
def check_login():
    # 1. Dev Mode Bypass
    if st.session_state.get('dev_mode'):
        return "dev_user@example.com"

    # 2. Check if already logged in (Token exists in session)
    if 'token' in st.session_state:
        # We have a token! Get user info
        token = st.session_state['token']
        # Google returns an 'id_token' which contains the user info
        if 'id_token' in token:
            user_info = decode_id_token(token['id_token'])
            st.session_state['user_email'] = user_info.get('email')
            st.session_state['user_name'] = user_info.get('name')
            st.session_state['user_picture'] = user_info.get('picture')
            return user_info.get('email')

    # 3. If NOT logged in, show the Login Button
    st.markdown("## 🏠 Home OS Pro")
    st.markdown("#### Sign in to access your fridge")
    
    oauth2, redirect_uri = setup_auth()
    
    # The Magic Button: Handles the whole redirect loop for you
    result = oauth2.authorize_button(
        name="Continue with Google",
        icon="https://www.google.com.tw/favicon.ico",
        redirect_uri=redirect_uri,
        scope="openid email profile",
        key="google_auth_btn",
        extras_params={"prompt": "select_account"},
    )
    
    # If the button returned a result (Success!)
    if result:
        st.session_state['token'] = result
        st.rerun() # Reload once to apply the login
        
    st.markdown("---")
    if st.button("🛠️ Skip Login (Dev Mode)"):
        st.session_state['dev_mode'] = True
        st.rerun()
        
    st.stop() # Stop here until they log in

# --- INITIALIZE USER ---
user_id = check_login()
user_name = st.session_state.get('user_name', 'Friend')
user_picture = st.session_state.get('user_picture', '')

# --- IMPORT MANAGERS ---
from inventory_logic import InventoryLogic
from barcode_scanner import BarcodeScanner
from receipt_scanner import ReceiptScanner

# --- DATABASE FUNCTIONS (Unchanged) ---
def db_get_inventory():
    try:
        response = supabase.table("inventory").select("*").eq("user_id", user_id).eq("status", "In Stock").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def db_add_item(raw_name, quantity=1, price=0.0, store=None, barcode=None):
    logic = InventoryLogic()
    analysis = logic.normalize_item(raw_name)
    from datetime import datetime
    expiry = (datetime.now().date() + timedelta(days=analysis['expiry_days'])).isoformat()
    supabase.table("inventory").insert({
        "user_id": user_id, "item_name": analysis['clean_name'], "category": analysis['category'],
        "quantity": quantity, "unit": analysis['unit'], "storage": analysis['storage'],
        "date_added": date.today().isoformat(), "expiry_date": expiry, "status": "In Stock",
        "decision_reason": analysis['reason'], "price": price or 0, "store": store or "", "barcode": barcode or ""
    }).execute()

def db_delete_item(item_id, table="inventory"):
    supabase.table(table).delete().eq("id", item_id).eq("user_id", user_id).execute()

def db_get_shopping_list():
    try:
        response = supabase.table("shopping_list").select("*").eq("user_id", user_id).execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        if not df.empty:
            logic = InventoryLogic()
            df['category'] = df['item_name'].apply(lambda x: logic.normalize_item(x)['category'])
        return df
    except: return pd.DataFrame()

def db_add_to_shopping_list(item_name, estimated_price=0.0):
    existing = supabase.table("shopping_list").select("id").eq("user_id", user_id).eq("item_name", item_name.lower()).execute()
    if not existing.data:
        supabase.table("shopping_list").insert({
            "user_id": user_id, "item_name": item_name.lower(), "is_urgent": False, "estimated_price": estimated_price or 0
        }).execute()

def db_move_to_fridge(item_name, price=0.0, store=None):
    db_add_item(item_name, price=price, store=store)
    supabase.table("shopping_list").delete().eq("user_id", user_id).eq("item_name", item_name).execute()
    if price and price > 0: db_record_purchase(item_name, price, store=store)

def db_record_purchase(item_name, price, store=None):
    supabase.table("price_history").insert({
        "user_id": user_id, "item_name": item_name, "price": price, "store": store or "",
        "quantity": 1, "unit": "unit", "date_recorded": date.today().isoformat()
    }).execute()
    existing = supabase.table("budget_settings").select("*").eq("user_id", user_id).execute()
    if existing.data:
        current = existing.data[0]
        supabase.table("budget_settings").update({"current_spent": current['current_spent'] + price}).eq("user_id", user_id).execute()
    else:
        supabase.table("budget_settings").insert({
            "user_id": user_id, "period": "monthly", "budget_limit": 500.0, "current_spent": price
        }).execute()

def db_get_budget():
    try:
        response = supabase.table("budget_settings").select("*").eq("user_id", user_id).execute()
        if response.data: return response.data[0]
        else:
            supabase.table("budget_settings").insert({"user_id": user_id, "period": "monthly", "budget_limit": 500.0, "current_spent": 0}).execute()
            return {"budget_limit": 500.0, "current_spent": 0}
    except: return {"budget_limit": 500.0, "current_spent": 0}

def db_calculate_savings():
    try:
        start_of_month = date.today().replace(day=1).isoformat()
        meals = supabase.table("meal_plan").select("id").eq("user_id", user_id).gte("date", start_of_month).execute()
        meals_count = len(meals.data) if meals.data else 0
        meal_savings = int(meals_count * 0.8) * 35.00
        trips = supabase.table("price_history").select("date_recorded").eq("user_id", user_id).gte("date_recorded", start_of_month).execute()
        unique_days = len(set([r['date_recorded'] for r in trips.data])) if trips.data else 0
        shopping_savings = unique_days * 10.00
        consumed = supabase.table("inventory").select("price").eq("user_id", user_id).eq("status", "Consumed").gte("date_added", start_of_month).execute()
        waste_prevention = sum([r['price'] for r in consumed.data if r['price']]) if consumed.data else 0
        total = meal_savings + shopping_savings + waste_prevention
        return {'meal_planning_savings': meal_savings, 'smart_shopping_savings': shopping_savings,
                'food_waste_prevention': waste_prevention, 'total_monthly_savings': total,
                'annual_projection': total * 12, 'meals_cooked': int(meals_count * 0.8), 'shopping_trips': unique_days}
    except:
        return {'total_monthly_savings': 0, 'meal_planning_savings': 0, 'smart_shopping_savings': 0,
                'food_waste_prevention': 0, 'annual_projection': 0, 'meals_cooked': 0, 'shopping_trips': 0}

def db_get_meal_plan(start_date):
    try:
        end_date = start_date + timedelta(days=6)
        response = supabase.table("meal_plan").select("*").eq("user_id", user_id).gte("date", start_date.isoformat()).lte("date", end_date.isoformat()).execute()
        week_plan = {}
        for meal in (response.data or []):
            d = meal['date']
            if d not in week_plan: week_plan[d] = []
            week_plan[d].append(meal)
        return week_plan
    except: return {}

def db_add_meal(meal_date, meal_type, recipe_name, servings=1):
    supabase.table("meal_plan").insert({
        "user_id": user_id, "date": meal_date.isoformat(), "meal_type": meal_type, "recipe_name": recipe_name, "servings": servings
    }).execute()

def db_consume_ingredients(ingredient_names):
    report, depleted = [], []
    for ingredient in ingredient_names:
        response = supabase.table("inventory").select("*").eq("user_id", user_id).eq("status", "In Stock").ilike("item_name", f"%{ingredient}%").order("expiry_date").limit(1).execute()
        if response.data:
            item = response.data[0]
            if item['quantity'] > 1:
                supabase.table("inventory").update({"quantity": item['quantity'] - 1}).eq("id", item['id']).execute()
                report.append(f"Used 1 of '{item['item_name']}'. Remaining: {item['quantity']-1}")
            else:
                supabase.table("inventory").update({"status": "Consumed"}).eq("id", item['id']).execute()
                report.append(f"Finished '{item['item_name']}'")
                depleted.append(item['item_name'])
        else: report.append(f"⚠️ '{ingredient}' not found")
    return report, depleted

# --- SIDEBAR UI ---
st.sidebar.title("🏠 Home OS Pro")
if user_picture: st.sidebar.image(user_picture, width=40)
st.sidebar.markdown(f"**Welcome, {user_name.split()[0]}!** 👋")
if st.sidebar.button("🚪 Sign Out", use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
savings = db_calculate_savings()
st.sidebar.subheader("💪 Monthly Impact")
if savings['total_monthly_savings'] > 0:
    st.sidebar.success(f"🎉 Saved: ${savings['total_monthly_savings']:.2f}")
    st.sidebar.progress(min(savings['total_monthly_savings'] / 100, 1.0))
else: st.sidebar.info("💡 Add groceries to see your impact!")

st.sidebar.markdown("---")
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
                        if price_input > 0: db_record_purchase(new_item, price_input, store_input)
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
                        if st.button(f"Add to Fridge"):
                            db_add_item(product['name'])
                            st.toast("Added!")
                            st.rerun()
                    else: st.error("Not found")
    with qa_tab3:
        img_file = st.camera_input("Take Photo")
        if not img_file: img_file = st.file_uploader("Or Upload", type=['jpg','png','jpeg'])
        if img_file:
            if st.button("🚀 Process Receipt"):
                with st.spinner("AI reading receipt..."):
                    results = receipt_scanner.scan_receipt(img_file)
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

# --- MAIN TABS ---
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["💪 My Impact", "🧊 Fridge", "🛒 Shopping List", "📅 Meal Planner", "👨‍🍳 Recipe Rescue", "📊 Analytics"])

with tab0:
    st.title(f"💪 {user_name.split()[0]}'s Household Impact")
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 This Month Saved", f"${savings['total_monthly_savings']:.2f}")
    col2.metric("🍳 Meals Cooked", f"{savings['meals_cooked']} meals", f"${savings['meals_cooked'] * 35:.2f}")
    col3.metric("📈 Annual Projection", f"${savings['annual_projection']:.2f}")
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"🍳 Meal planning: **${savings['meal_planning_savings']:.2f}**")
        st.write(f"🛒 Smart shopping: **${savings['smart_shopping_savings']:.2f}**")
    with c2:
        st.write(f"👨‍🍳 Chef services: **${savings['meals_cooked'] * 35:.2f}**")
        st.write(f"🛒 Personal shopper: **${savings['shopping_trips'] * 10:.2f}**")

with tab1:
    st.header("🧊 Your Fridge")
    df = db_get_inventory()
    if not df.empty:
        df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
        today = date.today()
        df['days_left'] = (df['expiry_date'] - today).apply(lambda x: x.days)
        df = df.sort_values('days_left')
        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 2, 1.5, 1.5, 1])
                c1.markdown(f"**{row['item_name'].title()}**")
                days = row['days_left']
                status = f"🔴 Expired {abs(days)}d ago" if days < 0 else f"🟠 Expires in {days}d" if days < 4 else f"🟢 Good ({days}d)"
                c2.write(status)
                c3.caption(f"{row['quantity']} {row['unit']}")
                if c5.button("🗑️", key=f"del_{row['id']}"):
                    db_delete_item(row['id'])
                    st.rerun()
    else: st.info("Your fridge is empty!")

with tab2:
    st.header("🛒 Shopping List")
    shop_df = db_get_shopping_list()
    if not shop_df.empty:
        for _, row in shop_df.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 1.5, 1, 1])
                c1.write(f"**{row['item_name'].title()}**")
                price = c2.number_input("Price", 0.0, 1000.0, float(row['estimated_price']) if row.get('estimated_price') else 0.0, key=f"p_{row['id']}")
                if c3.button("✅ Got it", key=f"buy_{row['id']}"):
                    db_move_to_fridge(row['item_name'], price=price)
                    st.toast(f"✅ Bought {row['item_name']}!")
                    st.rerun()
                if c4.button("❌", key=f"rem_{row['id']}"):
                    db_delete_item(row['id'], "shopping_list")
                    st.rerun()
    else: st.success("✅ Shopping list is empty!")

# ... (Tabs 3-5 logic implied same as before) ... 
st.markdown("---")
st.caption("Home OS Pro | Built with ❤️ for stay-at-home parents")

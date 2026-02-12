import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from supabase import create_client
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from translations import get_text
import os
import json

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

st.set_page_config(page_title="Home OS Pro", page_icon="🏠", layout="wide")

# --- LANGUAGE SELECTOR ---
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'en'

def t(key, *args):
    return get_text(st.session_state['lang'], key, *args)

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
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_uri=REDIRECT_URI
    )

def check_login():
    if st.session_state.get('dev_mode'):
        return st.session_state.get('user_id', 'dev@example.com')
    if st.session_state.get('user_id'):
        return st.session_state['user_id']

    query_params = st.query_params
    if "code" in query_params:
        try:
            flow = get_flow()
            flow.fetch_token(code=query_params["code"])
            credentials = flow.credentials
            user_info = id_token.verify_oauth2_token(
                credentials.id_token,
                google_requests.Request(),
                st.secrets["auth"]["client_id"],
                clock_skew_in_seconds=10
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

    # Language selector on login page
    col_lang1, col_lang2, col_lang3 = st.columns([3, 1, 1])
    with col_lang2:
        if st.button("🇺🇸 English", use_container_width=True,
                     type="primary" if st.session_state['lang'] == 'en' else "secondary"):
            st.session_state['lang'] = 'en'
            st.rerun()
    with col_lang3:
        if st.button("🇲🇽 Español", use_container_width=True,
                     type="primary" if st.session_state['lang'] == 'es' else "secondary"):
            st.session_state['lang'] = 'es'
            st.rerun()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"# 🏠 {t('app_title')}")
        st.markdown(f"### {t('app_tagline')}")
        st.markdown("---")
        st.markdown(t('login_track'))
        st.markdown(t('login_savings'))
        st.markdown(t('login_meals'))
        st.markdown(t('login_waste'))
        st.markdown(t('login_impact'))
        st.markdown("---")

        try:
            flow = get_flow()
            auth_url, _ = flow.authorization_url(
                prompt="select_account",
                access_type="offline",
                include_granted_scopes="false"
            )
            st.link_button(f"🔑 {t('sign_in_google')}", auth_url, use_container_width=True)
            st.caption(t('login_private'))
        except Exception as e:
            st.error(f"Auth setup error: {e}")

        st.markdown("---")
        if st.button(t('dev_mode'), use_container_width=True):
            st.session_state['dev_mode'] = True
            st.session_state['user_id'] = 'dev@example.com'
            st.session_state['user_name'] = 'Developer'
            st.session_state['user_picture'] = ''
            st.rerun()

    st.stop()

# --- INIT ---
user_id = check_login()
user_name = st.session_state.get('user_name', 'Friend')
user_picture = st.session_state.get('user_picture', '')

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
st.sidebar.title(f"🏠 {t('app_title')}")

# Language toggle in sidebar
lang_col1, lang_col2 = st.sidebar.columns(2)
with lang_col1:
    if st.button("🇺🇸 EN", use_container_width=True,
                 type="primary" if st.session_state['lang'] == 'en' else "secondary"):
        st.session_state['lang'] = 'en'
        st.rerun()
with lang_col2:
    if st.button("🇲🇽 ES", use_container_width=True,
                 type="primary" if st.session_state['lang'] == 'es' else "secondary"):
        st.session_state['lang'] = 'es'
        st.rerun()

st.sidebar.markdown("---")
if user_picture:
    st.sidebar.image(user_picture, width=40)
st.sidebar.markdown(f"**{t('welcome')}, {user_name.split()[0]}!** 👋")
if st.sidebar.button(t('sign_out'), use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
savings = db_calculate_savings()
st.sidebar.subheader(t('monthly_impact'))
if savings['total_monthly_savings'] > 0:
    st.sidebar.success(f"{t('saved_this_month')}: ${savings['total_monthly_savings']:.2f}")
    st.sidebar.progress(min(savings['total_monthly_savings'] / 500, 1.0))
else:
    st.sidebar.info(t('add_groceries_prompt'))

st.sidebar.markdown("---")
scanner = BarcodeScanner()
receipt_scanner_obj = ReceiptScanner()

with st.sidebar.expander(t('quick_add'), expanded=True):
    qa_tab1, qa_tab2, qa_tab3 = st.tabs([t('tab_type'), t('tab_barcode'), t('tab_receipt')])
    with qa_tab1:
        with st.form("add_form"):
            new_item = st.text_input(t('item_name'))
            qty = st.number_input(t('quantity'), 1, 100, 1)
            price_input = st.number_input(t('price'), 0.0, 1000.0, 0.0, step=0.01)
            store_input = st.text_input(t('store'))
            dest = st.radio(t('add_to'), [t('fridge'), t('shopping_list')])
            if st.form_submit_button(t('add_item')):
                if new_item:
                    if dest == t('fridge'):
                        db_add_item(new_item, qty, price_input, store_input)
                        if price_input > 0: db_record_purchase(new_item, price_input, store_input)
                        st.toast(f"{t('added_to_fridge')} {new_item}!")
                    else:
                        db_add_to_shopping_list(new_item, price_input)
                        st.toast(t('added_to_list'))
                    st.rerun()
    with qa_tab2:
        barcode_input = st.text_input(t('enter_barcode'))
        if st.button(t('lookup')):
            if barcode_input:
                with st.spinner(t('scanning')):
                    product = scanner.lookup_barcode(barcode_input)
                    if product:
                        st.success(f"{t('found')}: **{product['name']}**")
                        if st.button(t('add_to_fridge')):
                            db_add_item(product['name'])
                            st.rerun()
                    else: st.error(t('not_found'))
    with qa_tab3:
        img_file = st.camera_input(t('take_photo'))
        if not img_file: img_file = st.file_uploader(t('or_upload'), type=['jpg','png','jpeg'])
        if img_file:
            if st.button(t('process_receipt')):
                with st.spinner(t('reading_receipt')):
                    results = receipt_scanner_obj.scan_receipt(img_file)
                    st.session_state['scan_results'] = results
        if 'scan_results' in st.session_state:
            results = st.session_state['scan_results']
            if "error" in results: st.info(results['error'])
            else:
                st.success(t('found_items', len(results)))
                with st.form("receipt_review"):
                    selected = []
                    for i, item in enumerate(results):
                        c1, c2 = st.columns([3,1])
                        c1.write(f"**{item['item']}** (${item['price']})")
                        if c2.checkbox("✓", value=True, key=f"scan_{i}"): selected.append(item)
                    store_name = st.text_input(t('store_name'), "Walmart")
                    if st.form_submit_button(t('save_selected')):
                        for item in selected:
                            db_add_item(item['item'], quantity=item.get('qty',1), price=item['price'], store=store_name)
                            db_record_purchase(item['item'], item['price'], store=store_name)
                        st.toast(f"{t('save_selected')}!")
                        del st.session_state['scan_results']
                        st.rerun()

# --- MAIN TABS ---
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    t('tab_impact'), t('tab_fridge'), t('tab_shopping'),
    t('tab_meals'), t('tab_recipes'), t('tab_analytics')
])

with tab0:
    st.title(f"💪 {user_name.split()[0]}{t('impact_title')}")
    st.caption(t('impact_subtitle'))
    col1, col2, col3 = st.columns(3)
    col1.metric(t('this_month_saved'), f"${savings['total_monthly_savings']:.2f}", t('direct_cash_retained'))
    col2.metric(t('meals_cooked'), f"{savings['meals_cooked']}", f"${savings['meals_cooked']*35:.2f} {t('vs_eating_out')}")
    col3.metric(t('annual_projection'), f"${savings['annual_projection']:.2f}")
    st.markdown("---")
    c1, c2 = st.columns(2)
    chef_value = savings['meals_cooked'] * 35
    shopper_value = savings['shopping_trips'] * 10
    admin_value = 100.0
    total_value = chef_value + shopper_value + admin_value
    with c1:
        st.markdown(t('direct_savings'))
        st.write(f"{t('meal_planning')} **${savings['meal_planning_savings']:.2f}**")
        st.caption(t('cooked_vs_restaurant'))
        st.write(f"{t('smart_shopping')} **${savings['smart_shopping_savings']:.2f}**")
        st.caption(t('saved_delivery'))
        st.write(f"{t('waste_prevention')} **${savings['food_waste_prevention']:.2f}**")
        st.caption(t('food_saved_expiring'))
    with c2:
        st.markdown(t('labor_value'))
        st.write(f"{t('chef_services')} **${chef_value:.2f}**")
        st.write(f"{t('personal_shopper')} **${shopper_value:.2f}**")
        st.write(f"{t('admin_work')} **${admin_value:.2f}**")
    st.markdown("---")
    st.success(t('bottom_line', f"{total_value:.2f}", f"{total_value*12:,.2f}"))
    achievements = []
    if savings['food_waste_prevention'] >= 25:
        achievements.append(("♻️", t('waste_warrior'), t('waste_warrior_desc', f"{savings['food_waste_prevention']:.2f}")))
    if savings['smart_shopping_savings'] >= 30:
        achievements.append(("🎯", t('deal_hunter'), t('deal_hunter_desc', f"{savings['smart_shopping_savings']:.2f}")))
    if savings['meals_cooked'] >= 10:
        achievements.append(("👨‍🍳", t('meal_prep_master'), t('meal_prep_master_desc', savings['meals_cooked'])))
    if savings['total_monthly_savings'] >= 100:
        achievements.append(("💪", t('budget_hero'), t('budget_hero_desc', f"{savings['total_monthly_savings']:.2f}")))
    if achievements:
        st.markdown("---")
        st.subheader(t('achievements'))
        cols = st.columns(len(achievements))
        for i, (icon, title, desc) in enumerate(achievements):
            with cols[i]:
                st.success(f"{icon} **{title}**")
                st.caption(desc)

with tab1:
    st.header(t('your_fridge'))
    df = db_get_inventory()
    if not df.empty:
        df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
        today = date.today()
        df['days_left'] = (df['expiry_date'] - today).apply(lambda x: x.days)
        df = df.sort_values('days_left')
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t('in_stock'), len(df))
        c2.metric(t('expiring_soon'), len(df[df['days_left'] < 4]), delta_color="inverse")
        c3.metric(t('total_value'), f"${df['price'].sum():.2f}")
        c4.metric(t('frozen'), len(df[df['storage'] == 'frozen']))
        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 2, 1.5, 1.5, 1])
                c1.markdown(f"**{row['item_name'].title()}**")
                if row.get('decision_reason'): c1.caption(f"ℹ️ {row['decision_reason']}")
                days = row['days_left']
                c2.write(t('expired_ago', abs(days)) if days < 0 else t('expires_in', days) if days < 4 else t('good', days))
                c3.caption(f"{row['quantity']} {row['unit']} ({row['storage']})")
                if row.get('price'): c4.write(f"${row['price']:.2f}")
                if c5.button("🗑️", key=f"del_{row['id']}"): db_delete_item(row['id']); st.rerun()
    else:
        st.info(t('fridge_empty'))

with tab2:
    st.header(t('shopping_list_title'))
    shop_df = db_get_shopping_list()
    if not shop_df.empty:
        st.metric(t('items_to_buy'), len(shop_df))
        for cat in sorted(shop_df['category'].unique()):
            st.markdown(f"### {cat}")
            for _, row in shop_df[shop_df['category'] == cat].iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 1.5, 1, 1])
                    c1.write(f"**{row['item_name'].title()}**")
                    if row.get('estimated_price'): c1.caption(f"Est. ${row['estimated_price']:.2f}")
                    price = c2.number_input(t('price'), 0.0, 1000.0,
                        float(row['estimated_price']) if row.get('estimated_price') else 0.0,
                        step=0.01, key=f"p_{row['id']}")
                    if c3.button(t('got_it'), key=f"buy_{row['id']}"):
                        db_move_to_fridge(row['item_name'], price=price)
                        st.toast(f"{t('bought')} {row['item_name']}!")
                        st.rerun()
                    if c4.button("❌", key=f"rem_{row['id']}"): db_delete_item(row['id'], "shopping_list"); st.rerun()
    else:
        st.success(t('shopping_list_empty'))

with tab3:
    st.header(t('meal_planner_title'))
    start_date = st.date_input(t('week_starting'), value=date.today() - timedelta(days=date.today().weekday()))
    week_plan = db_get_meal_plan(start_date)
    meal_types = [t('breakfast'), t('lunch'), t('dinner'), t('snack')]
    day_names_en = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    day_names_es = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
    day_names = day_names_es if st.session_state['lang'] == 'es' else day_names_en
    for i, day_name in enumerate(day_names):
        current_date = start_date + timedelta(days=i)
        st.subheader(f"{day_name} — {current_date.strftime('%b %d')}")
        with st.expander(t('add_meal')):
            with st.form(f"meal_{i}"):
                m_type = st.selectbox(t('meal_type'), meal_types)
                r_name = st.text_input(t('meal_name'))
                if st.form_submit_button(t('save')):
                    if r_name: db_add_meal(current_date, m_type, r_name); st.toast(t('meal_added')); st.rerun()
        if current_date.isoformat() in week_plan:
            for meal in week_plan[current_date.isoformat()]:
                with st.container(border=True):
                    c1, c2 = st.columns([1,4])
                    c1.write(f"**{meal['meal_type'].title()}**")
                    c2.write(meal['recipe_name'])

with tab4:
    st.header(t('recipe_rescue_title'))
    st.caption(t('recipe_subtitle'))
    if st.button(t('find_recipes'), type="primary"):
        try:
            expiring = supabase.table("inventory").select("item_name").eq("user_id", user_id).eq("status", "In Stock").lte("expiry_date", (date.today() + timedelta(days=7)).isoformat()).execute()
            if expiring.data:
                from recipe_manager import suggest_recipes_from_list
                st.session_state['recipes'] = suggest_recipes_from_list(list(set([r['item_name'] for r in expiring.data])))
            else:
                st.info(t('no_expiring'))
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
                        st.caption(f"{t('uses')} {', '.join(used)}")
                        if missed: st.caption(f"{t('needs')} {', '.join(missed)}")
                        b1, b2 = st.columns(2)
                        if missed and b1.button(t('add_missing'), key=f"s_{r['id']}"):
                            for m in missed: db_add_to_shopping_list(m)
                            st.toast("✅")
                        if b2.button(t('cook_this'), key=f"c_{r['id']}"):
                            report, _ = db_consume_ingredients(used)
                            st.balloons()
                            for line in report: st.write(f"• {line}")
        else:
            st.warning(t('no_recipes'))

with tab5:
    st.header(t('analytics_title'))
    budget = db_get_budget()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(t('budget_title'))
        limit = float(budget.get('budget_limit', 500))
        spent = float(budget.get('current_spent', 0))
        st.metric(t('monthly_budget'), f"${limit:.2f}")
        st.metric(t('spent_this_month'), f"${spent:.2f}", delta=f"${limit-spent:.2f} {t('remaining')}")
        st.progress(min(spent/limit, 1.0) if limit > 0 else 0)
        with st.expander(t('update_budget')):
            with st.form("budget_form"):
                new_b = st.number_input(t('new_budget'), 0.0, 10000.0, limit)
                if st.form_submit_button(t('update')):
                    supabase.table("budget_settings").update({"budget_limit": new_b, "current_spent": 0}).eq("user_id", user_id).execute()
                    st.toast(t('updated'))
                    st.rerun()
    with c2:
        st.subheader(t('spending_by_category'))
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
                st.info(t('add_purchases'))
        except:
            st.info(t('add_purchases'))

st.markdown("---")
st.caption(t('built_with_love'))

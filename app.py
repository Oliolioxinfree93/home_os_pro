import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from supabase import create_client
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from translations import get_text
from styles import get_css
from report_generator import generate_monthly_report
import os
import json
import streamlit.components.v1 as components

# Only disable HTTPS requirement in local dev, never in production
if os.getenv('ENV') == 'dev':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

st.set_page_config(page_title="Home OS Pro", page_icon="🏠", layout="wide")
st.markdown(get_css(), unsafe_allow_html=True)

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
            if user_info.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError("Invalid token issuer")
            # Use 'sub' as user_id — Google's immutable unique ID (safer than email)
            # Store email separately for display only
            st.session_state['user_id'] = user_info['sub']
            st.session_state['user_email'] = user_info['email']
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

        # Dev mode only visible in local development
        if os.getenv('ENV') == 'dev':
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

    # Shareable monthly report
    st.markdown("---")
    report_col1, report_col2 = st.columns([3, 1])
    report_col1.markdown("#### 📄 " + ("Monthly Report" if st.session_state['lang'] == 'en' else "Reporte Mensual"))
    report_col1.caption("Share your contribution with your partner or save it for your records." if st.session_state['lang'] == 'en' else "Comparte tu contribución con tu pareja o guárdala para tus registros.")
    if report_col2.button("📤 " + ("Generate" if st.session_state['lang'] == 'en' else "Generar"), use_container_width=True, type="primary"):
        st.session_state['show_report'] = True

    if st.session_state.get('show_report'):
        report_html = generate_monthly_report(user_name, savings, lang=st.session_state['lang'])
        st.components.v1.html(report_html, height=820, scrolling=True)
        st.download_button(
            label="⬇️ Download Report" if st.session_state['lang'] == 'en' else "⬇️ Descargar Reporte",
            data=report_html,
            file_name=f"HomeOS_Report_{__import__('datetime').date.today().strftime('%Y_%m')}.html",
            mime="text/html",
            use_container_width=True
        )
        st.caption("💡 To save as PDF: open the downloaded file in your browser → Print → Save as PDF" if st.session_state['lang'] == 'en' else "💡 Para guardar como PDF: abre el archivo en tu navegador → Imprimir → Guardar como PDF")
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
                c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1.5, 1.5, 1, 1])
                c1.markdown(f"**{row['item_name'].title()}**")
                if row.get('decision_reason'): c1.caption(f"ℹ️ {row['decision_reason']}")
                days = row['days_left']
                c2.write(t('expired_ago', abs(days)) if days < 0 else t('expires_in', days) if days < 4 else t('good', days))
                c3.caption(f"{row['quantity']} {row['unit']} ({row['storage']})")
                if row.get('price'): c4.write(f"${row['price']:.2f}")

                # Edit button
                edit_key = f"editing_{row['id']}"
                if c5.button("✏️", key=f"edit_btn_{row['id']}"):
                    st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                if c6.button("🗑️", key=f"del_{row['id']}"):
                    db_delete_item(row['id'])
                    st.rerun()

                # Edit form — shows inline when pencil clicked
                if st.session_state.get(edit_key, False):
                    with st.form(key=f"edit_form_{row['id']}"):
                        st.markdown("**✏️ Edit Item**" if st.session_state['lang'] == 'en' else "**✏️ Editar Producto**")
                        ec1, ec2, ec3 = st.columns(3)
                        new_name = ec1.text_input(
                            "Name" if st.session_state['lang'] == 'en' else "Nombre",
                            value=row['item_name'].title()
                        )
                        new_price = ec2.number_input(
                            "Price ($)" if st.session_state['lang'] == 'en' else "Precio ($)",
                            value=float(row['price']) if row.get('price') else 0.0,
                            step=0.01, min_value=0.0
                        )
                        new_qty = ec3.number_input(
                            "Quantity" if st.session_state['lang'] == 'en' else "Cantidad",
                            value=float(row['quantity']) if row.get('quantity') else 1.0,
                            step=1.0, min_value=0.0
                        )
                        ec4, ec5 = st.columns(2)
                        new_store = ec4.text_input(
                            "Store" if st.session_state['lang'] == 'en' else "Tienda",
                            value=row.get('store', '') or ''
                        )
                        new_expiry = ec5.date_input(
                            "Expiry Date" if st.session_state['lang'] == 'en' else "Fecha de Vencimiento",
                            value=row['expiry_date']
                        )
                        save_col, cancel_col = st.columns(2)
                        save = save_col.form_submit_button(
                            "💾 Save" if st.session_state['lang'] == 'en' else "💾 Guardar",
                            use_container_width=True
                        )
                        cancel = cancel_col.form_submit_button(
                            "Cancel" if st.session_state['lang'] == 'en' else "Cancelar",
                            use_container_width=True
                        )
                        if save:
                            try:
                                supabase.table("inventory").update({
                                    "item_name": new_name.lower(),
                                    "price": new_price,
                                    "quantity": new_qty,
                                    "store": new_store,
                                    "expiry_date": new_expiry.isoformat()
                                }).eq("id", row['id']).eq("user_id", user_id).execute()
                                st.session_state[edit_key] = False
                                st.toast("✅ Saved!" if st.session_state['lang'] == 'en' else "✅ ¡Guardado!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                        if cancel:
                            st.session_state[edit_key] = False
                            st.rerun()
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
                    # Edit name inline
                    edit_sl_key = f"edit_sl_{row['id']}"
                    if c4.button("✏️", key=f"edit_sl_btn_{row['id']}"):
                        st.session_state[edit_sl_key] = not st.session_state.get(edit_sl_key, False)
                    if st.session_state.get(edit_sl_key, False):
                        with st.form(f"edit_sl_form_{row['id']}"):
                            new_sl_name = st.text_input(
                                "Item name" if st.session_state['lang'] == 'en' else "Nombre",
                                value=row['item_name'].title()
                            )
                            sl_save, sl_cancel = st.columns(2)
                            if sl_save.form_submit_button("💾 Save" if st.session_state['lang'] == 'en' else "💾 Guardar"):
                                supabase.table("shopping_list").update({
                                    "item_name": new_sl_name.lower()
                                }).eq("id", row['id']).eq("user_id", user_id).execute()
                                st.session_state[edit_sl_key] = False
                                st.toast("✅ Updated!")
                                st.rerun()
                            if sl_cancel.form_submit_button("Cancel" if st.session_state['lang'] == 'en' else "Cancelar"):
                                st.session_state[edit_sl_key] = False
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
                    c1, c2, c3 = st.columns([1, 4, 1])
                    c1.write(f"**{meal['meal_type'].title()}**")
                    c2.write(meal['recipe_name'])
                    if c3.button("🗑️", key=f"del_meal_{meal['id']}"):
                        supabase.table("meal_plan").delete().eq("id", meal['id']).eq("user_id", user_id).execute()
                        st.rerun()

with tab4:
    st.header(t('recipe_rescue_title'))

    # Two recipe modes
    mode_en = ["🚨 Use Expiring Food", "🧊 Use Full Inventory"]
    mode_es = ["🚨 Usar Comida por Vencer", "🧊 Usar Todo el Inventario"]
    mode_labels = mode_es if st.session_state['lang'] == 'es' else mode_en
    recipe_mode = st.radio(
        "Find recipes based on:" if st.session_state['lang'] == 'en' else "Buscar recetas usando:",
        mode_labels,
        horizontal=True
    )

    if st.button(t('find_recipes'), type="primary"):
        try:
            from recipe_manager import suggest_recipes_from_list

            if recipe_mode == mode_labels[0]:
                # Expiring soon — within 7 days
                r = supabase.table("inventory").select("item_name").eq("user_id", user_id).eq("status", "In Stock").lte("expiry_date", (date.today() + timedelta(days=7)).isoformat()).execute()
                if r.data:
                    ingredients = list(set([i['item_name'] for i in r.data]))
                    label = "expiring"
                else:
                    st.info(t('no_expiring'))
                    ingredients = []
            else:
                # Full inventory
                r = supabase.table("inventory").select("item_name").eq("user_id", user_id).eq("status", "In Stock").execute()
                if r.data:
                    ingredients = list(set([i['item_name'] for i in r.data]))
                    label = "inventory"
                else:
                    st.info(t('fridge_empty'))
                    ingredients = []

            if ingredients:
                spinner_msg = "🤖 Finding recipes..." if st.session_state['lang'] == 'en' else "🤖 Buscando recetas..."
                with st.spinner(spinner_msg):
                    st.session_state['recipes'] = suggest_recipes_from_list(
                        ingredients,
                        lang=st.session_state['lang']
                    )
                    st.session_state['recipe_ingredients'] = ingredients

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
                        # Time and difficulty badges
                        if r.get('time') or r.get('difficulty'):
                            badge_col1, badge_col2, _ = st.columns([1, 1, 3])
                            if r.get('time'): badge_col1.caption(f"⏱️ {r['time']}")
                            if r.get('difficulty'): badge_col2.caption(f"📊 {r['difficulty']}")

                        used = [i['name'] for i in r.get('usedIngredients', [])]
                        missed = [i['name'] for i in r.get('missedIngredients', [])]
                        if used: st.caption(f"{t('uses')} {', '.join(used)}")
                        if missed: st.caption(f"{t('needs')} {', '.join(missed)}")

                        # Brief instructions preview
                        if r.get('instructions'):
                            st.caption(f"📝 {r['instructions']}")

                        b1, b2, b3 = st.columns(3)

                        # Add missing to shopping list
                        if missed and b1.button(t('add_missing'), key=f"s_{r['id']}"):
                            for m in missed:
                                db_add_to_shopping_list(m)
                            st.toast("✅")

                        # Get full recipe details
                        if b2.button("📖 Full Recipe" if st.session_state['lang'] == 'en' else "📖 Receta Completa", key=f"detail_{r['id']}"):
                            from recipe_manager import get_recipe_details
                            with st.spinner("Loading..." if st.session_state['lang'] == 'en' else "Cargando..."):
                                details = get_recipe_details(
                                    r['title'],
                                    st.session_state.get('recipe_ingredients', used),
                                    lang=st.session_state['lang']
                                )
                                st.session_state[f"details_{r['id']}"] = details

                        # Cook this — mark ingredients as consumed
                        if b3.button(t('cook_this'), key=f"c_{r['id']}"):
                            report, depleted = db_consume_ingredients(used)
                            st.balloons()
                            for line in report:
                                st.write(f"• {line}")
                            if depleted:
                                for item in depleted:
                                    db_add_to_shopping_list(item)
                                st.toast("🛒 Added depleted items to shopping list!")

                        # Show full recipe details if loaded
                        if f"details_{r['id']}" in st.session_state:
                            details = st.session_state[f"details_{r['id']}"]
                            if "error" not in details:
                                with st.expander("📖 Full Recipe", expanded=True):
                                    st.markdown(f"**Servings:** {details.get('servings', 4)} | **Time:** {details.get('time', '30 min')}")
                                    st.markdown("**Ingredients:**")
                                    for ing in details.get('ingredients', []):
                                        st.write(f"• {ing.get('amount', '')} {ing.get('item', '')}")
                                    st.markdown("**Instructions:**")
                                    for i, step in enumerate(details.get('steps', []), 1):
                                        st.write(f"{i}. {step}")
                                    if details.get('tips'):
                                        st.info(f"💡 {details['tips']}")
        else:
            st.warning(recipes.get('error', t('no_recipes')))

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
                fig = px.pie(df_ph.groupby('category')['price'].sum().reset_index(), values='price', names='category',
                             color_discrete_sequence=['#2D5016','#7A9E5F','#C8952A','#C4572A','#4a7c29','#a0c878'])
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_family='DM Sans')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(t('add_purchases'))
        except:
            st.info(t('add_purchases'))

    # Price comparison — full width below
    st.markdown("---")
    st.subheader("🏪 " + ("Price Comparison by Store" if st.session_state['lang'] == 'en' else "Comparación de Precios por Tienda"))
    st.caption("Which store gives you the best price on each item?" if st.session_state['lang'] == 'en' else "¿Qué tienda te da el mejor precio por producto?")

    try:
        ph_full = supabase.table("price_history").select("item_name, price, store, date_recorded").eq("user_id", user_id).execute()
        if ph_full.data and len(ph_full.data) >= 2:
            df_price = pd.DataFrame(ph_full.data)
            df_price = df_price[df_price['store'].notna() & (df_price['store'] != '')]

            if not df_price.empty:
                # Group by item + store, get average price
                comparison = df_price.groupby(['item_name', 'store'])['price'].agg(['mean', 'count']).reset_index()
                comparison.columns = ['Item', 'Store', 'Avg Price', 'Times Bought']
                comparison['Avg Price'] = comparison['Avg Price'].round(2)

                # Find cheapest store per item
                cheapest = comparison.loc[comparison.groupby('Item')['Avg Price'].idxmin()][['Item', 'Store', 'Avg Price']]
                cheapest = cheapest.rename(columns={'Store': 'Cheapest Store', 'Avg Price': 'Best Price'})

                # Only show items bought at 2+ stores (meaningful comparison)
                items_multi_store = comparison.groupby('Item')['Store'].nunique()
                items_to_compare = items_multi_store[items_multi_store >= 2].index

                if len(items_to_compare) > 0:
                    st.markdown("#### 🏆 " + ("Best Deals Found" if st.session_state['lang'] == 'en' else "Mejores Precios Encontrados"))
                    for item in items_to_compare:
                        item_data = comparison[comparison['Item'] == item].sort_values('Avg Price')
                        best_price = item_data.iloc[0]['Avg Price']
                        worst_price = item_data.iloc[-1]['Avg Price']
                        savings_pct = ((worst_price - best_price) / worst_price * 100)

                        with st.container(border=True):
                            h1, h2 = st.columns([3, 1])
                            h1.markdown(f"**{item.title()}**")
                            h2.markdown(f"💰 Save **{savings_pct:.0f}%**")
                            for _, store_row in item_data.iterrows():
                                is_best = store_row['Avg Price'] == best_price
                                prefix = "🥇 " if is_best else "　"
                                color = "#2D5016" if is_best else "#6B6B6B"
                                st.markdown(
                                    f"<span style='color:{color}'>{prefix}**{store_row['Store']}** — ${store_row['Avg Price']:.2f}</span>",
                                    unsafe_allow_html=True
                                )

                    # Total savings potential
                    total_potential = sum(
                        comparison[comparison['Item'] == item]['Avg Price'].max() -
                        comparison[comparison['Item'] == item]['Avg Price'].min()
                        for item in items_to_compare
                    )
                    st.success(f"🎯 {'Shopping smart on these items could save you' if st.session_state['lang'] == 'en' else 'Comprar inteligente en estos productos podría ahorrarte'} **${total_potential:.2f}** {'per trip' if st.session_state['lang'] == 'en' else 'por viaje'}")

                else:
                    st.info("📊 " + ("Buy the same item at different stores to see price comparisons here." if st.session_state['lang'] == 'en' else "Compra el mismo producto en diferentes tiendas para ver comparaciones aquí."))

                # Full price history table in expander
                with st.expander("📋 " + ("Full Price History" if st.session_state['lang'] == 'en' else "Historial Completo de Precios")):
                    display_df = comparison.sort_values(['Item', 'Avg Price'])
                    display_df.columns = ['Item', 'Store', 'Avg Price ($)', 'Times Bought']
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("🏪 " + ("Add the store name when saving receipts to enable price comparison." if st.session_state['lang'] == 'en' else "Agrega el nombre de la tienda al guardar recibos para activar la comparación de precios."))
        else:
            st.info("📊 " + ("Scan receipts from different stores to see which has the best prices." if st.session_state['lang'] == 'en' else "Escanea recibos de diferentes tiendas para ver cuál tiene los mejores precios."))
    except Exception as e:
        st.info("📊 " + ("Scan a few receipts to unlock price comparison." if st.session_state['lang'] == 'en' else "Escanea algunos recibos para activar la comparación de precios."))

st.markdown('<div class="footer-text">' + t('built_with_love') + '</div>', unsafe_allow_html=True)

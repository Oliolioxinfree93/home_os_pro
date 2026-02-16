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
from fridge_animation import get_fridge_animation, get_pantry_animation
import os
import json
import streamlit.components.v1 as components

# Only disable HTTPS requirement in local dev, never in production
if os.getenv('ENV') == 'dev':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

st.set_page_config(page_title="Home OS Pro", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")
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

def db_get_pantry():
    try:
        r = supabase.table("inventory").select("*").eq("user_id", user_id).eq("status", "In Stock").eq("storage", "pantry").execute()
        return pd.DataFrame(r.data) if r.data else pd.DataFrame()
    except: return pd.DataFrame()

def clean_item_name(name):
    """Strip markdown, asterisks, extra spaces from item names before saving."""
    import re
    name = name.replace('*', '').replace('_', '').replace('`', '')
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name

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
        if 'add_form_key' not in st.session_state:
            st.session_state['add_form_key'] = 0
        with st.form(f"add_form_{st.session_state['add_form_key']}"):
            new_item = st.text_input(t('item_name'))
            qty = st.number_input(t('quantity'), 1, 100, 1)
            price_input = st.number_input(t('price'), 0.0, 1000.0, 0.0, step=0.01)
            store_input = st.text_input(t('store'))
            pantry_label = "🏺 Pantry" if st.session_state['lang'] == 'en' else "🏺 Despensa"
            dest = st.radio(t('add_to'), [t('fridge'), pantry_label, t('shopping_list')])
            all_cats_en = ['Dairy','Meat','Produce','Bakery','Pantry','Frozen','Beverages','Snacks','Condiments','Grains','Cleaning','Personal Care','Other']
            all_cats_es = ['Lácteos','Carne','Verduras/Frutas','Panadería','Despensa','Congelados','Bebidas','Botanas','Condimentos','Granos','Limpieza','Cuidado Personal','Otro']
            all_cats = all_cats_es if st.session_state['lang'] == 'es' else all_cats_en
            auto_label = "🔍 Auto-detect" if st.session_state['lang'] == 'en' else "🔍 Auto-detectar"
            manual_cat = st.selectbox(
                "Category" if st.session_state['lang'] == 'en' else "Categoría",
                [auto_label] + all_cats
            )
            if st.form_submit_button(t('add_item')):
                if new_item:
                    if dest == t('fridge'):
                        db_add_item(new_item, qty, price_input, store_input)
                        if price_input > 0: db_record_purchase(new_item, price_input, store_input)
                        if manual_cat not in ("Auto-detect", "🔍 Auto-detect", "🔍 Auto-detectar"):
                            try:
                                r = supabase.table("inventory").select("id").eq("user_id", user_id).eq("item_name", new_item.lower()).order("id", desc=True).limit(1).execute()
                                if r.data:
                                    supabase.table("inventory").update({"category": manual_cat}).eq("id", r.data[0]['id']).execute()
                            except: pass
                        msg = f"{t('added_to_fridge')} {new_item}!"

                    elif dest == pantry_label:
                        try:
                            from inventory_logic import InventoryLogic
                            logic = InventoryLogic()
                            a = logic.normalize_item(new_item)
                            expiry = (__import__('datetime').date.today() + __import__('datetime').timedelta(days=180)).isoformat()
                            # Robust category fallback — if auto-detect fails, use Pantry
                            auto_cat = a.get('category', '')
                            if manual_cat not in ("Auto-detect", "🔍 Auto-detect", "🔍 Auto-detectar"):
                                final_cat = manual_cat
                            elif auto_cat and auto_cat.lower() not in ('unsorted', '', 'other'):
                                final_cat = auto_cat
                            else:
                                final_cat = 'Pantry'
                            supabase.table("inventory").insert({
                                "user_id": user_id, "item_name": clean_item_name(a['clean_name']), "category": final_cat,
                                "quantity": qty, "unit": a['unit'], "storage": "pantry",
                                "date_added": date.today().isoformat(), "expiry_date": expiry,
                                "status": "In Stock", "decision_reason": "Added to pantry",
                                "price": price_input or 0, "store": store_input or "", "barcode": ""
                            }).execute()
                            if price_input > 0: db_record_purchase(new_item, price_input, store_input)
                            msg = f"🏺 Added {new_item} to pantry!"
                        except Exception as e:
                            st.error(f"Error: {e}")
                            msg = None

                    else:
                        db_add_to_shopping_list(new_item, price_input)
                        msg = f"🛒 {t('added_to_list')}"

                    # Reset form by incrementing key, then rerun
                    st.session_state['add_form_key'] += 1
                    if msg: st.toast(msg)
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
                            db_add_item(clean_item_name(item['item']), quantity=item.get('qty',1), price=item['price'], store=store_name)
                            db_record_purchase(item['item'], item['price'], store=store_name)
                        st.toast(f"{t('save_selected')}!")
                        del st.session_state['scan_results']
                        st.rerun()

# --- MAIN TABS ---
# ── TODAY'S BRIEFING ──
try:
    _today = date.today()
    _inv = supabase.table("inventory").select("item_name,expiry_date,status").eq("user_id", user_id).eq("status","In Stock").execute()
    _sl  = supabase.table("shopping_list").select("id").eq("user_id", user_id).eq("bought", False).execute()
    _meal_q = supabase.table("meal_plan").select("meal_name").eq("user_id", user_id).eq("meal_date", date.today().isoformat()).eq("meal_type","dinner").execute()

    _expiring = []
    for it in _inv.data:
        try:
            ed = pd.to_datetime(it['expiry_date']).date()
            if (ed - _today).days <= 2:
                _expiring.append(it['item_name'].replace('*','').strip().title())
        except: pass

    _dinner = _meal_q.data[0]['meal_name'] if _meal_q.data else None
    _sl_count = len(_sl.data) if _sl.data else 0

    # Current rhythm block
    import datetime as _dt
    _hour = _dt.datetime.now().hour
    _cur_block = "morning" if _hour < 10 else "midday" if _hour < 13 else "afternoon" if _hour < 16 else "evening"
    _cur_block_label = {"morning":"Morning","midday":"Midday","afternoon":"Afternoon","evening":"Evening"}.get(_cur_block,"")
    try:
        _rhythm_now = supabase.table("daily_rhythm").select("must_do,done").eq("user_id", user_id).eq("day_of_week", date.today().strftime("%A")).eq("block_id", _cur_block).execute()
        _rhythm_must = _rhythm_now.data[0].get("must_do","") if _rhythm_now.data else ""
        _rhythm_done = _rhythm_now.data[0].get("done", False) if _rhythm_now.data else False
    except:
        _rhythm_must = ""
        _rhythm_done = False

    try:
        _mood_today = supabase.table("mood_checkins").select("score").eq("user_id", user_id).eq("checkin_date", _today.isoformat()).execute()
        _mood_done  = len(_mood_today.data) > 0
        _mood_score = _mood_today.data[0]['score'] if _mood_today.data else None
    except:
        _mood_done = False
        _mood_score = None

    _brief_col, _mood_col = st.columns([3, 1])

    with _brief_col:
        _parts = []
        if _rhythm_must and not _rhythm_done:
            _parts.append("🌅 **Now (" + _cur_block_label + "):** " + _rhythm_must)
        if _expiring:
            _elist = ", ".join(_expiring[:3]) + ("..." if len(_expiring) > 3 else "")
            _parts.append("⏰ **Expiring:** " + _elist)
        if _dinner:
            _parts.append("🍽️ **Tonight:** " + _dinner)
        if _sl_count:
            _parts.append("🛒 **Shopping:** " + str(_sl_count) + " item" + ("s" if _sl_count != 1 else ""))
        _lbl = "Today's Briefing" if st.session_state['lang']=='en' else "Resumen de Hoy"
        _border = "#7A9E5F" if not _parts else "#C8952A"
        _body   = "<br>".join(_parts) if _parts else ("✅ <strong>All good today!</strong>" if st.session_state['lang']=='en' else "✅ <strong>¡Todo bien hoy!</strong>")
        st.markdown(
            '<div style="background:white;border:1px solid #E8E4DE;border-left:4px solid ' + _border +             ';border-radius:12px;padding:12px 16px;margin-bottom:12px;">' +             '<div style="font-size:0.72rem;color:#6B6B6B;font-weight:600;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">' + _lbl + '</div>' +             _body + '</div>',
            unsafe_allow_html=True
        )

    with _mood_col:
        _mood_emojis = ["😩","😕","😐","🙂","😊"]
        if _mood_done and _mood_score:
            _disp_emoji = _mood_emojis[_mood_score - 1]
            st.markdown(
                '<div style="background:white;border:1px solid #E8E4DE;border-radius:12px;padding:10px;text-align:center;margin-bottom:12px;">' +
                '<div style="font-size:0.7rem;color:#6B6B6B;">' + ("Today's mood" if st.session_state['lang']=='en' else "Hoy") + '</div>' +
                '<div style="font-size:1.8rem;">' + _disp_emoji + '</div></div>',
                unsafe_allow_html=True
            )
        else:
            _mlabel = "How are you?" if st.session_state['lang']=='en' else "¿Cómo estás?"
            st.markdown('<div style="font-size:0.72rem;color:#6B6B6B;text-align:center;margin-bottom:4px;">' + _mlabel + '</div>', unsafe_allow_html=True)
            _mcols = st.columns(5)
            for _mi, (_mc, _me) in enumerate(zip(_mcols, _mood_emojis)):
                if _mc.button(_me, key="mood_btn_" + str(_mi+1)):
                    try:
                        supabase.table("mood_checkins").upsert({
                            "user_id": user_id, "checkin_date": _today.isoformat(), "score": _mi + 1
                        }, on_conflict="user_id,checkin_date").execute()
                    except:
                        supabase.table("mood_checkins").insert({
                            "user_id": user_id, "checkin_date": _today.isoformat(), "score": _mi + 1
                        }).execute()
                    st.rerun()
except Exception as _be:
    pass

# --- MAIN TABS ---
tab0, tab1, tab_pantry, tab2, tab3, tab4, tab_nutrition, tab_dump, tab_rhythm, tab5 = st.tabs([
    t('tab_impact'), t('tab_fridge'),
    "🏺 " + ("Pantry" if st.session_state['lang'] == 'en' else "Despensa"),
    t('tab_shopping'), t('tab_meals'), t('tab_recipes'),
    "🥗 " + ("Nutrition" if st.session_state['lang'] == 'en' else "Nutrición"),
    "🧠 " + ("Brain Dump" if st.session_state['lang'] == 'en' else "Descarga Mental"),
    "🌅 " + ("Daily Rhythm" if st.session_state['lang'] == 'en' else "Ritmo Diario"),
    t('tab_analytics')
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
    # Exclude pantry items from fridge view
    if not df.empty and 'storage' in df.columns:
        df = df[df['storage'] != 'pantry']
    if not df.empty:
        df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
        today = date.today()
        df['days_left'] = (df['expiry_date'] - today).apply(lambda x: x.days)
        df = df.sort_values('days_left')

        # ── Metrics row ──
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t('in_stock'), len(df))
        c2.metric(t('expiring_soon'), len(df[df['days_left'] < 4]), delta_color="inverse")
        c3.metric(t('total_value'), f"${df['price'].sum():.2f}")
        c4.metric(t('frozen'), len(df[df['storage'] == 'frozen']))

        # ── Fridge door animation ──
        if 'fridge_selected' not in st.session_state:
            st.session_state['fridge_selected'] = None

        anim_col, list_col = st.columns([2, 3])
        with anim_col:
            items_for_anim = df[['item_name','days_left','storage','category']].to_dict('records')
            components.html(
                get_fridge_animation(items_for_anim, lang=st.session_state['lang']),
                height=300, scrolling=False
            )
        with list_col:
            # Tappable item pills — grouped by shelf
            st.caption("👆 " + ("Tap an item to select" if st.session_state['lang']=='en' else "Toca un artículo para seleccionar"))
            shelves = [
                ("⚠️", df[df['days_left'] < 4], "#e65100"),
                ("✓", df[(df['days_left'] >= 4) & (df['storage'] != 'frozen')], "#2D5016"),
                ("❄️", df[df['storage'] == 'frozen'], "#1565c0"),
            ]
            for icon, shelf_df, color in shelves:
                if shelf_df.empty: continue
                items_list = shelf_df.to_dict('records')
                cols_per_row = 2
                for row_start in range(0, len(items_list), cols_per_row):
                    row_items = items_list[row_start:row_start+cols_per_row]
                    pill_cols = st.columns(cols_per_row)
                    for col_idx, item in enumerate(row_items):
                        iid = item['id']
                        iname = item['item_name'].replace('*','').strip().title()[:13]
                        is_sel = st.session_state['fridge_selected'] == iid
                        if pill_cols[col_idx].button(
                            f"{icon} {'★ ' if is_sel else ''}{iname}",
                            key=f"pill_f_{iid}",
                            use_container_width=True,
                            type="primary" if is_sel else "secondary"
                        ):
                            st.session_state['fridge_selected'] = None if is_sel else iid
                            st.session_state[f"editing_{iid}"] = False
                            st.rerun()

        # ── Action panel — appears below animation when item selected ──
        ALL_CATS = ['Dairy','Meat','Produce','Bakery','Pantry','Frozen',
                    'Beverages','Snacks','Condiments','Grains','Cleaning','Personal Care','Unsorted']
        sel_id = st.session_state.get('fridge_selected')
        if sel_id:
            sel_rows = df[df['id'] == sel_id]
            if not sel_rows.empty:
                row = sel_rows.iloc[0]
                name = row['item_name'].replace('*','').strip().title()
                cat = row.get('category') or 'Unsorted'
                if cat.lower() in ('unknown','unsorted',''): cat = 'Unsorted'
                with st.container(border=True):
                    st.markdown(f"**✏️ {name}** `{cat}`")
                    a1, a2, a3, a4 = st.columns(4)
                    new_cat = a1.selectbox("Move to", ALL_CATS,
                        index=ALL_CATS.index(cat) if cat in ALL_CATS else 0,
                        key=f"mv_top_f_{sel_id}", label_visibility="collapsed")
                    if a2.button("📦 Move", key=f"domv_top_f_{sel_id}", use_container_width=True):
                        supabase.table("inventory").update({"category": new_cat}).eq("id", sel_id).eq("user_id", user_id).execute()
                        st.session_state['fridge_selected'] = None
                        st.toast(f"Moved to {new_cat}!")
                        st.rerun()
                    if a3.button("✏️ Edit", key=f"edit_top_f_{sel_id}", use_container_width=True):
                        st.session_state[f"editing_{sel_id}"] = True
                        st.rerun()
                    if a4.button("🗑️ Delete", key=f"del_top_f_{sel_id}", use_container_width=True):
                        db_delete_item(sel_id)
                        st.session_state['fridge_selected'] = None
                        st.rerun()

        st.markdown("---")
        st.markdown("#### " + ("All Items" if st.session_state['lang']=='en' else "Todos los Artículos"))

        ALL_CATS = ['Dairy','Meat','Produce','Bakery','Pantry','Frozen',
                    'Beverages','Snacks','Condiments','Grains','Cleaning','Personal Care','Unsorted']

        for _, row in df.iterrows():
            item_id = row['id']
            edit_key = f"editing_{item_id}"
            is_selected = st.session_state['fridge_selected'] == item_id
            name = row['item_name'].replace('*','').strip().title()
            days = row['days_left']
            cat = row.get('category') or 'Unsorted'
            if cat.lower() in ('unknown','unsorted',''): cat = 'Unsorted'

            # Card styling — gold highlight when selected
            border_style = "border: 2px solid #C8952A; background: #FDF6E9;" if is_selected else ""
            with st.container(border=True):
                if border_style:
                    st.markdown(f'<div style="{border_style} border-radius:12px; padding:2px; margin:-8px -10px 6px -10px;"></div>', unsafe_allow_html=True)

                # Tap row — full width button to select/deselect
                tap_col, info_col = st.columns([1, 6])
                sel_icon = "🟡" if is_selected else "⬜"
                if tap_col.button(sel_icon, key=f"sel_f_{item_id}", help="Tap to select"):
                    st.session_state['fridge_selected'] = None if is_selected else item_id
                    st.rerun()

                with info_col:
                    st.markdown(f"**{name}**  `{cat}`")
                    exp_txt = (t('expired_ago', abs(days)) if days < 0
                               else t('expires_in', days) if days < 4
                               else t('good', days))
                    price_txt = f" · ${row['price']:.2f}" if row.get('price') else ""
                    st.caption(f"{exp_txt} · {row['quantity']} {row['unit']}{price_txt}")

                # ── SELECTED: show action bar ──
                if is_selected:
                    st.markdown('<div style="background:#FDF6E9; border-top:1px solid #E8C97A; padding:8px 0 2px; margin-top:4px;">', unsafe_allow_html=True)
                    a1, a2, a3, a4 = st.columns(4)

                    # Quick move to category
                    new_cat = a1.selectbox("📦 Move to",
                        ALL_CATS,
                        index=ALL_CATS.index(cat) if cat in ALL_CATS else len(ALL_CATS)-1,
                        key=f"mv_f_{item_id}", label_visibility="collapsed")
                    if a2.button("✅ Move", key=f"domv_f_{item_id}"):
                        supabase.table("inventory").update({"category": new_cat}).eq("id", item_id).eq("user_id", user_id).execute()
                        st.session_state['fridge_selected'] = None
                        st.toast(f"Moved to {new_cat}!")
                        st.rerun()
                    if a3.button("✏️ Edit", key=f"edit_btn_{item_id}"):
                        st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                    if a4.button("🗑️ Del", key=f"del_{item_id}"):
                        db_delete_item(item_id)
                        st.session_state['fridge_selected'] = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

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
                        ec4, ec5, ec6 = st.columns(3)
                        new_store = ec4.text_input(
                            "Store" if st.session_state['lang'] == 'en' else "Tienda",
                            value=row.get('store', '') or ''
                        )
                        all_cats = ['Dairy','Meat','Produce','Bakery','Pantry','Frozen','Beverages','Snacks','Condiments','Grains','Other']
                        current_cat = row.get('category', 'Other') or 'Other'
                        if current_cat not in all_cats: current_cat = 'Other'
                        new_cat = ec5.selectbox(
                            "Category" if st.session_state['lang'] == 'en' else "Categoría",
                            all_cats,
                            index=all_cats.index(current_cat)
                        )
                        new_expiry = ec6.date_input(
                            "Expiry" if st.session_state['lang'] == 'en' else "Vencimiento",
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
                                    "category": new_cat,
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

with tab_pantry:
    pantry_title = "🏺 Pantry" if st.session_state['lang'] == 'en' else "🏺 Despensa"
    st.header(pantry_title)

    pantry_df = db_get_pantry()

    if not pantry_df.empty:
        pantry_df['expiry_date'] = pd.to_datetime(pantry_df['expiry_date']).dt.date
        today = date.today()
        pantry_df['days_left'] = (pantry_df['expiry_date'] - today).apply(lambda x: x.days)

    if not pantry_df.empty:
        pa, pb, pc = st.columns(3)
        pa.metric("📦 " + ("Items" if st.session_state['lang'] == 'en' else "Productos"), len(pantry_df))
        pb.metric("⚠️ " + ("Expiring Soon" if st.session_state['lang'] == 'en' else "Por Vencer"),
                  len(pantry_df[pantry_df['days_left'] < 14]))
        pc.metric("💰 " + ("Value" if st.session_state['lang'] == 'en' else "Valor"),
                  f"${pantry_df['price'].sum():.2f}")

    if 'pantry_selected' not in st.session_state:
        st.session_state['pantry_selected'] = None

    ALL_CATS_P = ['Dairy','Meat','Produce','Bakery','Pantry','Frozen',
                  'Beverages','Snacks','Condiments','Grains','Cleaning','Personal Care','Unsorted']

    if not pantry_df.empty:
        pantry_df['category'] = pantry_df['category'].fillna('Unsorted')
        pantry_df.loc[pantry_df['category'].str.lower().isin(['unknown','']), 'category'] = 'Unsorted'

        # ── Pantry shelf animation + tappable pills side by side ──
        p_anim_col, p_pill_col = st.columns([2, 3])

        with p_anim_col:
            pantry_items_anim = pantry_df[['item_name','days_left','category']].to_dict('records')
            num_cats = pantry_df['category'].nunique()
            pantry_height = max(160, 80 + num_cats * 110)
            components.html(
                get_pantry_animation(pantry_items_anim, lang=st.session_state['lang']),
                height=pantry_height, scrolling=False
            )

        with p_pill_col:
            st.caption("👆 " + ("Tap an item to select" if st.session_state['lang']=='en' else "Toca un artículo para seleccionar"))
            # Unsorted first so they're easy to find and categorize
            cats_present = (['Unsorted'] if 'Unsorted' in pantry_df['category'].values else []) +                            sorted([c for c in pantry_df['category'].unique() if c != 'Unsorted'])
            shelf_icons = {'Unsorted':'⚠️','Dairy':'🥛','Meat':'🥩','Produce':'🥦',
                           'Bakery':'🍞','Frozen':'❄️','Beverages':'🥤','Snacks':'🍿',
                           'Condiments':'🧴','Grains':'🌾','Cleaning':'🧹','Personal Care':'🧼'}
            for cat in cats_present:
                cat_items = pantry_df[pantry_df['category'] == cat]
                icon = shelf_icons.get(cat, '📦')
                st.markdown(f'<div style="font-size:9px;font-weight:700;color:#8B7355;text-transform:uppercase;letter-spacing:.06em;margin:6px 0 3px;">{icon} {cat}</div>', unsafe_allow_html=True)
                items_list = cat_items.to_dict('records')
                cols_per_row = 2
                for row_start in range(0, len(items_list), cols_per_row):
                    row_items = items_list[row_start:row_start+cols_per_row]
                    pill_cols = st.columns(cols_per_row)
                    for col_idx, item in enumerate(row_items):
                        iid = item['id']
                        iname = item['item_name'].replace('*','').strip().title()[:13]
                        is_sel = st.session_state['pantry_selected'] == iid
                        if pill_cols[col_idx].button(
                            f"{icon} {'★ ' if is_sel else ''}{iname}",
                            key=f"pill_p_{iid}",
                            use_container_width=True,
                            type="primary" if is_sel else "secondary"
                        ):
                            st.session_state['pantry_selected'] = None if is_sel else iid
                            st.session_state[f"editing_pantry_{iid}"] = False
                            st.rerun()

        # ── Action panel below both columns ──
        sel_id = st.session_state.get('pantry_selected')
        if sel_id:
            sel_rows = pantry_df[pantry_df['id'] == sel_id]
            if not sel_rows.empty:
                prow = sel_rows.iloc[0]
                pname = prow['item_name'].replace('*','').strip().title()
                pcat = prow.get('category') or 'Unsorted'
                with st.container(border=True):
                    st.markdown(f"**✏️ {pname}** `{pcat}`")
                    a1, a2, a3, a4 = st.columns(4)
                    new_pcat = a1.selectbox("Move to", ALL_CATS_P,
                        index=ALL_CATS_P.index(pcat) if pcat in ALL_CATS_P else len(ALL_CATS_P)-1,
                        key=f"mv_top_p_{sel_id}", label_visibility="collapsed")
                    if a2.button("📦 Move", key=f"domv_top_p_{sel_id}", use_container_width=True):
                        supabase.table("inventory").update({"category": new_pcat}).eq("id", sel_id).eq("user_id", user_id).execute()
                        st.session_state['pantry_selected'] = None
                        st.toast(f"📦 Moved to {new_pcat}!")
                        st.rerun()
                    if a3.button("✏️ Edit", key=f"edit_top_p_{sel_id}", use_container_width=True):
                        st.session_state[f"editing_pantry_{sel_id}"] = True
                        st.rerun()
                    if a4.button("🗑️ Delete", key=f"del_top_p_{sel_id}", use_container_width=True):
                        db_delete_item(sel_id)
                        st.session_state['pantry_selected'] = None
                        st.rerun()

        st.markdown("---")
        st.markdown("#### " + ("All Items" if st.session_state['lang']=='en' else "Todos los Artículos"))

        st.markdown("### " + ("All Pantry Items" if st.session_state['lang'] == 'en' else "Todos los Productos"))
        if 'pantry_selected' not in st.session_state:
            st.session_state['pantry_selected'] = None

        ALL_CATS_P = ['Dairy','Meat','Produce','Bakery','Pantry','Frozen',
                      'Beverages','Snacks','Condiments','Grains','Cleaning','Personal Care','Unsorted']

        # Show Unsorted shelf first if any exist
        unsorted_items = pantry_df[pantry_df['category'].str.lower().isin(['unsorted','unknown',''])]
        if not unsorted_items.empty:
            st.markdown("### 📦 " + ("Unsorted — tap to categorize" if st.session_state['lang'] == 'en' else "Sin Categoría — toca para organizar"))

        for _, row in pantry_df.sort_values(['category','days_left']).iterrows():
            item_id = row['id']
            edit_key = f"editing_pantry_{item_id}"
            is_selected = st.session_state['pantry_selected'] == item_id
            name = row['item_name'].replace('*','').strip().title()
            days = row['days_left']
            cat = row.get('category') or 'Unsorted'
            if cat.lower() in ('unknown','unsorted',''): cat = 'Unsorted'

            with st.container(border=True):
                # Gold highlight strip when selected
                if is_selected:
                    st.markdown('<div style="height:3px; background: linear-gradient(90deg,#C8952A,#F5E6C8); border-radius:4px; margin:-8px -10px 8px -10px;"></div>', unsafe_allow_html=True)

                tap_col, info_col = st.columns([1, 7])
                sel_icon = "🟡" if is_selected else "⬜"
                if tap_col.button(sel_icon, key=f"sel_p_{item_id}"):
                    st.session_state['pantry_selected'] = None if is_selected else item_id
                    st.rerun()

                with info_col:
                    cat_badge = f" `{cat}`" if cat != 'Unsorted' else " ⚠️ `Unsorted`"
                    st.markdown(f"**{name}**{cat_badge}")
                    exp_txt = (t('expired_ago', abs(days)) if days < 0
                               else t('expires_in', days) if days < 14
                               else t('good', days))
                    price_txt = f" · ${row['price']:.2f}" if row.get('price') else ""
                    st.caption(f"{exp_txt} · {row['quantity']} {row['unit']}{price_txt}")

                # ── SELECTED: action bar ──
                if is_selected:
                    st.markdown('<div style="border-top:1px solid #E8C97A; padding-top:8px; margin-top:4px;">', unsafe_allow_html=True)
                    a1, a2, a3, a4 = st.columns(4)
                    new_cat = a1.selectbox(
                        "📦 Category",
                        ALL_CATS_P,
                        index=ALL_CATS_P.index(cat) if cat in ALL_CATS_P else 0,
                        key=f"mv_p_{item_id}", label_visibility="collapsed"
                    )
                    if a2.button("✅ Move", key=f"domv_p_{item_id}"):
                        supabase.table("inventory").update({"category": new_cat}).eq("id", item_id).eq("user_id", user_id).execute()
                        st.session_state['pantry_selected'] = None
                        st.toast(f"📦 Moved to {new_cat}!")
                        st.rerun()
                    if a3.button("✏️ Edit", key=f"edit_p_{item_id}"):
                        st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                    if a4.button("🗑️ Del", key=f"del_p_{item_id}"):
                        db_delete_item(item_id)
                        st.session_state['pantry_selected'] = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                if st.session_state.get(edit_key, False):
                    with st.form(key=f"edit_pantry_{row['id']}"):
                        ep1, ep2, ep3 = st.columns(3)
                        new_name  = ep1.text_input("Name" if st.session_state['lang'] == 'en' else "Nombre", value=row['item_name'].title())
                        new_price = ep2.number_input("Price ($)", value=float(row['price']) if row.get('price') else 0.0, step=0.01)
                        new_qty   = ep3.number_input("Qty", value=float(row['quantity']) if row.get('quantity') else 1.0, step=1.0)
                        ep4, ep5 = st.columns(2)
                        p_cats = ['Dairy','Meat','Produce','Bakery','Pantry','Frozen','Beverages','Snacks','Condiments','Grains','Cleaning','Personal Care','Other']
                        p_cur_cat = row.get('category', 'Pantry') or 'Pantry'
                        # Normalize bad values like 'unsorted', 'Unsorted', ''
                        if not p_cur_cat or p_cur_cat.lower() in ('unsorted', 'other') or p_cur_cat not in p_cats:
                            p_cur_cat = 'Pantry'
                        new_p_cat = ep4.selectbox(
                            "Category" if st.session_state['lang'] == 'en' else "Categoría",
                            p_cats, index=p_cats.index(p_cur_cat)
                        )
                        new_expiry = ep5.date_input("Expiry" if st.session_state['lang'] == 'en' else "Vencimiento", value=row['expiry_date'])
                        sv, cv = st.columns(2)
                        if sv.form_submit_button("💾 Save" if st.session_state['lang'] == 'en' else "💾 Guardar"):
                            supabase.table("inventory").update({
                                "item_name": new_name.lower(), "price": new_price,
                                "quantity": new_qty, "category": new_p_cat,
                                "expiry_date": new_expiry.isoformat()
                            }).eq("id", row['id']).eq("user_id", user_id).execute()
                            st.session_state[edit_key] = False
                            st.toast("✅ Saved!")
                            st.rerun()
                        if cv.form_submit_button("Cancel" if st.session_state['lang'] == 'en' else "Cancelar"):
                            st.session_state[edit_key] = False
                            st.rerun()
    else:
        st.info(
            "🏺 Your pantry is empty. Add items using the sidebar and select 'Pantry' as the destination."
            if st.session_state['lang'] == 'en' else
            "🏺 Tu despensa está vacía. Agrega productos desde el menú y selecciona 'Despensa' como destino."
        )

    # One-time fix for items with ** in their names
    with st.expander("🔧 Fix item names" if st.session_state['lang'] == 'en' else "🔧 Corregir nombres"):
        st.caption("Run this once to clean up any items with ** or formatting characters in their names." if st.session_state['lang'] == 'en' else "Ejecuta esto una vez para limpiar nombres con ** u otros caracteres.")
        if st.button("🧹 Clean item names", use_container_width=True):
            try:
                all_items = supabase.table("inventory").select("id, item_name").eq("user_id", user_id).execute()
                fixed = 0
                for item in all_items.data:
                    if '*' in item['item_name'] or '_' in item['item_name']:
                        clean = item['item_name'].replace('*','').replace('_','').strip().lower()
                        supabase.table("inventory").update({"item_name": clean}).eq("id", item['id']).execute()
                        fixed += 1
                st.success(f"✅ Fixed {fixed} item names!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.header(t('shopping_list_title'))

    # Whiteboard / handwritten list scanner
    with st.expander("📸 " + ("Scan Whiteboard or Written List" if st.session_state['lang']=='en' else "Escanear Pizarrón o Lista"), expanded=False):
        st.caption("Photo of a whiteboard, notepad, sticky note -- Gemini reads it and adds items." if st.session_state['lang']=='en'
                   else "Foto de un pizarron o lista escrita -- Gemini la lee y agrega los articulos.")
        wb_photo = st.camera_input("Point camera at your list" if st.session_state['lang']=='en' else "Apunta la camara a tu lista")
        if not wb_photo:
            wb_photo = st.file_uploader("Or upload a photo" if st.session_state['lang']=='en' else "O sube una foto",
                                        type=["jpg","jpeg","png"], key="wb_upload")
        if wb_photo:
            if st.button("Read List", type="primary", use_container_width=True, key="wb_read_btn"):
                with st.spinner("Reading your list..." if st.session_state['lang']=='en' else "Leyendo tu lista..."):
                    try:
                        import base64 as _b64lib, requests as _wreq, json as _wjson
                        _api_key = st.secrets["GOOGLE_API_KEY"]
                        _img_bytes = wb_photo.getvalue()
                        _b64_str = _b64lib.b64encode(_img_bytes).decode()
                        _lang_str = "Spanish" if st.session_state['lang']=='es' else "English"
                        _prompt = (
                            "This is a photo of a handwritten shopping list or whiteboard. "
                            "Extract every grocery or household item you can read. "
                            "Return ONLY a JSON array of item name strings, like: "
                            '["milk", "eggs", "bread"] '
                            "If nothing is readable, return []. "
                            "Respond in " + _lang_str + ". Return ONLY the JSON array."
                        )
                        _payload = {
                            "contents": [{
                                "parts": [
                                    {"inline_data": {"mime_type": "image/jpeg", "data": _b64_str}},
                                    {"text": _prompt}
                                ]
                            }],
                            "generationConfig": {"temperature": 0.1}
                        }
                        _r = _wreq.post(
                            "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key=" + _api_key,
                            json=_payload, timeout=20
                        )
                        _raw = _r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        if "```" in _raw:
                            _raw = _raw.split("```")[1]
                            if _raw.startswith("json"): _raw = _raw[4:]
                        _detected = _wjson.loads(_raw.strip())
                        if _detected:
                            st.session_state["wb_items"] = _detected
                        else:
                            st.warning("Could not read any items. Try a clearer photo." if st.session_state['lang']=='en'
                                       else "No se pudieron leer articulos. Intenta con una foto mas clara.")
                    except Exception as _we:
                        st.error(f"Error reading image: {_we}")

        if st.session_state.get("wb_items"):
            st.markdown("**" + ("Detected -- uncheck any to skip:" if st.session_state['lang']=='en' else "Detectados -- desmarca los que no quieras:") + "**")
            _sel = []
            for _wi, _wname in enumerate(st.session_state["wb_items"]):
                if st.checkbox(_wname.title(), value=True, key=f"wb_chk_{_wi}"):
                    _sel.append(_wname)
            if _sel and st.button(
                f"Add {len(_sel)} items to Shopping List" if st.session_state['lang']=='en' else f"Agregar {len(_sel)} articulos",
                type="primary", use_container_width=True, key="wb_add_btn"
            ):
                for _si in _sel:
                    db_add_to_shopping_list(_si, 0)
                st.toast(f"Added {len(_sel)} items to your list!")
                del st.session_state["wb_items"]
                st.rerun()

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
    meal_types_en = ['breakfast', 'lunch', 'dinner', 'snack']
    meal_types_es = ['desayuno', 'almuerzo', 'cena', 'merienda']
    meal_types = meal_types_es if st.session_state['lang'] == 'es' else meal_types_en
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
                    meal_type_raw = meal['meal_type'].lower()
                    meal_translations = {'breakfast':'desayuno','lunch':'almuerzo','dinner':'cena','snack':'merienda',
                                         'desayuno':'breakfast','almuerzo':'lunch','cena':'dinner','merienda':'snack'}
                    if st.session_state['lang'] == 'es':
                        meal_type_display = meal_translations.get(meal_type_raw, meal_type_raw).title()
                    else:
                        meal_type_display = meal_translations.get(meal_type_raw, meal_type_raw).title() if meal_type_raw in meal_translations and meal_type_raw in meal_types_es else meal_type_raw.title()
                    c1.write(f"**{meal_type_display}**")
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

    find_btn_label = (
        "🧊 Find Recipes From Inventory" if recipe_mode == mode_labels[1]
        else "🚨 Find Recipes Using Expiring Food"
    ) if st.session_state['lang'] == 'en' else (
        "🧊 Buscar Recetas del Inventario" if recipe_mode == mode_labels[1]
        else "🚨 Buscar Recetas con Comida por Vencer"
    )
    if st.button(find_btn_label, type="primary"):
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

with tab_nutrition:
    nutr_title = "🥗 Nutrition Goals" if st.session_state['lang'] == 'en' else "🥗 Metas Nutricionales"
    st.header(nutr_title)
    st.caption(
        "Set your nutrition targets and we'll find the best portions from what you have." if st.session_state['lang'] == 'en'
        else "Establece tus metas nutricionales y encontramos las mejores porciones de lo que tienes."
    )

    # ── Goal sliders ──
    st.markdown("### 🎯 " + ("Your Goals" if st.session_state['lang'] == 'en' else "Tus Metas"))

    g1, g2, g3, g4 = st.columns(4)
    goal_cal  = g1.number_input("🔥 " + ("Calories" if st.session_state['lang'] == 'en' else "Calorías"),
                                 min_value=0, max_value=2000, value=500, step=50)
    goal_pro  = g2.number_input("💪 " + ("Protein (g)" if st.session_state['lang'] == 'en' else "Proteína (g)"),
                                 min_value=0, max_value=200, value=30, step=5)
    goal_carb = g3.number_input("🌾 " + ("Carbs (g)" if st.session_state['lang'] == 'en' else "Carbohidratos (g)"),
                                 min_value=0, max_value=300, value=50, step=5)
    goal_fat  = g4.number_input("🫒 " + ("Fat (g)" if st.session_state['lang'] == 'en' else "Grasa (g)"),
                                 min_value=0, max_value=100, value=15, step=5)

    # Visual goal bars
    st.markdown("---")
    bar_cols = st.columns(4)
    macros = [
        ("🔥", "Cal",  goal_cal,  2000, "#C8952A"),
        ("💪", "Pro",  goal_pro,  200,  "#2D5016"),
        ("🌾", "Carb", goal_carb, 300,  "#7A9E5F"),
        ("🫒", "Fat",  goal_fat,  100,  "#C4572A"),
    ]
    for col, (icon, label, val, max_val, color) in zip(bar_cols, macros):
        pct = min(int(val / max_val * 100), 100)
        col.markdown(f"""
        <div style="text-align:center; padding:12px; background:white; border-radius:12px; border:1px solid #E8E4DE;">
            <div style="font-size:1.4rem;">{icon}</div>
            <div style="font-family:'Fraunces',serif; font-size:1.3rem; font-weight:600; color:{color};">{val}</div>
            <div style="font-size:0.7rem; color:#6B6B6B; margin-bottom:6px;">{label}</div>
            <div style="background:#E8E4DE; border-radius:99px; height:6px;">
                <div style="background:{color}; width:{pct}%; height:6px; border-radius:99px;"></div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Find meal suggestion ──
    btn_label = "🔍 Find Best Meal From My Fridge" if st.session_state['lang'] == 'en' else "🔍 Encontrar la Mejor Comida de Mi Refrigerador"
    if st.button(btn_label, type="primary", use_container_width=True):
        try:
            from nutrition_engine import suggest_portions_for_goals
            # Get all in-stock items
            all_items = supabase.table("inventory").select("item_name, storage, category").eq("user_id", user_id).eq("status", "In Stock").execute()
            if all_items.data:
                goals = {"calories": goal_cal, "protein": goal_pro, "carbs": goal_carb, "fat": goal_fat}
                with st.spinner("🤖 " + ("Finding the best match..." if st.session_state['lang'] == 'en' else "Buscando la mejor combinación...")):
                    suggestion = suggest_portions_for_goals(all_items.data, goals, lang=st.session_state['lang'])
                st.session_state['nutrition_suggestion'] = suggestion
            else:
                st.info("Add items to your fridge or pantry first!" if st.session_state['lang'] == 'en' else "¡Primero agrega artículos a tu refrigerador o despensa!")
        except Exception as e:
            st.error(f"Error: {e}")

    # ── Show suggestion ──
    if 'nutrition_suggestion' in st.session_state:
        sug = st.session_state['nutrition_suggestion']
        if "error" not in sug:
            st.markdown("### 🍽️ " + (sug.get('meal_name', 'Suggested Meal')))

            # Totals vs goals comparison
            total = sug.get('total_nutrition', {})
            t1, t2, t3, t4 = st.columns(4)
            def render_vs(col, icon, label, actual, goal, color):
                pct = min(int(actual / goal * 100), 100) if goal > 0 else 0
                over = actual > goal
                bar_color = "#C4572A" if over else color
                col.markdown(f"""
                <div style="text-align:center; padding:10px; background:white; border-radius:12px; border:2px solid {'#C4572A' if over else '#E8E4DE'};">
                    <div style="font-size:1.1rem;">{icon}</div>
                    <div style="font-family:'Fraunces',serif; font-size:1.1rem; font-weight:600; color:{bar_color};">{actual}</div>
                    <div style="font-size:0.65rem; color:#6B6B6B;">of {goal} {label}</div>
                    <div style="background:#E8E4DE; border-radius:99px; height:5px; margin-top:5px;">
                        <div style="background:{bar_color}; width:{pct}%; height:5px; border-radius:99px;"></div>
                    </div>
                    {'<div style="font-size:0.65rem;color:#C4572A;">over goal</div>' if over else ''}
                </div>""", unsafe_allow_html=True)

            render_vs(t1, "🔥", "cal",  total.get('calories',0), goal_cal,  "#C8952A")
            render_vs(t2, "💪", "g pro", total.get('protein',0),  goal_pro,  "#2D5016")
            render_vs(t3, "🌾", "g carb",total.get('carbs',0),    goal_carb, "#7A9E5F")
            render_vs(t4, "🫒", "g fat", total.get('fat',0),      goal_fat,  "#C4572A")

            # Item breakdown
            st.markdown("#### " + ("What to eat & how much:" if st.session_state['lang'] == 'en' else "Qué comer y cuánto:"))
            for item in sug.get('items', []):
                with st.container(border=True):
                    ic1, ic2, ic3 = st.columns([1, 3, 4])
                    ic1.markdown(f"<div style='font-size:2rem;text-align:center'>{item.get('emoji','🍽️')}</div>", unsafe_allow_html=True)
                    ic2.markdown(f"**{item['name'].title()}**")
                    ic2.markdown(f"<span style='background:#F5E6C8;color:#2D5016;padding:3px 10px;border-radius:20px;font-weight:600;font-size:0.9rem'>📏 {item['amount']}</span>", unsafe_allow_html=True)
                    ic3.caption(f"🔥 {item.get('calories',0)} cal  💪 {item.get('protein',0)}g  🌾 {item.get('carbs',0)}g  🫒 {item.get('fat',0)}g")

            if sug.get('tip'):
                st.info(f"💡 {sug['tip']}")

        else:
            st.warning(sug.get('error', 'Could not generate suggestion. Try again.'))

with tab_rhythm:
    _rh_title = "🌅 Daily Rhythm" if st.session_state['lang']=='en' else "🌅 Ritmo Diario"
    st.header(_rh_title)
    st.caption(
        "Anchor points for your day -- not a strict schedule. One must-do, one nice-to-have per block."
        if st.session_state['lang']=='en' else
        "Puntos de ancla para tu dia -- no un horario estricto. Un deber y un opcional por bloque."
    )

    # Default blocks
    _default_blocks = [
        {"id": "morning",   "label": "Morning",   "emoji": "🌅", "time": "7-10am"},
        {"id": "midday",    "label": "Midday",    "emoji": "☀️",  "time": "10am-1pm"},
        {"id": "afternoon", "label": "Afternoon", "emoji": "🌤️", "time": "1-4pm"},
        {"id": "evening",   "label": "Evening",   "emoji": "🌙", "time": "4-7pm"},
    ]
    _default_blocks_es = [
        {"id": "morning",   "label": "Mañana",    "emoji": "🌅", "time": "7-10am"},
        {"id": "midday",    "label": "Mediodia",  "emoji": "☀️",  "time": "10am-1pm"},
        {"id": "afternoon", "label": "Tarde",     "emoji": "🌤️", "time": "1-4pm"},
        {"id": "evening",   "label": "Noche",     "emoji": "🌙", "time": "4-7pm"},
    ]
    _blocks = _default_blocks_es if st.session_state['lang']=='es' else _default_blocks

    # Load saved rhythm from Supabase
    _today_str = date.today().isoformat()
    _dow = date.today().strftime("%A")  # Monday, Tuesday...

    try:
        _saved = supabase.table("daily_rhythm").select("*").eq("user_id", user_id).eq("day_of_week", _dow).execute()
        _saved_map = {r["block_id"]: r for r in (_saved.data or [])}
    except:
        _saved_map = {}

    st.markdown("### " + (_dow if st.session_state['lang']=='en' else _dow))

    _must_label  = "Must do" if st.session_state['lang']=='en' else "Obligatorio"
    _nice_label  = "Nice to have" if st.session_state['lang']=='en' else "Opcional"
    _done_label  = "Done" if st.session_state['lang']=='en' else "Hecho"
    _save_label  = "Save Rhythm" if st.session_state['lang']=='en' else "Guardar Ritmo"

    _any_changed = False
    _updates = {}

    for _blk in _blocks:
        _bid = _blk["id"]
        _saved_blk = _saved_map.get(_bid, {})
        _must_val  = _saved_blk.get("must_do", "")
        _nice_val  = _saved_blk.get("nice_to_have", "")
        _done_val  = _saved_blk.get("done", False)

        with st.container(border=True):
            _hcol, _dcol = st.columns([5, 1])
            _hcol.markdown(f"**{_blk['emoji']} {_blk['label']}** `{_blk['time']}`")
            _done_check = _dcol.checkbox(_done_label, value=_done_val, key=f"rh_done_{_bid}")

            _c1, _c2 = st.columns(2)
            _must_input = _c1.text_input(
                f"✅ {_must_label}",
                value=_must_val,
                placeholder=("e.g. Lunch for kids" if st.session_state['lang']=='en' else "p.ej. Almuerzo para los ninos"),
                key=f"rh_must_{_bid}"
            )
            _nice_input = _c2.text_input(
                f"⭐ {_nice_label}",
                value=_nice_val,
                placeholder=("e.g. Park walk" if st.session_state['lang']=='en' else "p.ej. Paseo al parque"),
                key=f"rh_nice_{_bid}"
            )
            _updates[_bid] = {
                "must_do": _must_input,
                "nice_to_have": _nice_input,
                "done": _done_check
            }

    if st.button(_save_label, type="primary", use_container_width=True, key="rh_save"):
        try:
            for _bid, _udata in _updates.items():
                _existing = _saved_map.get(_bid)
                _row = {
                    "user_id": user_id,
                    "day_of_week": _dow,
                    "block_id": _bid,
                    "must_do": _udata["must_do"],
                    "nice_to_have": _udata["nice_to_have"],
                    "done": _udata["done"]
                }
                if _existing:
                    supabase.table("daily_rhythm").update(_row).eq("id", _existing["id"]).execute()
                else:
                    supabase.table("daily_rhythm").insert(_row).execute()
            st.toast("Rhythm saved!" if st.session_state['lang']=='en' else "Ritmo guardado!")
            st.rerun()
        except Exception as _re:
            st.error(f"Error saving: {_re}")

    # Progress summary
    _done_count = sum(1 for b in _blocks if _updates.get(b["id"], {}).get("done", False))
    _total = len(_blocks)
    if _done_count > 0:
        st.markdown("---")
        _prog_pct = int(_done_count / _total * 100)
        st.markdown(f"**{'Today:' if st.session_state['lang']=='en' else 'Hoy:'} {_done_count}/{_total} blocks done**")
        st.progress(_prog_pct / 100)
        if _done_count == _total:
            st.success("Full day done. That is enough." if st.session_state['lang']=='en' else "Dia completo. Eso es suficiente.")

    # Bare minimum mode
    st.markdown("---")
    with st.expander("🔋 " + ("Bare Minimum Mode -- tough day?" if st.session_state['lang']=='en' else "Modo Minimo -- dia dificil?")):
        st.caption(
            "On hard days, this is all that matters. Everything else can wait."
            if st.session_state['lang']=='en' else
            "En dias dificiles, solo esto importa. Todo lo demas puede esperar."
        )
        _bm_items = [
            ("🍽️", "Feed the kids" if st.session_state['lang']=='en' else "Dar de comer a los ninos"),
            ("💧", "Keep everyone hydrated" if st.session_state['lang']=='en' else "Mantener a todos hidratados"),
            ("😴", "Nap/rest when they rest" if st.session_state['lang']=='en' else "Descansar cuando ellos descansan"),
            ("❤️", "One moment of connection" if st.session_state['lang']=='en' else "Un momento de conexion"),
        ]
        for _icon, _item in _bm_items:
            st.markdown(f"{_icon} {_item}")
        st.info(
            "You showed up today. That is the job."
            if st.session_state['lang']=='en' else
            "Apareciste hoy. Eso es el trabajo."
        )

with tab_dump:
    _dump_title = "🧠 Brain Dump" if st.session_state['lang']=='en' else "🧠 Descarga Mental"
    st.header(_dump_title)
    st.caption(
        "Get it out of your head. Type anything — tasks, worries, ideas, reminders. Gemini will sort it for you." if st.session_state['lang']=='en'
        else "Sácalo de tu cabeza. Escribe cualquier cosa: tareas, preocupaciones, ideas. Gemini lo organiza."
    )

    # ── Quick capture ──
    with st.form("brain_dump_form", clear_on_submit=True):
        dump_text = st.text_area(
            "What's on your mind?" if st.session_state['lang']=='en' else "¿Qué tienes en mente?",
            placeholder="milk is running low, call dentist, need to return Amazon package, Emma has soccer at 4pm..." if st.session_state['lang']=='en'
            else "Se está acabando la leche, llamar al dentista, Emma tiene fútbol a las 4pm...",
            height=100
        )
        col_ai, col_plain = st.columns(2)
        submit_ai    = col_ai.form_submit_button(
            "✨ Save + Sort with AI" if st.session_state['lang']=='en' else "✨ Guardar + Ordenar con IA",
            use_container_width=True, type="primary"
        )
        submit_plain = col_plain.form_submit_button(
            "💾 Just Save" if st.session_state['lang']=='en' else "💾 Solo Guardar",
            use_container_width=True
        )

    if (submit_ai or submit_plain) and dump_text.strip():
        if submit_ai:
            # Ask Gemini to split into categorized items
            try:
                import requests as _req, json as _json
                _api_key = st.secrets["GOOGLE_API_KEY"]
                _lang_str = "Spanish" if st.session_state['lang']=='es' else "English"
                _prompt = f"""Split this brain dump into individual items and assign each a category.
Categories: grocery, task, appointment, reminder, idea, personal, worry, other

Input: {dump_text}

Return ONLY a JSON array:
[
  {{"text": "call dentist", "category": "appointment"}},
  {{"text": "milk is running low", "category": "grocery"}}
]
Respond in {_lang_str}. Return ONLY JSON, no markdown."""
                _r = _req.post(
                    f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={_api_key}",
                    json={{"contents": [{{"parts": [{{"text": _prompt}}]}}], "generationConfig": {{"temperature": 0.2}}}},
                    timeout=15
                )
                _raw = _r.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                if "```" in _raw: _raw = _raw.split("```")[1]; _raw = _raw[4:] if _raw.startswith("json") else _raw
                _items = _json.loads(_raw.strip())
                for _item in _items:
                    supabase.table("brain_dump").insert({
                        "user_id": user_id,
                        "content": _item.get("text", ""),
                        "category": _item.get("category", "other"),
                        "done": False
                    }).execute()
                st.toast(f"✨ Sorted {len(_items)} items!")
            except Exception as _de:
                # Fallback: save as single item
                supabase.table("brain_dump").insert({"user_id": user_id, "content": dump_text, "category": "other", "done": False}).execute()
                st.toast("💾 Saved!")
        else:
            supabase.table("brain_dump").insert({"user_id": user_id, "content": dump_text, "category": "other", "done": False}).execute()
            st.toast("💾 Saved!")
        st.rerun()

    # ── Display items grouped by category ──
    try:
        _all_dumps = supabase.table("brain_dump").select("*").eq("user_id", user_id).eq("done", False).order("created_at", desc=True).execute()
        _dumps = _all_dumps.data or []
    except:
        _dumps = []

    if _dumps:
        # Group by category
        _cat_icons = {
            "grocery":"🛒", "task":"✅", "appointment":"📅",
            "reminder":"⏰", "idea":"💡", "personal":"💛",
            "worry":"😟", "other":"📝"
        }
        _cats = {}
        for _d in _dumps:
            _c = _d.get("category","other")
            _cats.setdefault(_c, []).append(_d)

        # Show "Add to shopping list" button for grocery items
        _grocery_items = _cats.get("grocery", [])
        if _grocery_items:
            if st.button("🛒 " + ("Move all groceries to Shopping List" if st.session_state['lang']=='en' else "Mover grocerías a Lista de Compras"), use_container_width=True):
                for _gi in _grocery_items:
                    try:
                        supabase.table("shopping_list").insert({"user_id": user_id, "item_name": _gi['content'], "quantity": 1, "price": 0, "bought": False, "date_added": date.today().isoformat()}).execute()
                        supabase.table("brain_dump").update({"done": True}).eq("id", _gi['id']).execute()
                    except: pass
                st.toast("🛒 Added to shopping list!")
                st.rerun()

        for _cat, _items in sorted(_cats.items()):
            _icon = _cat_icons.get(_cat, "📝")
            _cat_label = _cat.title()
            st.markdown(f"**{_icon} {_cat_label}** ({len(_items)})")
            for _item in _items:
                _dc1, _dc2 = st.columns([8, 1])
                _dc1.markdown(f"• {_item['content']}")
                if _dc2.button("✓", key=f"done_dump_{_item['id']}"):
                    supabase.table("brain_dump").update({"done": True}).eq("id", _item['id']).execute()
                    st.rerun()
    else:
        st.info("🧠 " + ("Your head is clear! Add something above." if st.session_state['lang']=='en' else "¡Tu mente está despejada! Agrega algo arriba."))

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

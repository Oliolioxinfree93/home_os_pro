import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client
from streamlit_google_auth import Authenticate

# ---------------------------------------------------
# APP CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="Home OS Pro", page_icon="🏠", layout="wide")

# ---------------------------------------------------
# SUPABASE CONNECTION (SAFE CACHE)
# ---------------------------------------------------
@st.cache_resource
def get_supabase():
    try:
        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"],
        )
    except Exception:
        return None

supabase = get_supabase()

# ---------------------------------------------------
# AUTHENTICATION (PRODUCTION SAFE VERSION)
# ---------------------------------------------------
def init_auth():
    if "authenticator" not in st.session_state:
        st.session_state["authenticator"] = Authenticate(
            secret_credentials_path=None,
            client_id=st.secrets["auth"]["client_id"],
            client_secret=st.secrets["auth"]["client_secret"],
            redirect_uri=st.secrets["auth"]["redirect_uri"],
            cookie_name="home_os_v8",
            cookie_key="secure_key_v8",
            cookie_expiry_days=30,
        )
    return st.session_state["authenticator"]

authenticator = init_auth()


def handle_auth():
    if st.session_state.get("connected"):
        return

    # Only check if OAuth callback exists
    if "code" in st.query_params:
        try:
            authenticator.check_authentification()
        except Exception:
            st.session_state["connected"] = False

handle_auth()


def get_current_user():
    if st.session_state.get("dev_mode"):
        return "dev_user@example.com"

    if st.session_state.get("connected"):
        user_info = st.session_state.get("user_info", {})
        return user_info.get("email")

    return None


def show_login_screen():
    st.markdown("## 🏠 Home OS Pro")
    st.markdown("### See the real value you bring to your family")
    st.markdown("---")

    login_url = authenticator.get_authorization_url()
    st.link_button("🔑 Sign in with Google", login_url, use_container_width=True)

    st.markdown("---")

    if st.button("🛠️ Skip Login (Dev Mode)", use_container_width=True):
        st.session_state["dev_mode"] = True
        st.session_state["connected"] = True
        st.session_state["user_info"] = {
            "name": "Dev User",
            "email": "dev_user@example.com",
            "picture": "",
        }
        st.rerun()


# ---------------------------------------------------
# LOGIN GATE
# ---------------------------------------------------
user_id = get_current_user()

if not user_id:
    show_login_screen()
    st.stop()

# ---------------------------------------------------
# USER INFO
# ---------------------------------------------------
if st.session_state.get("dev_mode"):
    user_name = "Dev User"
    user_picture = ""
    st.warning("⚠️ Developer Mode Active")
else:
    user_info = st.session_state.get("user_info", {})
    user_name = user_info.get("name", "Friend")
    user_picture = user_info.get("picture", "")

# ---------------------------------------------------
# IMPORT YOUR LOGIC MODULES
# ---------------------------------------------------
from inventory_logic import InventoryLogic
from barcode_scanner import BarcodeScanner
from receipt_scanner import ReceiptScanner

# ---------------------------------------------------
# DATABASE FUNCTIONS
# ---------------------------------------------------
def db_get_inventory():
    try:
        res = supabase.table("inventory")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "In Stock")\
            .execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except:
        return pd.DataFrame()


def db_add_item(name, qty=1, price=0.0, store=None):
    logic = InventoryLogic()
    analysis = logic.normalize_item(name)

    expiry = (date.today() + timedelta(days=analysis["expiry_days"])).isoformat()

    supabase.table("inventory").insert({
        "user_id": user_id,
        "item_name": analysis["clean_name"],
        "category": analysis["category"],
        "quantity": qty,
        "unit": analysis["unit"],
        "storage": analysis["storage"],
        "date_added": date.today().isoformat(),
        "expiry_date": expiry,
        "status": "In Stock",
        "decision_reason": analysis["reason"],
        "price": price,
        "store": store or "",
    }).execute()


def db_delete_item(item_id, table="inventory"):
    supabase.table(table)\
        .delete()\
        .eq("id", item_id)\
        .eq("user_id", user_id)\
        .execute()


# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.title("🏠 Home OS Pro")

if user_picture:
    st.sidebar.image(user_picture, width=40)

st.sidebar.markdown(f"**Welcome, {user_name.split()[0]}!** 👋")

if st.sidebar.button("🚪 Sign Out", use_container_width=True):
    st.session_state.clear()
    authenticator.logout()
    st.rerun()

# ---------------------------------------------------
# MAIN TABS
# ---------------------------------------------------
tab0, tab1, tab2 = st.tabs(["💪 My Impact", "🧊 Fridge", "🛒 Shopping List"])

# ---------------------------------------------------
# TAB 0 – IMPACT
# ---------------------------------------------------
with tab0:
    st.title(f"💪 {user_name.split()[0]}'s Household Impact")
    st.info("Your economic contribution made visible.")

# ---------------------------------------------------
# TAB 1 – FRIDGE
# ---------------------------------------------------
with tab1:
    st.header("🧊 Your Fridge")

    df = db_get_inventory()

    if not df.empty:
        df["expiry_date"] = pd.to_datetime(df["expiry_date"]).dt.date
        df["days_left"] = (df["expiry_date"] - date.today()).dt.days

        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.markdown(f"**{row['item_name'].title()}**")
                c2.write(f"{row['days_left']} days left")
                if c3.button("🗑️", key=row["id"]):
                    db_delete_item(row["id"])
                    st.rerun()
    else:
        st.info("Your fridge is empty!")

# ---------------------------------------------------
# TAB 2 – SHOPPING LIST
# ---------------------------------------------------
with tab2:
    st.header("🛒 Shopping List")
    st.info("Coming next…")

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------
st.markdown("---")
st.caption("Home OS Pro | Built with ❤️ for stay-at-home parents")

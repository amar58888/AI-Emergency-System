import streamlit as st
import speech_recognition as sr
import datetime
import geocoder
import cv2
import smtplib
from twilio.rest import Client
import firebase_admin
from firebase_admin import credentials, firestore

# ---------------- CONFIG ----------------

ACCOUNT_SID = "TWILIO_SID"
AUTH_TOKEN = "TWILIO_NUMBER"
TWILIO_NUMBER = "TWILIO_NUMBER"
TARGET_NUMBER = "TARGET_NUMBER"

EMAIL = "ajuamarjyoth@gmail.com"
APP_PASSWORD = "iuvayzkbgbvfnqml"
RECEIVER_EMAIL = "24dtsa11@kristujayanti.com"

# Firebase init
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Voice recognizer
recognizer = sr.Recognizer()

# Twilio client
client = Client(ACCOUNT_SID, AUTH_TOKEN)

# ---------------- FUNCTIONS ----------------

# 📍 Get Location
def get_location():
    g = geocoder.ip('me')
    return g.latlng if g.latlng else [0, 0]

# 📸 Capture Photo
def capture_photo():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        filename = "captured.jpg"
        cv2.imwrite(filename, frame)
        cap.release()
        return filename
    cap.release()
    return None

# 🔊 Play Alarm
def play_alarm():
    try:
        with open("sounds/alarm.wav", "rb") as f:
            st.audio(f.read(), format="audio/wav", autoplay=True)
    except Exception as e:
        st.warning(f"⚠️ Alarm error: {e}")

# 📱 SMS + WhatsApp
def send_sms_whatsapp(location):
    lat, lon = location
    map_link = f"https://www.google.com/maps?q={lat},{lon}"

    message = f"🚨 EMERGENCY ALERT!\n📍 Location: {map_link}\nHelp needed immediately!"

    try:
        client.messages.create(
    body=message,
    from_='whatsapp:+14155238886',  
    to='whatsapp:' + TARGET_NUMBER
)

        st.success("📱 SMS Sent!")

    except Exception as e:
        st.error(f"SMS Error: {e}")

# 📧 Email Alert
def send_email(location):
    lat, lon = location
    map_link = f"https://www.google.com/maps?q={lat},{lon}"

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, APP_PASSWORD)

        subject = "EMERGENCY ALERT"
        body = f"""
EMERGENCY ALERT!

Location:
{map_link}

Help needed immediately!
        """

        message = f"Subject: {subject}\n\n{body}"

        server.sendmail(EMAIL, RECEIVER_EMAIL, message)
        server.quit()

        st.success("📧 Email Sent!")

    except Exception as e:
        st.error(f"Email Error: {e}")

# 🚨 Emergency
def trigger_emergency():
    time = datetime.datetime.now()

    location = get_location()
    lat, lon = location

    st.error("🚨 EMERGENCY ACTIVATED 🚨")
    st.write(f"⏰ Time: {time}")
    st.write(f"📍 Location: {lat}, {lon}")

    st.markdown(f"[📍 Open in Maps](https://www.google.com/maps?q={lat},{lon})")

    # Camera
    photo = capture_photo()
    if photo:
        st.image(photo, caption="📸 Captured Evidence")

    # Alarm
    play_alarm()

    # Alerts
    send_sms_whatsapp(location)
    send_email(location)

    # Firebase save
    data = {
        "time": str(time),
        "latitude": lat,
        "longitude": lon,
        "status": "Emergency Triggered"
    }
    db.collection("emergencies").add(data)

# 🎤 Voice
def listen_voice():
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... Speak now")

            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5)

            text = recognizer.recognize_google(audio)
            st.success(f"You said: {text}")

            if "help" in text.lower() or "save me" in text.lower():
                trigger_emergency()
            else:
                st.warning("No emergency word detected")

    except sr.WaitTimeoutError:
        st.error("⏱️ Timeout: No voice detected")

    except sr.UnknownValueError:
        st.error("🤷 Could not understand audio")

    except Exception as e:
        st.error(f"❌ Error: {e}")

# ---------------- UI ----------------

st.set_page_config(page_title="AI Emergency System", layout="centered")

st.title("🚨 AI Emergency System (Ultimate)")
st.write("Say 'HELP' or 'SAVE ME' OR press Panic Button")

# 🎤 Voice
if st.button("🎤 Start Listening"):
    listen_voice()

# 🔴 Panic
if st.button("🔴 PANIC BUTTON"):
    trigger_emergency()

# 📊 Logs
st.subheader("📊 Emergency Logs")

docs = db.collection("emergencies").stream()
for doc in docs:
    st.write(doc.to_dict())
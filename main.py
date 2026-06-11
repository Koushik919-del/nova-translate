import streamlit.components.v1 as components

components.html("""
    <meta name="google-site-verification" content="4yS5dM4B4u47bwLOxSwHp3AHWOrAbcaKQDN9HCbMB3g"/>
""", height=0)

import streamlit as st
from PIL import Image
import pytesseract

# Use Linux path for Streamlit Cloud
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

from deep_translator import GoogleTranslator
from gtts import gTTS
import tempfile
import os
import speech_recognition as sr
import requests

# ==== CONFIGURATION ====
st.set_page_config(page_title="Nova Translate", page_icon="🌐")

# ==== DISPLAY LOGO ====
st.markdown("<h1 style='text-align: center;'>🌐 Nova Translate</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center;'>Smart assistant for OCR, translation, pronunciation, and websites.</h5>", unsafe_allow_html=True)

# ==== Language Setup ====
all_langs = GoogleTranslator().get_supported_languages(as_dict=True)
sorted_lang_names = sorted(all_langs.keys())

# ==== Styling ====
st.markdown("""
    <style>
    .block-container {
        max-width: 920px;
        padding-top: 5rem;
    }

    h1, h5 {
        letter-spacing: 0;
    }

    div.stButton > button {
        width: 100%;
        min-height: 72px;
        border-radius: 16px;
        padding: 16px 22px;
        margin: 0;
        display: block;
        font-size: 1.05rem;
        font-weight: 700;
        line-height: 1.2;
        white-space: normal;
        word-break: normal;
        overflow-wrap: normal;
        border: 1px solid rgba(148, 163, 184, 0.32);
        transition: transform 120ms ease, border-color 120ms ease, background 120ms ease;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.78);
    }

    div.stButton > button:active {
        transform: translateY(0);
    }

    [data-testid="column"] {
        padding: 0.4rem;
    }

    @media (max-width: 640px) {
        .block-container {
            padding-top: 3rem;
        }

        div.stButton > button {
            min-height: 64px;
            padding: 14px 18px;
            font-size: 1rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ==== Page Controller ====
if "page" not in st.session_state:
    st.session_state.page = "home"

def go(page_name):
    if st.session_state.page != page_name:
        st.session_state.page = page_name
        st.rerun()
# === HOME PAGE ===
if st.session_state.page == "home":
    top_left, top_right = st.columns(2)
    bottom_left, bottom_right = st.columns(2)

    with top_left:
        image_clicked = st.button("📸 Image Text Translate", use_container_width=True)
    with top_right:
        text_clicked = st.button("📝 Text Translation", use_container_width=True)
    with bottom_left:
        practice_clicked = st.button("🎤 Pronunciation Practice", use_container_width=True)
    with bottom_right:
        website_clicked = st.button("🌍 Translate Website", use_container_width=True)

    if image_clicked:
        go("ocr")
    elif text_clicked:
        go("translate")
    elif practice_clicked:
        go("practice")
    elif website_clicked:
        go("website")

# === WEBSITE TRANSLATOR ===
elif st.session_state.page == "website":
    st.title("Website Translator")
    url = st.text_input("Enter website URL:")
    selected_lang = st.selectbox("Translate to:", sorted_lang_names)
    lang_code = all_langs[selected_lang.lower()]

    if st.button("Translate Website"):
        if not url.startswith("http"):
            url = "http://" + url
        translated_url = f"https://translate.google.com/translate?sl=auto&tl={lang_code}&u={url}"
        st.success("\u2705 Click below to view translated site:")
        st.markdown(f"[🌍 Open Website in {selected_lang.title()}]({translated_url})", unsafe_allow_html=True)

    if st.button("🔙 Back to Home"):
        go("home")

# === OCR PAGE ===
elif st.session_state.page == "ocr":
    st.title("📸 Image Text Scanner & Translator")
    uploaded_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        text = pytesseract.image_to_string(image)
        st.text_area("Extracted Text", text, height=150)

        if text.strip():
            selected_lang = st.selectbox("Translate to:", sorted_lang_names)
            lang_code = all_langs[selected_lang.lower()]
            if st.button("Translate"):
                try:
                    translated = GoogleTranslator(source='auto', target=lang_code).translate(text)
                    st.success("✅ Translated Text:")
                    st.text_area("Translation", translated, height=150)
                except Exception as e:
                    st.error(f"Translation failed: {e}")
    if st.button("🔙 Back to Home"):
        go("home")

# === TEXT TRANSLATION PAGE ===
elif st.session_state.page == "translate":
    st.title("📝 Text Translation")
    text = st.text_input("Enter text:")
    selected_lang = st.selectbox("Translate to:", sorted_lang_names)
    lang_code = all_langs[selected_lang.lower()]

    if st.button("Translate"):
        if text:
            try:
                translated = GoogleTranslator(source='auto', target=lang_code).translate(text)
                st.success(f"✅ Translation: {translated}")
                tts = gTTS(translated, lang=lang_code)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                    tts.save(tmp_audio.name)
                    st.audio(tmp_audio.name, format="audio/mp3")
            except Exception as e:
                st.error(f"Translation error: {e}")
    if st.button("🔙 Back to Home"):
        go("home")

# === PRONUNCIATION PAGE ===
elif st.session_state.page == "practice":
    st.title("🎤 Pronunciation Practice")
    expected_phrase = st.text_input("Expected phrase:")
    audio_file = st.file_uploader("Upload voice (WAV/MP3):", type=["wav", "mp3"])
    selected_lang = st.selectbox("Language spoken:", sorted_lang_names)
    lang_code = all_langs[selected_lang.lower()]

    if expected_phrase and audio_file:
        try:
            recognizer = sr.Recognizer()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
                temp_wav.write(audio_file.read())
                wav_path = temp_wav.name

            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)

            user_said = recognizer.recognize_google(audio_data, language=lang_code)
            st.write(f"🚢 You said: `{user_said}`")
            if expected_phrase.lower().strip() in user_said.lower():
                st.success("✅ Great job!")
            else:
                st.warning("❌ Try again!")
        except Exception as e:
            st.error(f"Error: {e}")
    if st.button("🔙 Back to Home"):
        go("home")


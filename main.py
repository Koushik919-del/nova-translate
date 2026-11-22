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
st.markdown("""
    <div class="nova-hero">
        <div class="nova-brand">
            <span class="nova-mark">🌐</span>
            <span>Nova Translate</span>
        </div>
        <p class="nova-kicker">LANGUAGE TOOLS, ALL IN ONE PLACE</p>
        <p class="nova-subtitle">Translate text and websites, pull words from images, and practice pronunciation.</p>
    </div>
""", unsafe_allow_html=True)

# ==== Language Setup ====
all_langs = GoogleTranslator().get_supported_languages(as_dict=True)
sorted_lang_names = sorted(all_langs.keys())

# ==== Styling ====
st.markdown("""
    <style>
    :root {
        color-scheme: dark;
        --nova-bg: #080d18;
        --nova-panel: #101a2a;
        --nova-line: #263b58;
        --nova-text: #f4f7ff;
        --nova-muted: #a2b0c6;
        --nova-accent: #92d7ff;
        --nova-lime: #d6f57a;
    }
    .stApp {
        color: var(--nova-text);
        background:
            radial-gradient(ellipse at 14% 0%, rgba(37, 105, 153, .24), transparent 34%),
            radial-gradient(ellipse at 92% 14%, rgba(91, 81, 181, .18), transparent 30%),
            var(--nova-bg);
    }
    [data-testid="stAppViewContainer"] {
        background: transparent;
    }
    header[data-testid="stHeader"] {
        background: rgba(8, 13, 24, .58);
        backdrop-filter: blur(16px);
    }
    .block-container {
        max-width: 1000px;
        padding: clamp(2rem, 7vh, 5.25rem) clamp(1rem, 4vw, 2.4rem) 4rem;
    }
    .nova-hero {
        text-align: center;
        margin: 0 auto 2.1rem;
        max-width: 760px;
    }
    .nova-brand {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: .8rem;
        color: var(--nova-text);
        font-size: clamp(2.2rem, 6vw, 3.8rem);
        font-weight: 800;
        letter-spacing: -.055em;
        line-height: 1.08;
    }
    .nova-mark {
        display: inline-grid;
        place-items: center;
        width: clamp(3rem, 8vw, 4.25rem);
        height: clamp(3rem, 8vw, 4.25rem);
        border: 1px solid rgba(146, 215, 255, .32);
        border-radius: 1.2rem;
        background: linear-gradient(145deg, rgba(79, 164, 214, .2), rgba(121, 112, 218, .18));
        box-shadow: 0 12px 36px rgba(29, 120, 174, .14), inset 0 1px rgba(255,255,255,.08);
        font-size: clamp(1.75rem, 5vw, 2.5rem);
    }
    .nova-kicker {
        margin: 1.2rem 0 .45rem;
        color: var(--nova-accent);
        font-size: .72rem;
        font-weight: 750;
        letter-spacing: .18em;
    }
    .nova-subtitle {
        max-width: 600px;
        margin: 0 auto;
        color: var(--nova-muted);
        font-size: clamp(.95rem, 2.2vw, 1.08rem);
        line-height: 1.65;
    }
    h1, h2, h3 {
        color: var(--nova-text);
        letter-spacing: -.035em;
    }
    h1 {
        font-weight: 780;
    }
    div[data-testid="stButton"] {
        height: 100%;
    }
    div[data-testid="stButton"] > button {
        width: 100%;
        min-height: 92px;
        padding: 1.15rem 1.4rem;
        border: 1px solid var(--nova-line);
        border-radius: 18px;
        background: linear-gradient(145deg, rgba(20, 34, 54, .96), rgba(13, 23, 39, .96));
        color: var(--nova-text);
        box-shadow: 0 10px 30px rgba(0, 0, 0, .16), inset 0 1px rgba(255,255,255,.045);
        font-size: 1.05rem;
        font-weight: 680;
        line-height: 1.35;
        white-space: normal;
        transition: transform .18s cubic-bezier(.2,.8,.2,1), border-color .18s, box-shadow .18s, background .18s;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-3px);
        border-color: rgba(146, 215, 255, .68);
        background: linear-gradient(145deg, rgba(25, 47, 73, .98), rgba(16, 31, 52, .98));
        box-shadow: 0 16px 34px rgba(0, 0, 0, .28), 0 0 0 1px rgba(146,215,255,.06);
        color: #fff;
    }
    div[data-testid="stButton"] > button:active {
        transform: translateY(0) scale(.985);
    }
    div[data-testid="stButton"] > button:focus-visible {
        outline: 2px solid var(--nova-accent);
        outline-offset: 3px;
    }
    [data-testid="column"] {
        padding: .45rem;
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        border-color: #30445f;
        border-radius: 12px;
        background: #101a2a;
    }
    input, textarea {
        color: var(--nova-text) !important;
    }
    div[data-testid="stFileUploader"] section {
        border: 1px dashed #48617e;
        border-radius: 16px;
        background: rgba(16, 26, 42, .72);
    }
    div[data-testid="stAlert"] {
        border-radius: 13px;
    }
    audio {
        width: 100%;
        border-radius: 12px;
    }
    a {
        color: #a9ddff;
    }
    @media (max-width: 640px) {
        .block-container {
            padding-top: 2.5rem;
        }
        .nova-hero {
            margin-bottom: 1.35rem;
        }
        .nova-brand {
            gap: .6rem;
        }
        .nova-mark {
            border-radius: .95rem;
        }
        div[data-testid="stButton"] > button {
            min-height: 76px;
            padding: 1rem;
            font-size: 1rem;
        }
        [data-testid="column"] {
            padding: .28rem;
        }
    }
    @media (prefers-reduced-motion: reduce) {
        div[data-testid="stButton"] > button {
            transition: none;
        }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stButton"] > button:active {
            transform: none;
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


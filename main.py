import difflib
import hashlib
import io
import re
import shutil
import unicodedata
from urllib.parse import urlencode, urlsplit

import pytesseract
import speech_recognition as sr
import streamlit as st
import streamlit.components.v1 as components
from deep_translator import GoogleTranslator
from gtts import gTTS
from gtts.lang import tts_langs
from PIL import Image, ImageOps, UnidentifiedImageError
from pydub import AudioSegment

st.set_page_config(page_title="Nova Translate", page_icon="🌐", layout="wide")

components.html("""
    <meta name="google-site-verification" content="4yS5dM4B4u47bwLOxSwHp3AHWOrAbcaKQDN9HCbMB3g"/>
""", height=0)

tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

FALLBACK_LANGUAGES = {
    "Arabic": "ar",
    "Chinese (Simplified)": "zh-CN",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
}

@st.cache_data(ttl=86400, show_spinner=False)
def get_languages():
    try:
        raw_languages = GoogleTranslator().get_supported_languages(as_dict=True)
        languages = {
            str(name).replace("_", " ").title(): str(code)
            for name, code in raw_languages.items()
            if str(name).strip() and str(code).strip()
        }
        if languages:
            return dict(sorted(languages.items(), key=lambda item: item[0].casefold())), False
    except Exception:
        pass
    return FALLBACK_LANGUAGES, True

def choose_language(label, key):
    languages, using_fallback = get_languages()
    if using_fallback:
        st.caption("The full language list is temporarily unavailable. Common languages are still available.")
    selected = st.selectbox(label, list(languages), key=key)
    return languages[selected]

def split_translation(text, limit=4500):
    remaining = text.strip()
    chunks = []
    while len(remaining) > limit:
        boundary = max(remaining.rfind("\n", 0, limit), remaining.rfind(" ", 0, limit))
        if boundary < int(limit * 0.65):
            boundary = limit
        chunks.append(remaining[:boundary].strip())
        remaining = remaining[boundary:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks

def translate_text(text, target_code):
    text = str(text or "").strip()
    if not text:
        raise ValueError("Enter some text first.")
    translator = GoogleTranslator(source="auto", target=target_code)
    translated_chunks = [translator.translate(chunk) for chunk in split_translation(text)]
    return "\n\n".join(chunk for chunk in translated_chunks if chunk)

@st.cache_data(show_spinner=False, max_entries=12)
def extract_image_text(image_bytes):
    with Image.open(io.BytesIO(image_bytes)) as source:
        image = ImageOps.exif_transpose(source)
        image.load()
        image.thumbnail((3200, 3200))
        prepared = ImageOps.grayscale(image)
        return pytesseract.image_to_string(prepared, config="--oem 3 --psm 6").strip()

def normalize_phrase(text):
    normalized = unicodedata.normalize("NFKC", str(text)).casefold()
    return " ".join(
        "".join(character for character in normalized if character.isalnum() or character.isspace()).split()
    )

def phrase_match(expected, spoken):
    expected_normalized = normalize_phrase(expected)
    spoken_normalized = normalize_phrase(spoken)
    if not expected_normalized or not spoken_normalized:
        return 0.0
    if expected_normalized in spoken_normalized:
        return 1.0
    return difflib.SequenceMatcher(None, expected_normalized, spoken_normalized).ratio()

def speech_language(target_code):
    common_locales = {
        "ar": "ar-SA",
        "de": "de-DE",
        "en": "en-US",
        "es": "es-ES",
        "fr": "fr-FR",
        "hi": "hi-IN",
        "it": "it-IT",
        "ja": "ja-JP",
        "ko": "ko-KR",
        "pt": "pt-BR",
        "ru": "ru-RU",
        "zh-CN": "zh-CN",
        "zh-TW": "zh-TW",
    }
    return common_locales.get(target_code, target_code)

def prepare_audio(audio_bytes, extension):
    if len(audio_bytes) > 15 * 1024 * 1024:
        raise ValueError("Choose an audio file under 15 MB.")
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=extension)
    except Exception as error:
        raise ValueError("I couldn't open that audio file. Try exporting it again as WAV or MP3.") from error
    if len(audio) > 60_000:
        raise ValueError("Keep the recording under 60 seconds so it can be checked reliably.")
    if len(audio) < 250:
        raise ValueError("That recording is too short. Try recording the full phrase.")
    audio = audio.set_channels(1).set_frame_rate(16_000)
    output = io.BytesIO()
    audio.export(output, format="wav")
    output.seek(0)
    return output

def translate_site_url(raw_url, target_code):
    value = str(raw_url or "").strip()
    if not value:
        raise ValueError("Enter a website address first.")
    if not re.match(r"^https?://", value, flags=re.IGNORECASE):
        value = "https://" + value
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a complete website address, like example.com.")
    if parsed.username or parsed.password or any(character.isspace() for character in value):
        raise ValueError("That website address doesn't look right.")
    query = urlencode({"sl": "auto", "tl": target_code, "u": value})
    return "https://translate.google.com/translate?" + query

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
    [data-testid="stAppViewContainer"] { background: transparent; }
    header[data-testid="stHeader"] {
        background: rgba(8, 13, 24, .58);
        backdrop-filter: blur(16px);
    }
    .block-container {
        max-width: 1000px;
        padding: clamp(2rem, 7vh, 5.25rem) clamp(1rem, 4vw, 2.4rem) 4rem;
    }
    .nova-hero {
        max-width: 760px;
        margin: 0 auto 2.1rem;
        text-align: center;
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
    h1, h2, h3 { color: var(--nova-text); letter-spacing: -.035em; }
    h1 { font-weight: 780; }
    div[data-testid="stButton"] { height: 100%; }
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
    div[data-testid="stButton"] > button:active { transform: translateY(0) scale(.985); }
    div[data-testid="stButton"] > button:focus-visible {
        outline: 2px solid var(--nova-accent);
        outline-offset: 3px;
    }
    [data-testid="column"] { padding: .45rem; }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        border-color: #30445f;
        border-radius: 12px;
        background: #101a2a;
    }
    input, textarea { color: var(--nova-text) !important; }
    div[data-testid="stFileUploader"] section {
        border: 1px dashed #48617e;
        border-radius: 16px;
        background: rgba(16, 26, 42, .72);
    }
    div[data-testid="stAlert"] { border-radius: 13px; }
    audio { width: 100%; border-radius: 12px; }
    a { color: #a9ddff; }
    @media (max-width: 640px) {
        .block-container { padding-top: 2.5rem; }
        .nova-hero { margin-bottom: 1.35rem; }
        .nova-brand { gap: .6rem; }
        .nova-mark { border-radius: .95rem; }
        div[data-testid="stButton"] > button {
            min-height: 76px;
            padding: 1rem;
            font-size: 1rem;
        }
        [data-testid="column"] { padding: .28rem; }
    }
    @media (prefers-reduced-motion: reduce) {
        div[data-testid="stButton"] > button { transition: none; }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stButton"] > button:active { transform: none; }
    }
    </style>
""", unsafe_allow_html=True)

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

if "page" not in st.session_state:
    st.session_state.page = "home"

if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = ""
if "ocr_source_id" not in st.session_state:
    st.session_state.ocr_source_id = ""
if "ocr_translation" not in st.session_state:
    st.session_state.ocr_translation = None
if "text_translation" not in st.session_state:
    st.session_state.text_translation = None
if "practice_result" not in st.session_state:
    st.session_state.practice_result = None
if "website_translation" not in st.session_state:
    st.session_state.website_translation = None

def go(page_name):
    st.session_state.page = page_name
    st.rerun()

def back_button(key):
    if st.button("← Back to home", key=key, use_container_width=True):
        go("home")

if st.session_state.page == "home":
    top_left, top_right = st.columns(2)
    bottom_left, bottom_right = st.columns(2)

    with top_left:
        image_clicked = st.button("📸 Image Text Translate", key="home_image", use_container_width=True)
    with top_right:
        text_clicked = st.button("📝 Text Translation", key="home_text", use_container_width=True)
    with bottom_left:
        practice_clicked = st.button("🎤 Pronunciation Practice", key="home_practice", use_container_width=True)
    with bottom_right:
        website_clicked = st.button("🌍 Translate Website", key="home_website", use_container_width=True)

    if image_clicked:
        go("ocr")
    elif text_clicked:
        go("translate")
    elif practice_clicked:
        go("practice")
    elif website_clicked:
        go("website")

elif st.session_state.page == "website":
    st.title("🌍 Website Translator")
    st.caption("Open a translated version of a public website.")
    url = st.text_input("Website address", placeholder="example.com", key="website_url")
    target_code = choose_language("Translate to", "website_language")

    if st.button("Translate website", key="translate_website", use_container_width=True):
        try:
            translated_url = translate_site_url(url, target_code)
            st.session_state.website_translation = {"source": url.strip(), "target": target_code, "url": translated_url}
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("I couldn't prepare that link. Check the address and try again.")

    result = st.session_state.website_translation
    if result and result["source"] == url.strip() and result["target"] == target_code:
        st.link_button("🌍 Open translated website", result["url"], use_container_width=True)

    back_button("website_back")

elif st.session_state.page == "ocr":
    st.title("📸 Image Text Translate")
    st.caption("Upload a clear image and Nova will read the text before translating it.")
    uploaded_file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg"], key="image_upload")
    image_bytes = uploaded_file.getvalue() if uploaded_file else b""
    image_id = hashlib.sha256(image_bytes).hexdigest() if image_bytes else ""

    if image_id and image_id != st.session_state.ocr_source_id:
        st.session_state.ocr_source_id = image_id
        st.session_state.ocr_text = ""
        st.session_state.ocr_translation = None

    if uploaded_file:
        try:
            with Image.open(io.BytesIO(image_bytes)) as preview:
                image = ImageOps.exif_transpose(preview)
                image.load()
                st.image(image, caption="Uploaded image", use_container_width=True)
        except (UnidentifiedImageError, OSError):
            st.error("That image couldn't be opened. Try a PNG or JPG file.")
            image_bytes = b""
            image_id = ""

    if image_bytes and st.button("Read text from image", key="read_image_text", use_container_width=True):
        try:
            with st.spinner("Reading text from your image..."):
                st.session_state.ocr_text = extract_image_text(image_bytes)
            st.session_state.ocr_translation = None
        except pytesseract.TesseractNotFoundError:
            st.error("The text reader isn't installed right now. Please try again later.")
        except Exception:
            st.error("I couldn't read that image. Try a sharper image with the text facing forward.")

    if image_id and st.session_state.ocr_source_id == image_id and st.session_state.ocr_text:
        extracted_text = st.text_area("Text found in the image", value=st.session_state.ocr_text, height=160, key="ocr_text_editor")
        target_code = choose_language("Translate to", "ocr_language")

        if st.button("Translate image text", key="translate_ocr", use_container_width=True):
            try:
                with st.spinner("Translating the text..."):
                    translated = translate_text(extracted_text, target_code)
                st.session_state.ocr_translation = {
                    "source": extracted_text,
                    "target": target_code,
                    "text": translated,
                }
            except ValueError as error:
                st.warning(str(error))
            except Exception:
                st.error("The text was read, but translation failed. Try again in a moment.")

        result = st.session_state.ocr_translation
        if result and result["source"] == extracted_text and result["target"] == target_code:
            st.text_area("Translation", value=result["text"], height=180, key="ocr_translation_output")

    elif image_id and st.session_state.ocr_source_id == image_id and not st.session_state.ocr_text:
        st.info("Choose “Read text from image” to start.")

    back_button("ocr_back")

elif st.session_state.page == "translate":
    st.title("📝 Text Translation")
    st.caption("Translate a sentence or longer passage, then listen when speech is available.")
    source_text = st.text_area("Text to translate", height=160, placeholder="Type or paste text here.", key="source_text")
    target_code = choose_language("Translate to", "text_language")

    if st.button("Translate text", key="translate_text", use_container_width=True):
        try:
            with st.spinner("Translating..."):
                translated = translate_text(source_text, target_code)
            audio_bytes = None
            audio_message = ""
            if len(translated) <= 4000:
                try:
                    if target_code not in tts_langs():
                        audio_message = "Speech playback isn't available for this language."
                    else:
                        audio_file = io.BytesIO()
                        gTTS(translated, lang=target_code).write_to_fp(audio_file)
                        audio_bytes = audio_file.getvalue()
                except Exception:
                    audio_message = "The translation worked, but speech playback couldn't be made right now."
            else:
                audio_message = "The translation is ready. Speech playback is unavailable for long passages."
            st.session_state.text_translation = {
                "source": source_text,
                "target": target_code,
                "text": translated,
                "audio": audio_bytes,
                "audio_message": audio_message,
            }
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("Translation failed. Try again, or use a shorter passage.")

    result = st.session_state.text_translation
    if result and result["source"] == source_text and result["target"] == target_code:
        st.text_area("Translation", value=result["text"], height=180, key="text_translation_output")
        if result["audio"]:
            st.audio(result["audio"], format="audio/mp3")
        elif result["audio_message"]:
            st.caption(result["audio_message"])

    back_button("text_back")

elif st.session_state.page == "practice":
    st.title("🎤 Pronunciation Practice")
    st.caption("Upload a short recording. Nova compares what it hears with your phrase.")
    expected_phrase = st.text_input("Phrase to say", max_chars=500, placeholder="Type the phrase you practiced.", key="expected_phrase")
    audio_file = st.file_uploader("Recording (WAV or MP3, under 15 MB)", type=["wav", "mp3"], key="practice_audio")
    target_code = choose_language("Language spoken", "practice_language")

    if st.button("Check pronunciation", key="check_pronunciation", use_container_width=True):
        if not expected_phrase.strip():
            st.warning("Type the phrase you practiced first.")
        elif not audio_file:
            st.warning("Upload a WAV or MP3 recording first.")
        else:
            try:
                extension = audio_file.name.rsplit(".", 1)[-1].lower()
                with st.spinner("Listening to your recording..."):
                    prepared_audio = prepare_audio(audio_file.getvalue(), extension)
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(prepared_audio) as source:
                        audio_data = recognizer.record(source)
                    spoken_text = recognizer.recognize_google(
                        audio_data,
                        language=speech_language(target_code),
                    )
                score = phrase_match(expected_phrase, spoken_text)
                st.session_state.practice_result = {
                    "source": hashlib.sha256(audio_file.getvalue()).hexdigest(),
                    "expected": expected_phrase.strip(),
                    "target": target_code,
                    "spoken": spoken_text,
                    "score": score,
                }
            except ValueError as error:
                st.warning(str(error))
            except sr.UnknownValueError:
                st.warning("I couldn't make out the recording. Try a quieter room and say the phrase clearly.")
            except sr.RequestError:
                st.error("Speech recognition is unavailable right now. Please try again later.")
            except Exception:
                st.error("I couldn't check that recording. Try another WAV or MP3 file.")

    result = st.session_state.practice_result
    current_audio_id = hashlib.sha256(audio_file.getvalue()).hexdigest() if audio_file else ""
    if result and result["source"] == current_audio_id and result["expected"] == expected_phrase.strip() and result["target"] == target_code:
        st.write("I heard:")
        st.info(result["spoken"])
        st.progress(result["score"], text=f"Phrase match: {round(result['score'] * 100)}%")
        if result["score"] >= 0.85:
            st.success("Nice work — that was a close match.")
        else:
            st.warning("Try it once more, a little slower.")

    back_button("practice_back")

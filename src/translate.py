# src/translate.py
import os, time, json, logging
import requests

DEEPL_KEY = os.getenv("DEEPL_API_KEY")
GOOGLE_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")

class Translator:
    def translate(self, text: str) -> str:
        return text

class DeepLTranslator(Translator):
    def translate(self, text: str) -> str:
        if not text or not DEEPL_KEY:
            return text
        try:
            r = requests.post(
            "https://api.deepl.com/v2/translate",
            data={"auth_key": DEEPL_KEY, "text": text, "target_lang": "EN"}, timeout=20,
            )
            r.raise_for_status()
            data = r.json()
            return "\n".join([t["text"] for t in data.get("translations", [])]) or text
        except Exception as e:
            logging.warning(f"DeepL translate failed: {e}")
            return text

class GoogleTranslator(Translator):
    def translate(self, text: str) -> str:
        if not text or not GOOGLE_KEY:
            return text
        try:
            r = requests.post(
            "https://translation.googleapis.com/language/translate/v2",
            params={"key": GOOGLE_KEY},
            json={"q": text, "target": "en"}, timeout=20,
            )
            r.raise_for_status(); data = r.json()
            return "\n".join([tr["translatedText"] for tr in data.get("data", {}).get("translations", [])]) or text
        except Exception as e:
            logging.warning(f"Google translate failed: {e}")
            return text

    def get_translator() -> Translator:
        if DEEPL_KEY:
            return DeepLTranslator()
        if GOOGLE_KEY:
            return GoogleTranslator()
        return Translator()
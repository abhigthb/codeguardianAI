import os, json, re, time
from google import genai
from google.genai import types
from config import MODEL_NAME


def _get_key():
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY")


_client = None

def _client_get():
    global _client
    if _client is None:
        key = _get_key()
        if not key:
            raise RuntimeError("GEMINI_API_KEY not found. Add it to .streamlit/secrets.toml")
        _client = genai.Client(api_key=key)
    return _client


def ask(prompt: str, system: str = "", retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            resp = _client_get().models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system, temperature=0.2),
            )
            return resp.text or ""
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(4 * (attempt + 1))  # back off and retry


def ask_json(prompt: str, system: str = ""):
    """Asks the model for JSON and safely parses it. Returns [] on failure."""
    text = ask(prompt, system)
    text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return []
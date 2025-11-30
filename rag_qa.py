import os
from typing import List

import google.generativeai as genai

# Prefer GEMINI_API_KEY, fall back to GOOGLE_API_KEY if needed
_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if _API_KEY:
    genai.configure(api_key=_API_KEY)


def _ensure_configured() -> str:
    """Return empty string if OK, or error message if API key missing."""
    if not _API_KEY:
        return (
            "Gemini API key is not configured. "
            "Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment."
        )
    return ""


def ask_gemini_with_context(context_chunks: List[str], question: str) -> str:
    """
    Sends question + retrieved context to Gemini and returns the answer.
    Uses a fast, cheap model for RAG.
    """
    key_error = _ensure_configured()
    if key_error:
        return f"Error calling Gemini API: {key_error}"

    context_text = "\n\n--- Retrieved Context ---\n" + \
        "\n\n".join(context_chunks)

    prompt = f"""
You are an AI assistant. Use ONLY the provided context to answer the question.

{context_text}

--- QUESTION ---
{question}

Provide a clear and helpful answer.
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return getattr(response, "text", "").strip() or "(No answer returned by model.)"
    except Exception as e:
        return f"Error calling Gemini API: {e}"

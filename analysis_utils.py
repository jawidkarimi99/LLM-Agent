# analysis_utils.py
"""
Utility functions for sentiment analysis, keyword extraction,
and document-level statistics for visualization and analytics.
"""

from rag_qa import ask_gemini_with_context


# --------------------------------------------------------------------
# Helper: safely truncate long text for prompt limits
# --------------------------------------------------------------------
def _safe_text(text, limit=3000):
    if not text:
        return ""
    return text[:limit]


# --------------------------------------------------------------------
# SENTIMENT ANALYSIS
# --------------------------------------------------------------------
def analyze_sentiment(text: str) -> str:
    """
    Classify overall sentiment as Positive, Negative, or Neutral.
    Returns a single word.
    """
    text = _safe_text(text)

    prompt = f"""
    You are a sentiment classifier. Read the document text and classify the
    overall sentiment strictly as one of the following:

    - Positive
    - Negative
    - Neutral

    Respond with ONLY one word, no explanation.

    Document:
    {text}
    """

    result = ask_gemini_with_context([text], prompt)
    return result.strip()


# --------------------------------------------------------------------
# KEYWORD EXTRACTION
# --------------------------------------------------------------------
def extract_keywords(text: str, max_keywords=5):
    """
    Extract important keywords from the document using Gemini.
    Returns a Python list of strings.
    """
    text = _safe_text(text)

    prompt = f"""
    Extract the TOP {max_keywords} most important keywords from the following text.
    Respond ONLY with a comma-separated list of keywords. No sentences.

    Text:
    {text}
    """

    result = ask_gemini_with_context([text], prompt)
    keywords = [kw.strip() for kw in result.split(",")]
    return keywords


# --------------------------------------------------------------------
# DOCUMENT STATISTICS
# --------------------------------------------------------------------
def compute_document_stats(raw_text: str, summary: str = None):
    """
    Compute useful statistics for visualization.
    Returns a dictionary.
    """
    if not raw_text:
        raw_text = ""

    return {
        "length": len(raw_text),
        "summary_length": len(summary) if summary else 0,
        "word_count": len(raw_text.split()),
        "line_count": raw_text.count("\n") + 1,
    }


# --------------------------------------------------------------------
# FULL ANALYSIS PIPELINE
# --------------------------------------------------------------------
def analyze_document(raw_text: str, summary: str = None):
    """
    Return a full analysis package:
    - sentiment
    - keywords
    - stats
    """
    sentiment = analyze_sentiment(raw_text)
    keywords = extract_keywords(raw_text)
    stats = compute_document_stats(raw_text, summary)

    return {
        "sentiment": sentiment,
        "keywords": keywords,
        "stats": stats
    }

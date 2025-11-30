from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL


def ask_gemini(chunks, question):
    client = genai.Client(api_key=GEMINI_API_KEY)

    context = ""
    for i, ch in enumerate(chunks, start=1):
        context += f"[Chunk {i} | Source: {ch['meta']['source']}]\n"
        context += ch["text"] + "\n\n"

    prompt = f"""
You are a retrieval-augmented question answering system.
Answer ONLY using the context provided.

--- CONTEXT ---
{context}
--- END CONTEXT ---

Question: {question}

If the answer cannot be found in the context, say "Not found".
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    return response.text

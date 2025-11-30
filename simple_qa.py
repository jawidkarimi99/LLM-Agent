import os
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

# PDF/docx libraries
import fitz  # PyMuPDF for PDFs
from docx import Document as DocxDocument


def load_text_from_file(path):
    ext = os.path.splitext(path)[1].lower()

    if ext == ".txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    elif ext == ".docx":
        doc = DocxDocument(path)
        return "\n".join([p.text for p in doc.paragraphs])

    elif ext == ".pdf":
        text = []
        pdf = fitz.open(path)
        for page in pdf:
            text.append(page.get_text())
        return "\n".join(text)

    else:
        raise ValueError("Unsupported file type: " + ext)


def ask_gemini(context_text, question):
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
You are a question-answering assistant.

Answer the user's question ONLY using the text below.
If the answer is not found in the document, say "Not found".

--- BEGIN DOCUMENT ---
{context_text[:15000]}  # safety limit
--- END DOCUMENT ---

Question: {question}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    return response.text


def main():
    print("=== Simple Document QA ===")

    path = input("Enter path to file (.txt / .pdf / .docx): ").strip()
    question = input("Enter your question: ").strip()

    print("\nLoading document...\n")
    doc_text = load_text_from_file(path)

    print("Asking Gemini...\n")
    answer = ask_gemini(doc_text, question)

    print("=== ANSWER ===\n")
    print(answer)


if __name__ == "__main__":
    main()

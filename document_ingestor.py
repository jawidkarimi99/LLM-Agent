import requests
from bs4 import BeautifulSoup
import docx
import PyPDF2
import os


class DocumentIngestor:

    def load(self, path_or_url):
        """Universal loader that chooses correct method."""
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return self._load_url(path_or_url)

        if path_or_url.endswith(".txt"):
            return self._load_txt(path_or_url)

        if path_or_url.endswith(".docx"):
            return self._load_docx(path_or_url)

        if path_or_url.endswith(".pdf"):
            return self._load_pdf(path_or_url)

        # Fallback: treat anything else as text
        return self._load_txt(path_or_url)

    # -----------------------------------------------------
    # TXT LOADER
    # -----------------------------------------------------
    def _load_txt(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except:
            with open(filepath, "r", encoding="latin-1") as f:
                return f.read()

    # -----------------------------------------------------
    # DOCX LOADER
    # -----------------------------------------------------
    def _load_docx(self, filepath):
        doc = docx.Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs])

    # -----------------------------------------------------
    # PDF LOADER (non-scanned PDFs)
    # -----------------------------------------------------
    def _load_pdf(self, filepath):
        text = ""
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                try:
                    text += page.extract_text() + "\n"
                except:
                    continue
        return text

    # -----------------------------------------------------
    # URL LOADER (HTML pages)
    # -----------------------------------------------------
    def _load_url(self, url):
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts/styles
        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        return text.strip()

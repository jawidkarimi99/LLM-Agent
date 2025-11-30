import fitz  # PyMuPDF for scanned PDF fallback
import pytesseract
from PIL import Image
import io


def extract_text_from_image(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        return f"[OCR_IMAGE_ERROR] {e}"


def extract_text_from_scanned_pdf(path):
    try:
        doc = fitz.open(path)
        text = ""

        for page in doc:
            pix = page.get_pixmap()
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            text += pytesseract.image_to_string(img) + "\n"

        return text.strip()

    except Exception as e:
        return f"[OCR_PDF_ERROR] {e}"

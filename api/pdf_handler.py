import fitz  # pymupdf
import re
import pytesseract
from PIL import Image
import io

# Point pytesseract at the installed Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def fix_ligature_artifacts(text: str) -> str:
    """
    Some PDFs have their 'f' character (as part of an 'fi' or 'fl' ligature)
    misread as '6' during extraction. This restores it.
    """
    text = re.sub(r'6(?=[a-z])', 'f', text)
    return text


def ocr_pdf_pages(pdf_bytes: bytes, max_pages: int = 3) -> str:
    """
    Renders PDF pages as images and runs OCR on them.
    Capped at max_pages to keep this fast for a demo.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    ocr_text_parts = []
    pages_to_process = min(len(doc), max_pages)

    for page_num in range(pages_to_process):
        page = doc[page_num]
        # Render page at higher resolution for better OCR accuracy
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        page_text = pytesseract.image_to_string(image)
        ocr_text_parts.append(page_text.strip())

    doc.close()

    combined = "\n\n".join(ocr_text_parts)
    return fix_ligature_artifacts(combined.strip())


def extract_text_from_pdf(pdf_bytes: bytes) -> dict:
    """
    Attempts direct text extraction from a PDF.
    Falls back to OCR if the PDF appears to be scanned (no extractable text).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    full_text = ""
    for page in doc:
        full_text += page.get_text()

    page_count = doc.page_count
    doc.close()

    full_text = full_text.strip()
    full_text = fix_ligature_artifacts(full_text)

    is_likely_scanned = len(full_text) < 20

    used_ocr = False
    if is_likely_scanned:
        full_text = ocr_pdf_pages(pdf_bytes)
        used_ocr = True

    return {
        "text": full_text,
        "is_likely_scanned": is_likely_scanned,
        "used_ocr": used_ocr,
        "page_count": page_count
    }
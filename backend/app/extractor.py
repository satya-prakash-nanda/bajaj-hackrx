import os
import tempfile
import logging
import zipfile
from typing import List, Union
from urllib.parse import urlparse

import requests
import pandas as pd
from pydantic import HttpUrl
from fpdf import FPDF
from PIL import Image
from docx import Document as DocxDocument
from langchain_core.documents import Document as LCDocument
from langchain_community.document_loaders import PyMuPDFLoader

logger = logging.getLogger(__name__)

# ------------------------------
# File Download Utility
# ------------------------------
def download_file(file_url: str, default_suffix: str) -> str:
    logger.info(f"🌐 Downloading file from URL: {file_url}")
    try:
        parsed = urlparse(file_url)
        ext = os.path.splitext(parsed.path)[1]
        if not ext:
            ext = default_suffix

        response = requests.get(file_url, timeout=20)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            tmp_file.write(response.content)
            temp_path = tmp_file.name

        logger.info(f"✅ File downloaded to: {temp_path}")
        return temp_path
    except requests.RequestException as e:
        logger.error(f"❌ Failed to download file: {e}")
        raise

# ------------------------------
# PDF Writing Helper
# ------------------------------
def _safe_pdf_write(pdf: FPDF, text: str, cell_h=8):
    """Write text to PDF with unicode fallback."""
    try:
        pdf.multi_cell(0, cell_h, txt=text)
    except UnicodeEncodeError:
        pdf.multi_cell(0, cell_h, txt=text.encode('latin-1', 'replace').decode('latin-1'))

# ------------------------------
# Linux + Windows-Compatible Converters
# ------------------------------
def docx_to_pdf(docx_path: str) -> str:
    """
    Convert DOCX to PDF with full Unicode support (Windows/Linux/Mac).
    """
    logger.info(f"📝 Converting DOCX to PDF: {docx_path}")
    try:
        pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        
        # Load DOCX
        doc = DocxDocument(docx_path)
        
        # Init PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Fonts folder is inside "app"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_dir = os.path.join(base_dir, "app", "fonts")
        font_path = os.path.join(font_dir, "DejaVuSans.ttf")
        
        if os.path.exists(font_path):
            pdf.add_font("DejaVu", "", font_path, uni=True)  # Enable Unicode
            pdf.set_font("DejaVu", size=12)
            logger.info(f"✅ Using Unicode font: {font_path}")
        else:
            raise FileNotFoundError(
                f"Missing font {font_path}. Download DejaVuSans.ttf and place it in app/fonts/"
            )
        
        # Add paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                pdf.multi_cell(0, 8, text)  # No encoding errors
        
        # Save PDF
        pdf.output(pdf_path)
        logger.info(f"✅ Saved PDF: {pdf_path}")
        return pdf_path
    
    except Exception as e:
        logger.error(f"❌ Failed to convert DOCX to PDF: {e}")
        raise


def image_to_pdf(image_path: str) -> str:
    logger.info(f"🖼️ Converting image to PDF: {image_path}")
    try:
        pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        image = Image.open(image_path).convert("RGB")
        image.save(pdf_path, "PDF")
        logger.info(f"✅ Image converted to PDF: {pdf_path}")
        return pdf_path
    except Exception as e:
        logger.error(f"❌ Failed to convert image to PDF: {e}")
        raise

def xlsx_to_pdf(xlsx_path: str) -> str:
    logger.info(f"📊 Converting XLSX to PDF: {xlsx_path}")
    try:
        df = pd.read_excel(xlsx_path)
        pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=10)

        for _, row in df.iterrows():
            row_str = " | ".join(str(cell) for cell in row)
            _safe_pdf_write(pdf, row_str, cell_h=8)

        pdf.output(pdf_path)
        logger.info(f"✅ XLSX converted to PDF: {pdf_path}")
        return pdf_path
    except Exception as e:
        logger.error(f"❌ Failed to convert XLSX to PDF: {e}")
        raise

def process_pdf_zip(zip_path: str) -> str:
    logger.info(f"📦 Extracting PDF from ZIP: {zip_path}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for file in z.namelist():
                if file.lower().endswith(".pdf"):
                    extracted_path = z.extract(file, tempfile.gettempdir())
                    logger.info(f"✅ Extracted PDF: {extracted_path}")
                    return extracted_path
        raise ValueError("No PDF found in zip file.")
    except Exception as e:
        logger.error(f"❌ Failed to process ZIP: {e}")
        raise

def eml_to_pdf(eml_path: str) -> str:
    logger.info(f"📧 Converting EML to PDF: {eml_path}")
    try:
        pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=10)

        with open(eml_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            _safe_pdf_write(pdf, content, cell_h=5)

        pdf.output(pdf_path)
        logger.info(f"✅ EML converted to PDF: {pdf_path}")
        return pdf_path
    except Exception as e:
        logger.error(f"❌ Failed to convert EML to PDF: {e}")
        raise

def msg_to_pdf(msg_path: str) -> str:
    logger.info(f"📨 Converting MSG to PDF: {msg_path}")
    try:
        import extract_msg
        msg = extract_msg.Message(msg_path)
        pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=10)

        content = f"From: {msg.sender}\nTo: {msg.to}\nDate: {msg.date}\nSubject: {msg.subject}\n\n{msg.body}"
        _safe_pdf_write(pdf, content, cell_h=5)

        pdf.output(pdf_path)
        logger.info(f"✅ MSG converted to PDF: {pdf_path}")
        return pdf_path
    except ImportError:
        logger.error("❌ extract_msg package not installed. Run: pip install extract_msg")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to convert MSG to PDF: {e}")
        raise

# ------------------------------
# Main Extraction Function
# ------------------------------
def extract_text_only(file_path: Union[str, HttpUrl]) -> List[LCDocument]:
    """
    Extracts text from a file using PyMuPDFLoader and returns LangChain Document objects.
    Handles URLs, DOCX, EML, MSG, XLSX, JPG/PNG, ZIP formats as well.
    """
    logger.info(f"📄 Starting text extraction for: {file_path}")

    # Convert HttpUrl → string
    if isinstance(file_path, HttpUrl):
        file_path = str(file_path)

    # If URL → download first
    if file_path.startswith("http://") or file_path.startswith("https://"):
        parsed = urlparse(file_path)
        ext = os.path.splitext(parsed.path)[1].lower()
        file_path = download_file(file_path, ext or ".pdf")

    # Convert formats to PDF if needed
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".docx":
        file_path = docx_to_pdf(file_path)
    elif ext in [".jpg", ".jpeg", ".png"]:
        file_path = image_to_pdf(file_path)
    elif ext == ".xlsx":
        file_path = xlsx_to_pdf(file_path)
    elif ext == ".zip":
        file_path = process_pdf_zip(file_path)
    elif ext == ".eml":
        file_path = eml_to_pdf(file_path)
    elif ext == ".msg":
        file_path = msg_to_pdf(file_path)
    elif ext != ".pdf":
        raise ValueError(f"Unsupported file type: {ext}")

    # Load PDF into LangChain docs
    try:
        logger.info(f"📥 Loading PDF with PyMuPDFLoader: {file_path}")
        loader = PyMuPDFLoader(file_path)
        docs: List[LCDocument] = loader.load()
        logger.info(f"✅ Extracted {len(docs)} document chunks.")
        return docs
    except Exception as e:
        logger.error(f"❌ PDF parsing failed: {e}")
        raise

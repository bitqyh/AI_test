import re
import hashlib
from pathlib import Path
from typing import Optional

from app.config import PDF_MAX_CHARS


def compute_file_md5(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def clean_text(text: str) -> str:
    text = re.sub(r"[^\u4e00-\u9fff\u3400-\u4dbfa-zA-Z0-9\s.,;:!?@#\$%^&*()\[\]{}\-+=_/\\|~`'\"<>\n]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{3,}", "  ", text)
    text = re.sub(r"(\n\s*)+\n", "\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line)
    return text


def extract_text_with_pypdf(file_path: str) -> Optional[str]:
    try:
        from langchain_community.document_loaders import PyPDFLoader

        loader = PyPDFLoader(file_path)
        pages = loader.load()
        text = "\n".join(page.page_content for page in pages)
        return text
    except Exception:
        return None


def extract_text_with_pdfplumber(file_path: str) -> str:
    import pdfplumber

    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
            for table in page.extract_tables():
                for row in table:
                    row_text = " | ".join(
                        str(cell) if cell is not None else "" for cell in row
                    )
                    text_parts.append(row_text)
    return "\n".join(text_parts)


def load_pdf_text(file_path: str) -> str:
    text = extract_text_with_pypdf(file_path)
    if not text or len(text.strip()) < 50:
        text = extract_text_with_pdfplumber(file_path)
    if not text:
        raise ValueError("无法从PDF中提取文本内容，请检查文件是否有效。")
    text = clean_text(text)
    if len(text) > PDF_MAX_CHARS:
        text = text[:PDF_MAX_CHARS]
    return text

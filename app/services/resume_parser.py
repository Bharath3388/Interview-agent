import io
import logging
from typing import Optional

from fastapi import UploadFile

logger = logging.getLogger(__name__)


class ResumeParser:
    async def parse(self, file: UploadFile) -> str:
        """Extract text from uploaded PDF or DOCX resume."""
        content = await file.read()
        filename = (file.filename or "").lower()

        if filename.endswith(".pdf"):
            return self._parse_pdf(content)
        elif filename.endswith(".docx"):
            return self._parse_docx(content)
        else:
            # Try as plain text
            try:
                return content.decode("utf-8", errors="ignore")
            except Exception:
                return ""

    def _parse_pdf(self, content: bytes) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n".join(pages)
        except Exception as e:
            logger.error("PDF parsing error: %s", e)
            return ""

    def _parse_docx(self, content: bytes) -> str:
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            logger.error("DOCX parsing error: %s", e)
            return ""

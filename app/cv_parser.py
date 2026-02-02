import os
import logging
from typing import Optional
from pathlib import Path
import docx
from PyPDF2 import PdfReader
import aiofiles

logger = logging.getLogger(__name__)


class CVParser:
    """Parse CV files (PDF, DOCX, TXT) and extract text."""
    
    @staticmethod
    async def parse_file(file_path: str, file_type: Optional[str] = None) -> str:
        """
        Parse a CV file and return extracted text.
        
        Args:
            file_path: Path to the CV file
            file_type: File type (pdf, docx, txt). If None, inferred from extension.
        
        Returns:
            Extracted text content
        """
        path = Path(file_path)
        
        if file_type is None:
            file_type = path.suffix.lower().lstrip('.')
        
        if file_type == 'pdf':
            return await CVParser._parse_pdf(file_path)
        elif file_type == 'docx':
            return await CVParser._parse_docx(file_path)
        elif file_type == 'txt':
            return await CVParser._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    @staticmethod
    async def _parse_pdf(file_path: str) -> str:
        """Parse PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise
    
    @staticmethod
    async def _parse_docx(file_path: str) -> str:
        """Parse DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            logger.error(f"Error parsing DOCX {file_path}: {e}")
            raise
    
    @staticmethod
    async def _parse_txt(file_path: str) -> str:
        """Parse TXT file."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                text = await f.read()
            return text.strip()
        except Exception as e:
            logger.error(f"Error parsing TXT {file_path}: {e}")
            raise

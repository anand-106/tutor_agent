from typing import List, Dict, Any
import fitz  # PyMuPDF
from docx import Document  # Make sure to use python-docx, not docx
import re
from pathlib import Path
import logging
from .logger_config import setup_logger

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = {'.pdf', '.docx', '.txt'}
        self.logger = setup_logger('document_processor')

    def process_document(self, file_path: str) -> str:
        """Process different document formats and return clean text"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
                
            file_ext = file_path.suffix.lower()
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            self.logger.info(f"Processing document: {file_path}")
            
            if file_ext == '.pdf':
                return self._process_pdf(file_path)
            elif file_ext == '.docx':
                return self._process_docx(file_path)
            else:
                return self._process_txt(file_path)
                
        except Exception as e:
            self.logger.error(f"Error processing document {file_path}: {str(e)}")
            raise

    def _process_pdf(self, file_path: str) -> str:
        """Extract text from PDF files"""
        try:
            text = ""
            with fitz.open(file_path) as doc:
                for page_num, page in enumerate(doc):
                    try:
                        text += page.get_text()
                        self.logger.debug(f"Processed PDF page {page_num + 1}")
                    except Exception as e:
                        self.logger.warning(f"Error processing page {page_num + 1}: {str(e)}")
            
            cleaned_text = self._clean_text(text)
            self.logger.info(f"Successfully processed PDF: {file_path}")
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Error processing PDF {file_path}: {str(e)}")
            raise

    def _process_docx(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            cleaned_text = self._clean_text(text)
            self.logger.info(f"Successfully processed DOCX: {file_path}")
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Error processing DOCX {file_path}: {str(e)}")
            raise

    def _process_txt(self, file_path: str) -> str:
        """Read text from TXT files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            cleaned_text = self._clean_text(text)
            self.logger.info(f"Successfully processed TXT: {file_path}")
            return cleaned_text
            
        except UnicodeDecodeError:
            self.logger.warning(f"UTF-8 decode failed, trying with alternative encodings: {file_path}")
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        text = file.read()
                    return self._clean_text(text)
                except UnicodeDecodeError:
                    continue
            raise
            
        except Exception as e:
            self.logger.error(f"Error processing TXT {file_path}: {str(e)}")
            raise

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        try:
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            # Remove special characters but keep necessary punctuation
            text = re.sub(r'[^\w\s.,!?;:-]', '', text)
            cleaned_text = text.strip()
            
            if not cleaned_text:
                self.logger.warning("Cleaning resulted in empty text")
            
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Error cleaning text: {str(e)}")
            raise 
import fitz
import docx
import pandas as pd
from ollama_backend import OllamaOCRBackend
from database import insert_page
import logging
logger = logging.getLogger(__name__)


class ExtractionFactory:
    """
    Implements a Strategy/Factory pattern to dynamically route incoming documents
    to highly-specialized parsers, maintaining Data Homogenization for the Database.
    """
    
    @staticmethod
    def extract_text(file_path: str, filename: str, metadata: dict = None):
        """Routing hub for Omni-Format extraction"""
        ext = filename.split('.')[-1].lower()
        if metadata is None:
            metadata = {}
            
        if ext == 'pdf':
            ExtractionFactory._process_pdf(file_path, filename, metadata)
        elif ext == 'docx':
            ExtractionFactory._process_docx(file_path, filename, metadata)
        elif ext == 'txt':
            ExtractionFactory._process_txt(file_path, filename, metadata)
        elif ext in ['csv', 'xlsx']:
            ExtractionFactory._process_spreadsheet(file_path, filename, metadata, ext)
        elif ext in ['png', 'jpeg', 'jpg']:
            ExtractionFactory._process_image(file_path, filename, metadata)
        else:
            raise ValueError(f"Unsupported Omni-format extension: {ext}")

    @staticmethod
    def _process_pdf(file_path, filename, metadata):
        doc = fitz.open(file_path)
        pdf_meta = doc.metadata or {}
        cleaned_meta = {k: v for k, v in pdf_meta.items() if v}
        metadata.update(cleaned_meta)
        
        for page_index in range(len(doc)):
            page = doc[page_index]
            blocks = page.get_text("blocks")
            blocks.sort(key=lambda b: (b[1], b[0]))
            page_text = "\n\n".join([b[4].strip() for b in blocks if b[4].strip()])
            
            insert_page(filename, metadata, page_index + 1, page_text)
        doc.close()

    @staticmethod
    def _process_docx(file_path, filename, metadata):
        doc = docx.Document(file_path)
        # Structural conversion: Array of paragraphs to single string
        full_text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        insert_page(filename, metadata, 1, full_text)

    @staticmethod
    def _process_txt(file_path, filename, metadata):
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        insert_page(filename, metadata, 1, full_text)

    @staticmethod
    def _process_spreadsheet(file_path, filename, metadata, ext):
        try:
            if ext == 'csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
                
            # Serialize DataFrame to JSON records
            json_array = df.to_json(orient='records', indent=2)
            structured_text = f"Spreadsheet Data Layout:\n{json_array}"
            insert_page(filename, metadata, 1, structured_text)
        except Exception as e:
            raise Exception(f"Spreadsheet parsing failed: {str(e)}")

    @staticmethod
    def _process_image(file_path, filename, metadata):
        try:
            # Route through Ollama Vision OCR Model
            backend = OllamaOCRBackend()
            if not backend.is_available():
                raise Exception("Ollama server is unreachable. Ensure the service is running at http://localhost:11434 and 'deepseek-ocr:3b' is pulled.")
            logger.info("Ollama server is reachable. Extracting text from image...")
                
            resp = backend.extract_text(file_path, filename)
            extracted_text = resp.text if resp.text else "(No text extracted by Vision Model)"
            logger.info(f"Extracted text: {extracted_text}")
            insert_page(filename, metadata, 1, extracted_text)
        except Exception as e:
            raise Exception(f"Image parsing failed: {str(e)}")

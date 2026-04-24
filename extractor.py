import fitz  # PyMuPDF
from database import insert_page

def process_pdf(file_path: str, document_name: str):
    """
    Reads a PDF, extracts metadata, and inserts each page's text into the database.
    """
    doc = fitz.open(file_path)
    metadata = doc.metadata
    
    # Clean up metadata to ensure it's serializable and valid
    cleaned_metadata = {k: v for k, v in metadata.items() if v}

    for page_index in range(len(doc)):
        page = doc[page_index]
        
        # Use "blocks" extraction to maintain structural hierarchy and cleaner line breaks
        blocks = page.get_text("blocks")
        # Sort blocks by vertical then horizontal position to ensure reading order
        blocks.sort(key=lambda b: (b[1], b[0]))
        
        # Join block text with double newlines to separate logical paragraphs/sections
        page_text = "\n\n".join([b[4].strip() for b in blocks if b[4].strip()])
        
        # We store page_index + 1 so it corresponds to a human-readable page number
        insert_page(document_name, cleaned_metadata, page_index + 1, page_text)
        
    doc.close()

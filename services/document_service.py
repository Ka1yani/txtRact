import os
import shutil
from fastapi import UploadFile
from extractor import process_pdf

class DocumentService:
    """
    Service responsible for handling document-level operations.
    Follows the Single Responsibility Principle (SRP).
    """
    
    @staticmethod
    def process_and_store_upload(file: UploadFile) -> str:
        """
        Saves a temporary file, processes it, and cleans up after.
        Clean up uses a finally block to ensure resilience.
        """
        temp_file_path = f"temp_{file.filename}"
        try:
            # Save the file temporarily
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            # Process the PDF and insert into DB
            process_pdf(temp_file_path, file.filename)
            return file.filename
        finally:
            # Guaranteed cleanup even if extraction fails
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

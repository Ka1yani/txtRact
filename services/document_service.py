import os
import shutil
from fastapi import UploadFile
from services.worker import process_document_task

class DocumentService:
    """
    Service responsible for handling document-level operations using Celery workers.
    Follows the Single Responsibility Principle (SRP).
    """
    
    @staticmethod
    def process_and_store_upload(file: UploadFile) -> dict:
        """
        Saves a temporary file and dispatches a background processing task.
        Returns the task ID and document name.
        """
        temp_file_path = f"temp_{file.filename}"
        
        # Save the file temporarily for the worker to pick up
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Dispatch the background task via Celery
        task = process_document_task.delay(temp_file_path, file.filename)
            
        return {
            "document_name": file.filename,
            "task_id": task.id,
            "status": "queued"
        }

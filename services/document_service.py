import os
import shutil
import uuid
from fastapi import UploadFile, BackgroundTasks
from services.worker import process_document_bg, task_status_store

class DocumentService:
    """
    Service responsible for handling document-level operations using native FastAPI BackgroundTasks.
    Follows the Single Responsibility Principle (SRP).
    """
    
    @staticmethod
    def process_and_store_upload(file: UploadFile, background_tasks: BackgroundTasks) -> dict:
        """
        Saves a temporary file and dispatches a native FastAPI background task.
        Returns the generated task ID and document name.
        """
        task_id = str(uuid.uuid4())
        temp_file_path = f"temp_{file.filename}"
        
        # Save the file temporarily
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Register the initial status
        task_status_store[task_id] = "queued"
        
        # Add to FastAPI background tasks
        background_tasks.add_task(process_document_bg, task_id, temp_file_path, file.filename)
            
        return {
            "document_name": file.filename,
            "task_id": task_id,
            "status": "queued"
        }

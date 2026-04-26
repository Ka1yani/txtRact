import os
import shutil
import uuid
from fastapi import UploadFile, BackgroundTasks
from services.worker import process_document_bg, task_status_store

import logging

logger = logging.getLogger(__name__)

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
        
        logger.info(f"Initiating temporary file persistence for {file.filename} -> {temp_file_path}")
        # Save the file temporarily
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size_bytes = os.path.getsize(temp_file_path)
            
        # Register the initial status
        logger.info(f"Registering task {task_id} into in-memory store. (Size: {file_size_bytes} bytes)")
        task_status_store[task_id] = "queued"
        
        # Add to FastAPI background tasks
        logger.info(f"Delegating task {task_id} to background worker pool.")
        background_tasks.add_task(process_document_bg, task_id, temp_file_path, file.filename, file_size_bytes)
            
        return {
            "document_name": file.filename,
            "task_id": task_id,
            "status": "queued"
        }

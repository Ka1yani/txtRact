import os
from services.extraction_factory import ExtractionFactory

import logging

logger = logging.getLogger(__name__)

# In-memory store for task statuses (Redis-less implementation)
# Note: In a multi-worker production environment (Gunicorn), 
# this would need to be moved to a shared DB state.
task_status_store = {}

def process_document_bg(task_id: str, file_path: str, document_name: str, file_size_bytes: int = 0):
    """
    Background worker logic for FastAPI BackgroundTasks.
    """
    logger.info(f"Background worker started for task: {task_id} | Document: {document_name}")
    try:
        task_status_store[task_id] = "processing"
        metadata = {"file_size_bytes": file_size_bytes}
        ExtractionFactory.extract_text(file_path, document_name, metadata)
        
        # Cleanup temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Temporary file {file_path} cleaned up successfully.")
            
        task_status_store[task_id] = "completed"
        logger.info(f"Background worker completed successfully for task: {task_id}")
    except Exception as e:
        task_status_store[task_id] = f"failed: {str(e)}"
        # Log failure for visibility
        logger.error(f"Task {task_id} failed abruptly: {e}", exc_info=True)

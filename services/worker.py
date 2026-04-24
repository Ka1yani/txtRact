import os
from extractor import process_pdf

# In-memory store for task statuses (Redis-less implementation)
# Note: In a multi-worker production environment (Gunicorn), 
# this would need to be moved to a shared DB state.
task_status_store = {}

def process_document_bg(task_id: str, file_path: str, document_name: str):
    """
    Background worker logic for FastAPI BackgroundTasks.
    """
    try:
        task_status_store[task_id] = "processing"
        process_pdf(file_path, document_name)
        
        # Cleanup temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        task_status_store[task_id] = "completed"
    except Exception as e:
        task_status_store[task_id] = f"failed: {str(e)}"
        # Log failure for visibility
        print(f"Task {task_id} failed: {e}")

import os
from celery import Celery
from extractor import process_pdf
from database import SYNC_DATABASE_URL

# Configure Celery to use Redis as the message broker
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Standard Celery configuration for document processing tasks
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_track_started=True,
    task_ignore_result=False
)

@celery_app.task(name="process_document_task")
def process_document_task(file_path: str, document_name: str):
    """
    Background task to process a PDF and index it in the database.
    """
    try:
        process_pdf(file_path, document_name)
        # We delete the temp file here after successful processing in the background
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"status": "completed", "document": document_name}
    except Exception as e:
        # Maintain the file if it fails for debugging or cleanup elsewhere
        return {"status": "failed", "error": str(e), "document": document_name}

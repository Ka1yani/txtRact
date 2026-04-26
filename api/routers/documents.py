from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from services.document_service import DocumentService
from services.worker import task_status_store
from database import get_all_documents

import logging

logger = logging.getLogger(__name__)

# Utilizing APIRouter for structural organization
router = APIRouter(tags=["documents"])

@router.get("/documents/all")
async def fetch_all_documents():
    """
    Fetches the comprehensive catalog of all documents uploaded and extracted in the DB.
    """
    try:
        docs = await get_all_documents()
        return {"status": "success", "documents": docs}
    except Exception as e:
        logger.error(f"Failed to fetch documents catalog: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching documents catalog")

# Dependency Injection function to supply the service
def get_document_service() -> DocumentService:
    return DocumentService()

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
):
    """
    Endpoint strictly responsible for handling the API Request/Response.
    Delegates all heavy lifting to the injected DocumentService with background tasks.
    """
    logger.info(f"API Request Received: POST /upload | Filename: {file.filename}")
    supported_extensions = ('.pdf', '.docx', '.txt', '.csv', '.xlsx', '.png', '.jpeg', '.jpg')
    if not file.filename.lower().endswith(supported_extensions):
        logger.warning(f"File upload rejected: {file.filename} (Unsupported extension)")
        raise HTTPException(status_code=400, detail=f"Unsupported file format. Allowed: {supported_extensions}")
        
    try:
        result = service.process_and_store_upload(file, background_tasks)
        logger.info(f"Upload successfully delegated to background tasks for {file.filename} | Task ID: {result['task_id']}")
        return {
            "status": "accepted", 
            "message": f"Processing of {result['document_name']} has been started in the background.",
            "task_id": result["task_id"]
        }
    except Exception as e:
        logger.error(f"Failed to process upload request for {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Checks the status of a specific background document processing task.
    Reads from the local in-memory task_status_store.
    """
    status = task_status_store.get(task_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Task ID not found.")
        
    return {
        "task_id": task_id,
        "status": status
    }

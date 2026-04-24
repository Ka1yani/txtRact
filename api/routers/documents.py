from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from services.document_service import DocumentService
from services.worker import task_status_store

# Utilizing APIRouter for structural organization
router = APIRouter(tags=["documents"])

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
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        result = service.process_and_store_upload(file, background_tasks)
        return {
            "status": "accepted", 
            "message": f"Processing of {result['document_name']} has been started in the background.",
            "task_id": result["task_id"]
        }
    except Exception as e:
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

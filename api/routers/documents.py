from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from services.document_service import DocumentService

# Utilizing APIRouter for structural organization
router = APIRouter(tags=["documents"])

# Dependency Injection function to supply the service
def get_document_service() -> DocumentService:
    return DocumentService()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    """
    Endpoint strictly responsible for handling the API Request/Response.
    Delegates all heavy lifting to the injected DocumentService.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        result = service.process_and_store_upload(file)
        return {
            "status": "accepted", 
            "message": f"Processing of {result['document_name']} has been queued.",
            "task_id": result["task_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Checks the status of a specific background document processing task.
    """
    from services.worker import celery_app
    task_result = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }


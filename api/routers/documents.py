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
        filename = service.process_and_store_upload(file)
        return {"status": "success", "message": f"{filename} processed and indexed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

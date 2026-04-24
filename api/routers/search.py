from fastapi import APIRouter, HTTPException, Depends
from services.search_service import SearchService

router = APIRouter(tags=["search"])

def get_search_service() -> SearchService:
    return SearchService()

@router.get("/search")
async def search(
    q: str,
    service: SearchService = Depends(get_search_service)
):
    """
    Search Endpoint. 
    Uses the injected SearchService to execute the intent parsing and DB calls.
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
        
    try:
        return service.execute_search(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

from fastapi import APIRouter, HTTPException, Depends
from services.search_service import SearchService

import logging

logger = logging.getLogger(__name__)

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
    logger.info(f"API Request Received: GET /search | Query: '{q}'")
    if not q:
        logger.warning("Search request failed: Missing query parameter 'q'")
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
        
    try:
        return await service.execute_search(q)
    except Exception as e:
        logger.error(f"Search endpoint error for query '{q}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

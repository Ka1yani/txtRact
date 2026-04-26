import logging
import re
from typing import Dict, Any
from database import search_database, search_by_page_number, resolve_document_filename

logger = logging.getLogger(__name__)

class SearchService:
    """
    Service responsible for executing search queries and intelligent intent parsing.
    Follows the Single Responsibility Principle (SRP).
    """
    
    @staticmethod
    async def execute_search(query: str) -> Dict[str, Any]:
        """
        Detects user intent (e.g. specific page vs standard text search) 
        and routes it to the appropriate database functionality dynamically assessing extensions.
        """
        logger.info(f"Parsing intent for search query: '{query}'")
        
        # Detect requested page
        page_match = re.search(r"page\s+(\d+)", query.lower())
        page_number = int(page_match.group(1)) if page_match else None
        
        # Matches "document [name]", "of [name]", or "from [name]"
        doc_match = re.search(r"(?:document|of|from)\s+([\w\-]+)", query.lower())
        
        if doc_match:
            partial_doc_name = doc_match.group(1).strip()
            # 1. Resolve true extension from Database
            true_filename = await resolve_document_filename(partial_doc_name)
            
            if true_filename:
                logger.info(f"Resolved partial name '{partial_doc_name}' to true filename: '{true_filename}'")
                ext = true_filename.split('.')[-1].lower()
                
                # 2. Strategy Logic Tree based on Format
                
                # BRANCH A: Monolithic Data (Spreadsheets & Images)
                if ext in ['csv', 'xlsx', 'png', 'jpeg', 'jpg']:
                    logger.info(f"Format-Aware Rule: '{ext}' is monolithic. Forcing page_number = 1.")
                    results = await search_by_page_number(1, document_name=true_filename)
                    intent_msg = f"Extracted entire visual/tabular data structure from '{true_filename}'."
                    return {"query": query, "interpreted_intent": intent_msg, "results": results}
                    
                # BRANCH B.1: Paginated Data (Text/Docs) WITH Page Parameter
                elif ext in ['pdf', 'doc', 'docx', 'txt'] and page_number is not None:
                    logger.info(f"Format-Aware Rule: Strict pagination applied to '{true_filename}', Page {page_number}.")
                    results = await search_by_page_number(page_number, document_name=true_filename)
                    intent_msg = f"Fetched strictly page {page_number} from '{true_filename}'."
                    return {"query": query, "interpreted_intent": intent_msg, "results": results}
                    
                # BRANCH B.2: Paginated Data WITHOUT Page Parameter
                elif ext in ['pdf', 'doc', 'docx', 'txt'] and page_number is None:
                    logger.warning(f"Format-Aware Rule Triggered: General text query against multi-page {ext}. Falling back to standard inverted Search.")

        # Fallback: Default text keyword search (If B.2 or missing document context)
        logger.info(f"Executing standard GIN inverted keyword vector search for: '{query}' across all bounds.")
        results = await search_database(query)
        logger.info(f"Retrieved {len(results)} results via standard vector search.")
        return {"query": query, "results": results}

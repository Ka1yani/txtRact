import re
from typing import Dict, Any
from database import search_database, search_by_page_number

class SearchService:
    """
    Service responsible for executing search queries and intelligent intent parsing.
    Follows the Single Responsibility Principle (SRP).
    """
    
    @staticmethod
    def execute_search(query: str) -> Dict[str, Any]:
        """
        Detects user intent (e.g. specific page vs standard text search) 
        and routes it to the appropriate database functionality.
        """
        # Intelligently detect if the user asked for a specific page using Regex
        page_match = re.search(r"page\s+(\d+)", query.lower())
        doc_match = re.search(r"document\s+([\w\-\.]+)", query.lower())
        
        if page_match:
            # Intent: Specific page query
            page_number = int(page_match.group(1))
            doc_name = None
            
            if doc_match:
                doc_name = doc_match.group(1).strip()
                # Ensure we handle some potential trailing dots/spaces
                if doc_name.endswith('.'):
                    doc_name = doc_name[:-1]
            
            results = search_by_page_number(page_number, document_name=doc_name)
            
            intent_msg = f"Fetch entire content of page {page_number}"
            if doc_name:
                intent_msg += f" strictly from document '{doc_name}'"
                
            return {
                "query": query, 
                "interpreted_intent": intent_msg, 
                "results": results
            }
            
        # Fallback: Default text keyword search
        results = search_database(query)
        return {"query": query, "results": results}

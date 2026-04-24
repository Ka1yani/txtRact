import pytest
from services.search_service import SearchService
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_search_service_intent_parsing():
    search_service = SearchService()
    
    # Mocking search_by_page_number
    with patch('services.search_service.search_by_page_number', new_callable=AsyncMock) as mock_page_search:
        mock_page_search.return_value = [{"document_name": "test.pdf", "page_number": 5, "page_text": "Content"}]
        
        # Test direct page intent
        response = await search_service.execute_search("give me page 5 of report.pdf")
        
        assert "interpreted_intent" in response
        assert "page 5" in response["interpreted_intent"]
        assert "report.pdf" in response["interpreted_intent"]
        mock_page_search.assert_called_with(5, document_name="report.pdf")

@pytest.mark.asyncio
async def test_search_service_keyword_fallback():
    search_service = SearchService()
    
    # Mocking search_database
    with patch('services.search_service.search_database', new_callable=AsyncMock) as mock_db_search:
        mock_db_search.return_value = [{"document_name": "manual.pdf", "page_number": 1, "page_text": "Installation guide"}]
        
        # Test keyword search
        response = await search_service.execute_search("installation guide")
        
        assert "interpreted_intent" not in response
        assert response["query"] == "installation guide"
        mock_db_search.assert_called_with("installation guide")

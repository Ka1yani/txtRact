import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database import init_db, Document, DocumentPage, search_database, search_by_page_number, insert_page, AsyncSessionLocal, async_engine
from sqlalchemy import select, text

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db_schema():
    await init_db()
    yield
    await async_engine.dispose()

@pytest.mark.asyncio
async def test_insert_and_retrieve_document():
    # Use the synchronous insert_page for testing
    test_metadata = {"author": "Test Author", "creationDate": "2024-01-01"}
    insert_page("test_doc.pdf", test_metadata, 1, "This is the content of page one.")
    
    # Verify via async session
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Document).filter(Document.filename == "test_doc.pdf"))
        doc = result.scalar_one_or_none()
        assert doc is not None
        assert doc.author == "Test Author"
        
        result_pages = await session.execute(select(DocumentPage).filter(DocumentPage.document_id == doc.id))
        pages = result_pages.scalars().all()
        assert len(pages) >= 1

@pytest.mark.asyncio
async def test_full_text_search():
    test_metadata = {"author": "Search Tester"}
    insert_page("search_doc.pdf", test_metadata, 1, "The quick brown fox jumps over the lazy dog.")
    
    # Wait a tiny bit for the computed column if needed (though it should be instant)
    await asyncio.sleep(0.1)
    
    results = await search_database("fox")
    assert len(results) > 0
    assert "fox" in results[0]["page_text"]

@pytest.mark.asyncio
async def test_exact_page_search():
    test_metadata = {"author": "Page Tester"}
    insert_page("report_v1.pdf", test_metadata, 3, "Confidential Financial Data for Page 3.")
    
    results = await search_by_page_number(3, document_name="report_v1.pdf")
    assert len(results) == 1
    assert "Confidential" in results[0]["page_text"]

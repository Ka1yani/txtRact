import asyncio
from database import insert_page, get_all_documents, sync_engine, Document
from sqlalchemy import text

def test_insert():
    try:
        # Check current columns in table manually
        with sync_engine.connect() as conn:
            res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'core_documents'"))
            print("Current DB Columns:", [r[0] for r in res])
            
        print("Testing page insert...")
        insert_page("test_diagnostic.pdf", {"file_size_bytes": 1024, "author": "Bot"}, 1, "Testing DB")
        print("Page inserted perfectly!")
        
        with sync_engine.connect() as conn:
            conn.execute(text("DELETE FROM core_documents WHERE filename = 'test_diagnostic.pdf'"))
            conn.commit()
    except Exception as e:
        print(f"Insert crash: {e}")

if __name__ == "__main__":
    test_insert()

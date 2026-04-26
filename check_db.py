import asyncio
from database import async_engine, Document
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

async def check():
    async with async_engine.begin() as conn:
        try:
            res = await conn.execute(text("SELECT count(*) FROM core_documents;"))
            print(f"Table exists! Documents count: {res.fetchone()[0]}")
        except Exception as e:
            print(f"Error: {e}")
            
    print("Trying to create tables...")
    try:
        from database import init_db
        await init_db()
        print("Created successfully.")
    except Exception as e:
        print(f"Create error: {e}")
        
    async with async_engine.begin() as conn:
        try:
            res = await conn.execute(text("SELECT count(*) FROM core_documents;"))
            print(f"Table exists now! Documents count: {res.fetchone()[0]}")
        except Exception as e:
            print(f"Error finally: {e}")

if __name__ == "__main__":
    asyncio.run(check())

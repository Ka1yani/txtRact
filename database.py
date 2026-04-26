import os
import asyncio
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Index, Computed
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy import text
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

SYNC_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Sync Engine used strictly for synchronous processes (like background PyMuPDF extraction)
sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Async Engine used exclusively for Lightning Fast FastAPI Retrieval execution
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class Document(Base):
    __tablename__ = 'core_documents'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False, unique=True)
    author = Column(String, nullable=True)
    creation_date = Column(String, nullable=True)
    total_pages = Column(Integer, default=0)
    file_size_bytes = Column(Integer, default=0)
    upload_status = Column(String, default="completed")
    raw_metadata = Column(JSONB, nullable=True)
    
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")

class DocumentPage(Base):
    __tablename__ = 'core_document_pages'
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('core_documents.id', ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    page_content = Column(Text, nullable=False)
    search_vector = Column(TSVECTOR, Computed("to_tsvector('english', page_content)", persisted=True))
    
    document = relationship("Document", back_populates="pages")

# Explicit GIN Index definition via SQLAlchemy indexing structures
Index('idx_core_doc_pages_search', DocumentPage.search_vector, postgresql_using='gin')

async def init_db():
    """Syncs new Object-Relational Models securely without destroying persistence."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ------------- Legacy Wrappers adapted to New Strict Normalised Schema -------------

def insert_page(document_name: str, metadata: dict, page_number: int, page_text: str):
    """Synchronous strict DB insertion using Document and DocumentPage mapping."""
    logger.debug(f"Attempting to insert Database record for '{document_name}', Page {page_number}")
    with SyncSessionLocal() as session:
        doc = session.query(Document).filter(Document.filename == document_name).first()
        if not doc:
            author = metadata.get('author', 'Unknown')
            creation_date = metadata.get('creationDate', 'Unknown')
            doc = Document(
                filename=document_name,
                author=author,
                creation_date=creation_date,
                file_size_bytes=metadata.get('file_size_bytes', 0),
                raw_metadata=metadata,
                total_pages=0
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)
            logger.info(f"Created new Database Document Head for '{document_name}'")
            
        if page_number > doc.total_pages:
            doc.total_pages = page_number
            session.commit()
            
        page = DocumentPage(
            document_id=doc.id,
            page_number=page_number,
            page_content=page_text
        )
        session.add(page)
        session.commit()
        logger.debug(f"Page {page_number} for '{document_name}' successfully committed to DB.")

async def resolve_document_filename(partial_name: str) -> str:
    """Queries DB to resolve a partial filename to its exact filename (with extension)."""
    async with AsyncSessionLocal() as session:
        sql = "SELECT filename FROM core_documents WHERE filename ILIKE :partial LIMIT 1;"
        result = await session.execute(text(sql), {"partial": f"%{partial_name}%"})
        row = result.fetchone()
        return row[0] if row else None

async def get_all_documents():
    """Retrieves all registered documents from the DB for cataloging."""
    async with AsyncSessionLocal() as session:
        sql = "SELECT filename, creation_date, file_size_bytes, total_pages FROM core_documents ORDER BY id DESC;"
        result = await session.execute(text(sql))
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

async def search_database(query: str):
    """Asynchronous Fast Full-Text SQL GIN Search"""
    async with AsyncSessionLocal() as session:
        sql = """
            SELECT dp.id, d.filename as document_name, d.author, d.creation_date, d.raw_metadata as metadata, dp.page_number, dp.page_content as page_text,
                   ts_rank(dp.search_vector, websearch_to_tsquery('english', :query)) AS rank
            FROM core_document_pages dp
            JOIN core_documents d ON dp.document_id = d.id
            WHERE dp.search_vector @@ websearch_to_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT 5;
        """
        result = await session.execute(text(sql), {"query": query})
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

async def search_by_page_number(page_number: int, document_name: str = None):
    """Deterministic exact-matched intent query running rigid JOIN queries."""
    async with AsyncSessionLocal() as session:
        if document_name:
            sql = """
                SELECT dp.id, d.filename as document_name, d.author, d.creation_date, d.raw_metadata as metadata, dp.page_number, dp.page_content as page_text,
                       1.0 AS rank
                FROM core_document_pages dp
                JOIN core_documents d ON dp.document_id = d.id
                WHERE dp.page_number = :page_number AND d.filename ILIKE :filename
                ORDER BY d.filename
            """
            result = await session.execute(text(sql), {"page_number": page_number, "filename": f"%{document_name}%"})
        else:
            sql = """
                SELECT dp.id, d.filename as document_name, d.author, d.creation_date, d.raw_metadata as metadata, dp.page_number, dp.page_content as page_text,
                       1.0 AS rank
                FROM core_document_pages dp
                JOIN core_documents d ON dp.document_id = d.id
                WHERE dp.page_number = :page_number
                ORDER BY d.filename
            """
            result = await session.execute(text(sql), {"page_number": page_number})
            
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

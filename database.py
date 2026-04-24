import os
import psycopg2
import psycopg2.extras
import json
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "postgres")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # Create the table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS document_pages (
            id SERIAL PRIMARY KEY,
            document_name TEXT NOT NULL,
            metadata JSONB,
            page_number INTEGER NOT NULL,
            page_text TEXT NOT NULL
        )
    """)
    # Create an index for faster full-text search
    cur.execute("""
        CREATE INDEX IF NOT EXISTS document_pages_text_idx 
        ON document_pages 
        USING GIN (to_tsvector('english', page_text));
    """)
    conn.commit()
    cur.close()
    conn.close()

def insert_page(document_name: str, metadata: dict, page_number: int, page_text: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO document_pages (document_name, metadata, page_number, page_text)
        VALUES (%s, %s, %s, %s)
    """, (document_name, json.dumps(metadata), page_number, page_text))
    conn.commit()
    cur.close()
    conn.close()

def search_database(query: str):
    conn = get_connection()
    # Using DictCursor to have dict-like results
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # We use websearch_to_tsquery which is a bit more forgiving for plain language searches
    sql = """
        SELECT id, document_name, metadata, page_number, page_text,
               ts_rank(to_tsvector('english', page_text), websearch_to_tsquery('english', %s)) AS rank
        FROM document_pages
        WHERE to_tsvector('english', page_text) @@ websearch_to_tsquery('english', %s)
        ORDER BY rank DESC
        LIMIT 5;
    """
    cur.execute(sql, (query, query))
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return [dict(row) for row in results]

def search_by_page_number(page_number: int, document_name: str = None):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    if document_name:
        sql = """
            SELECT id, document_name, metadata, page_number, page_text,
                   1.0 AS rank
            FROM document_pages
            WHERE page_number = %s AND document_name = %s
            ORDER BY document_name
        """
        cur.execute(sql, (page_number, document_name))
    else:
        sql = """
            SELECT id, document_name, metadata, page_number, page_text,
                   1.0 AS rank
            FROM document_pages
            WHERE page_number = %s
            ORDER BY document_name
        """
        cur.execute(sql, (page_number,))
    
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return [dict(row) for row in results]

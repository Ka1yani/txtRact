import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
import re
from database import init_db, search_database, search_by_page_number
from extractor import process_pdf

app = FastAPI(title="Document Text Extractor API")

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.on_event("startup")
def startup_event():
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing DB: {e}")

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    # Save the file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Process the PDF and insert into DB
        process_pdf(temp_file_path, file.filename)
    except Exception as e:
        # Ensure cleanup on failure
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
        
    # Clean up after successful processing
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
        
    return {"status": "success", "message": f"{file.filename} processed and indexed successfully."}

@app.get("/search")
async def search(q: str):
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
        
    try:
        # Intelligently detect if the user asked for a specific page using Regex
        page_match = re.search(r"page\s+(\d+)", q.lower())
        doc_match = re.search(r"document\s+([\w\-\.]+)", q.lower())
        
        if page_match:
            # They are asking for a specific page (e.g. "page 13")
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
                "query": q, 
                "interpreted_intent": intent_msg, 
                "results": results
            }
        # Default text keyword search
        results = search_database(q)
        return {"query": q, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

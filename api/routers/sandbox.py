import fitz
import random
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(tags=["sandbox"])

@router.post("/analyze_blocks")
async def analyze_pdf_blocks(file: UploadFile = File(...)):
    """
    In-memory Sandbox Endpoint.
    Opens a PDF stream, selects a random page, and extracts bounding coordinates dynamically
    to visualize the PyMuPDF processing logic for the frontend visualizer.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        # Read file directly into an in-memory byte stream
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        num_pages = len(doc)
        if num_pages == 0:
            raise HTTPException(status_code=400, detail="PDF is empty.")
            
        # 1. Pick a random page logic as requested
        random_page_idx = random.randint(0, num_pages - 1)
        page = doc[random_page_idx]
        
        # 2. Extract Raw PyMuPDF Blocks
        raw_blocks = page.get_text("blocks")
        
        # We cap text at 80 characters to prevent massive blocks polluting the UI sandbox
        parsed_raw_blocks = []
        for b in raw_blocks:
            text = b[4].strip()
            # If text has content and is block_type == 0 (Text, not image)
            if text and len(b) > 6 and b[6] == 0:
                # Replace newline characters physically to keep sandbox UI one-liners clear
                cleaned_text = text.replace('\n', ' ')
                parsed_raw_blocks.append({
                    "x0": round(b[0], 1),
                    "y0": round(b[1], 1),
                    "text": cleaned_text[:80] + "..." if len(cleaned_text) > 80 else cleaned_text,
                })
                
        # 3. Apply the Spatial Sorting Lambda mimicking our real extractor.py logic
        sorted_blocks = sorted(parsed_raw_blocks, key=lambda b: (b["y0"], b["x0"]))
        
        doc.close()
        
        return {
            "status": "success",
            "page_number": random_page_idx + 1,
            "total_pages": num_pages,
            "raw_blocks": parsed_raw_blocks,
            "sorted_blocks": sorted_blocks
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sandbox Error: {str(e)}")

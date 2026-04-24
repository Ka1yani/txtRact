# txtRact Data Ingestion Pipeline

This document explains the complete lifecycle of a PDF file uploaded to the txtRact application, charting its journey from the Streamlit UI to the PostgreSQL database.

---

## High-Level Overview

1. **User Uploads File:** The user selects a PDF in the Streamlit frontend.
2. **Asynchronous Dispatch:** The FastAPI backend receives the file, saves it temporarily, and hands it off to an independent background thread so the user isn't forced to wait (No HTTP Timeouts).
3. **High-Fidelity Extraction:** A worker process reads the PDF using PyMuPDF, preserving the physical layout (blocks, paragraphs) and reading order.
4. **Normalized Database Storage:** The document's metadata is stored once in a relational SQL table. Each page's text is then stored in a linked table, where the PostgreSQL database automatically calculates a high-speed Search Vector (`TSVECTOR`) index for future retrieval.
5. **Cleanup:** The temporary file is securely deleted to save server storage.

---

## Detailed Step-by-Step Breakdown

### Step 1: The Client Request
- **Location:** `frontend.py`
- When you click "Upload & Index", Streamlit encodes the PDF file as a multipart form-data payload and sends an HTTP POST request to the backend `http://127.0.0.1:8000/upload`.
- While waiting, Streamlit triggers a loop that pings the `GET /status/{task_id}` background tracker endpoint every 2 seconds to update the UI progress bar.

### Step 2: The API Router
- **Location:** `api/routers/documents.py -> @router.post("/upload")`
- The endpoint relies on **Dependency Injection** to summon the `DocumentService` and FastAPI's native `BackgroundTasks` module.
- It validates that the file has a `.pdf` extension. 
- It passes the file object off to the service layer and returns a `status: accepted` response with the generated `task_id` practically instantly.

### Step 3: Temporary Storage & Task Dispatching
- **Location:** `services/document_service.py -> DocumentService.process_and_store_upload()`
- A unique `UUID` is generated for the `task_id`.
- The file is saved synchronously to the server's disk using a buffered `shutil.copyfileobj` command. This chunking method prevents massive files from blowing up the server's RAM.
- The `task_id` status is recorded as `"queued"` in the `task_status_store` (an in-memory dictionary).
- The `process_document_bg` function is injected into the FastAPI Background Thread pool.

### Step 4: The Background Worker
- **Location:** `services/worker.py -> process_document_bg()`
- Operating on a secondary thread (meaning it won't block other users from searching or using the app), the worker updates the task queue to `"processing"`.
- It executes the core engine: `process_pdf()`.
- **Failure Resilience**: The entire processing block is wrapped in a `try/except`. If the PDF is corrupted, the task updates to `"failed: {error}"` instead of crashing the server.

### Step 5: High-Fidelity Text Parsing (PyMuPDF Mechanics)
- **Location:** `extractor.py -> process_pdf()`
- The application uses `PyMuPDF (fitz)` to open the saved temporary file.
- **Deep Dive: How PyMuPDF Extracts Graphic Data**:
  - A PDF is not a continuous stream of text like a text file; it is a programmatic canvas. Words, sentences, and letters are "painted" at specific `(x, y)` coordinates, often completely out of logical reading order.
  - When we call `page.get_text("blocks")`, PyMuPDF parses the raw PDF byte-stream and mathematically reconstructs the document's graphical layout. 
  - Instead of returning a jumbled text string, it groups visually connected text together and returns a list of "Block" tuples structured as: `(x0, y0, x1, y1, "text_content", block_number, block_type)`.
    - `(x0, y0)` to `(x1, y1)`: The exact Bounding Box area of the paragraph on the page.
    - `block_type`: An integer distinguishing readable text (`0`) from underlying images (`1`).
- **Algorithmic Execution**:
  - **Spatial Sorting**: Because a PDF might draw the footer first and the header last, our code re-sorts these extracted blocks by their bounding box coordinates. We use a function sorting by `y` (vertical position), then `x` (horizontal position). This guarantees the system indexes the text left-to-right, top-to-bottom—exactly as human eyes read it.
  - **Structural Assembly**: The script isolates the pure string content from these sorted text blocks. It then joins them using *double newlines* (`\n\n`). This forces the unstructured text to artificially inherit logical paragraph separation, headings, and a clean reading flow before being pushed to the database.

### Step 6: Normalized SQL Transaction
- **Location:** `database.py -> insert_page()`
- Processing utilizes the synchronous `SessionLocal()` engine to ensure stable sequential writing.
- **Document Creation (Parent Table)**: The database attempts to fetch an existing `core_documents` row matching the `filename`. If one doesn't exist, it creates a new normalized parent record with the `author` and `raw_metadata`. This prevents data duplication.
- **Page Creation (Child Table)**: The script creates a new `core_document_pages` row linked to the parent via a Foreign Key `document_id`.

### Step 7: Hardware-Level Indexing (PostgreSQL)
- **Location:** Database Server Engine (`GIN Functional Index`)
- When the `core_document_pages` row is saved, PostgreSQL looks at the `page_content`.
- The schema defines `search_vector` as a `Computed TSVECTOR` column. 
- *Instead of Python doing the heavy lifting*, the Postgres C++ Engine natively strips the language of stop-words and converts the extracted string into a highly optimized search hash (`to_tsvector('english', page_content)`). This is why keyword searches are lightning-fast.

### Step 8: Cleanup and Completion
- **Location:** `services/worker.py -> process_document_bg()`
- The worker executes `os.remove(file_path)` to delete the temporary PDF off the host server disk.
- The `task_status_store` is updated to `"completed"`.
- On the next 2-second ping, the Streamlit frontend realizes the task is done, renders green balloons, and maxes out the progress bar!

# Phase 2 Enhancement Report: Asynchronous High-Fidelity Extraction

## Executive Summary
Phase 2 has successfully decoupled the document extraction process from the HTTP request cycle. By introducing a background task worker architecture, the application now supports large-scale PDF processing without risking API timeouts or freezing the user interface. Additionally, the extraction quality has been upgraded to preserve document structural integrity.

## Current State vs. Previous State

| Feature | Previous State (Phase 1) | Enhanced State (Phase 2) |
| :--- | :--- | :--- |
| **Processing Strategy** | **Synchronous**: API blocks until the entire PDF is parsed. | **Asynchronous**: API dispatches a "Task" to a background worker and returns immediately. |
| **System Resilience** | High risk of HTTP Timeouts for large PDFs. | Immune to HTTP Timeouts; processing happens in an isolated Celery instance. |
| **Extraction Quality** | Basic string extraction (loss of paragraph/block context). | **High-Fidelity Block Extraction**: Preserves logical paragraphs and reading order. |
| **Task Management** | No way to track document processing status. | Introduced `/status/{task_id}` endpoint to monitor extraction progress. |

## Technical Impact

### 1. High-Fidelity Block Parsing
We shifted the core extraction logic in `extractor.py` to use PyMuPDF's block-based extraction:
- **Spatial Awareness:** Blocks are now sorted by their $(y, x)$ coordinates, ensuring the text is read exactly as a human would, regardless of the internal PDF structure.
- **Structural Integrity:** Metadata and text are joined with double-newlines between blocks, preserving the logical separation of paragraphs and sections in the database.

### 2. Celery & Redis Background Architecture
The extraction logic is now a standalone Celery task.
- **Improved UX:** The application now follows the "Accepted" pattern (HTTP 202). Users get an immediate response with a `task_id`, allowing the frontend (Phase 3) to show progress bars.
- **Concurrency:** Multiple documents can be extracted simultaneously by scaling the number of Celery workers without impacting the performance of the search API.

### 3. Graceful Cleanup
Temporary files are now deleted *inside* the background worker immediately after successful processing, ensuring the server disk remains clean even when handling large volumes of data.

## Running the Background System
To enable the background processing, a Celery worker must be running alongside the FastAPI app. 

**Standard Execution Command:**
```bash
celery -A services.worker.celery_app worker --loglevel=info -P solo
```
*(Note: `-P solo` is recommended for standard Windows environments)*.

## Next Steps
In **Phase 3**, we will upgrade the Streamlit frontend to utilize the new `task_id` for real-time progress tracking and implement a high-fidelity document viewer.

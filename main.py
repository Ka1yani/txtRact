from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from database import init_db
from api.routers import documents, search, sandbox

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager.
    Replaces deprecated @app.on_event("startup").
    Handles graceful startup and shutdown processes.
    """
    # System Startup
    try:
        await init_db()
        print("Database Schema initialized via Async ORM.")
    except Exception as e:
        print(f"Error initializing DB: {e}")
        
    yield
    
    # System Shutdown
    print("Application shutdown sequence initiated.")

# Initialize API App
app = FastAPI(
    title="Document Text Extractor API",
    description="A modern, scalable Document API built adhering to SOLID principles.",
    version="1.1.0",
    lifespan=lifespan
)

# Connect Feature Routers (Modularity via FastAPI Routers)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(sandbox.router)

@app.get("/", include_in_schema=False)
async def root():
    """Redirects the root URL to the interactive API documentation."""
    return RedirectResponse(url="/docs")

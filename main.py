"""
Local Print Bridge - FastAPI Application
=========================================
A lightweight SSR application that bridges Dynamics 365 (D365) and local USB printers.

Flow:
1. D365 POSTs JSON data (ZPL commands) to /api/print-jobs
2. Server saves data to SQLite and returns a URL
3. D365 opens that URL in the user's browser
4. Server renders an HTML page with the data pre-filled
5. The HTML page connects to a LOCAL WebSocket script (ws://localhost:8765)
   running on the user's PC to trigger the actual printing
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# =============================================================================
# Database Configuration
# =============================================================================

# SQLite database path - stored in /app/data for Docker volume persistence
DATABASE_URL = "sqlite:///./data/printjobs.db"

# Create engine with check_same_thread=False for FastAPI's async nature
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite with threads
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# =============================================================================
# SQLAlchemy Models
# =============================================================================

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class PrintJob(Base):
    """
    PrintJob model - stores print job data in SQLite.
    
    Attributes:
        id: UUID string, primary key
        data_json: JSON string containing the print data (ZPL commands, etc.)
        created_at: Timestamp when the job was created
    """
    __tablename__ = "print_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables on startup
Base.metadata.create_all(bind=engine)


# =============================================================================
# Pydantic Schemas
# =============================================================================

class PrintJobCreate(BaseModel):
    """
    Schema for creating a new print job.
    Accepts any JSON data - the structure is flexible to support various print formats.
    """
    data: list[Dict[str, Any]]  # Array of ZPL data objects


class PrintJobResponse(BaseModel):
    """Response schema after creating a print job."""
    job_id: str
    view_url: str


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Local Print Bridge",
    description="Bridge between D365 and local USB printers",
    version="1.0.0"
)

# Configure Jinja2 templates directory
templates = Jinja2Templates(directory="templates")


# =============================================================================
# Dependency: Database Session
# =============================================================================

def get_db():
    """
    Dependency that provides a database session.
    Ensures proper cleanup after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - shows a simple landing page."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/api/print-jobs", response_model=PrintJobResponse)
async def create_print_job(request: Request, job_data: PrintJobCreate):
    """
    Create a new print job.
    
    Accepts JSON data containing ZPL commands, saves to SQLite,
    and returns a URL for viewing/printing.
    
    Args:
        request: FastAPI request object (for building URLs)
        job_data: Print job data containing ZPL commands
    
    Returns:
        job_id: UUID of the created job
        view_url: Full URL to view and print the job
    
    Example Request:
        POST /api/print-jobs
        {
            "data": [
                {"zpl": "^XA\\n^FO50,50\\n^BQN,2,5\\n^FDQA,HELLO WORLD^FS\\n^XZ\\n"}
            ]
        }
    """
    db = SessionLocal()
    try:
        # Generate unique ID for this print job
        job_id = str(uuid.uuid4())
        
        # Serialize the data to JSON string for storage
        data_json = json.dumps(job_data.model_dump())
        
        # Create and save the print job
        print_job = PrintJob(id=job_id, data_json=data_json)
        db.add(print_job)
        db.commit()
        
        # Build the view URL using the request's base URL
        # This ensures the URL works regardless of proxy/container setup
        base_url = str(request.base_url).rstrip("/")
        view_url = f"{base_url}/view?id={job_id}"
        
        return PrintJobResponse(job_id=job_id, view_url=view_url)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create print job: {str(e)}")
    finally:
        db.close()


@app.get("/view", response_class=HTMLResponse)
async def view_print_job(request: Request, id: str):
    """
    View a print job by ID.
    
    Fetches the print job from the database and renders an HTML page
    with the data pre-filled. The page includes JavaScript to connect
    to the local WebSocket bridge for printing.
    
    Args:
        request: FastAPI request object
        id: UUID of the print job to view
    
    Returns:
        HTML page with print job data and WebSocket integration
    """
    db = SessionLocal()
    try:
        # Query the print job by ID
        print_job = db.query(PrintJob).filter(PrintJob.id == id).first()
        
        if not print_job:
            # Render error page if job not found
            return templates.TemplateResponse(
                request=request,
                name="print_page.html",
                context={
                    "error": True,
                    "error_message": f"Print job with ID '{id}' not found.",
                    "job_id": None,
                    "data": None
                }
            )
        
        # Parse the stored JSON data
        job_data = json.loads(print_job.data_json)
        
        # Render the print page with data
        return templates.TemplateResponse(
            request=request,
            name="print_page.html",
            context={
                "error": False,
                "job_id": print_job.id,
                "data": job_data.get("data", []),
                "created_at": print_job.created_at.isoformat() if print_job.created_at else None,
                # Pass raw JSON for JavaScript consumption
                "data_json": json.dumps(job_data)
            }
        )
    
    finally:
        db.close()


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker/container monitoring."""
    return {"status": "healthy", "service": "local-print-bridge"}


# =============================================================================
# Startup Event
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Runs on application startup.
    Ensures the data directory exists for SQLite database.
    """
    import os
    os.makedirs("data", exist_ok=True)
    print("Local Print Bridge started successfully!")
    print("Database: ./data/printjobs.db")

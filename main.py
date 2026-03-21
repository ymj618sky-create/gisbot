"""
GIS Agent - Main Application Entry Point

FastAPI application for the GIS Agent system with nanobot architecture.
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.routes.agent_nanobot import router
from core.config import load_config

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting GIS Agent API...")
    print(f"   Workspace: {Path.cwd()}")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")

    # Load configuration if config.json exists
    config_path = Path("config.json")
    if config_path.exists():
        try:
            config = load_config()
            print(f"   Configuration loaded from {config_path}")
        except Exception as e:
            print(f"   Warning: Failed to load config: {e}")

    yield

    # Shutdown
    print("Shutting down GIS Agent API...")


# Create FastAPI application
app = FastAPI(
    title="GIS Agent API",
    description="AI-powered GIS data analysis agent with nanobot architecture",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "GIS Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/api/nanobot/chat",
            "stream": "/api/nanobot/stream/{channel}/{chat_id}",
            "tools": "/api/nanobot/tools",
            "skills": "/api/nanobot/skills",
            "sessions": "/api/nanobot/sessions"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
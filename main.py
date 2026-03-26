"""
GIS Agent - Main Application Entry Point

FastAPI application for the GIS Agent system.
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from api.routes.agent import router, reset_agent_loop
from api.routes.workspace import router as workspace_router
from api.routes.upload import router as upload_router
from core.config import load_config, reset_timeout_config

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

    # 预加载超时配置
    from core.config import get_timeout_config
    timeout_config = get_timeout_config()
    print(f"   Timeout config: {timeout_config}")

    yield

    # Shutdown
    print("Shutting down GIS Agent API...")
    # 重置单例，释放资源
    reset_agent_loop()
    reset_timeout_config()
    print("   Agent loop and config cleaned up")


# Create FastAPI application
app = FastAPI(
    title="GIS Agent API",
    description="AI-powered GIS data analysis agent",
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
app.include_router(workspace_router)
app.include_router(upload_router, prefix="/api", tags=["upload"])

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount uploads directory for accessing uploaded files
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Mount workspace root directory for accessing workspace files
workspace_dir = Path(__file__).parent / "workspace"
workspace_dir.mkdir(parents=True, exist_ok=True)
app.mount("/workspace", StaticFiles(directory=str(workspace_dir)), name="workspace")

# Root endpoint - serve chat interface
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with chat interface."""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return """
    <html>
        <head><title>GIS Agent API</title></head>
        <body>
            <h1>GIS Agent API</h1>
            <p>API is running. See <a href="/docs">API Documentation</a></p>
        </body>
    </html>
    """


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import ALLOWED_ORIGINS
from app.database import create_schema
from app.graph.builder import build_graph
from app.routers import graph as graph_router
from app.routers import chat as chat_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create schema and build graph."""
    logger.info("Starting O2C Graph System...")
    create_schema()
    build_graph()
    logger.info("System ready!")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="O2C Context Graph System",
    description="Graph-based data modeling and LLM-powered query interface for SAP Order-to-Cash data",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(graph_router.router)
app.include_router(chat_router.router)


@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "o2c-graph-system"}

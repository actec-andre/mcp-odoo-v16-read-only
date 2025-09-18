#!/usr/bin/env python
"""
Synchronous HTTP API server for n8n compatibility
Provides direct HTTP endpoints for MCP tools without SSE complexity
"""
import sys
import os
import logging
import datetime
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from odoo_mcp.odoo_client import get_odoo_client


def setup_logging():
    """Set up logging"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Pydantic models for API
class ToolExecuteRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any]

class ToolExecuteResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None

class ToolsListResponse(BaseModel):
    tools: List[Dict[str, Any]]


# Create FastAPI app
app = FastAPI(title="Odoo MCP HTTP API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Odoo client
odoo_client = None

@app.on_event("startup")
async def startup_event():
    global odoo_client
    logger = logging.getLogger(__name__)
    logger.info("=== ODOO HTTP API STARTING ===")

    try:
        odoo_client = get_odoo_client()
        logger.info("Odoo client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Odoo client: {e}")
        raise


@app.get("/")
async def root():
    return {"message": "Odoo MCP HTTP API", "version": "1.0.0"}


@app.get("/tools", response_model=ToolsListResponse)
async def list_tools():
    """List available MCP tools"""
    tools = [
        {
            "name": "execute_method",
            "description": "Execute a read-only method on an Odoo model",
            "schema": {
                "type": "object",
                "properties": {
                    "model": {"type": "string"},
                    "method": {"type": "string"},
                    "args": {"type": "array"},
                    "kwargs": {"type": "object"}
                },
                "required": ["model", "method"],
                "additionalProperties": False
            }
        }
    ]
    return ToolsListResponse(tools=tools)


@app.post("/tools/execute", response_model=ToolExecuteResponse)
async def execute_tool(request: ToolExecuteRequest):
    """Execute an MCP tool synchronously"""
    global odoo_client

    if not odoo_client:
        raise HTTPException(status_code=500, detail="Odoo client not initialized")

    try:
        if request.tool == "execute_method":
            args = request.arguments
            model = args.get("model")
            method = args.get("method")
            method_args = args.get("args", [])
            method_kwargs = args.get("kwargs", {})

            if not model or not method:
                raise HTTPException(status_code=400, detail="model and method are required")

            # Execute the Odoo method
            result = odoo_client.execute_method(model, method, *method_args, **method_kwargs)

            return ToolExecuteResponse(success=True, result=result)

        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Tool execution error: {e}", exc_info=True)
        return ToolExecuteResponse(success=False, error=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global odoo_client
    return {
        "status": "healthy",
        "odoo_connected": odoo_client is not None,
        "timestamp": datetime.datetime.now().isoformat()
    }


def main():
    """Main entry point"""
    logger = setup_logging()

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8081"))

    logger.info(f"Starting Odoo HTTP API server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
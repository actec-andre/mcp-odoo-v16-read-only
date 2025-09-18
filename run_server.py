#!/usr/bin/env python
"""
Standalone script to run the Odoo MCP server 
Uses the same approach as in the official MCP SDK examples
"""
import sys
import os
import asyncio
import anyio
import logging
import datetime

from mcp.server.stdio import stdio_server
from mcp.server.lowlevel import Server
import mcp.types as types

from odoo_mcp.server import mcp  # FastMCP instance from our code


def setup_logging():
    """Set up logging to both console and file"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"mcp_server_{timestamp}.log")
    
    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Format for both handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def main() -> int:
    """
    Run the MCP server based on the official examples
    """
    logger = setup_logging()
    
    try:
        logger.info("=== ODOO MCP SERVER STARTING ===")
        logger.info(f"Python version: {sys.version}")
        logger.info("Environment variables:")
        for key, value in os.environ.items():
            if key.startswith("ODOO_"):
                if key == "ODOO_PASSWORD":
                    logger.info(f"  {key}: ***hidden***")
                else:
                    logger.info(f"  {key}: {value}")

        # Import mcp at the top level to avoid UnboundLocalError
        from odoo_mcp.server import mcp

        logger.info(f"MCP object type: {type(mcp)}")

        # Check if we should run in HTTP mode (for DigitalOcean) or stdio mode
        if os.environ.get("DEPLOYMENT_MODE") == "http":
            # HTTP mode for DigitalOcean App Platform
            logger.info("Starting Odoo MCP server with HTTP transport...")
            import uvicorn
            from fastapi import FastAPI

            # Create FastAPI app and mount both MCP apps
            app = FastAPI(title="Odoo MCP Server")

            # Mount SSE app for real-time communication
            sse_app = mcp.sse_app()
            app.mount("/mcp/sse", sse_app)

            # Mount HTTP app for n8n JSON-RPC compatibility
            http_app = mcp.http_app()
            app.mount("/mcp", http_app)

            # Run uvicorn server
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=int(os.environ.get("PORT", "8080")),
                log_level="info"
            )
        else:
            # Stdio mode for local development
            async def arun():
                logger.info("Starting Odoo MCP server with stdio transport...")
                async with stdio_server() as streams:
                    logger.info("Stdio server initialized, running MCP server...")
                    await mcp._mcp_server.run(
                        streams[0], streams[1], mcp._mcp_server.create_initialization_options()
                    )

            # Run server
            anyio.run(arun)
        logger.info("MCP server stopped normally")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
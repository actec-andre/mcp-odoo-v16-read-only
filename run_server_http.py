#!/usr/bin/env python
"""
Standalone script to run the Odoo MCP server with HTTP streamable transport
Enhanced version supporting both STDIO and HTTP streamable for n8n integration
"""
import sys
import os
import logging
import datetime
import uvicorn

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


def main():
    """Main entry point with flexible transport support"""
    logger = setup_logging()

    logger.info("=== ODOO MCP SERVER (HTTP) STARTING ===")
    logger.info(f"Python version: {sys.version}")

    # Determine transport mode
    transport = os.environ.get("TRANSPORT", "http").lower()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))

    logger.info(f"Transport mode: {transport}")
    logger.info(f"MCP object type: {type(mcp)}")

    try:
        if transport == "http" or transport == "sse":
            # HTTP streamable mode for n8n integration (better compatibility)
            logger.info(f"Starting MCP server with HTTP streamable transport on {host}:{port}...")

            # Get SSE app from FastMCP (works for HTTP streamable too)
            http_app = mcp.sse_app()

            # Run with uvicorn
            uvicorn.run(
                http_app,
                host=host,
                port=port,
                log_level="info"
            )
        else:
            # STDIO mode fallback
            logger.info("Starting MCP server with STDIO transport...")
            mcp.run()

        logger.info("MCP server stopped normally")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
"""Model Context Protocol discovery surface.

This router exposes a lightweight MCP-style capability map so MCP clients can
introspect Vectory features and route to the existing REST endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("", summary="MCP server metadata")
async def mcp_metadata():
    """Return MCP discovery metadata for Vectory."""
    return {
        "name": "vectory",
        "title": "Vectory MCP Surface",
        "version": __version__,
        "protocol_version": "2025-03-26",
        "description": (
            "Discovery surface for mapping MCP clients to Vectory's existing "
            "REST APIs for vector collections, retrieval, and ingestion."
        ),
        "endpoints": {
            "tools": "/api/mcp/tools",
            "resources": "/api/mcp/resources",
        },
    }


@router.get("/tools", summary="List MCP tools")
async def list_mcp_tools():
    """Return MCP tool definitions mapped to Vectory REST operations."""
    return {
        "tools": [
            {
                "name": "list_collections",
                "description": "List available vector collections.",
                "rest": {"method": "GET", "path": "/api/collections"},
            },
            {
                "name": "create_collection",
                "description": "Create a vector collection.",
                "rest": {"method": "POST", "path": "/api/collections"},
            },
            {
                "name": "insert_vectors",
                "description": "Insert vectors into a collection.",
                "rest": {"method": "POST", "path": "/api/collections/{collection_id}/vectors"},
            },
            {
                "name": "query_collection",
                "description": "Run semantic similarity search against a collection.",
                "rest": {"method": "POST", "path": "/api/collections/{collection_id}/query"},
            },
            {
                "name": "upload_for_ingestion",
                "description": "Upload a file to begin ingestion.",
                "rest": {"method": "POST", "path": "/api/ingestion/upload"},
            },
            {
                "name": "get_system_metrics",
                "description": "Fetch Vectory health and usage metrics.",
                "rest": {"method": "GET", "path": "/api/system/metrics"},
            },
        ]
    }


@router.get("/resources", summary="List MCP resources")
async def list_mcp_resources():
    """Return available resource handles for MCP clients."""
    return {
        "resources": [
            {
                "uri": "vectory://system/info",
                "name": "System information",
                "description": "Server capabilities and limits.",
                "rest": {"method": "GET", "path": "/api/system/system/info"},
            },
            {
                "uri": "vectory://system/models",
                "name": "Embedding models",
                "description": "Supported embedding model configurations.",
                "rest": {"method": "GET", "path": "/api/system/models"},
            },
            {
                "uri": "vectory://collections",
                "name": "Collections",
                "description": "Collection catalog and metadata.",
                "rest": {"method": "GET", "path": "/api/collections"},
            },
        ]
    }

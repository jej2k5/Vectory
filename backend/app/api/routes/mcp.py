"""Model Context Protocol surface built on top of Vectory's REST API routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app import __version__

router = APIRouter(prefix="/mcp", tags=["mcp"])


@dataclass(frozen=True)
class MCPMapping:
    """Mapping between an MCP primitive and an underlying REST endpoint."""

    name: str
    description: str
    method: str
    path: str


TOOLS: dict[str, MCPMapping] = {
    "list_collections": MCPMapping(
        name="list_collections",
        description="List available vector collections.",
        method="GET",
        path="/api/collections",
    ),
    "create_collection": MCPMapping(
        name="create_collection",
        description="Create a vector collection.",
        method="POST",
        path="/api/collections",
    ),
    "insert_vectors": MCPMapping(
        name="insert_vectors",
        description="Insert vectors into a collection.",
        method="POST",
        path="/api/collections/{collection_id}/vectors",
    ),
    "query_collection": MCPMapping(
        name="query_collection",
        description="Run semantic similarity search against a collection.",
        method="POST",
        path="/api/collections/{collection_id}/query",
    ),
    "upload_for_ingestion": MCPMapping(
        name="upload_for_ingestion",
        description="Upload a file to begin ingestion.",
        method="POST",
        path="/api/ingestion/upload",
    ),
    "get_system_metrics": MCPMapping(
        name="get_system_metrics",
        description="Fetch Vectory health and usage metrics.",
        method="GET",
        path="/api/system/metrics",
    ),
    "update_vector": MCPMapping(
        name="update_vector",
        description="Update a vector's text content, metadata, or embedding.",
        method="PATCH",
        path="/api/collections/{collection_id}/vectors/{vector_id}",
    ),
    "delete_vector": MCPMapping(
        name="delete_vector",
        description="Delete a single vector from a collection.",
        method="DELETE",
        path="/api/collections/{collection_id}/vectors/{vector_id}",
    ),
}

RESOURCES: dict[str, MCPMapping] = {
    "system_info": MCPMapping(
        name="system_info",
        description="Server capabilities and limits.",
        method="GET",
        path="/api/system/system/info",
    ),
    "system_models": MCPMapping(
        name="system_models",
        description="Supported embedding model configurations.",
        method="GET",
        path="/api/system/models",
    ),
    "collections": MCPMapping(
        name="collections",
        description="Collection catalog and metadata.",
        method="GET",
        path="/api/collections",
    ),
}


class ToolInvokeRequest(BaseModel):
    """Tool invocation payload."""

    args: dict[str, Any] = Field(default_factory=dict)


async def _dispatch_to_api(
    request: Request,
    mapping: MCPMapping,
    *,
    args: dict[str, Any] | None = None,
) -> Any:
    """Dispatch an MCP operation to the mapped REST API endpoint."""
    args = args or {}

    try:
        path = mapping.path.format(**args)
    except KeyError as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Missing required path parameter: {exc.args[0]}. "
                f"Expected by path template '{mapping.path}'."
            ),
        ) from exc

    remaining_args = {k: v for k, v in args.items() if f"{{{k}}}" not in mapping.path}
    query_params = remaining_args if mapping.method == "GET" else None
    json_body = remaining_args if mapping.method in {"POST", "PATCH", "PUT"} else None

    passthrough_headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() in {"authorization", "x-api-key"}
    }

    transport = httpx.ASGITransport(app=request.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://vectory.local") as client:
        response = await client.request(
            method=mapping.method,
            url=path,
            headers=passthrough_headers,
            params=query_params,
            json=json_body,
        )

    if response.status_code >= 400:
        detail: Any
        try:
            detail = response.json()
        except ValueError:
            detail = {"message": response.text}
        raise HTTPException(status_code=response.status_code, detail=detail)

    if not response.content:
        return {"status": response.status_code}
    return response.json()


@router.get("", summary="MCP server metadata")
async def mcp_metadata():
    """Return MCP discovery metadata for Vectory."""
    return {
        "name": "vectory",
        "title": "Vectory MCP Surface",
        "version": __version__,
        "protocol_version": "2025-03-26",
        "description": "MCP surface layered on top of existing Vectory REST API routes.",
        "endpoints": {
            "tools": "/api/mcp/tools",
            "invoke_tool": "/api/mcp/tools/{tool_name}/invoke",
            "resources": "/api/mcp/resources",
            "read_resource": "/api/mcp/resources/{resource_name}",
        },
    }


@router.get("/tools", summary="List MCP tools")
async def list_mcp_tools():
    """Return MCP tool definitions mapped to Vectory REST operations."""
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "rest": {"method": tool.method, "path": tool.path},
            }
            for tool in TOOLS.values()
        ]
    }


@router.post("/tools/{tool_name}/invoke", summary="Invoke an MCP tool")
async def invoke_mcp_tool(tool_name: str, payload: ToolInvokeRequest, request: Request):
    """Execute an MCP tool by forwarding to the corresponding REST endpoint."""
    mapping = TOOLS.get(tool_name)
    if mapping is None:
        raise HTTPException(status_code=404, detail=f"Unknown MCP tool '{tool_name}'.")

    result = await _dispatch_to_api(request, mapping, args=payload.args)
    return {"tool": tool_name, "result": result}


@router.get("/resources", summary="List MCP resources")
async def list_mcp_resources():
    """Return available resource handles for MCP clients."""
    return {
        "resources": [
            {
                "name": resource.name,
                "uri": f"vectory://{name}",
                "description": resource.description,
                "rest": {"method": resource.method, "path": resource.path},
            }
            for name, resource in RESOURCES.items()
        ]
    }


@router.get("/resources/{resource_name}", summary="Read an MCP resource")
async def read_mcp_resource(resource_name: str, request: Request):
    """Read an MCP resource by forwarding to the corresponding REST endpoint."""
    mapping = RESOURCES.get(resource_name)
    if mapping is None:
        raise HTTPException(status_code=404, detail=f"Unknown MCP resource '{resource_name}'.")

    result = await _dispatch_to_api(request, mapping)
    return {"resource": resource_name, "result": result}

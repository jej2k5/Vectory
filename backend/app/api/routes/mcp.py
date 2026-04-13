"""Model Context Protocol surface built on top of Vectory's REST API routes."""

from __future__ import annotations

import json
import re
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
    "list_vectors": MCPMapping(
        name="list_vectors",
        description="List vectors in a collection with pagination.",
        method="GET",
        path="/api/collections/{collection_id}/vectors",
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


class JsonRpcRequest(BaseModel):
    """Incoming JSON-RPC 2.0 request envelope."""

    jsonrpc: str = Field("2.0", pattern=r"^2\.0$")
    id: int | str | None = None
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


def _jsonrpc_success(request_id: int | str | None, result: Any) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 success response dict."""
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _jsonrpc_error(
    request_id: int | str | None,
    code: int,
    message: str,
    data: Any = None,
) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 error response dict."""
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


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


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 method handlers (reuse existing TOOLS/RESOURCES dicts)
# ---------------------------------------------------------------------------


def _extract_path_params(path: str) -> list[str]:
    """Extract parameter names from a URL template like ``/api/collections/{collection_id}``."""
    return re.findall(r"\{(\w+)\}", path)


def _handle_initialize() -> dict[str, Any]:
    """Handle ``initialize`` – return server capabilities and metadata."""
    return {
        "protocolVersion": "2025-03-26",
        "serverInfo": {
            "name": "vectory",
            "version": __version__,
        },
        "capabilities": {
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False},
        },
    }


def _handle_tools_list() -> dict[str, Any]:
    """Handle ``tools/list`` – return tool definitions in MCP JSON-RPC format."""
    tools = []
    for tool in TOOLS.values():
        path_params = _extract_path_params(tool.path)
        properties = {
            p: {"type": "string", "description": f"Path parameter: {p}"}
            for p in path_params
        }
        tools.append(
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                },
            }
        )
    return {"tools": tools}


async def _handle_tools_call(params: dict[str, Any], request: Request) -> dict[str, Any]:
    """Handle ``tools/call`` – invoke a tool by name."""
    tool_name = params.get("name")
    if not tool_name:
        raise HTTPException(status_code=400, detail="Missing 'name' in params for tools/call")

    mapping = TOOLS.get(tool_name)
    if mapping is None:
        raise HTTPException(status_code=404, detail=f"Unknown MCP tool '{tool_name}'.")

    arguments = params.get("arguments", {})
    result = await _dispatch_to_api(request, mapping, args=arguments)
    return {
        "content": [
            {"type": "text", "text": json.dumps(result, default=str)},
        ],
    }


def _handle_resources_list() -> dict[str, Any]:
    """Handle ``resources/list`` – return resource definitions."""
    return {
        "resources": [
            {
                "uri": f"vectory://{name}",
                "name": resource.name,
                "description": resource.description,
                "mimeType": "application/json",
            }
            for name, resource in RESOURCES.items()
        ]
    }


async def _handle_resources_read(params: dict[str, Any], request: Request) -> dict[str, Any]:
    """Handle ``resources/read`` – read a resource by URI."""
    uri = params.get("uri", "")
    resource_name = uri.removeprefix("vectory://") if uri.startswith("vectory://") else uri

    mapping = RESOURCES.get(resource_name)
    if mapping is None:
        raise HTTPException(status_code=404, detail=f"Unknown MCP resource '{resource_name}'.")

    result = await _dispatch_to_api(request, mapping)
    return {
        "contents": [
            {
                "uri": f"vectory://{resource_name}",
                "mimeType": "application/json",
                "text": json.dumps(result, default=str),
            },
        ],
    }


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


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


@router.post("", summary="JSON-RPC 2.0 MCP endpoint")
async def jsonrpc_handler(body: JsonRpcRequest, request: Request):
    """Handle MCP JSON-RPC 2.0 requests.

    Dispatches the ``method`` field to existing MCP functionality and returns
    a well-formed JSON-RPC 2.0 response.
    """
    method = body.method
    params = body.params
    request_id = body.id

    try:
        if method == "initialize":
            result = _handle_initialize()
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = _handle_tools_list()
        elif method == "tools/call":
            result = await _handle_tools_call(params, request)
        elif method == "resources/list":
            result = _handle_resources_list()
        elif method == "resources/read":
            result = await _handle_resources_read(params, request)
        else:
            return _jsonrpc_error(request_id, -32601, f"Method not found: {method}")
    except HTTPException as exc:
        return _jsonrpc_error(
            request_id,
            -32000,
            str(exc.detail) if isinstance(exc.detail, str) else "Server error",
            data=exc.detail if not isinstance(exc.detail, str) else None,
        )
    except Exception as exc:
        return _jsonrpc_error(request_id, -32603, f"Internal error: {exc}")

    return _jsonrpc_success(request_id, result)


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

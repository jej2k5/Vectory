"""Tests for MCP routing surface."""

from __future__ import annotations

import json

from httpx import ASGITransport, AsyncClient

from app.main import app

# ---------------------------------------------------------------------------
# Existing REST-style tests
# ---------------------------------------------------------------------------


async def test_mcp_tools_list_exposes_rest_mappings():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/mcp/tools")

    assert response.status_code == 200
    body = response.json()
    assert "tools" in body
    assert any(tool["name"] == "list_collections" for tool in body["tools"])


async def test_mcp_tools_list_includes_vector_mutation_tools():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/mcp/tools")

    assert response.status_code == 200
    body = response.json()
    tool_names = [tool["name"] for tool in body["tools"]]
    assert "update_vector" in tool_names
    assert "delete_vector" in tool_names
    assert len(body["tools"]) == 9


async def test_mcp_tool_invoke_is_layered_over_rest_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/mcp/tools/list_collections/invoke",
            json={"args": {"skip": 0, "limit": 1}},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["tool"] == "list_collections"
    assert "result" in body
    assert "items" in body["result"]


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 tests
# ---------------------------------------------------------------------------


async def test_jsonrpc_initialize_returns_capabilities():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "init-1",
                "method": "initialize",
                "params": {},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["jsonrpc"] == "2.0"
    assert body["id"] == "init-1"
    result = body["result"]
    assert "protocolVersion" in result
    assert result["serverInfo"]["name"] == "vectory"
    assert "tools" in result["capabilities"]
    assert "resources" in result["capabilities"]


async def test_jsonrpc_ping_returns_empty_result():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "ping-1",
                "method": "ping",
                "params": {},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["result"] == {}
    assert body["id"] == "ping-1"


async def test_jsonrpc_tools_list_returns_all_tools():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "tl-1",
                "method": "tools/list",
                "params": {},
            },
        )

    assert response.status_code == 200
    body = response.json()
    tools = body["result"]["tools"]
    assert len(tools) == 9
    tool_names = [t["name"] for t in tools]
    assert "list_collections" in tool_names
    assert "query_collection" in tool_names
    for tool in tools:
        assert "inputSchema" in tool


async def test_jsonrpc_tools_call_dispatches_to_rest():
    """Verify tools/call routes through to the underlying REST endpoint.

    When a database is available the result contains collection data.
    Without a database the handler still returns a well-formed JSON-RPC
    response (either a result with content or a server-error).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "tc-1",
                "method": "tools/call",
                "params": {
                    "name": "list_collections",
                    "arguments": {"skip": 0, "limit": 1},
                },
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "tc-1"
    assert body["jsonrpc"] == "2.0"
    # With a real database the result contains content; without one we get
    # a JSON-RPC error because the upstream REST endpoint fails.
    if "result" in body:
        content = body["result"]["content"]
        assert len(content) >= 1
        assert content[0]["type"] == "text"
        inner = json.loads(content[0]["text"])
        assert "items" in inner
    else:
        assert "error" in body
        assert body["error"]["code"] in (-32000, -32603)


async def test_jsonrpc_tools_call_unknown_tool_returns_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "tc-err-1",
                "method": "tools/call",
                "params": {"name": "nonexistent_tool", "arguments": {}},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == -32000


async def test_jsonrpc_tools_call_missing_name_returns_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "tc-noname-1",
                "method": "tools/call",
                "params": {"arguments": {}},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == -32000


async def test_jsonrpc_resources_list_returns_all_resources():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "rl-1",
                "method": "resources/list",
                "params": {},
            },
        )

    assert response.status_code == 200
    body = response.json()
    resources = body["result"]["resources"]
    assert len(resources) == 3
    assert all("uri" in r for r in resources)
    assert all("mimeType" in r for r in resources)


async def test_jsonrpc_resources_read_dispatches_to_rest():
    """Verify resources/read routes through to the underlying REST endpoint.

    Without a live database the upstream call may fail, in which case the
    handler returns a well-formed JSON-RPC error.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "rr-1",
                "method": "resources/read",
                "params": {"uri": "vectory://collections"},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["jsonrpc"] == "2.0"
    assert body["id"] == "rr-1"
    if "result" in body:
        contents = body["result"]["contents"]
        assert len(contents) >= 1
        assert contents[0]["uri"] == "vectory://collections"
        assert contents[0]["mimeType"] == "application/json"
    else:
        assert "error" in body
        assert body["error"]["code"] in (-32000, -32603)


async def test_jsonrpc_unknown_method_returns_method_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "unk-1",
                "method": "completions/complete",
                "params": {},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == -32601
    assert "Method not found" in body["error"]["message"]


async def test_jsonrpc_preserves_request_id():
    """The response id must exactly match the request id, per JSON-RPC 2.0 spec."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for req_id in ["route-discover-test-12345", 42, "abc"]:
            response = await client.post(
                "/api/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "method": "ping",
                    "params": {},
                },
            )
            body = response.json()
            assert body["id"] == req_id


async def test_existing_rest_endpoints_still_work():
    """Adding the POST handler must not break existing GET/REST endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp_meta = await client.get("/api/mcp")
        assert resp_meta.status_code == 200
        assert "name" in resp_meta.json()

        resp_tools = await client.get("/api/mcp/tools")
        assert resp_tools.status_code == 200
        assert "tools" in resp_tools.json()

        resp_res = await client.get("/api/mcp/resources")
        assert resp_res.status_code == 200
        assert "resources" in resp_res.json()


async def test_jsonrpc_works_at_root_mcp_path():
    """JSON-RPC endpoint should also be available at /mcp (without /api prefix)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "root-1",
                "method": "tools/list",
                "params": {},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["jsonrpc"] == "2.0"
    assert body["id"] == "root-1"
    tools = body["result"]["tools"]
    assert len(tools) == 9

"""Tests for MCP routing surface."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.main import app


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

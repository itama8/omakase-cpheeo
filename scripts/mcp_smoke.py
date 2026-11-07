"""Connect to a running server over MCP and exercise every tool.

Usage: uv run python scripts/mcp_smoke.py [http://127.0.0.1:8765/mcp]
"""

import asyncio
import json
import sys

from mcp import Client


async def main(url: str) -> int:
    async with Client(url) as client:
        tools = await client.list_tools()
        names = sorted(t.name for t in tools.tools)
        print("tools:", names)
        assert names == ["fetch", "get_clause", "get_toc", "list_manuals", "search"], names

        def payload(result):
            if result.structured_content:
                return result.structured_content.get("result", result.structured_content)
            return json.loads(result.content[0].text)

        found = payload(await client.call_tool("search", {"query": "minimum slope for 200 mm sewer", "limit": 3}))
        top = found["results"][0]
        print("search top:", top["id"], "|", top["citation"])
        assert top["id"] == "SEW-2013-A:T3.13"
        assert found["attribution"]["cited_by"] == "Omakase"

        clause = payload(await client.call_tool("get_clause", {"id": "SEW-2013-A:3.6"}))
        print("clause:", clause["citation"], "| tables:", [t["id"] for t in clause.get("tables", [])])
        assert clause["text"].startswith("Estimate of flow")

        toc = payload(await client.call_tool("get_toc", {"manual": "SEW-2013-A", "chapter": "3", "max_depth": 1}))
        print("toc entries:", len(toc["entries"]), toc["entries"][:2])

        doc = payload(await client.call_tool("fetch", {"id": "SEW-2013-A:T3.2"}))
        print("fetch:", doc["title"], "| url:", doc["url"])
        assert "2.50" in doc["text"] and doc["metadata"]["manual"] == "SEW-2013-A"

        bad = await client.call_tool("get_clause", {"id": "SEW-2013-A:99.9"})
        print("unknown id is_error:", bad.is_error)
        assert bad.is_error
    print("MCP smoke: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765/mcp")))

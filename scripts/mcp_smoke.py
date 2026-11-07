"""Connect to a running server over MCP and exercise every tool.

Usage: uv run python scripts/mcp_smoke.py [http://127.0.0.1:8765/mcp]
"""

import asyncio
import json
import sys

import urllib.request

from mcp import Client

BRAND_SUFFIX = " · via Omakase CPHEEO"


async def main(url: str) -> int:
    base = url.rsplit("/mcp", 1)[0]
    req = urllib.request.Request(f"{base}/icon.png", headers={"User-Agent": "omakase-cpheeo-smoke"})
    with await asyncio.to_thread(urllib.request.urlopen, req) as icon:
        body, ctype = icon.read(), icon.headers.get("content-type")
        print("icon:", icon.status, ctype, len(body), "bytes")
        assert icon.status == 200 and ctype == "image/png"

    async with Client(url) as client:
        info = client.server_info
        print("server:", info.name, "|", info.title, "| icons:", [i.src[:60] for i in info.icons or []])
        assert info.name == "Omakase CPHEEO" and info.title.startswith("Omakase CPHEEO") and info.icons
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
        assert top["citation"].endswith(BRAND_SUFFIX) and top["citation_plain"] + BRAND_SUFFIX == top["citation"]
        assert top["source_name"] == "Omakase CPHEEO"

        clause = payload(await client.call_tool("get_clause", {"id": "SEW-2013-A:3.6"}))
        print("clause:", clause["citation"], "| tables:", [t["id"] for t in clause.get("tables", [])])
        assert clause["text"].startswith("Estimate of flow")

        toc = payload(await client.call_tool("get_toc", {"manual": "SEW-2013-A", "chapter": "3", "max_depth": 1}))
        print("toc entries:", len(toc["entries"]), toc["entries"][:2])

        doc = payload(await client.call_tool("fetch", {"id": "SEW-2013-A:T3.2"}))
        print("fetch:", doc["title"], "| url:", doc["url"])
        assert "2.50" in doc["text"] and doc["metadata"]["manual"] == "SEW-2013-A"
        assert doc["title"].startswith("Omakase CPHEEO · ") and "Source: Omakase CPHEEO search" in doc["text"]
        assert doc["metadata"]["citation"].endswith(BRAND_SUFFIX) and doc["metadata"]["source_name"] == "Omakase CPHEEO"

        manuals = {m["id"] for m in payload(await client.call_tool("list_manuals", {}))["manuals"]}
        print("manuals:", sorted(manuals))
        assert {"SEW-2013-A", "WS-2024-A", "WS-2024-B", "WS-2024-C"} <= manuals, manuals

        water = payload(await client.call_tool("search", {"query": "economical size of pumping main", "limit": 3}))
        print("water search top:", water["results"][0]["id"])
        assert water["results"][0]["id"] == "WS-2024-A:AN6.1"
        t22 = payload(await client.call_tool("get_clause", {"id": "WS-2024-A:T2.2"}))
        print("text table:", t22["citation"], "| source:", t22.get("source"))
        assert t22.get("source") == "table text in the manual PDF" and "Service reservoirs" in t22["table_markdown"]

        bad = await client.call_tool("get_clause", {"id": "SEW-2013-A:99.9"})
        print("unknown id is_error:", bad.is_error)
        assert bad.is_error
    print("MCP smoke: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765/mcp")))

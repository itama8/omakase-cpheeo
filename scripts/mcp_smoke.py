"""Connect to a running server over MCP and exercise every tool.

Usage: uv run python scripts/mcp_smoke.py [http://127.0.0.1:8765/mcp]
"""

import asyncio
import base64
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
        ids = [r["id"] for r in found["results"]]
        print("search results:", ids)
        assert "SEW-2013-A:T3.13" in ids
        top = next(r for r in found["results"] if r["id"] == "SEW-2013-A:T3.13")
        assert found["attribution"]["cited_by"] == "Omakase"
        assert top["citation"].endswith(BRAND_SUFFIX) and top["citation_plain"] + BRAND_SUFFIX == top["citation"]
        assert top["source_name"] == "Omakase CPHEEO"

        for query in ("minimum sanitary sewer diameter", "minimum pipe diameter for gravity sewer"):
            diameter = payload(await client.call_tool("search", {"query": query, "limit": 3}))
            assert diameter["results"][0]["id"] == "SEW-2013-A:3.14", diameter["results"]
        print("diameter ranking: direct criterion first for sanitary and gravity sewer queries")

        clause = payload(await client.call_tool("get_clause", {"id": "SEW-2013-A:3.6"}))
        print("clause:", clause["citation"], "| tables:", [t["id"] for t in clause.get("tables", [])])
        assert clause["text"].startswith("Estimate of flow")

        toc = payload(await client.call_tool("get_toc", {"manual": "SEW-2013-A", "chapter": "3", "max_depth": 1}))
        print("toc entries:", len(toc["entries"]), toc["entries"][:2])

        fetched = await client.call_tool("fetch", {"id": "SEW-2013-A:T3.2"})
        doc = payload(fetched)
        print("fetch:", doc["title"], "| url:", doc["url"])
        assert "2.50" in doc["text"] and doc["metadata"]["manual"] == "SEW-2013-A"
        pictures = [c for c in fetched.content if c.type == "image"]
        assert pictures and pictures[0].mime_type == "image/png"
        assert base64.b64decode(pictures[0].data).startswith(b"\x89PNG")
        table_result = await client.call_tool("get_clause", {"id": "SEW-2013-A:T3.2"})
        table = payload(table_result)
        assert table['transcription_status']=='verified' and table['verified_transcriptions'][0]['state']=='verified'
        assert ['Above 20,001 to 50,000','2.50'] in table['verified_transcriptions'][0]['rows']
        assert table["images"]
        assert "OCR" not in table.get("source", "")
        assert any(c.type == "image" for c in table_result.content)
        ref = table["images"][0]
        assert ref["pdf_page"] and ref["page_label"]
        image_path = f"/img/{table['id']}/{ref['seq']}.png"
        with await asyncio.to_thread(urllib.request.urlopen, base + image_path) as image:
            assert image.headers.get("content-type") == "image/png"
            assert image.read() == base64.b64decode(pictures[0].data)
        with await asyncio.to_thread(urllib.request.urlopen, base + "/c/" + table["id"]) as page:
            assert image_path in page.read().decode()
        figure_result = await client.call_tool("get_clause", {"id": "SEW-2013-A:F3.4"})
        figure = payload(figure_result)
        assert figure["images"] and any(c.type == "image" for c in figure_result.content)
        print("source images: table + figure MCP blocks, HTTP bytes and clause page verified")
        assert doc["title"].startswith("Omakase CPHEEO · ") and "Source: Omakase CPHEEO search" in doc["text"]
        assert doc["metadata"]["citation"].endswith(BRAND_SUFFIX) and doc["metadata"]["source_name"] == "Omakase CPHEEO"

        equation_result = await client.call_tool('get_clause', {'id':'SEW-2013-A:E5.30'})
        equation = payload(equation_result)
        assert equation['transcription_status']=='verified' and '/ 9.17' in equation['verified_text']
        assert '1.024' in equation['verified_transcriptions'][0]['latex']
        assert any(b.type=='image' for b in equation_result.content)
        eq_doc = payload(await client.call_tool('fetch',{'id':equation['id']}))
        assert '9.17' in eq_doc['text'] and eq_doc['metadata']['verified_transcriptions']
        parent = payload(await client.call_tool('get_clause', {'id':'SEW-2013-A:5.8.1.7.5.3'}))
        assert any(e['id']==equation['id'] for e in parent['equations'])
        with await asyncio.to_thread(urllib.request.urlopen, base+'/c/'+equation['id']) as page:
            assert '9.17' in page.read().decode()
        unclear = payload(await client.call_tool('get_clause', {'id':'SEW-2013-A:Ep180-1'}))
        assert unclear['transcription_status']=='unclear' and 'verified_text' not in unclear and unclear['images']
        node_table = payload(await client.call_tool('get_clause', {'id':'WS-2024-A:AN6.6-T5'}))
        assert any(r['pdf_page']==1158 for r in node_table['images'])
        assert node_table['verified_transcriptions'][0]['rows'][-1]==['14','node14','18.7','18','21','3','3']
        assert '1071 to 1072' in node_table['citation']
        print('verified content: numerical row, Equation 5.30 math/images/parent/HTML, unclear fallback and water continuation')

        manuals = {m["id"] for m in payload(await client.call_tool("list_manuals", {}))["manuals"]}
        print("manuals:", sorted(manuals))
        assert {"SEW-2013-A", "WS-2024-A", "WS-2024-B", "WS-2024-C"} <= manuals, manuals

        water = payload(await client.call_tool("search", {"query": "economical size of pumping main", "limit": 3}))
        water_ids = [r["id"] for r in water["results"]]
        print("water search results:", water_ids)
        assert "WS-2024-A:AN6.1" in water_ids
        t22 = payload(await client.call_tool("get_clause", {"id": "WS-2024-A:T2.2"}))
        print("text table:", t22["citation"], "| source:", t22.get("source"))
        assert t22.get("source") == "table text in the manual PDF" and "Service reservoirs" in t22["table_markdown"]

        appendix_search = payload(await client.call_tool("search", {"query": "Appendix A 3.2 B", "limit": 3}))
        assert appendix_search["results"][0]["id"] == "SEW-2013-A:A3.2B"
        appendix_result = await client.call_tool("get_clause", {"id": "SEW-2013-A:A7.1"})
        appendix = payload(appendix_result)
        assert appendix["images"][0]["page_label"] == "A - 144"
        assert appendix["images"][0]["pdf_page"] == 915
        assert any(c.type == "image" for c in appendix_result.content)
        appendix_table = payload(await client.call_tool("search", {"query": "Table A 7.3- 1", "limit": 3}))
        assert appendix_table["results"][0]["id"] == "SEW-2013-A:TA7.3-1"
        with await asyncio.to_thread(urllib.request.urlopen, base + "/v1/clause/SEW-2013-A:A.1.1") as legacy:
            old_clause = json.load(legacy)
            assert old_clause["id"] == "SEW-2013-A:A1.1" and len(old_clause["images"]) == 15
        print("appendices: lettered sheet lookup, scanned source image, table reference and legacy link verified")

        bad = await client.call_tool("get_clause", {"id": "SEW-2013-A:99.9"})
        print("unknown id is_error:", bad.is_error)
        assert bad.is_error
    print("MCP smoke: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765/mcp")))

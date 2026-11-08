"""One process serving the same Library over MCP (streamable HTTP at /mcp) and REST (/v1/*)."""

from __future__ import annotations

import base64
import html
import os
from functools import cache
from pathlib import Path
from urllib.parse import urlparse

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, Icon, ImageContent, TextContent
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from .service import SOURCE_NAME, Library, attribution, icon_url, public_url

ASSETS = Path(__file__).resolve().parents[2] / "assets"
ICON_SMALL = ASSETS / "omakase-icon-256.png"  # served at /icon.png
ICON_LARGE = ASSETS / "omakase-icon.png"  # 1024 px original
FAVICON = ASSETS / "favicon.ico"

INSTRUCTIONS = """\
Omakase CPHEEO search: the Government of India CPHEEO manuals, searchable with exact citations.
Corpus: Manual on Sewerage and Sewage Treatment Systems, Part A: Engineering (2013); Manual on Water Supply and Treatment Systems, Parts A, B and C (2024). More manuals are being added; call list_manuals for the current set.

How to use:
- Call `search` with the engineer's question in plain words. Results are ranked units (sections, tables, figures) with a ready `citation` string.
- Call `fetch` (or `get_clause` for structured fields) with a result `id` to read the full clause or table before quoting a value.
- Link each citation to the result's `url`, which opens the clause on an Omakase page.
- When you state a value from the manual, quote it and give the `citation` exactly as returned. Do not cite a clause you did not retrieve.
- Many tables and all figures are pictures of the printed page. `get_clause` and `fetch` attach those pictures as images (and give an image `url`). Read values from the image and cite the `citation`; verified visual transcriptions are supplied where explicitly marked. These cover only their listed source regions. If a value is unclear, say so and ask the user to check the printed page.
- If the manuals do not cover the question, say so instead of answering from memory.
- Name the source as "Omakase CPHEEO": each `citation` already ends with "· via Omakase CPHEEO"; keep that suffix when you copy it.
- End answers that rely on these results with: "Sources via Omakase CPHEEO search."
"""


@cache
def _asset(path: Path) -> bytes:
    return path.read_bytes()


def server_icons() -> list[Icon]:
    """The Omakase icon: a public URL when the server has one, else an inline data: URI."""
    if url := icon_url():
        return [Icon(src=url, mime_type="image/png", sizes=["256x256"])]
    data = base64.b64encode(_asset(ICON_SMALL)).decode()
    return [Icon(src=f"data:image/png;base64,{data}", mime_type="image/png", sizes=["256x256"])]


def _with_images(lib: Library, payload: dict, clause: dict) -> CallToolResult:
    """The JSON payload plus the clause's page pictures as image content blocks."""
    import json

    content: list = [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=1))]
    for unit_id, ref, mime, data in lib.images_for(clause):
        content.append(TextContent(type="text", text=f"{unit_id}, image {ref['seq']}: printed page {ref['page_label'] or 'unknown'}, PDF page {ref['pdf_page']}:"))
        content.append(ImageContent(type="image", data=base64.b64encode(data).decode(), mime_type=mime))
    return CallToolResult(content=content, structured_content=payload)


def build_server(db: str | None = None) -> MCPServer:
    lib = Library(db)
    mcp = MCPServer(
        name=SOURCE_NAME,
        title=f"{SOURCE_NAME}: search and cite CPHEEO manuals",
        description="Omakase CPHEEO: search and cite the Government of India CPHEEO manuals with clause, table and page.",
        icons=server_icons(),
        instructions=INSTRUCTIONS,
        website_url=os.environ.get("OMAKASE_CPHEEO_BRAND_URL"),
        version="0.1.0",
    )

    @mcp.tool(title="Omakase CPHEEO: search manuals")
    def search(query: str, domain: str | None = None, manual: str | None = None, kind: str | None = None, limit: int = 8) -> dict:
        """Search the CPHEEO manuals and return citable sections and tables.

        query: the question or terms, e.g. "minimum slope for 200 mm sewer" or "Table 3.13".
        domain: optional filter: sewerage, water, stormwater, solid-waste.
        manual: optional manual id from list_manuals, e.g. SEW-2013-A or WS-2024-A.
        kind: optional unit kind: section, table, figure, appendix.
        limit: number of results, 1-25.
        """
        return lib.search(query, domain=domain, manual_id=manual, kind=kind, limit=limit)

    @mcp.tool(title="Omakase CPHEEO: read a clause or table")
    def get_clause(id: str, include_children: bool = False) -> CallToolResult:
        """Return section text, native PDF table rows, or source images for scanned tables and figures, by id (e.g. SEW-2013-A:3.6, SEW-2013-A:T3.2 or WS-2024-A:AN6.1).

        include_children: also return the numbered subsections of a section.
        """
        clause = lib.get_clause(id, include_children=include_children)
        return _with_images(lib, clause, clause)

    @mcp.tool(title="Omakase CPHEEO: fetch a clause")
    def fetch(id: str) -> CallToolResult:
        """Return one section or table as a document with id, title, text, url and metadata.

        id: a result id from search, e.g. SEW-2013-A:T3.13.
        """
        return _with_images(lib, lib.fetch(id), lib.get_clause(id))

    @mcp.tool(title="Omakase CPHEEO: list manuals")
    def list_manuals() -> dict:
        """List the manuals in the corpus with edition, part and how many sections and tables each has."""
        return lib.list_manuals()

    @mcp.tool(title="Omakase CPHEEO: table of contents")
    def get_toc(manual: str, chapter: str | None = None, max_depth: int = 2) -> dict:
        """Return a manual's chapters, sections and tables. chapter limits it to one chapter (e.g. "3")."""
        return lib.get_toc(manual, chapter=chapter, max_depth=max_depth)

    # ---- REST: the same operations for scripts and anything that is not an MCP client.

    def _error(e: Exception, status: int) -> JSONResponse:
        return JSONResponse({"error": str(e).strip("'\"")}, status_code=status)

    @mcp.custom_route("/icon.png", methods=["GET"])
    async def icon(_: Request) -> Response:
        return Response(_asset(ICON_SMALL), media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})

    @mcp.custom_route("/icon-1024.png", methods=["GET"])
    async def icon_large(_: Request) -> Response:
        return Response(_asset(ICON_LARGE), media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})

    @mcp.custom_route("/favicon.ico", methods=["GET"])
    async def favicon(_: Request) -> Response:
        return Response(_asset(FAVICON), media_type="image/x-icon", headers={"Cache-Control": "public, max-age=86400"})

    @mcp.custom_route("/img/{id:path}", methods=["GET"])
    async def unit_image(request: Request) -> Response:
        """/img/SEW-2013-A:T3.2/0.png: picture of the printed page for a unit."""
        unit_id, _, name = request.path_params["id"].rpartition("/")
        try:
            mime, data = lib.image(unit_id, int(name.split(".")[0]))
        except (KeyError, ValueError) as e:
            return _error(e, 404)
        return Response(data, media_type=mime, headers={"Cache-Control": "public, max-age=86400"})

    @mcp.custom_route("/health", methods=["GET"])
    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"ok": True, "manuals": list(lib.manuals)})

    @mcp.custom_route("/v1/search", methods=["GET"])
    async def rest_search(request: Request) -> JSONResponse:
        p = request.query_params
        if not p.get("q"):
            return _error(ValueError("missing q"), 400)
        try:
            limit = int(p.get("limit", 8))
        except ValueError:
            return _error(ValueError("limit must be an integer"), 400)
        return JSONResponse(lib.search(p["q"], domain=p.get("domain"), manual_id=p.get("manual"), kind=p.get("kind"), limit=limit))

    @mcp.custom_route("/v1/clause/{id:path}", methods=["GET"])
    async def rest_clause(request: Request) -> JSONResponse:
        try:
            return JSONResponse(lib.get_clause(request.path_params["id"], include_children=request.query_params.get("children") == "1"))
        except KeyError as e:
            return _error(e, 404)

    @mcp.custom_route("/c/{id:path}", methods=["GET"])
    async def clause_page(request: Request) -> HTMLResponse:
        try:
            c = lib.get_clause(request.path_params["id"])
        except KeyError as e:
            return HTMLResponse(_page("Not found", f"<p>{html.escape(str(e))}</p>"), status_code=404)
        return HTMLResponse(_page(c["citation_plain"], _clause_html(c)))

    @mcp.custom_route("/v1/manuals", methods=["GET"])
    async def rest_manuals(_: Request) -> JSONResponse:
        return JSONResponse(lib.list_manuals())

    @mcp.custom_route("/v1/toc/{manual}", methods=["GET"])
    async def rest_toc(request: Request) -> JSONResponse:
        try:
            return JSONResponse(lib.get_toc(request.path_params["manual"], chapter=request.query_params.get("chapter")))
        except KeyError as e:
            return _error(e, 404)

    return mcp


def _table_html(markdown: str) -> str:
    rows = [r for r in markdown.splitlines() if r.startswith("|") and not set(r) <= set("|-")]
    out = []
    for i, r in enumerate(rows):
        tag = "th" if i == 0 else "td"
        cells = "".join(f"<{tag}>{html.escape(c.strip())}</{tag}>" for c in r.strip("|").split("|"))
        out.append(f"<tr>{cells}</tr>")
    return f"<table>{''.join(out)}</table>"


def _clause_html(c: dict) -> str:
    import json

    parts = [f"<p class=cite>{html.escape(c['citation_plain'])}</p>"]
    if c.get("unverified_regions"):
        parts.append("<p class=warn>Unverified source region. " + html.escape(" ".join(c.get("transcription_notes",[]))) + "</p>")
    if c.get("verified_text"):
        parts.append("<pre style='white-space:pre-wrap'>" + html.escape(c["verified_text"]) + "</pre>")
        evidence = [{k:t[k] for k in ('id','source_sha256','regions','verification')} for t in c['verified_transcriptions']]
        parts.append("<p>" + html.escape(c['verification_scope']) + "</p><details><summary>Transcription source and visual checks</summary><pre style='white-space:pre-wrap'>" + html.escape(json.dumps(evidence,ensure_ascii=False,indent=2)) + "</pre></details>")
    if c.get("table_markdown"):
        parts.append(_table_html(c["table_markdown"]))
    parts += _images_html(c)
    for para in (c.get("text") or "").splitlines():
        parts.append(f"<p>{html.escape(para)}</p>")
    for t in c.get("tables", []):
        parts.append(f"<h2>{html.escape(t['citation'])}</h2>")
        parts.append(_clause_html(t))
    for e in c.get("equations", []):
        parts.append(_clause_html(e))
    return "\n".join(parts)


def _images_html(u: dict) -> list[str]:
    out = []
    for r in u.get("images", []):
        src = f"/img/{u['id']}/{r['seq']}.{'png' if r['mime'] == 'image/png' else 'jpg'}"
        page = f"Printed page {r['page_label']} (PDF page {r['pdf_page']})" if r['page_label'] else f"PDF page {r['pdf_page']}"
        alt = html.escape(f"{u['citation_plain']} ({page})")
        out.append(f"<figure><img src='{html.escape(src)}' alt='{alt}' width='{r['width']}' height='{r['height']}'><figcaption>{html.escape(page)}</figcaption></figure>")
    return out


def _page(title: str, body: str) -> str:
    a = attribution()
    brand = f"<a href='{html.escape(a['url'])}'>Omakase</a>" if a.get("url") else "Omakase"
    return f"""<!doctype html><html lang=en><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>{html.escape(title)} · Omakase CPHEEO</title>
<link rel=icon href="/favicon.ico" sizes="any"><link rel=icon type="image/png" href="/icon.png"><link rel=apple-touch-icon href="/icon.png">
<style>body{{font:16px/1.55 system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem;color:#222}}
.cite{{font-weight:600}}.warn{{background:#fff4d6;padding:.5rem .75rem;border-radius:4px}}
table{{border-collapse:collapse;margin:1rem 0}}td,th{{border:1px solid #bbb;padding:.3rem .6rem;text-align:left}}
footer{{margin-top:3rem;color:#666;font-size:.9rem}}
figure{{margin:1rem 0}}figure img{{max-width:100%;height:auto;border:1px solid #ddd}}figcaption{{color:#666;font-size:.85rem}}
header{{display:flex;align-items:center;gap:.6rem;margin-bottom:1.5rem;font-weight:700;font-size:1.15rem}}
header img{{width:36px;height:36px;border-radius:8px}}</style>
<body><header><img src="/icon.png" alt="" width=36 height=36><span>Omakase CPHEEO</span></header>{body}<footer>CPHEEO search by {brand}. {html.escape(a['note'])}</footer></body></html>"""


def _transport_security() -> TransportSecuritySettings:
    """Accept localhost plus the public host (tunnel or deployment) named in OMAKASE_CPHEEO_PUBLIC_URL."""
    hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    origins = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]
    # Hosted assistants that connect to remote MCP servers.
    origins += ["https://chatgpt.com", "https://chat.openai.com", "https://claude.ai"]
    if base := public_url():
        u = urlparse(base)
        hosts += [u.netloc, f"{u.hostname}:*"]
        origins.append(f"{u.scheme}://{u.netloc}")
    for extra in filter(None, os.environ.get("OMAKASE_CPHEEO_ALLOWED_ORIGINS", "").split(",")):
        origins.append(extra.strip())
    return TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=hosts, allowed_origins=origins)


def serve(host: str = "127.0.0.1", port: int = 8765, db: str | None = None) -> None:
    build_server(db).run(
        "streamable-http",
        host=host,
        port=port,
        stateless_http=True,
        json_response=True,
        transport_security=_transport_security(),
    )

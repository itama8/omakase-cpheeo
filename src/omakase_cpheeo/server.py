"""One process serving the same Library over MCP (streamable HTTP at /mcp) and REST (/v1/*)."""

from __future__ import annotations

import os

from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import JSONResponse

from .service import Library

INSTRUCTIONS = """\
Omakase CPHEEO search: the Government of India CPHEEO manuals, searchable with exact citations.
Corpus: Manual on Sewerage and Sewage Treatment Systems, Part A: Engineering (2013). More manuals are being added; call list_manuals for the current set.

How to use:
- Call `search` with the engineer's question in plain words. Results are ranked units (sections, tables, figures) with a ready `citation` string.
- Call `get_clause` with a result `id` to read the full clause or table before quoting a value.
- When you state a value from the manual, quote it and give the `citation` exactly as returned. Do not cite a clause you did not retrieve.
- Tables marked `needs_review` were read by OCR from an image. Say so when quoting them, and point the user to the printed page to confirm the number.
- If the manuals do not cover the question, say so instead of answering from memory.
- End answers that rely on these results with: "Sources via Omakase CPHEEO search."
"""


def build_server(db: str | None = None) -> MCPServer:
    lib = Library(db)
    mcp = MCPServer(
        name="omakase-cpheeo",
        title="Omakase CPHEEO search",
        description="Search and cite CPHEEO manuals (Government of India) with clause, table and page.",
        instructions=INSTRUCTIONS,
        website_url=os.environ.get("OMAKASE_CPHEEO_BRAND_URL"),
        version="0.1.0",
    )

    @mcp.tool(title="Search CPHEEO manuals")
    def search(query: str, domain: str | None = None, manual: str | None = None, kind: str | None = None, limit: int = 8) -> dict:
        """Search the CPHEEO manuals and return citable sections and tables.

        query: the question or terms, e.g. "minimum slope for 200 mm sewer" or "Table 3.13".
        domain: optional filter: sewerage, water, stormwater, solid-waste.
        manual: optional manual id from list_manuals, e.g. SEW-2013-A.
        kind: optional unit kind: section, table, figure, appendix.
        limit: number of results, 1-25.
        """
        return lib.search(query, domain=domain, manual_id=manual, kind=kind, limit=limit)

    @mcp.tool(title="Read a clause or table")
    def get_clause(id: str, include_children: bool = False) -> dict:
        """Return the full text of a section, or the rows of a table, by id (e.g. SEW-2013-A:3.6 or SEW-2013-A:T3.2).

        include_children: also return the numbered subsections of a section.
        """
        return lib.get_clause(id, include_children=include_children)

    @mcp.tool(title="List manuals")
    def list_manuals() -> dict:
        """List the manuals in the corpus with edition, part and how many sections and tables each has."""
        return lib.list_manuals()

    @mcp.tool(title="Table of contents")
    def get_toc(manual: str, chapter: str | None = None, max_depth: int = 2) -> dict:
        """Return a manual's chapters, sections and tables. chapter limits it to one chapter (e.g. "3")."""
        return lib.get_toc(manual, chapter=chapter, max_depth=max_depth)

    # ---- REST: the same operations for scripts and anything that is not an MCP client.

    def _error(e: Exception, status: int) -> JSONResponse:
        return JSONResponse({"error": str(e).strip("'\"")}, status_code=status)

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


def serve(host: str = "127.0.0.1", port: int = 8765, db: str | None = None) -> None:
    build_server(db).run("streamable-http", host=host, port=port, stateless_http=True, json_response=True)

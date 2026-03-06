"""Knowledge Base RAG MCP tools — ingest and search documents."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post, api_delete


# ── Search ──

async def handle_search_knowledge(arguments: dict) -> list[TextContent]:
    query = arguments.get("query")
    if not query:
        return [TextContent(type="text", text="Please provide a search query.")]

    payload = {"query": query, "limit": arguments.get("limit", 5)}
    if arguments.get("doc_type"):
        payload["doc_type"] = arguments["doc_type"]

    response = api_post("/knowledge/search", json=payload)
    response.raise_for_status()
    data = response.json()

    results = data.get("results", [])
    if not results:
        return [TextContent(type="text", text=f"No knowledge base results for: {query}")]

    text = f"Found {len(results)} results for: {query}\n\n"
    for i, r in enumerate(results, 1):
        text += f"**{i}. {r['document_title']}** ({r.get('doc_type', 'unknown')}) — {r['similarity']:.0%} match\n"
        text += f"   Source: {r.get('source', 'N/A')}\n"
        # Show first 300 chars of content
        content_preview = r['content'][:300]
        if len(r['content']) > 300:
            content_preview += "..."
        text += f"   {content_preview}\n\n"

    return [TextContent(type="text", text=text)]


# ── Ingest Text ──

async def handle_ingest_knowledge(arguments: dict) -> list[TextContent]:
    title = arguments.get("title")
    content = arguments.get("content")
    if not title or not content:
        return [TextContent(type="text", text="Please provide both title and content.")]

    payload = {
        "title": title,
        "content": content,
        "doc_type": arguments.get("doc_type", "plain_text"),
    }
    if arguments.get("source"):
        payload["source"] = arguments["source"]

    response = api_post("/knowledge/ingest/text", json=payload)
    response.raise_for_status()
    data = response.json()
    return [TextContent(type="text", text=data.get("message", "Document ingested."))]


# ── Ingest URL ──

async def handle_ingest_url(arguments: dict) -> list[TextContent]:
    url = arguments.get("url")
    if not url:
        return [TextContent(type="text", text="Please provide a URL.")]

    payload = {"url": url}
    if arguments.get("title"):
        payload["title"] = arguments["title"]

    response = api_post("/knowledge/ingest/url", json=payload)
    response.raise_for_status()
    data = response.json()
    return [TextContent(type="text", text=data.get("message", "Webpage ingested."))]


# ── List Documents ──

async def handle_list_knowledge_docs(arguments: dict) -> list[TextContent]:
    params = {}
    if arguments.get("doc_type"):
        params["doc_type"] = arguments["doc_type"]

    response = api_get("/knowledge/documents", params=params)
    response.raise_for_status()
    data = response.json()

    docs = data.get("documents", [])
    if not docs:
        return [TextContent(type="text", text="Knowledge base is empty. Use ingest tools to add documents.")]

    text = f"Knowledge Base — {len(docs)} documents:\n\n"
    for d in docs:
        text += f"  #{d['id']} {d['title']} [{d.get('doc_type', '?')}] — {d['chunk_count']} chunks\n"

    return [TextContent(type="text", text=text)]


# ── Get Document ──

async def handle_get_knowledge_doc(arguments: dict) -> list[TextContent]:
    doc_id = arguments.get("document_id")
    if not doc_id:
        return [TextContent(type="text", text="Please provide a document_id.")]

    response = api_get(f"/knowledge/documents/{doc_id}")
    response.raise_for_status()
    data = response.json()

    text = f"**{data['title']}** (#{data['id']})\n"
    text += f"Type: {data.get('doc_type', 'unknown')}\n"
    text += f"Source: {data.get('source', 'N/A')}\n"
    text += f"Chunks: {data.get('chunk_count', 0)}\n\n"
    # Show first 2000 chars
    content = data.get("content", "")
    if len(content) > 2000:
        text += content[:2000] + "\n\n... (truncated)"
    else:
        text += content

    return [TextContent(type="text", text=text)]


# ── Delete Document ──

async def handle_delete_knowledge_doc(arguments: dict) -> list[TextContent]:
    doc_id = arguments.get("document_id")
    if not doc_id:
        return [TextContent(type="text", text="Please provide a document_id.")]

    response = api_delete(f"/knowledge/documents/{doc_id}")
    response.raise_for_status()
    data = response.json()
    return [TextContent(type="text", text=data.get("message", f"Document {doc_id} deleted."))]


# ── Tool Registration ──

register_tool(Tool(
    name="search_knowledge_base",
    description="Search the knowledge base using semantic/AI search. Searches across all ingested documents — contracts, deal notes, market reports, PDFs, webpages. Voice: 'What do we know about 1031 exchanges?' or 'Find info about flood zone regulations'.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural language search query"},
            "limit": {"type": "number", "description": "Max results (default 5)", "default": 5},
            "doc_type": {"type": "string", "description": "Filter by type: pdf, contract, deal_notes, market_report, email, meeting_notes, plain_text, webpage"},
        },
        "required": ["query"],
    },
), handle_search_knowledge)

register_tool(Tool(
    name="ingest_knowledge",
    description="Add text content to the knowledge base. Use for deal notes, contract summaries, meeting notes, market insights, or any text you want to remember and search later. Voice: 'Save these deal notes to the knowledge base'.",
    inputSchema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Document title"},
            "content": {"type": "string", "description": "Full text content to ingest"},
            "doc_type": {"type": "string", "description": "Type: plain_text, deal_notes, contract, market_report, meeting_notes, email", "default": "plain_text"},
            "source": {"type": "string", "description": "Source identifier (file path, URL, etc.)"},
        },
        "required": ["title", "content"],
    },
), handle_ingest_knowledge)

register_tool(Tool(
    name="ingest_webpage",
    description="Fetch a webpage and add it to the knowledge base. Useful for saving market reports, articles, or reference pages. Voice: 'Save this webpage to the knowledge base'.",
    inputSchema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch and ingest"},
            "title": {"type": "string", "description": "Optional title (defaults to URL)"},
        },
        "required": ["url"],
    },
), handle_ingest_url)

register_tool(Tool(
    name="list_knowledge_docs",
    description="List all documents in the knowledge base. Voice: 'What's in the knowledge base?' or 'Show me all saved documents'.",
    inputSchema={
        "type": "object",
        "properties": {
            "doc_type": {"type": "string", "description": "Filter by type: pdf, contract, deal_notes, market_report, email, meeting_notes, plain_text, webpage"},
        },
    },
), handle_list_knowledge_docs)

register_tool(Tool(
    name="get_knowledge_doc",
    description="Get full content of a knowledge base document by ID.",
    inputSchema={
        "type": "object",
        "properties": {
            "document_id": {"type": "number", "description": "Document ID"},
        },
        "required": ["document_id"],
    },
), handle_get_knowledge_doc)

register_tool(Tool(
    name="delete_knowledge_doc",
    description="Delete a document from the knowledge base.",
    inputSchema={
        "type": "object",
        "properties": {
            "document_id": {"type": "number", "description": "Document ID to delete"},
        },
        "required": ["document_id"],
    },
), handle_delete_knowledge_doc)

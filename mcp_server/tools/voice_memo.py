"""Voice Memo MCP tools — transcribe audio and ingest into RAG."""
import os

from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_post, _default_headers, API_BASE_URL


# ── Transcribe Voice Memo ──

async def handle_transcribe_voice_memo(arguments: dict) -> list[TextContent]:
    file_path = arguments.get("file_path")
    if not file_path:
        return [TextContent(type="text", text="Please provide a file_path to the audio file.")]

    if not os.path.exists(file_path):
        return [TextContent(type="text", text=f"File not found: {file_path}")]

    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            response = api_post("/voice-memo/transcribe", files=files)

        response.raise_for_status()
        data = response.json()

        transcript = data.get("transcript", "")
        text = f"Transcription complete:\n\n{transcript}"
        return [TextContent(type="text", text=text)]

    except Exception as e:
        return [TextContent(type="text", text=f"Transcription failed: {e}")]


# ── Process Voice Memo (Transcribe + RAG Ingest) ──

async def handle_process_voice_memo(arguments: dict) -> list[TextContent]:
    file_path = arguments.get("file_path")
    if not file_path:
        return [TextContent(type="text", text="Please provide a file_path to the audio file.")]

    if not os.path.exists(file_path):
        return [TextContent(type="text", text=f"File not found: {file_path}")]

    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            form_data = {}
            if arguments.get("title"):
                form_data["title"] = arguments["title"]
            if arguments.get("property_id"):
                form_data["property_id"] = str(arguments["property_id"])
            if arguments.get("contact_id"):
                form_data["contact_id"] = str(arguments["contact_id"])

            response = api_post("/voice-memo/process", files=files, data=form_data)

        response.raise_for_status()
        data = response.json()

        transcript = data.get("transcript", "")
        doc_id = data.get("document_id")
        chunk_count = data.get("chunk_count", 0)

        text = f"Voice memo processed and ingested into Knowledge Base.\n\n"
        text += f"Document ID: {doc_id}\n"
        text += f"Chunks created: {chunk_count}\n\n"
        text += f"Transcript:\n{transcript}"
        return [TextContent(type="text", text=text)]

    except Exception as e:
        return [TextContent(type="text", text=f"Voice memo processing failed: {e}")]


# ── Tool Registration ──

register_tool(Tool(
    name="transcribe_voice_memo",
    description="Transcribe an audio file (voice memo) to text using OpenAI Whisper. Supports mp3, wav, m4a, ogg, webm, mp4, flac. Voice: 'Transcribe this voice note' or 'What did I say in this recording?'.",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute path to the audio file to transcribe"},
        },
        "required": ["file_path"],
    },
), handle_transcribe_voice_memo)

register_tool(Tool(
    name="process_voice_memo",
    description="Transcribe an audio file AND ingest the transcript into the Knowledge Base for RAG search. Optionally link to a property or contact. Voice: 'Save this voice memo to the knowledge base' or 'Process my voice note for property 123'.",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute path to the audio file"},
            "title": {"type": "string", "description": "Optional title for the knowledge base document"},
            "property_id": {"type": "number", "description": "Optional property ID to associate with"},
            "contact_id": {"type": "number", "description": "Optional contact ID to associate with"},
        },
        "required": ["file_path"],
    },
), handle_process_voice_memo)

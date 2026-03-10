"""Document Analysis — Analyze inspection reports, contracts, and other real estate documents."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_analyze_document(arguments: dict) -> list[TextContent]:
    """Analyze a document using AI to extract insights based on document type."""
    file_path = arguments.get("file_path")
    analysis_type = arguments.get("analysis_type", "general")

    if not file_path:
        return [TextContent(type="text", text="Error: file_path is required.")]

    response = api_post("/documents/analyze", json={
        "file_path": file_path,
        "analysis_type": analysis_type,
    })
    response.raise_for_status()
    data = response.json()

    analysis = data.get("analysis", {})
    doc_type = data.get("document_type", analysis_type)

    text = f"**Document Analysis ({doc_type})**\n\n"
    text += f"File: {file_path}\n\n"

    if analysis.get("summary"):
        text += f"**Summary:**\n{analysis['summary']}\n\n"

    if analysis.get("key_findings"):
        text += "**Key Findings:**\n"
        for finding in analysis["key_findings"]:
            text += f"- {finding}\n"
        text += "\n"

    if analysis.get("risk_level"):
        text += f"**Risk Level:** {analysis['risk_level']}\n"

    if analysis.get("recommendations"):
        text += "\n**Recommendations:**\n"
        for rec in analysis["recommendations"]:
            text += f"- {rec}\n"

    if not analysis:
        text += data.get("message", "Analysis complete. No structured results returned.")

    return [TextContent(type="text", text=text)]


async def handle_extract_issues(arguments: dict) -> list[TextContent]:
    """Extract issues from an inspection report document."""
    file_path = arguments.get("file_path")

    if not file_path:
        return [TextContent(type="text", text="Error: file_path is required.")]

    response = api_post("/documents/extract-issues", json={
        "file_path": file_path,
    })
    response.raise_for_status()
    data = response.json()

    issues = data.get("issues", [])
    text = f"**Inspection Report Issues**\n\n"
    text += f"File: {file_path}\n"
    text += f"Total issues found: {len(issues)}\n\n"

    # Group by severity if available
    critical = [i for i in issues if i.get("severity") == "critical"]
    major = [i for i in issues if i.get("severity") == "major"]
    minor = [i for i in issues if i.get("severity") == "minor"]
    other = [i for i in issues if i.get("severity") not in ("critical", "major", "minor")]

    if critical:
        text += f"**Critical ({len(critical)}):**\n"
        for issue in critical:
            text += f"- {issue.get('description', issue.get('title', 'Unknown'))}\n"
            if issue.get("estimated_cost"):
                text += f"  Est. cost: {issue['estimated_cost']}\n"
        text += "\n"

    if major:
        text += f"**Major ({len(major)}):**\n"
        for issue in major:
            text += f"- {issue.get('description', issue.get('title', 'Unknown'))}\n"
            if issue.get("estimated_cost"):
                text += f"  Est. cost: {issue['estimated_cost']}\n"
        text += "\n"

    if minor:
        text += f"**Minor ({len(minor)}):**\n"
        for issue in minor:
            text += f"- {issue.get('description', issue.get('title', 'Unknown'))}\n"
        text += "\n"

    if other:
        text += f"**Other ({len(other)}):**\n"
        for issue in other:
            text += f"- {issue.get('description', issue.get('title', 'Unknown'))}\n"
        text += "\n"

    if data.get("total_estimated_cost"):
        text += f"**Total Estimated Repair Cost:** {data['total_estimated_cost']}\n"

    if not issues:
        text += "No issues extracted. The document may not be a recognized inspection report format."

    return [TextContent(type="text", text=text)]


async def handle_extract_terms(arguments: dict) -> list[TextContent]:
    """Extract key terms and clauses from a contract document."""
    file_path = arguments.get("file_path")

    if not file_path:
        return [TextContent(type="text", text="Error: file_path is required.")]

    response = api_post("/documents/extract-terms", json={
        "file_path": file_path,
    })
    response.raise_for_status()
    data = response.json()

    terms = data.get("terms", {})
    text = f"**Contract Terms Extraction**\n\n"
    text += f"File: {file_path}\n\n"

    if terms.get("parties"):
        text += "**Parties:**\n"
        for party in terms["parties"]:
            text += f"- {party}\n"
        text += "\n"

    if terms.get("price"):
        text += f"**Purchase Price:** {terms['price']}\n"

    if terms.get("closing_date"):
        text += f"**Closing Date:** {terms['closing_date']}\n"

    if terms.get("contingencies"):
        text += "\n**Contingencies:**\n"
        for cont in terms["contingencies"]:
            text += f"- {cont}\n"

    if terms.get("deadlines"):
        text += "\n**Key Deadlines:**\n"
        for deadline in terms["deadlines"]:
            text += f"- {deadline}\n"

    if terms.get("special_clauses"):
        text += "\n**Special Clauses:**\n"
        for clause in terms["special_clauses"]:
            text += f"- {clause}\n"

    if not terms:
        text += data.get("message", "No terms extracted. The document may not be a recognized contract format.")

    return [TextContent(type="text", text=text)]


async def handle_compare_documents(arguments: dict) -> list[TextContent]:
    """Compare two documents and highlight differences."""
    file_path_1 = arguments.get("file_path_1")
    file_path_2 = arguments.get("file_path_2")

    if not file_path_1 or not file_path_2:
        return [TextContent(type="text", text="Error: Both file_path_1 and file_path_2 are required.")]

    response = api_post("/documents/compare", json={
        "file_path_1": file_path_1,
        "file_path_2": file_path_2,
    })
    response.raise_for_status()
    data = response.json()

    text = f"**Document Comparison**\n\n"
    text += f"Document 1: {file_path_1}\n"
    text += f"Document 2: {file_path_2}\n\n"

    if data.get("similarity_score") is not None:
        text += f"**Similarity Score:** {data['similarity_score']}%\n\n"

    differences = data.get("differences", [])
    if differences:
        text += f"**Differences Found ({len(differences)}):**\n\n"
        for i, diff in enumerate(differences, 1):
            text += f"{i}. **{diff.get('section', 'Unknown Section')}**\n"
            if diff.get("doc1_text"):
                text += f"   Doc 1: {diff['doc1_text']}\n"
            if diff.get("doc2_text"):
                text += f"   Doc 2: {diff['doc2_text']}\n"
            if diff.get("significance"):
                text += f"   Significance: {diff['significance']}\n"
            text += "\n"
    else:
        text += "No significant differences found.\n"

    if data.get("summary"):
        text += f"\n**Summary:** {data['summary']}\n"

    return [TextContent(type="text", text=text)]


async def handle_document_types(arguments: dict) -> list[TextContent]:
    """List supported document types for analysis."""
    response = api_get("/documents/types")
    response.raise_for_status()
    data = response.json()

    types = data.get("types", [])
    text = "**Supported Document Types**\n\n"

    if types:
        for doc_type in types:
            name = doc_type.get("name", "Unknown")
            desc = doc_type.get("description", "")
            formats = ", ".join(doc_type.get("formats", []))
            text += f"- **{name}**: {desc}"
            if formats:
                text += f" (formats: {formats})"
            text += "\n"
    else:
        text += "- Inspection Reports (PDF, DOCX)\n"
        text += "- Purchase Contracts (PDF, DOCX)\n"
        text += "- Lease Agreements (PDF, DOCX)\n"
        text += "- Disclosure Forms (PDF)\n"
        text += "- Appraisal Reports (PDF)\n"
        text += "- General Documents (PDF, DOCX, TXT)\n"

    return [TextContent(type="text", text=text)]


# ── Registration ──

register_tool(
    Tool(
        name="analyze_inspection_report",
        description=(
            "Analyze a real estate document such as an inspection report, contract, or general document. "
            "Uses AI to extract key findings, risk levels, and recommendations. "
            "Voice: 'Analyze this inspection report', 'Review the contract at /path/to/file', "
            "'What does this document say?', 'Summarize the appraisal report'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the document file to analyze",
                },
                "analysis_type": {
                    "type": "string",
                    "description": "Type of analysis to perform",
                    "enum": ["inspection_report", "contract", "general"],
                    "default": "general",
                },
            },
            "required": ["file_path"],
        },
    ),
    handle_analyze_document,
)

register_tool(
    Tool(
        name="extract_inspection_issues",
        description=(
            "Extract and categorize all issues from a property inspection report. "
            "Groups issues by severity (critical, major, minor) with estimated repair costs. "
            "Voice: 'What issues did the inspection find?', 'Extract problems from the inspection report', "
            "'List all defects from the home inspection', 'How bad is the inspection report?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the inspection report file",
                },
            },
            "required": ["file_path"],
        },
    ),
    handle_extract_issues,
)

register_tool(
    Tool(
        name="extract_contract_terms",
        description=(
            "Extract key terms, clauses, deadlines, and contingencies from a real estate contract. "
            "Identifies parties, purchase price, closing date, contingencies, and special clauses. "
            "Voice: 'What are the terms of this contract?', 'Extract deadlines from the purchase agreement', "
            "'What contingencies are in this contract?', 'Summarize the contract terms'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the contract document",
                },
            },
            "required": ["file_path"],
        },
    ),
    handle_extract_terms,
)

register_tool(
    Tool(
        name="compare_documents",
        description=(
            "Compare two real estate documents side-by-side and highlight differences. "
            "Useful for comparing contract versions, competing offers, or inspection re-checks. "
            "Voice: 'Compare these two contracts', 'What changed between the original and revised offer?', "
            "'Show differences between inspection reports', 'Compare the two appraisals'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "file_path_1": {
                    "type": "string",
                    "description": "Path to the first document",
                },
                "file_path_2": {
                    "type": "string",
                    "description": "Path to the second document",
                },
            },
            "required": ["file_path_1", "file_path_2"],
        },
    ),
    handle_compare_documents,
)

register_tool(
    Tool(
        name="list_document_types",
        description=(
            "List all supported document types for analysis. "
            "Shows what kinds of real estate documents can be analyzed and in which formats. "
            "Voice: 'What document types can you analyze?', 'What formats do you support?', "
            "'Can you read inspection reports?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_document_types,
)

"""Agent Onboarding - Manage onboarding questions, answers, and completion status."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_get_onboarding_questions(arguments: dict) -> list[TextContent]:
    """Get the list of onboarding questions for new agents."""
    response = api_get("/onboarding/questions")
    response.raise_for_status()
    data = response.json()

    questions = data if isinstance(data, list) else data.get("questions", [])

    if not questions:
        return [TextContent(type="text", text="No onboarding questions found.")]

    text = f"**Onboarding Questions ({len(questions)})**\n\n"
    for i, q in enumerate(questions, 1):
        q_text = q.get("question", q.get("text", str(q)))
        category = q.get("category", "")
        required = q.get("required", False)
        q_id = q.get("id", i)

        text += f"{i}. **{q_text}**\n"
        if category:
            text += f"   Category: {category}\n"
        if required:
            text += f"   Required: Yes\n"
        if q.get("options"):
            text += f"   Options: {', '.join(q['options'])}\n"
        text += f"   ID: {q_id}\n\n"

    return [TextContent(type="text", text=text)]


async def handle_get_onboarding_categories(arguments: dict) -> list[TextContent]:
    """Get the available onboarding question categories."""
    response = api_get("/onboarding/categories")
    response.raise_for_status()
    data = response.json()

    categories = data if isinstance(data, list) else data.get("categories", [])

    if not categories:
        return [TextContent(type="text", text="No onboarding categories found.")]

    text = f"**Onboarding Categories ({len(categories)})**\n\n"
    for i, cat in enumerate(categories, 1):
        if isinstance(cat, str):
            text += f"{i}. {cat}\n"
        else:
            cat_name = cat.get("name", str(cat))
            cat_desc = cat.get("description", "")
            text += f"{i}. **{cat_name}**"
            if cat_desc:
                text += f" - {cat_desc}"
            text += "\n"

    return [TextContent(type="text", text=text)]


async def handle_submit_onboarding(arguments: dict) -> list[TextContent]:
    """Submit onboarding answers for an agent."""
    answers = arguments.get("answers", {})
    agent_id = arguments.get("agent_id")

    if not answers:
        return [TextContent(type="text", text="Error: No answers provided. Please provide answers as a dict of question_id: answer pairs.")]

    payload = {"answers": answers}
    if agent_id:
        payload["agent_id"] = agent_id

    response = api_post("/onboarding/submit", json=payload)
    response.raise_for_status()
    result = response.json()

    text = f"**Onboarding Answers Submitted**\n\n"
    text += f"Questions answered: {len(answers)}\n"

    if result.get("completed"):
        text += f"Status: Complete\n"
    else:
        remaining = result.get("remaining", 0)
        if remaining:
            text += f"Remaining questions: {remaining}\n"
        text += f"Status: In Progress\n"

    if result.get("next_step"):
        text += f"\nNext step: {result['next_step']}\n"

    return [TextContent(type="text", text=text)]


async def handle_get_onboarding_status(arguments: dict) -> list[TextContent]:
    """Check the onboarding completion status for an agent."""
    agent_id = arguments.get("agent_id")
    if not agent_id:
        return [TextContent(type="text", text="Error: agent_id is required.")]

    response = api_get(f"/onboarding/status/{agent_id}")
    response.raise_for_status()
    status = response.json()

    completed = status.get("completed", False)
    progress = status.get("progress", 0)
    total = status.get("total_questions", 0)
    answered = status.get("answered", 0)

    text = f"**Onboarding Status for Agent {agent_id}**\n\n"
    text += f"Status: {'Complete' if completed else 'In Progress'}\n"
    text += f"Progress: {answered}/{total} questions answered ({progress}%)\n"

    if status.get("missing_categories"):
        text += f"\nMissing categories: {', '.join(status['missing_categories'])}\n"

    if status.get("completed_at"):
        text += f"Completed at: {status['completed_at']}\n"

    if not completed:
        text += f"\nUse 'get_onboarding_questions' to see remaining questions."

    return [TextContent(type="text", text=text)]


async def handle_complete_onboarding(arguments: dict) -> list[TextContent]:
    """Mark onboarding as complete for an agent."""
    agent_id = arguments.get("agent_id")

    payload = {}
    if agent_id:
        payload["agent_id"] = agent_id

    response = api_post("/onboarding/complete", json=payload)
    response.raise_for_status()
    result = response.json()

    if result.get("error"):
        return [TextContent(type="text", text=f"Error: {result['error']}")]

    text = f"**Onboarding Complete**\n\n"
    if agent_id:
        text += f"Agent ID: {agent_id}\n"
    text += f"Status: Completed\n"

    if result.get("completed_at"):
        text += f"Completed at: {result['completed_at']}\n"

    if result.get("next_steps"):
        text += f"\n**Next Steps:**\n"
        for step in result["next_steps"]:
            text += f"  - {step}\n"

    return [TextContent(type="text", text=text)]


# ── Registration ──

register_tool(
    Tool(
        name="get_onboarding_questions",
        description=(
            "Get the list of onboarding questions for new real estate agents. "
            "Returns all questions with their categories, options, and requirements. "
            "Voice: 'Show me the onboarding questions', 'What questions do new agents answer?', "
            "'Get the onboarding form', 'What do I need to fill out for onboarding?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_get_onboarding_questions,
)

register_tool(
    Tool(
        name="get_onboarding_categories",
        description=(
            "Get the available onboarding question categories. Categories group related "
            "questions together (e.g., personal info, markets, experience). "
            "Voice: 'What are the onboarding categories?', 'Show me question groups', "
            "'List onboarding sections'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_get_onboarding_categories,
)

register_tool(
    Tool(
        name="submit_onboarding",
        description=(
            "Submit onboarding answers for a real estate agent. Accepts a dictionary of "
            "question_id to answer mappings. Can be submitted incrementally. "
            "Voice: 'Submit my onboarding answers', 'Save these onboarding responses', "
            "'Fill in the onboarding form with these answers'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "answers": {
                    "type": "object",
                    "description": "Dictionary of question_id: answer pairs (e.g., {'q1': 'John', 'q2': 'Residential'})",
                },
                "agent_id": {
                    "type": "number",
                    "description": "Agent ID to submit answers for (optional, uses current agent if omitted)",
                },
            },
            "required": ["answers"],
        },
    ),
    handle_submit_onboarding,
)

register_tool(
    Tool(
        name="get_onboarding_status",
        description=(
            "Check the onboarding completion status for an agent. Shows progress, "
            "how many questions are answered, and what categories are missing. "
            "Voice: 'Check onboarding status for agent 1', 'Is agent 3 done with onboarding?', "
            "'How far along is the new agent in onboarding?', 'Onboarding progress check'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "number",
                    "description": "The agent's unique ID to check status for",
                },
            },
            "required": ["agent_id"],
        },
    ),
    handle_get_onboarding_status,
)

register_tool(
    Tool(
        name="complete_onboarding",
        description=(
            "Mark onboarding as complete for an agent. This finalizes the onboarding process "
            "and activates the agent's account. Should only be called after all required "
            "questions are answered. "
            "Voice: 'Mark onboarding complete for agent 1', 'Finish onboarding', "
            "'Complete the onboarding process', 'Finalize agent setup'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "number",
                    "description": "Agent ID to mark as complete (optional, uses current agent if omitted)",
                },
            },
        },
    ),
    handle_complete_onboarding,
)

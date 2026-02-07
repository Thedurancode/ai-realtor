from app.services.agent_tools import AgentTools
from app.services.exa_research_service import ExaResearchService


def test_extract_task_id_variants():
    service = ExaResearchService(api_key="x")
    assert service.extract_task_id({"task_id": "a1"}) == "a1"
    assert service.extract_task_id({"taskId": "a2"}) == "a2"
    assert service.extract_task_id({"id": "a3"}) == "a3"
    assert service.extract_task_id({}) is None


def test_extract_status_variants():
    service = ExaResearchService(api_key="x")
    assert service.extract_status({"status": "completed"}) == "completed"
    assert service.extract_status({"status": ""}) is None
    assert service.extract_status({}) is None


def test_agent_tools_register_exa_tools():
    tools = AgentTools(db=None)
    names = [tool["name"] for tool in tools.get_tool_schemas()]
    assert "exa_create_research_task" in names
    assert "exa_get_research_task" in names
    assert "exa_create_subdivision_research_task" in names


def test_build_property_dossier_instructions_contains_location_and_strategy():
    service = ExaResearchService(api_key="x")
    instructions = service.build_property_dossier_instructions(
        address="141 Throop Ave, New Brunswick, NJ 08901",
        county="Middlesex County",
        strategy="buy&hold",
    )

    assert "141 Throop Ave, New Brunswick, NJ 08901, Middlesex County" in instructions
    assert "underwriting model for buy&hold" in instructions
    assert "cite links for every major claim" in instructions


def test_build_subdivision_dossier_instructions_contains_key_goals():
    service = ExaResearchService(api_key="x")
    instructions = service.build_subdivision_dossier_instructions(
        address="141 Throop Ave, New Brunswick, NJ 08901",
        county="Middlesex County",
        target_strategy="subdivide and build duplexes",
        target_lot_count=3,
    )

    assert "141 Throop Ave, New Brunswick, NJ 08901, Middlesex County" in instructions
    assert "Target lot count goal: 3." in instructions
    assert "Primary strategy: subdivide and build duplexes." in instructions
    assert "minimum lot size/frontage/width/depth requirements" in instructions
    assert "go/no-go recommendation" in instructions

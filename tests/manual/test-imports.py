#!/usr/bin/env python3
"""
Test all Python imports to verify the codebase is properly integrated.
Run this before Docker deployment to catch import errors early.
"""

import sys
from importlib import import_module
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Test results
passed = []
failed = []

def test_import(module_path, description):
    """Test importing a module."""
    try:
        import_module(module_path)
        passed.append(description)
        print(f"✅ {description}")
        return True
    except Exception as e:
        failed.append((description, str(e)))
        print(f"❌ {description}")
        print(f"   Error: {e}")
        return False

print("🧪 Testing Python Imports")
print("=" * 60)
print()

# Test 1: Core models
print("📦 Core Models:")
test_import("app.models.agent", "Agent model")
test_import("app.models.property", "Property model")
test_import("app.models.contract", "Contract model")
test_import("app.models.contact", "Contact model")
test_import("app.models.conversation_history", "ConversationHistory model")
print()

# Test 2: ZeroClaw-inspired models
print("🔧 ZeroClaw-Inspired Models:")
test_import("app.models.workspace", "Workspace model")
test_import("app.models.skill", "Skill model (Skills System)")
test_import("app.models.voice_memory", "Voice Memory model")
print()

# Test 3: New services
print("⚙️  New Services:")
test_import("app.services.approval", "Approval Manager service")
test_import("app.services.credential_scrubbing", "Credential Scrubbing service")
test_import("app.services.observer", "Observer Pattern service")
test_import("app.services.sqlite_tuning", "SQLite Tuning service")
test_import("app.services.skills", "Skills System service")
print()

# Test 4: New routers
print("🌐 New Routers:")
test_import("app.routers.approval", "Approval router")
test_import("app.routers.credential_scrubbing", "Credential Scrubbing router")
test_import("app.routers.observer", "Observer router")
test_import("app.routers.sqlite_tuning", "SQLite Tuning router")
test_import("app.routers.skills", "Skills router")
test_import("app.routers.onboarding", "Onboarding router")
print()

# Test 5: Core services
print("🔨 Core Services:")
test_import("app.services.memory_graph", "Memory Graph service")
test_import("app.services.onboarding_service", "Onboarding service")
test_import("app.services.llm_service", "LLM service")
print()

# Test 6: MCP server
print("🤖 MCP Server:")
test_import("mcp_server.property_mcp", "Property MCP server")
print()

# Test 7: Database
print("💾 Database:")
test_import("app.database", "Database connection")
print()

# Test 8: Main app
print("🚀 Main Application:")
test_import("app.main", "Main FastAPI app")
print()

# Summary
print("=" * 60)
print(f"✅ Passed: {len(passed)}")
print(f"❌ Failed: {len(failed)}")
print()

if failed:
    print("Failed Imports:")
    for description, error in failed:
        print(f"  • {description}")
        print(f"    {error}")
    print()
    sys.exit(1)
else:
    print("🎉 All imports successful! Ready for Docker deployment.")
    sys.exit(0)

#!/usr/bin/env python3
"""Count all API endpoints in the system"""
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

router_files = [
    "app/routers/agents.py",
    "app/routers/address.py",
    "app/routers/properties.py",
    "app/routers/skip_trace.py",
    "app/routers/contacts.py",
    "app/routers/todos.py",
    "app/routers/agent_preferences.py",
    "app/routers/contracts.py",
]

print("="*70)
print("  API ENDPOINT COUNT")
print("="*70)
print()

total = 0
endpoint_details = {}

for file_path in router_files:
    path = PROJECT_ROOT / file_path
    if not path.exists():
        continue

    content = path.read_text()

    # Find all route decorators with details
    pattern = r'@router\.(get|post|patch|delete|put)\(["\']([^"\']+)'
    matches = re.findall(pattern, content)

    count = len(matches)
    total += count

    module_name = path.stem
    endpoint_details[module_name] = matches

    print(f"📁 {module_name.upper()}")
    print(f"   Endpoints: {count}")

    # Group by method
    methods = {}
    for method, route in matches:
        methods[method] = methods.get(method, 0) + 1

    method_str = ", ".join([f"{m.upper()}: {c}" for m, c in sorted(methods.items())])
    print(f"   Methods: {method_str}")
    print()

print("="*70)
print(f"  TOTAL: {total} API ENDPOINTS")
print("="*70)
print()

# Breakdown by category
print("📊 BREAKDOWN BY CATEGORY:")
print()

categories = {
    "Agent Management": ["agents", "agent_preferences"],
    "Property Management": ["properties", "address"],
    "Contact Management": ["contacts"],
    "Skip Tracing": ["skip_trace"],
    "Contract Management": ["contracts"],
    "Task Management": ["todos"],
}

for category, modules in categories.items():
    count = sum(len(endpoint_details.get(m, [])) for m in modules)
    print(f"   {category}: {count} endpoints")

print()

# List all endpoints
print("="*70)
print("  ALL ENDPOINTS")
print("="*70)
print()

for module_name, endpoints in sorted(endpoint_details.items()):
    if endpoints:
        print(f"📁 {module_name.upper()} ({len(endpoints)} endpoints):")
        for method, route in sorted(endpoints):
            print(f"   {method.upper():6} /{module_name}{route}")
        print()

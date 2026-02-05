#!/usr/bin/env python3
"""
Seed script to generate sample activity events for testing the activity feed
Generates 20 diverse activity events including tool calls, voice commands, and system events
"""

import requests
import time
import random
from datetime import datetime

# Backend API URL
API_BASE_URL = "http://localhost:8000"

# Sample activity events with diverse types
SAMPLE_ACTIVITIES = [
    {
        "tool_name": "list_properties",
        "user_source": "Claude Desktop",
        "event_type": "tool_call",
        "status": "success",
        "metadata": {
            "filter": "all",
            "limit": 10,
            "result_count": 7
        }
    },
    {
        "tool_name": "create_property",
        "user_source": "MCP Client",
        "event_type": "tool_call",
        "status": "success",
        "metadata": {
            "address": "123 Main St",
            "price": 500000,
            "bedrooms": 3,
            "bathrooms": 2
        }
    },
    {
        "tool_name": "send_contract",
        "user_source": "Voice Agent",
        "event_type": "voice_command",
        "status": "success",
        "metadata": {
            "template": "purchase_agreement",
            "recipient": "john.doe@email.com",
            "property_id": 5
        }
    },
    {
        "tool_name": "get_property",
        "user_source": "Claude Desktop",
        "event_type": "tool_call",
        "status": "success",
        "metadata": {
            "property_id": 3,
            "address": "456 Oak Ave"
        }
    },
    {
        "tool_name": "enrich_property",
        "user_source": "Background Worker",
        "event_type": "system_event",
        "status": "success",
        "metadata": {
            "property_id": 8,
            "source": "Zillow API",
            "enriched_fields": ["zestimate", "sqft", "year_built"]
        }
    },
    {
        "tool_name": "check_contract_status",
        "user_source": "Voice Agent",
        "event_type": "voice_command",
        "status": "success",
        "metadata": {
            "contract_id": 42,
            "status": "signed",
            "signed_by": ["buyer", "seller"]
        }
    },
    {
        "tool_name": "add_contact",
        "user_source": "MCP Client",
        "event_type": "tool_call",
        "status": "success",
        "metadata": {
            "name": "Jane Smith",
            "email": "jane.smith@email.com",
            "role": "buyer",
            "property_id": 3
        }
    },
    {
        "tool_name": "send_notification",
        "user_source": "System",
        "event_type": "system_event",
        "status": "success",
        "metadata": {
            "type": "new_lead",
            "message": "New buyer interested in 789 Broadway",
            "priority": "high"
        }
    },
    {
        "tool_name": "skip_trace_property",
        "user_source": "Claude Desktop",
        "event_type": "tool_call",
        "status": "success",
        "metadata": {
            "address": "789 Elm St",
            "owner_found": True,
            "phone": "+1-555-0123"
        }
    },
    {
        "tool_name": "delete_property",
        "user_source": "MCP Client",
        "event_type": "tool_call",
        "status": "error",
        "metadata": {
            "property_id": 999,
            "error": "Property not found"
        }
    },
    {
        "tool_name": "list_contracts",
        "user_source": "Voice Agent",
        "event_type": "voice_command",
        "status": "success",
        "metadata": {
            "address_filter": "141 Throop Ave",
            "match_count": 3
        }
    },
    {
        "tool_name": "update_property",
        "user_source": "Claude Desktop",
        "event_type": "tool_call",
        "status": "success",
        "metadata": {
            "property_id": 5,
            "updated_fields": ["price", "status"],
            "new_price": 475000
        }
    },
    {
        "tool_name": "validate_address",
        "user_source": "System",
        "event_type": "system_event",
        "status": "success",
        "metadata": {
            "input_address": "123 Main",
            "validated_address": "123 Main St, Brooklyn, NY 11201",
            "confidence": 0.95
        }
    },
    {
        "tool_name": "send_contract",
        "user_source": "MCP Client",
        "event_type": "tool_call",
        "status": "error",
        "metadata": {
            "contract_id": 15,
            "error": "Missing email address for recipient"
        }
    },
    {
        "tool_name": "list_properties_voice",
        "user_source": "Voice Agent",
        "event_type": "voice_command",
        "status": "success",
        "metadata": {
            "query": "show me properties on broadway",
            "normalized_query": "broadway",
            "match_count": 4
        }
    },
    {
        "tool_name": "create_contact",
        "user_source": "Claude Desktop",
        "event_type": "tool_call",
        "status": "success",
        "metadata": {
            "name": "Michael Brown",
            "email": "michael.brown@email.com",
            "phone": "+1-555-0456",
            "role": "agent"
        }
    },
    {
        "tool_name": "database_backup",
        "user_source": "Scheduler",
        "event_type": "system_event",
        "status": "success",
        "metadata": {
            "backup_size_mb": 12.5,
            "duration_seconds": 3.2,
            "backup_location": "s3://backups/2025-02-05.db"
        }
    },
    {
        "tool_name": "get_property",
        "user_source": "Voice Agent",
        "event_type": "voice_command",
        "status": "error",
        "metadata": {
            "query": "show property at one two three main",
            "error": "Multiple properties found, please be more specific"
        }
    },
    {
        "tool_name": "list_notifications",
        "user_source": "MCP Client",
        "event_type": "tool_call",
        "status": "success",
        "metadata": {
            "limit": 20,
            "unread_count": 5
        }
    },
    {
        "tool_name": "sync_external_data",
        "user_source": "Background Worker",
        "event_type": "system_event",
        "status": "success",
        "metadata": {
            "source": "Zillow API",
            "properties_updated": 12,
            "duration_seconds": 8.7
        }
    }
]


def send_activity(activity_data):
    """Send a single activity event to the API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/activities/log",
            json=activity_data,
            timeout=5
        )
        response.raise_for_status()

        activity_id = response.json().get("id")
        print(f"✓ Created activity #{activity_id}: {activity_data['tool_name']} ({activity_data['event_type']}) - {activity_data['status']}")

        # For some activities, simulate completion with duration
        if activity_data['status'] == 'success' and random.random() > 0.3:
            # Simulate a duration
            duration_ms = random.randint(100, 5000)

            # Update activity with duration
            update_response = requests.patch(
                f"{API_BASE_URL}/activities/{activity_id}",
                json={
                    "status": "success",
                    "duration_ms": duration_ms
                },
                timeout=5
            )
            update_response.raise_for_status()
            print(f"  ⏱  Updated with duration: {duration_ms}ms")

        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to create activity: {activity_data['tool_name']} - {str(e)}")
        return False


def main():
    """Main function to seed activity events"""
    print("=" * 60)
    print("Activity Feed Seed Script")
    print("=" * 60)
    print(f"Backend API: {API_BASE_URL}")
    print(f"Generating {len(SAMPLE_ACTIVITIES)} activity events...")
    print("=" * 60)
    print()

    # Test API connection
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        response.raise_for_status()
        print(f"✓ Connected to backend API")
        print()
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to connect to backend API: {str(e)}")
        print("  Make sure the backend is running: python3 -m uvicorn app.main:app --reload --port 8000")
        return

    # Send each activity with a small delay
    success_count = 0
    for i, activity in enumerate(SAMPLE_ACTIVITIES, 1):
        print(f"[{i}/{len(SAMPLE_ACTIVITIES)}] ", end="")
        if send_activity(activity):
            success_count += 1

        # Add a small delay between activities for visual effect
        time.sleep(0.5)

    print()
    print("=" * 60)
    print(f"Seeding complete! {success_count}/{len(SAMPLE_ACTIVITIES)} activities created")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Open frontend: http://localhost:3025/activity")
    print("2. Watch the activity feed update in real-time!")
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
TV Display Control - Send commands to the TV display from CLI
Acts like an MCP tool for controlling the TV display
"""
import requests
import json
import sys


API_URL = "http://localhost:8000"


def show_property(property_id=None, address=None, message=None):
    """Show a property on the TV display"""
    command = {"action": "show_property"}

    if property_id:
        command["property_id"] = property_id
    elif address:
        command["address"] = address
    else:
        print("Error: Must provide either property_id or address")
        return

    if message:
        command["message"] = message

    response = requests.post(f"{API_URL}/display/command", json=command)
    return response.json()


def agent_speak(message):
    """Make the agent speak a message"""
    command = {
        "action": "agent_speak",
        "message": message
    }
    response = requests.post(f"{API_URL}/display/command", json=command)
    return response.json()


def close_detail():
    """Close the property detail view"""
    command = {"action": "close_detail"}
    response = requests.post(f"{API_URL}/display/command", json=command)
    return response.json()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scripts/manual/tv_control.py show <address>")
        print("  python3 scripts/manual/tv_control.py show_id <property_id>")
        print("  python3 scripts/manual/tv_control.py speak <message>")
        print("  python3 scripts/manual/tv_control.py close")
        sys.exit(1)

    action = sys.argv[1]

    if action == "show" and len(sys.argv) >= 3:
        address = " ".join(sys.argv[2:])
        result = show_property(address=address)
        print(json.dumps(result, indent=2))

    elif action == "show_id" and len(sys.argv) >= 3:
        property_id = int(sys.argv[2])
        result = show_property(property_id=property_id)
        print(json.dumps(result, indent=2))

    elif action == "speak" and len(sys.argv) >= 3:
        message = " ".join(sys.argv[2:])
        result = agent_speak(message)
        print(json.dumps(result, indent=2))

    elif action == "close":
        result = close_detail()
        print(json.dumps(result, indent=2))

    else:
        print("Invalid command")
        sys.exit(1)

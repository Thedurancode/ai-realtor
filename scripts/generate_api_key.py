#!/usr/bin/env python3
"""Generate and store API keys for agents."""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.agent import Agent
from app.auth import generate_api_key, hash_api_key


def list_agents():
    db = SessionLocal()
    try:
        agents = db.query(Agent).all()
        if not agents:
            print("No agents found.")
            return
        print("\nAgents:")
        print("-" * 60)
        for agent in agents:
            has_key = "yes" if agent.api_key_hash else "no"
            print(f"  ID: {agent.id} | {agent.name} ({agent.email}) | key: {has_key}")
        print("-" * 60)
    finally:
        db.close()


def generate_key_for_agent(agent_id: int):
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            print(f"Agent {agent_id} not found.")
            sys.exit(1)

        api_key = generate_api_key()
        agent.api_key_hash = hash_api_key(api_key)
        db.commit()

        print(f"\nGenerated API key for {agent.name} (ID: {agent.id})")
        print(f"Key (save this — it won't be shown again):\n")
        print(f"  {api_key}\n")
        print(f"Add to .env:")
        print(f"  MCP_API_KEY={api_key}\n")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate API keys for agents")
    parser.add_argument("--list", action="store_true", help="List all agents")
    parser.add_argument("--agent-id", type=int, help="Agent ID to generate key for")
    args = parser.parse_args()

    if args.list:
        list_agents()
    elif args.agent_id:
        generate_key_for_agent(args.agent_id)
    else:
        parser.print_help()

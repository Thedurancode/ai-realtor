#!/usr/bin/env python3
"""Fetch and list your DocuSeal templates"""
import sys
sys.path.insert(0, '/Users/edduran/Documents/GitHub/ai-realtor')

import asyncio
from app.services.docuseal import docuseal_client
from app.config import settings

async def list_templates():
    """List all available DocuSeal templates"""
    print("=" * 70)
    print("  FETCHING YOUR DOCUSEAL TEMPLATES")
    print("=" * 70)

    print(f"\n📡 API URL: {settings.docuseal_api_url}")
    print(f"🔑 API Key: {settings.docuseal_api_key[:10]}..." if settings.docuseal_api_key else "❌ NOT SET")

    if not settings.docuseal_api_key:
        print("\n❌ ERROR: DOCUSEAL_API_KEY not set in .env file")
        print("\nAdd to your .env file:")
        print("DOCUSEAL_API_KEY=your_key_here")
        return

    try:
        print("\n🔍 Fetching templates...")
        templates = await docuseal_client.get_templates(limit=50)

        if not templates:
            print("\n⚠️  No templates found")
            print("\nCreate a template at:")
            print(f"   {settings.docuseal_api_url.replace('api.', '')}/templates")
            return

        print(f"\n✅ Found {len(templates)} template(s):\n")
        print("-" * 70)

        for i, template in enumerate(templates, 1):
            template_id = template.get('id')
            name = template.get('name', 'Unnamed')
            schema = template.get('schema', [])

            # Get roles from schema
            roles = []
            for field in schema:
                if isinstance(field, dict):
                    submitter = field.get('submitter')
                    if submitter and submitter not in roles:
                        roles.append(submitter)

            print(f"\n{i}. Template ID: {template_id}")
            print(f"   Name: {name}")
            print(f"   Roles: {', '.join(roles) if roles else 'No roles defined'}")

            # Show external_id if available
            if template.get('external_id'):
                print(f"   External ID: {template.get('external_id')}")

            # Show created date
            if template.get('created_at'):
                print(f"   Created: {template.get('created_at')}")

        print("\n" + "-" * 70)
        print("\n💡 To use a template, copy its Template ID")
        print("   Then run: python test_docuseal_integration.py")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("   • Check your API key is correct")
        print("   • Verify API URL is correct")
        print("   • Make sure you have templates created")

if __name__ == "__main__":
    asyncio.run(list_templates())

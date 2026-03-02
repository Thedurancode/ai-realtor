#!/usr/bin/env python3
"""
Setup Signature Realty Brand
"""
import requests
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREVIEW_OUTPUT_PATH = PROJECT_ROOT / "examples" / "output" / "signature_realty_preview.html"

# API Base URL
API_BASE = "https://ai-realtor.fly.dev"

def setup_signature_realty():
    """Create agent and brand for Signature Realty"""

    # Step 1: Register an agent
    print("Step 1: Creating agent for Signature Realty...")
    agent_data = {
        "name": "Jane Doe",
        "email": "jane@signaturerealty.com",
        "phone": "+14155551234",
        "license_number": "CA-12345678"
    }

    try:
        response = requests.post(f"{API_BASE}/agents/register", json=agent_data)
        response.raise_for_status()
        agent_result = response.json()
        agent_id = agent_result['id']
        api_key = agent_result['api_key']

        print(f"✅ Agent created successfully!")
        print(f"   Agent ID: {agent_id}")
        print(f"   API Key: {api_key}")
        print()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "Email already registered" in e.response.json().get('detail', ''):
            print("⚠️  Agent already exists, retrieving existing agent...")
            # Try to get existing agent
            response = requests.get(f"{API_BASE}/agents/")
            response.raise_for_status()
            agents = response.json()
            agent_id = None
            for agent in agents:
                if agent['email'] == "jane@signaturerealty.com":
                    agent_id = agent['id']
                    break

            if not agent_id and agents:
                # Use first available agent
                agent_id = agents[0]['id']

            print(f"✅ Using existing agent ID: {agent_id}")
            print()
        else:
            print(f"❌ Error creating agent: {e}")
            return

    # Step 2: Create Signature Realty Brand
    print("Step 2: Creating Signature Realty brand...")
    brand_data = {
        "company_name": "Signature Realty",
        "tagline": "Your Dream Home Awaits",
        "logo_url": "https://signaturerealty.com/logo.png",
        "website_url": "https://signaturerealty.com",

        # About
        "bio": "Signature Realty specializes in luxury residential properties in the greater Bay Area. With over 15 years of experience, we help clients find their perfect home.",
        "about_us": "Founded in 2010, Signature Realty has helped over 500 families find their dream homes. Our commitment to excellence and personalized service sets us apart.",
        "specialties": ["Luxury Homes", "First-Time Buyers", "Investment Properties", "Relocation"],
        "service_areas": [
            {"city": "San Francisco", "state": "CA"},
            {"city": "Palo Alto", "state": "CA"},
            {"city": "Mountain View", "state": "CA"}
        ],
        "languages": ["English", "Spanish"],

        # Brand Colors - Luxury Gold theme
        "primary_color": "#B45309",      # Deep gold/brown
        "secondary_color": "#D97706",    # Golden amber
        "accent_color": "#F59E0B",       # Bright gold
        "background_color": "#FFFBEB",   # Warm cream
        "text_color": "#78350F",         # Dark brown

        # Contact Info
        "display_phone": "+1 (415) 555-1234",
        "display_email": "hello@signaturerealty.com",
        "office_address": "123 Market Street, Suite 500, San Francisco, CA 94105",
        "office_phone": "+1 (415) 555-1000",

        # Social Media
        "social_media": {
            "facebook": "https://facebook.com/signaturerealty",
            "instagram": "https://instagram.com/signaturerealty",
            "linkedin": "https://linkedin.com/company/signaturerealty",
            "twitter": "https://twitter.com/signaturerealty"
        },

        # License Info
        "license_display_name": "Jane Doe - CA BRE #12345678",
        "license_number": "CA-12345678",
        "license_states": ["CA"],

        # Privacy Settings
        "show_profile": True,
        "show_contact_info": True,
        "show_social_media": True,

        # Email & Reports
        "email_template_style": "modern",
        "report_logo_placement": "top-left",

        # SEO
        "meta_title": "Signature Realty - Luxury Homes in San Francisco Bay Area",
        "meta_description": "Find your dream home with Signature Realty. Specializing in luxury residential properties in San Francisco, Palo Alto, and Mountain View.",
        "keywords": ["luxury real estate", "San Francisco homes", "Bay Area real estate", "signature realty"],

        # Analytics
        "google_analytics_id": "UA-123456789-1",
        "facebook_pixel_id": "1234567890"
    }

    try:
        response = requests.post(f"{API_BASE}/agent-brand/{agent_id}", json=brand_data)

        if response.status_code == 400 and "already exists" in response.json().get('detail', ''):
            print("⚠️  Brand already exists, updating...")
            response = requests.put(f"{API_BASE}/agent-brand/{agent_id}", json=brand_data)

        response.raise_for_status()
        brand_result = response.json()

        print(f"✅ Signature Realty brand created successfully!")
        print(f"   Brand ID: {brand_result['id']}")
        print(f"   Company: {brand_result['company_name']}")
        print(f"   Tagline: {brand_result['tagline']}")
        print(f"   Colors: {brand_result['primary_color']} (primary), {brand_result['secondary_color']} (secondary)")
        print()

    except requests.exceptions.HTTPError as e:
        print(f"❌ Error creating brand: {e}")
        print(f"   Response: {e.response.text if e.response else 'No response'}")
        return

    # Step 3: Generate Preview
    print("Step 3: Generating brand preview...")
    try:
        response = requests.post(f"{API_BASE}/agent-brand/{agent_id}/generate-preview")
        response.raise_for_status()
        preview_result = response.json()

        print(f"✅ Preview generated!")
        print(f"   Voice Summary: {preview_result.get('voice_summary', 'N/A')}")
        print()

        # Save HTML preview to file
        with open(PREVIEW_OUTPUT_PATH, 'w') as f:
            f.write(preview_result['html_preview'])
        print(f"💾 HTML preview saved to: {PREVIEW_OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
        print()

    except requests.exceptions.HTTPError as e:
        print(f"❌ Error generating preview: {e}")
        print()

    # Step 4: Get the complete brand profile
    print("Step 4: Retrieving complete brand profile...")
    try:
        response = requests.get(f"{API_BASE}/agent-brand/{agent_id}")
        response.raise_for_status()
        brand_profile = response.json()

        print(f"✅ Complete brand profile retrieved!")
        print(f"   ID: {brand_profile['id']}")
        print(f"   Agent ID: {brand_profile['agent_id']}")
        print(f"   Company: {brand_profile['company_name']}")
        print(f"   Tagline: {brand_profile['tagline']}")
        print(f"   Website: {brand_profile['website_url']}")
        print(f"   Phone: {brand_profile['display_phone']}")
        print(f"   Email: {brand_profile['display_email']}")
        print(f"   Office: {brand_profile['office_address']}")
        print()
        print(f"   Brand Colors:")
        print(f"      Primary:    {brand_profile['primary_color']}")
        print(f"      Secondary:  {brand_profile['secondary_color']}")
        print(f"      Accent:     {brand_profile['accent_color']}")
        print(f"      Background: {brand_profile['background_color']}")
        print(f"      Text:       {brand_profile['text_color']}")
        print()
        print(f"   Specialties: {', '.join(brand_profile['specialties'] or [])}")

        service_areas_list = [f"{a['city']}, {a['state']}" for a in (brand_profile['service_areas'] or [])]
        print(f"   Service Areas: {', '.join(service_areas_list)}")
        print(f"   Languages: {', '.join(brand_profile['languages'] or [])}")
        print()

    except requests.exceptions.HTTPError as e:
        print(f"❌ Error retrieving brand profile: {e}")
        print()

    print("=" * 60)
    print("🎉 Signature Realty setup complete!")
    print("=" * 60)
    print()
    print("You can now:")
    print(f"  • View the brand: GET /agent-brand/{agent_id}")
    print(f"  • Update the brand: PUT /agent-brand/{agent_id}")
    print(f"  • Generate preview: POST /agent-brand/{agent_id}/generate-preview")
    print(f"  • Apply color presets: POST /agent-brand/{agent_id}/apply-preset")
    print(f"  • Get public profile: GET /agent-brand/public/{agent_id}")
    print()

if __name__ == "__main__":
    setup_signature_realty()

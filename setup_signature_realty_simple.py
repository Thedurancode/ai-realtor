#!/usr/bin/env python3
"""
Setup Signature Realty Brand - Simple version with proper imports
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import ALL models first to avoid relationship errors
from app.database import SessionLocal
from app.models.agent import Agent
from app.models.agent_brand import AgentBrand
from app.models.property import Property

def setup_signature_realty():
    """Create agent and brand for Signature Realty"""

    db = SessionLocal()

    try:
        # Check for existing agent
        agent = db.query(Agent).filter(Agent.email == 'jane@signaturerealty.com').first()

        if not agent:
            # Create agent
            agent = Agent(
                name='Jane Doe',
                email='jane@signaturerealty.com',
                phone='+14155551234',
                license_number='CA-12345678'
            )
            db.add(agent)
            db.commit()
            db.refresh(agent)
            print(f'✅ Created agent: {agent.name} (ID: {agent.id})')
        else:
            print(f'✅ Using existing agent: {agent.name} (ID: {agent.id})')

        # Check for existing brand
        existing_brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent.id).first()

        if existing_brand:
            print(f'⚠️  Brand already exists, updating...')
            brand = existing_brand
        else:
            print('Creating new brand...')
            brand = AgentBrand(agent_id=agent.id)
            db.add(brand)

        # Update brand fields
        brand.company_name = 'Signature Realty'
        brand.tagline = 'Your Dream Home Awaits'
        brand.logo_url = 'https://signaturerealty.com/logo.png'
        brand.website_url = 'https://signaturerealty.com'

        brand.bio = 'Signature Realty specializes in luxury residential properties in the greater Bay Area. With over 15 years of experience, we help clients find their perfect home.'
        brand.about_us = 'Founded in 2010, Signature Realty has helped over 500 families find their dream homes. Our commitment to excellence and personalized service sets us apart.'
        brand.specialties = ['Luxury Homes', 'First-Time Buyers', 'Investment Properties', 'Relocation']
        brand.service_areas = [
            {'city': 'San Francisco', 'state': 'CA'},
            {'city': 'Palo Alto', 'state': 'CA'},
            {'city': 'Mountain View', 'state': 'CA'}
        ]
        brand.languages = ['English', 'Spanish']

        # Luxury Gold color scheme
        brand.primary_color = '#B45309'
        brand.secondary_color = '#D97706'
        brand.accent_color = '#F59E0B'
        brand.background_color = '#FFFBEB'
        brand.text_color = '#78350F'

        brand.display_phone = '+1 (415) 555-1234'
        brand.display_email = 'hello@signaturerealty.com'
        brand.office_address = '123 Market Street, Suite 500, San Francisco, CA 94105'
        brand.office_phone = '+1 (415) 555-1000'

        brand.social_media = {
            'facebook': 'https://facebook.com/signaturerealty',
            'instagram': 'https://instagram.com/signaturerealty',
            'linkedin': 'https://linkedin.com/company/signaturerealty',
            'twitter': 'https://twitter.com/signaturerealty'
        }

        brand.license_display_name = 'Jane Doe - CA BRE #12345678'
        brand.license_number = 'CA-12345678'
        brand.license_states = ['CA']

        brand.show_profile = True
        brand.show_contact_info = True
        brand.show_social_media = True

        brand.email_template_style = 'modern'
        brand.report_logo_placement = 'top-left'

        brand.meta_title = 'Signature Realty - Luxury Homes in San Francisco Bay Area'
        brand.meta_description = 'Find your dream home with Signature Realty. Specializing in luxury residential properties in San Francisco, Palo Alto, and Mountain View.'
        brand.keywords = ['luxury real estate', 'San Francisco homes', 'Bay Area real estate', 'signature realty']

        brand.google_analytics_id = 'UA-123456789-1'
        brand.facebook_pixel_id = '1234567890'

        db.commit()
        db.refresh(brand)

        print()
        print('🎉 Signature Realty brand setup complete!')
        print()
        print(f'   Agent ID: {agent.id}')
        print(f'   Brand ID: {brand.id}')
        print(f'   Company: {brand.company_name}')
        print(f'   Tagline: {brand.tagline}')
        print()
        print(f'   Brand Colors (Luxury Gold):')
        print(f'      Primary:    {brand.primary_color}')
        print(f'      Secondary:  {brand.secondary_color}')
        print(f'      Accent:     {brand.accent_color}')
        print(f'      Background: {brand.background_color}')
        print(f'      Text:       {brand.text_color}')
        print()
        print(f'   Contact Information:')
        print(f'      Phone: {brand.display_phone}')
        print(f'      Email: {brand.display_email}')
        print(f'      Office: {brand.office_address}')
        print()
        print(f'   Online Presence:')
        print(f'      Website: {brand.website_url}')
        print(f'      Facebook: {brand.social_media["facebook"]}')
        print(f'      Instagram: {brand.social_media["instagram"]}')
        print()
        print(f'   Specialties: {", ".join(brand.specialties)}')

        service_areas_formatted = ", ".join([f'{a["city"]}, {a["state"]}' for a in brand.service_areas])
        print(f'   Service Areas: {service_areas_formatted}')
        print(f'   Languages: {", ".join(brand.languages)}')
        print()

        return agent, brand

    except Exception as e:
        db.rollback()
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return None, None

    finally:
        db.close()

if __name__ == "__main__":
    agent, brand = setup_signature_realty()

    if agent and brand:
        print("=" * 60)
        print("🎯 Next Steps:")
        print("=" * 60)
        print()
        print("You can now use the Signature Realty brand in:")
        print(f"  • Facebook Ads: POST /facebook-ads/campaigns/generate?agent_id={agent.id}")
        print(f"  • Social Media: POST /postiz/posts/create?agent_id={agent.id}")
        print(f"  • View Brand: GET /agent-brand/{agent.id}")
        print(f"  • Generate Preview: POST /agent-brand/{agent.id}/generate-preview")
        print(f"  • Get Public Profile: GET /agent-brand/public/{agent.id}")
        print()

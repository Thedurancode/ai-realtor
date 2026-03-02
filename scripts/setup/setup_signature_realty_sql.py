#!/usr/bin/env python3
"""
Setup Signature Realty Brand - Using direct SQL to avoid model issues
"""
import os
import psycopg2
from urllib.parse import urlparse

# Get database URL from environment
database_url = os.environ.get('DATABASE_URL')

if not database_url:
    print("❌ DATABASE_URL environment variable not set")
    print("Please set it like: export DATABASE_URL='postgresql://...'")
    exit(1)

# Parse the database URL
parsed = urlparse(database_url)

db_kwargs = {
    'dbname': parsed.path[1:],  # Remove leading slash
    'user': parsed.username,
    'password': parsed.password,
    'host': parsed.hostname,
    'port': parsed.port or 5432
}

try:
    # Connect to database
    conn = psycopg2.connect(**db_kwargs)
    cur = conn.cursor()

    print("✅ Connected to database")

    # Check for existing agent
    cur.execute("SELECT id, name, email FROM agents WHERE email = %s", ('jane@signaturerealty.com',))
    agent_result = cur.fetchone()

    if agent_result:
        agent_id = agent_result[0]
        agent_name = agent_result[1]
        print(f"✅ Using existing agent: {agent_name} (ID: {agent_id})")
    else:
        # Create new agent
        cur.execute("""
            INSERT INTO agents (name, email, phone, license_number)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name
        """, ('Jane Doe', 'jane@signaturerealty.com', '+14155551234', 'CA-12345678'))

        agent_id, agent_name = cur.fetchone()
        print(f"✅ Created agent: {agent_name} (ID: {agent_id})")

    # Check for existing brand
    cur.execute("SELECT id, company_name FROM agent_brands WHERE agent_id = %s", (agent_id,))
    brand_result = cur.fetchone()

    if brand_result:
        brand_id = brand_result[0]
        print(f"⚠️  Brand already exists (ID: {brand_id}), updating...")
        update = True
    else:
        print("Creating new brand...")
        update = False

    # Brand data
    brand_data = {
        'agent_id': agent_id,
        'company_name': 'Signature Realty',
        'tagline': 'Your Dream Home Awaits',
        'logo_url': 'https://signaturerealty.com/logo.png',
        'website_url': 'https://signaturerealty.com',
        'bio': 'Signature Realty specializes in luxury residential properties in the greater Bay Area. With over 15 years of experience, we help clients find their perfect home.',
        'about_us': 'Founded in 2010, Signature Realty has helped over 500 families find their dream homes. Our commitment to excellence and personalized service sets us apart.',
        'specialties': ['Luxury Homes', 'First-Time Buyers', 'Investment Properties', 'Relocation'],
        'service_areas': [
            {'city': 'San Francisco', 'state': 'CA'},
            {'city': 'Palo Alto', 'state': 'CA'},
            {'city': 'Mountain View', 'state': 'CA'}
        ],
        'languages': ['English', 'Spanish'],
        'primary_color': '#B45309',
        'secondary_color': '#D97706',
        'accent_color': '#F59E0B',
        'background_color': '#FFFBEB',
        'text_color': '#78350F',
        'display_phone': '+1 (415) 555-1234',
        'display_email': 'hello@signaturerealty.com',
        'office_address': '123 Market Street, Suite 500, San Francisco, CA 94105',
        'office_phone': '+1 (415) 555-1000',
        'social_media': {
            'facebook': 'https://facebook.com/signaturerealty',
            'instagram': 'https://instagram.com/signaturerealty',
            'linkedin': 'https://linkedin.com/company/signaturerealty',
            'twitter': 'https://twitter.com/signaturerealty'
        },
        'license_display_name': 'Jane Doe - CA BRE #12345678',
        'license_number': 'CA-12345678',
        'license_states': ['CA'],
        'show_profile': True,
        'show_contact_info': True,
        'show_social_media': True,
        'email_template_style': 'modern',
        'report_logo_placement': 'top-left',
        'meta_title': 'Signature Realty - Luxury Homes in San Francisco Bay Area',
        'meta_description': 'Find your dream home with Signature Realty. Specializing in luxury residential properties in San Francisco, Palo Alto, and Mountain View.',
        'keywords': ['luxury real estate', 'San Francisco homes', 'Bay Area real estate', 'signature realty'],
        'google_analytics_id': 'UA-123456789-1',
        'facebook_pixel_id': '1234567890'
    }

    import json

    if update:
        # Update existing brand
        cur.execute("""
            UPDATE agent_brands SET
                company_name = %s,
                tagline = %s,
                logo_url = %s,
                website_url = %s,
                bio = %s,
                about_us = %s,
                specialties = %s,
                service_areas = %s,
                languages = %s,
                primary_color = %s,
                secondary_color = %s,
                accent_color = %s,
                background_color = %s,
                text_color = %s,
                display_phone = %s,
                display_email = %s,
                office_address = %s,
                office_phone = %s,
                social_media = %s,
                license_display_name = %s,
                license_number = %s,
                license_states = %s,
                show_profile = %s,
                show_contact_info = %s,
                show_social_media = %s,
                email_template_style = %s,
                report_logo_placement = %s,
                meta_title = %s,
                meta_description = %s,
                keywords = %s,
                google_analytics_id = %s,
                facebook_pixel_id = %s,
                updated_at = NOW()
            WHERE agent_id = %s
            RETURNING id
        """, (
            brand_data['company_name'],
            brand_data['tagline'],
            brand_data['logo_url'],
            brand_data['website_url'],
            brand_data['bio'],
            brand_data['about_us'],
            json.dumps(brand_data['specialties']),
            json.dumps(brand_data['service_areas']),
            json.dumps(brand_data['languages']),
            brand_data['primary_color'],
            brand_data['secondary_color'],
            brand_data['accent_color'],
            brand_data['background_color'],
            brand_data['text_color'],
            brand_data['display_phone'],
            brand_data['display_email'],
            brand_data['office_address'],
            brand_data['office_phone'],
            json.dumps(brand_data['social_media']),
            brand_data['license_display_name'],
            brand_data['license_number'],
            json.dumps(brand_data['license_states']),
            brand_data['show_profile'],
            brand_data['show_contact_info'],
            brand_data['show_social_media'],
            brand_data['email_template_style'],
            brand_data['report_logo_placement'],
            brand_data['meta_title'],
            brand_data['meta_description'],
            json.dumps(brand_data['keywords']),
            brand_data['google_analytics_id'],
            brand_data['facebook_pixel_id'],
            agent_id
        ))

        brand_id = cur.fetchone()[0]

    else:
        # Create new brand
        cur.execute("""
            INSERT INTO agent_brands (
                agent_id, company_name, tagline, logo_url, website_url,
                bio, about_us, specialties, service_areas, languages,
                primary_color, secondary_color, accent_color, background_color, text_color,
                display_phone, display_email, office_address, office_phone,
                social_media, license_display_name, license_number, license_states,
                show_profile, show_contact_info, show_social_media,
                email_template_style, report_logo_placement,
                meta_title, meta_description, keywords,
                google_analytics_id, facebook_pixel_id
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s
            )
            RETURNING id
        """, (
            agent_id,
            brand_data['company_name'],
            brand_data['tagline'],
            brand_data['logo_url'],
            brand_data['website_url'],
            brand_data['bio'],
            brand_data['about_us'],
            json.dumps(brand_data['specialties']),
            json.dumps(brand_data['service_areas']),
            json.dumps(brand_data['languages']),
            brand_data['primary_color'],
            brand_data['secondary_color'],
            brand_data['accent_color'],
            brand_data['background_color'],
            brand_data['text_color'],
            brand_data['display_phone'],
            brand_data['display_email'],
            brand_data['office_address'],
            brand_data['office_phone'],
            json.dumps(brand_data['social_media']),
            brand_data['license_display_name'],
            brand_data['license_number'],
            json.dumps(brand_data['license_states']),
            brand_data['show_profile'],
            brand_data['show_contact_info'],
            brand_data['show_social_media'],
            brand_data['email_template_style'],
            brand_data['report_logo_placement'],
            brand_data['meta_title'],
            brand_data['meta_description'],
            json.dumps(brand_data['keywords']),
            brand_data['google_analytics_id'],
            brand_data['facebook_pixel_id']
        ))

        brand_id = cur.fetchone()[0]

    conn.commit()

    print()
    print('🎉 Signature Realty brand setup complete!')
    print()
    print(f'   Agent ID: {agent_id}')
    print(f'   Brand ID: {brand_id}')
    print(f'   Company: {brand_data["company_name"]}')
    print(f'   Tagline: {brand_data["tagline"]}')
    print()
    print(f'   Brand Colors (Luxury Gold):')
    print(f'      Primary:    {brand_data["primary_color"]}')
    print(f'      Secondary:  {brand_data["secondary_color"]}')
    print(f'      Accent:     {brand_data["accent_color"]}')
    print(f'      Background: {brand_data["background_color"]}')
    print(f'      Text:       {brand_data["text_color"]}')
    print()
    print(f'   Contact Information:')
    print(f'      Phone: {brand_data["display_phone"]}')
    print(f'      Email: {brand_data["display_email"]}')
    print(f'      Office: {brand_data["office_address"]}')
    print()
    print(f'   Online Presence:')
    print(f'      Website: {brand_data["website_url"]}')
    print(f'      Facebook: {brand_data["social_media"]["facebook"]}')
    print(f'      Instagram: {brand_data["social_media"]["instagram"]}')
    print()
    print(f'   Specialties: {", ".join(brand_data["specialties"])}')
    print(f'   Languages: {", ".join(brand_data["languages"])}')
    print()

    print("=" * 60)
    print("🎯 Next Steps:")
    print("=" * 60)
    print()
    print("You can now use the Signature Realty brand in:")
    print(f"  • Facebook Ads: POST /facebook-ads/campaigns/generate?agent_id={agent_id}")
    print(f"  • Social Media: POST /postiz/posts/create?agent_id={agent_id}")
    print(f"  • View Brand: GET /agent-brand/{agent_id}")
    print(f"  • Generate Preview: POST /agent-brand/{agent_id}/generate-preview")
    print(f"  • Get Public Profile: GET /agent-brand/public/{agent_id}")
    print()

    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

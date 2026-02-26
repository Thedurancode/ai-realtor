#!/usr/bin/env python3
"""
Create a Facebook Ad Campaign for Signature Realty
"""
import os
import psycopg2
from urllib.parse import urlparse
import json

# Get database URL from environment
database_url = os.environ.get('DATABASE_URL')

if not database_url:
    print("❌ DATABASE_URL environment variable not set")
    exit(1)

# Parse the database URL
parsed = urlparse(database_url)

db_kwargs = {
    'dbname': parsed.path[1:],
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
    print()

    # Get Signature Realty brand
    agent_id = 3
    cur.execute("""
        SELECT id, company_name, tagline, logo_url, website_url,
               primary_color, secondary_color, accent_color,
               display_phone, display_email, bio
        FROM agent_brands
        WHERE agent_id = %s
    """, (agent_id,))

    brand = cur.fetchone()

    if not brand:
        print("❌ Signature Realty brand not found")
        exit(1)

    brand_id = brand[0]
    company_name = brand[1]
    tagline = brand[2]
    logo_url = brand[3]
    website_url = brand[4]
    primary_color = brand[5]
    secondary_color = brand[6]
    accent_color = brand[7]
    display_phone = brand[8]
    display_email = brand[9]
    bio = brand[10]

    print(f"🎨 Using brand: {company_name}")
    print(f"   Tagline: {tagline}")
    print(f"   Colors: {primary_color} (primary), {secondary_color} (secondary)")
    print()

    # Get a property to feature in the ad
    cur.execute("""
        SELECT id, address, city, state, price, bedrooms, bathrooms,
               square_feet, property_type, description
        FROM properties
        ORDER BY id
        LIMIT 1
    """)

    property = cur.fetchone()

    if not property:
        print("❌ No properties found")
        exit(1)

    prop_id = property[0]
    address = property[1]
    city = property[2]
    state = property[3]
    price = property[4]
    bedrooms = property[5] or 0
    bathrooms = property[6] or 0
    sqft = property[7] or 0
    prop_type = property[8]
    description = property[9]

    print(f"🏠 Featuring property: {address}, {city} {state}")
    print(f"   Price: ${price:,.0f}")
    print(f"   Beds: {bedrooms}, Baths: {bathrooms}, Sqft: {sqft}")
    print()

    # Create Facebook ad campaign
    print("📱 Creating Facebook Ad Campaign...")
    print()

    # Generate campaign data
    campaign_data = {
        'agent_id': agent_id,
        'campaign_name': f'Signature Realty - {city} Luxury Property',
        'campaign_objective': 'leads',
        'property_id': prop_id,
        'property_url': f'{website_url}/properties/{prop_id}',
        'daily_budget': 100,
        'target_audience': {
            'age_min': 35,
            'age_max': 65,
            'genders': ['male', 'female'],
            'locations': [
                {'city': city, 'state': state, 'radius': 25}
            ],
            'interests': ['luxury real estate', 'home buying', 'investment property'],
            'behaviors': ['luxury shoppers', 'homeowners']
        },
        'ad_creative': {
            'headline': f'Luxury {bedrooms}Bed/{bathrooms}Bath Home in {city}',
            'primary_text': f'''
Discover {address} in {city}, {state}.

{bedrooms} Bedrooms | {bathrooms} Bathrooms | {sqft:,} sq ft
Price: ${price:,.0f}

{description or 'Stunning luxury property with premium finishes and modern amenities.'}

{tagline}

Contact us today for a private showing!
            '''.strip(),
            'headline_color': primary_color,
            'cta_text': 'Learn More',
            'cta_button_color': accent_color,
            'display_url': website_url,
            'brand_name': company_name,
            'logo_url': logo_url
        },
        'ad_format': 'single_image',
        'ad_placements': ['facebook_feed', 'instagram_feed', 'facebook_story'],
        'campaign_start_date': '2026-02-25',
        'campaign_end_date': '2026-03-10',
        'status': 'draft'
    }

    # Insert campaign into database
    cur.execute("""
        INSERT INTO facebook_campaigns (
            agent_id, campaign_name, campaign_objective, property_id,
            daily_budget, targeting_audience, ad_copy, ad_format,
            start_date, end_date,
            campaign_status, campaign_id_meta, created_at
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s,
            %s, %s, NOW()
        )
        RETURNING id
    """, (
        campaign_data['agent_id'],
        campaign_data['campaign_name'],
        campaign_data['campaign_objective'],
        campaign_data['property_id'],
        campaign_data['daily_budget'],
        json.dumps(campaign_data['target_audience']),
        json.dumps({'primary_text': campaign_data['ad_creative']['primary_text'], 'headline': campaign_data['ad_creative']['headline']}),
        campaign_data['ad_format'],
        campaign_data['campaign_start_date'],
        campaign_data['campaign_end_date'],
        campaign_data['status'],
        None  # campaign_id_meta (not yet launched)
    ))

    campaign_id = cur.fetchone()[0]
    conn.commit()

    print("✅ Facebook Ad Campaign Created Successfully!")
    print()
    print("=" * 60)
    print("📊 Campaign Details")
    print("=" * 60)
    print()
    print(f"   Campaign ID: {campaign_id}")
    print(f"   Name: {campaign_data['campaign_name']}")
    print(f"   Objective: {campaign_data['campaign_objective']}")
    print(f"   Daily Budget: ${campaign_data['daily_budget']}")
    print(f"   Status: {campaign_data['status']}")
    print()
    print("   🏠 Property:")
    print(f"      Address: {address}")
    print(f"      City: {city}, {state}")
    print(f"      Price: ${price:,.0f}")
    print(f"      Beds: {bedrooms} | Baths: {bathrooms} | Sqft: {sqft:,}")
    print()
    print("   👥 Target Audience:")
    print(f"      Age: {campaign_data['target_audience']['age_min']} - {campaign_data['target_audience']['age_max']}")
    print(f"      Location: {city}, {state} (25 mile radius)")
    print(f"      Interests: {', '.join(campaign_data['target_audience']['interests'])}")
    print()
    print("   🎨 Ad Creative:")
    print(f"      Headline: {campaign_data['ad_creative']['headline']}")
    print(f"      CTA: {campaign_data['ad_creative']['cta_text']}")
    print(f"      Placements: {', '.join(campaign_data['ad_placements'])}")
    print()
    print("   📅 Schedule:")
    print(f"      Start: {campaign_data['campaign_start_date']}")
    print(f"      End: {campaign_data['campaign_end_date']}")
    print()
    print("   🎯 Brand Colors Applied:")
    print(f"      Headline Color: {campaign_data['ad_creative']['headline_color']}")
    print(f"      CTA Button Color: {campaign_data['ad_creative']['cta_button_color']}")
    print()

    print("=" * 60)
    print("🚀 Next Steps")
    print("=" * 60)
    print()
    print("1. Review the campaign details above")
    print("2. Launch to Meta Ads Manager:")
    print(f"   POST /facebook-ads/campaigns/{campaign_id}/launch")
    print()
    print("3. Track performance:")
    print(f"   POST /facebook-ads/campaigns/{campaign_id}/track")
    print()
    print("4. View analytics:")
    print(f"   GET /facebook-ads/analytics/campaign/{campaign_id}")
    print()

    # Save campaign details to file
    with open('/Users/edduran/Documents/GitHub/ai-realtor/signature_realty_facebook_ad.json', 'w') as f:
        json.dump({
            'campaign_id': campaign_id,
            'campaign_data': campaign_data,
            'property': {
                'id': prop_id,
                'address': address,
                'city': city,
                'state': state,
                'price': price,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'square_feet': sqft
            },
            'brand': {
                'company_name': company_name,
                'tagline': tagline,
                'primary_color': primary_color,
                'secondary_color': secondary_color
            }
        }, f, indent=2)

    print(f"💾 Campaign details saved to: signature_realty_facebook_ad.json")
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

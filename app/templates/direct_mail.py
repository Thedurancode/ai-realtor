"""
Pre-built Direct Mail Templates for Real Estate

Collection of professional HTML templates for postcards and letters.
Designed for Lob.com specifications.
"""

# =========================================================================
# JUST SOLD POSTCARD TEMPLATES
# =========================================================================

JUST_SOLD_TEMPLATE = {
    "name": "Just Sold",
    "description": "Announce a recently sold property to the neighborhood",
    "template_type": "postcard",
    "campaign_type": "just_sold",
    "required_variables": ["property_address", "sold_price", "agent_name", "agent_phone"],
    "front_html": """
<div style="padding: 40px; font-family: 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; box-sizing: border-box;">
    <div style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center;">
        <h1 style="color: #1E40AF; font-size: 42px; margin: 0 0 10px 0; font-weight: 800;">JUST SOLD!</h1>
        <div style="width: 80px; height: 4px; background: #1E40AF; margin: 20px auto;"></div>

        {% if property_photo %}
        <div style="margin: 20px 0;">
            <img src="{{property_photo}}" style="width: 100%; max-width: 400px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        </div>
        {% endif %}

        <h2 style="color: #333; font-size: 28px; margin: 20px 0 10px 0;">
            {{property_address}}
        </h2>

        <p style="color: #666; font-size: 18px; margin: 10px 0;">
            Sold for <strong style="color: #1E40AF; font-size: 24px;">{{sold_price}}</strong>
        </p>

        <p style="color: #555; font-size: 16px; margin: 30px 0;">
            Curious about your home's value?<br>
            I'd love to help you find out!
        </p>

        <div style="background: #1E40AF; color: white; padding: 15px 30px; border-radius: 50px; display: inline-block; margin: 20px 0;">
            <strong style="font-size: 20px;">{{agent_name}}</strong>
        </div>

        <p style="color: #666; font-size: 16px; margin: 10px 0;">
            📞 {{agent_phone}}
        </p>
    </div>
</div>
    """,
    "back_html": """
<div style="padding: 40px; font-family: 'Helvetica Neue', Arial, sans-serif; background: #f8f9fa; height: 100%; box-sizing: border-box;">
    <div style="background: white; border-radius: 20px; padding: 40px; height: calc(100% - 80px);">
        <h2 style="color: #1E40AF; font-size: 32px; text-align: center; margin: 0 0 30px 0;">Recent Sales in Your Area</h2>

        <div style="border-left: 4px solid #1E40AF; padding-left: 20px; margin: 30px 0;">
            <p style="color: #333; font-size: 16px; margin: 0 0 5px 0;"><strong>Why I Love This Neighborhood:</strong></p>
            <p style="color: #666; font-size: 14px; margin: 0;">
                Great schools, low crime rate, and strong property values make this area one of the most desirable places to live.
            </p>
        </div>

        <div style="background: #f0f9ff; padding: 20px; border-radius: 10px; margin: 30px 0;">
            <p style="color: #1E40AF; font-size: 18px; margin: 0 0 10px 0; font-weight: bold;">Market Update</p>
            <p style="color: #555; font-size: 14px; margin: 0;">
                Homes in this area are selling <strong>{{days_on_market}}</strong> days on average, with values up <strong>{{appreciation}}%</strong> from last year.
            </p>
        </div>

        <div style="text-align: center; margin-top: 40px;">
            <p style="color: #666; font-size: 16px; margin: 0;">
                <strong>Thinking of selling?</strong><br>
                Get a free, no-obligation valuation.
            </p>
            <p style="color: #1E40AF; font-size: 20px; margin: 10px 0;">
                {{agent_name}}
            </p>
            <p style="color: #666; font-size: 14px; margin: 0;">
                📞 {{agent_phone}}
            </p>
        </div>
    </div>
</div>
    """
}

# =========================================================================
# OPEN HOUSE INVITATION
# =========================================================================

OPEN_HOUSE_TEMPLATE = {
    "name": "Open House Invitation",
    "description": "Invite neighbors to an upcoming open house",
    "template_type": "postcard",
    "campaign_type": "open_house",
    "required_variables": ["property_address", "open_house_date", "open_house_time", "agent_name", "agent_phone"],
    "front_html": """
<div style="padding: 40px; font-family: 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(to bottom, #ff6b6b, #ee5a6f); height: 100%; box-sizing: border-box;">
    <div style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center;">
        <h1 style="color: #c92a2a; font-size: 36px; margin: 0 0 10px 0;">YOU'RE INVITED!</h1>

        <div style="background: #ffe5e5; padding: 15px; border-radius: 10px; margin: 20px 0;">
            <h2 style="color: #c92a2a; font-size: 24px; margin: 0 0 10px 0;">🏠 Open House</h2>
            <p style="color: #333; font-size: 20px; margin: 10px 0; font-weight: bold;">{{property_address}}</p>
        </div>

        <div style="margin: 30px 0;">
            <p style="color: #666; font-size: 18px; margin: 5px 0;">
                📅 <strong>{{open_house_date}}</strong>
            </p>
            <p style="color: #666; font-size: 18px; margin: 5px 0;">
                ⏰ <strong>{{open_house_time}}</strong>
            </p>
        </div>

        {% if property_photo %}
        <div style="margin: 20px 0;">
            <img src="{{property_photo}}" style="width: 100%; max-width: 400px; border-radius: 10px;">
        </div>
        {% endif %}

        <p style="color: #555; font-size: 16px; margin: 20px 0;">
            Come tour this beautiful property!<br>
            Refreshments will be served.
        </p>

        <div style="background: #c92a2a; color: white; padding: 15px 30px; border-radius: 50px; display: inline-block;">
            <strong style="font-size: 18px;">{{agent_name}}</strong>
        </div>

        <p style="color: #666; font-size: 14px; margin: 10px 0;">
            📞 {{agent_phone}}
        </p>
    </div>
</div>
    """,
    "back_html": None
}

# =========================================================================
# MARKET UPDATE POSTCARD
# =========================================================================

MARKET_UPDATE_TEMPLATE = {
    "name": "Market Update",
    "description": "Quarterly market statistics for a farm area",
    "template_type": "postcard",
    "campaign_type": "market_update",
    "required_variables": ["neighborhood", "quarter", "year", "avg_price", "days_on_market", "homes_sold", "agent_name", "agent_phone"],
    "front_html": """
<div style="padding: 40px; font-family: 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); height: 100%; box-sizing: border-box;">
    <div style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center;">
        <h1 style="color: #11998e; font-size: 36px; margin: 0 0 10px 0;">Q{{quarter}} {{year}} Market Update</h1>
        <h2 style="color: #333; font-size: 24px; margin: 0 0 30px 0;">{{neighborhood}}</h2>

        <div style="display: flex; justify-content: space-around; margin: 30px 0; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 120px; padding: 15px;">
                <p style="color: #11998e; font-size: 32px; font-weight: bold; margin: 0;">{{avg_price}}</p>
                <p style="color: #666; font-size: 14px; margin: 5px 0;">Average Price</p>
            </div>
            <div style="flex: 1; min-width: 120px; padding: 15px;">
                <p style="color: #11998e; font-size: 32px; font-weight: bold; margin: 0;">{{days_on_market}}</p>
                <p style="color: #666; font-size: 14px; margin: 5px 0;">Days on Market</p>
            </div>
            <div style="flex: 1; min-width: 120px; padding: 15px;">
                <p style="color: #11998e; font-size: 32px; font-weight: bold; margin: 0;">{{homes_sold}}</p>
                <p style="color: #666; font-size: 14px; margin: 5px 0;">Homes Sold</p>
            </div>
        </div>

        <p style="color: #555; font-size: 16px; margin: 30px 0;">
            What's your home worth in today's market?<br>
            I'd love to provide you with a free valuation.
        </p>

        <div style="background: #11998e; color: white; padding: 15px 30px; border-radius: 50px; display: inline-block;">
            <strong style="font-size: 18px;">{{agent_name}}</strong>
        </div>

        <p style="color: #666; font-size: 14px; margin: 10px 0;">
            📞 {{agent_phone}}
        </p>
    </div>
</div>
    """,
    "back_html": None
}

# =========================================================================
# NEW LISTING ANNOUNCEMENT
# =========================================================================

NEW_LISTING_TEMPLATE = {
    "name": "New Listing",
    "description": "Announce a new property listing to the neighborhood",
    "template_type": "postcard",
    "campaign_type": "new_listing",
    "required_variables": ["property_address", "property_price", "bedrooms", "bathrooms", "property_photo", "agent_name", "agent_phone"],
    "front_html": """
<div style="padding: 40px; font-family: 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); height: 100%; box-sizing: border-box;">
    <div style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center;">
        <div style="background: #ffe5f9; padding: 10px 20px; border-radius: 50px; display: inline-block; margin-bottom: 20px;">
            <span style="color: #c44569; font-size: 14px; font-weight: bold; letter-spacing: 2px;">NEW LISTING</span>
        </div>

        <h1 style="color: #c44569; font-size: 36px; margin: 0 0 10px 0;">Just Listed!</h1>

        {% if property_photo %}
        <div style="margin: 20px 0;">
            <img src="{{property_photo}}" style="width: 100%; max-width: 400px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        </div>
        {% endif %}

        <h2 style="color: #333; font-size: 24px; margin: 20px 0 10px 0;">
            {{property_address}}
        </h2>

        <div style="display: flex; justify-content: center; gap: 30px; margin: 20px 0; flex-wrap: wrap;">
            <div>
                <span style="color: #c44569; font-size: 20px;">{{bedrooms}}</span> 🛏️
            </div>
            <div>
                <span style="color: #c44569; font-size: 20px;">{{bathrooms}}</span> 🚿
            </div>
        </div>

        <p style="color: #666; font-size: 18px; margin: 20px 0;">
            <strong>Listed at:</strong> <span style="color: #c44569; font-size: 24px; font-weight: bold;">{{property_price}}</span>
        </p>

        <p style="color: #555; font-size: 16px; margin: 30px 0;">
            Beautiful home in a great neighborhood!<br>
            Schedule your private tour today.
        </p>

        <div style="background: #c44569; color: white; padding: 15px 30px; border-radius: 50px; display: inline-block;">
            <strong style="font-size: 18px;">{{agent_name}}</strong>
        </div>

        <p style="color: #666; font-size: 14px; margin: 10px 0;">
            📞 {{agent_phone}}
        </p>
    </div>
</div>
    """,
    "back_html": None
}

# =========================================================================
# PRICE REDUCTION
# =========================================================================

PRICE_REDUCTION_TEMPLATE = {
    "name": "Price Reduction",
    "description": "Announce a price reduction on a listing",
    "template_type": "postcard",
    "campaign_type": "price_reduction",
    "required_variables": ["property_address", "original_price", "new_price", "savings", "property_photo", "agent_name", "agent_phone"],
    "front_html": """
<div style="padding: 40px; font-family: 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); height: 100%; box-sizing: border-box;">
    <div style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center;">
        <h1 style="color: #d97706; font-size: 36px; margin: 0 0 10px 0;">PRICE REDUCED!</h1>

        {% if property_photo %}
        <div style="margin: 20px 0;">
            <img src="{{property_photo}}" style="width: 100%; max-width: 400px; border-radius: 10px;">
        </div>
        {% endif %}

        <h2 style="color: #333; font-size: 24px; margin: 20px 0 10px 0;">
            {{property_address}}
        </h2>

        <div style="background: #fef3c7; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <p style="color: #666; font-size: 16px; margin: 0;">Previously:</p>
            <p style="color: #999; font-size: 20px; text-decoration: line-through; margin: 5px 0;">{{original_price}}</p>
            <p style="color: #666; font-size: 16px; margin: 10px 0;">Now:</p>
            <p style="color: #d97706; font-size: 28px; font-weight: bold; margin: 5px 0;">{{new_price}}</p>
            <p style="color: #d97706; font-size: 18px; font-weight: bold; margin: 10px 0;">You save {{savings}}!</p>
        </div>

        <p style="color: #555; font-size: 16px; margin: 30px 0;">
            Don't miss this opportunity!<br>
            Schedule a showing today.
        </p>

        <div style="background: #d97706; color: white; padding: 15px 30px; border-radius: 50px; display: inline-block;">
            <strong style="font-size: 18px;">{{agent_name}}</strong>
        </div>

        <p style="color: #666; font-size: 14px; margin: 10px 0;">
            📞 {{agent_phone}}
        </p>
    </div>
</div>
    """,
    "back_html": None
}

# =========================================================================
# HELLO / FARMING POSTCARD
# =========================================================================

HELLO_FARMING_TEMPLATE = {
    "name": "Hello / Farming",
    "description": "Introduction to agent and farming a neighborhood",
    "template_type": "postcard",
    "campaign_type": "hello",
    "required_variables": ["agent_name", "agent_title", "agent_photo", "agent_phone", "agent_email", "brokerage"],
    "front_html": """
<div style="padding: 40px; font-family: 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%); height: 100%; box-sizing: border-box;">
    <div style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center;">
        <h1 style="color: #0ea5e9; font-size: 36px; margin: 0 0 30px 0;">Hello Neighbor!</h1>

        {% if agent_photo %}
        <div style="margin: 0 auto 30px; width: 150px; height: 150px; border-radius: 50%; overflow: hidden;">
            <img src="{{agent_photo}}" style="width: 100%; height: 100%; object-fit: cover;">
        </div>
        {% endif %}

        <h2 style="color: #333; font-size: 24px; margin: 0 0 10px 0;">{{agent_name}}</h2>
        <p style="color: #666; font-size: 18px; margin: 0 0 30px 0;">{{agent_title}}</p>
        <p style="color: #555; font-size: 16px; margin: 0 0 30px 0;">{{brokerage}}</p>

        <div style="background: #e0f7fa; padding: 20px; border-radius: 10px; margin: 30px 0;">
            <p style="color: #0ea5e9; font-size: 16px; margin: 0; font-weight: bold;">About Me</p>
            <p style="color: #555; font-size: 14px; margin: 10px 0;">
                As your local real estate expert, I'm here to help with all your property needs. Whether you're buying, selling, or just curious about the market, I'm happy to help!
            </p>
        </div>

        <p style="color: #555; font-size: 16px; margin: 30px 0;">
            Questions about real estate?<br>
            Feel free to reach out!
        </p>

        <p style="color: #0ea5e9; font-size: 20px; margin: 10px 0;">{{agent_name}}</p>
        <p style="color: #666; font-size: 14px; margin: 5px 0;">📞 {{agent_phone}}</p>
        <p style="color: #666; font-size: 14px; margin: 5px 0;">✉️ {{agent_email}}</p>
    </div>
</div>
    """,
    "back_html": None
}


# =========================================================================
# INTERESTED IN SELLING TEMPLATE
# =========================================================================

INTERESTED_IN_SELLING_TEMPLATE = {
    "name": "Interested in Selling?",
    "description": "Lead generation postcard asking homeowners if they're interested in selling",
    "template_type": "postcard",
    "campaign_type": "lead_generation",
    "required_variables": ["property_address", "agent_name", "agent_phone", "agent_email", "brokerage"],
    "front_html": """
<div style="padding: 40px; font-family: 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); height: 100%; box-sizing: border-box;">
    <div style="background: white; border-radius: 20px; padding: 40px 30px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center;">

        <!-- Eye-catching header -->
        <h1 style="color: #e91e63; font-size: 42px; margin: 0 0 10px 0; font-weight: 900; letter-spacing: -1px;">
            ARE YOU INTERESTED
        </h1>
        <h1 style="color: #e91e63; font-size: 42px; margin: 0 0 30px 0; font-weight: 900; letter-spacing: -1px;">
            IN SELLING?
        </h1>

        <div style="width: 100px; height: 4px; background: #e91e63; margin: 0 auto 40px;"></div>

        <!-- Property address -->
        <div style="background: #fce4ec; padding: 20px; border-radius: 15px; margin: 0 0 30px;">
            <p style="color: #666; font-size: 14px; margin: 0 0 5px; text-transform: uppercase; letter-spacing: 1px;">
                Your Home at
            </p>
            <h2 style="color: #333; font-size: 32px; margin: 0; font-weight: 700;">
                {{property_address}}
            </h2>
        </div>

        <!-- Main message -->
        <p style="color: #555; font-size: 18px; margin: 0 0 20px; line-height: 1.5;">
            The real estate market is <strong>hot right now!</strong> Home values are up, and buyers are looking for properties like yours.
        </p>

        <div style="background: #fff3e0; padding: 25px; border-radius: 15px; margin: 30px 0; border-left: 5px solid #ff9800;">
            <p style="color: #e65100; font-size: 17px; margin: 0 0 15px; font-weight: bold;">
                🏠 Curious About Your Home's Value?
            </p>
            <p style="color: #555; font-size: 15px; margin: 0; line-height: 1.6;">
                I can provide you with a <strong>FREE, no-obligation</strong> market analysis of your property's current value. No pressure, just information.
            </p>
        </div>

        <div style="background: #e8f5e9; padding: 25px; border-radius: 15px; margin: 30px 0; border-left: 5px solid #4caf50;">
            <p style="color: #2e7d32; font-size: 17px; margin: 0 0 15px; font-weight: bold;">
                💰 Ready to Sell? We Make It Easy!
            </p>
            <p style="color: #555; font-size: 15px; margin: 0; line-height: 1.6;">
                <strong>We handle everything:</strong><br>
                Professional photography • Marketing • Showings • Negotiations • Closing
            </p>
        </div>

        <!-- Call to action -->
        <div style="margin: 40px 0;">
            <p style="color: #e91e63; font-size: 20px; margin: 0 0 15px; font-weight: 800;">
                Let's Chat! No Pressure, Just Conversation.
            </p>
            <p style="color: #666; font-size: 16px; margin: 0;">
                Call or text anytime, or email me for your free home value report.
            </p>
        </div>

        <!-- Agent info -->
        <div style="background: #f5f5f5; padding: 25px; border-radius: 15px;">
            <h3 style="color: #333; font-size: 28px; margin: 0 0 5px;">{{agent_name}}</h3>
            <p style="color: #666; font-size: 16px; margin: 0 0 15px;">{{brokerage}}</p>

            <div style="margin-top: 20px;">
                <p style="color: #e91e63; font-size: 22px; margin: 0; font-weight: 700;">📞 {{agent_phone}}</p>
                <p style="color: #666; font-size: 16px; margin: 10px 0;">✉️ {{agent_email}}</p>
            </div>
        </div>

        <!-- Bottom note -->
        <p style="color: #999; font-size: 12px; margin: 40px 0 0; font-style: italic;">
            This is not a solicitation if your property is currently listed. We respect your privacy and can remove you from our mailing list upon request.
        </p>
    </div>
</div>
    """,
    "back_html": """
<div style="padding: 40px; font-family: 'Helvetica Neue', Arial, sans-serif; background: #f5f5f5; height: 100%; box-sizing: border-box;">
    <div style="background: white; border-radius: 20px; padding: 40px; height: 100%; box-sizing: border-box;">

        <h1 style="color: #e91e63; font-size: 36px; margin: 0 0 30px; text-align: center; font-weight: 800;">
            Why Work With Me?
        </h1>

        <!-- Value props -->
        <div style="margin: 0 0 30px;">
            <h3 style="color: #333; font-size: 22px; margin: 0 0 10px;">🎯 Local Expert</h3>
            <p style="color: #666; font-size: 15px; margin: 0; line-height: 1.6;">
                I know this neighborhood inside and out. I understand what buyers are looking for and how to position your home to get top dollar.
            </p>
        </div>

        <div style="margin: 0 0 30px;">
            <h3 style="color: #333; font-size: 22px; margin: 0 0 10px;">📊 Data-Driven Pricing</h3>
            <p style="color: #666; font-size: 15px; margin: 0; line-height: 1.6;">
                I use advanced market analytics to price your home strategically—not too high, not too low—just right to attract qualified buyers.
            </p>
        </div>

        <div style="margin: 0 0 30px;">
            <h3 style="color: #333; font-size: 22px; margin: 0 0 10px;">📱 Proactive Marketing</h3>
            <p style="color: #666; font-size: 15px; margin: 0; line-height: 1.6;">
                Your home gets maximum exposure across 100+ websites, social media, and our network of 10,000+ buyers.
            </p>
        </div>

        <div style="margin: 0 0 30px;">
            <h3 style="color: #333; font-size: 22px; margin: 0 0 10px;">💬 Clear Communication</h3>
            <p style="color: #666; font-size: 15px; margin: 0; line-height: 1.6;">
                You'll always know what's happening. I provide weekly updates and am available to answer your questions anytime.
            </p>
        </div>

        <div style="margin: 0 0 40px;">
            <h3 style="color: #333; font-size: 22px; margin: 0 0 10px;">🤝 Full-Service Support</h3>
            <p style="color: #666; font-size: 15px; margin: 0; line-height: 1.6;">
                From listing to closing, I handle every detail. You focus on your life while I handle selling your home.
            </p>
        </div>

        <!-- Testimonial placeholder -->
        <div style="background: #f9f9f9; padding: 25px; border-radius: 15px; margin: 30px 0; border-left: 5px solid #e91e63;">
            <p style="color: #555; font-size: 15px; margin: 0; font-style: italic; line-height: 1.6;">
                "{{agent_name}} made the entire process smooth and stress-free. We got multiple offers and sold above asking price!"
            </p>
            <p style="color: #999; font-size: 13px; margin: 10px 0 0;">— Happy Seller</p>
        </div>

        <!-- Contact CTA -->
        <div style="background: #e91e63; color: white; padding: 30px; border-radius: 15px; text-align: center;">
            <h3 style="font-size: 24px; margin: 0 0 15px;">Get Your Free Home Value Report</h3>
            <p style="font-size: 18px; margin: 0 0 20px;">
                Call or text today!
            </p>
            <p style="font-size: 28px; margin: 0; font-weight: 800;">{{agent_phone}}</p>
        </div>

        <!-- Footer -->
        <div style="text-align: center; margin-top: 40px;">
            <p style="color: #999; font-size: 14px; margin: 0;">{{agent_name}}</p>
            <p style="color: #999; font-size: 12px; margin: 5px 0;">{{brokerage}}</p>
            <p style="color: #ccc; font-size: 11px; margin: 20px 0 0;">
                Equal Housing Opportunity. This communication is not a solicitation if your property is currently listed.
            </p>
        </div>
    </div>
</div>
    """
}


# =========================================================================
# TEMPLATE REGISTRY
# =========================================================================

TEMPLATES = {
    "just_sold": JUST_SOLD_TEMPLATE,
    "open_house": OPEN_HOUSE_TEMPLATE,
    "market_update": MARKET_UPDATE_TEMPLATE,
    "new_listing": NEW_LISTING_TEMPLATE,
    "price_reduction": PRICE_REDUCTION_TEMPLATE,
    "hello": HELLO_FARMING_TEMPLATE,
    "interested_in_selling": INTERESTED_IN_SELLING_TEMPLATE
}


def get_template(template_name: str) -> dict:
    """
    Get a template by name

    Args:
        template_name: Name of the template

    Returns:
        Template dictionary with all fields

    Raises:
        ValueError: If template not found
    """
    template = TEMPLATES.get(template_name)
    if not template:
        available = ", ".join(TEMPLATES.keys())
        raise ValueError(f"Template '{template_name}' not found. Available: {available}")

    return template


def list_templates() -> List[dict]:
    """List all available templates"""
    return [
        {
            "name": name,
            "description": tmpl["description"],
            "type": tmpl["template_type"],
            "campaign": tmpl["campaign_type"]
        }
        for name, tmpl in TEMPLATES.items()
    ]


def render_template(template_html: str, variables: dict) -> str:
    """
    Render a template with variables

    Args:
        template_html: HTML template with {{variable}} placeholders
        variables: Dictionary of variables to merge

    Returns:
        Rendered HTML string
    """
    from jinja2 import Template

    template = Template(template_html)

    # Handle missing variables gracefully
    class SafeDict(dict):
        def __missing__(self, key):
            return f"{{{{{key}}}}}"

    safe_vars = SafeDict(variables)
    return template.render(**safe_vars)


def seed_direct_mail_templates(db, agent_id: int = 1) -> int:
    """
    Seed pre-built direct mail templates to the database.

    Creates templates if they don't already exist for the agent.
    Skips templates that already exist (by name).

    Args:
        db: Database session
        agent_id: Agent ID to assign templates to (default: 1)

    Returns:
        Number of templates created
    """
    from app.models.direct_mail import DirectMailTemplate, MailType

    created_count = 0

    for template_key, template_data in TEMPLATES.items():
        # Check if template already exists
        existing = db.query(DirectMailTemplate).filter(
            DirectMailTemplate.agent_id == agent_id,
            DirectMailTemplate.name == template_data["name"]
        ).first()

        if existing:
            continue  # Skip existing templates

        # Create new template
        template = DirectMailTemplate(
            agent_id=agent_id,
            name=template_data["name"],
            description=template_data["description"],
            template_type=template_data["template_type"],
            campaign_type=template_data["campaign_type"],
            front_html_template=template_data["front_html"],
            back_html_template=template_data.get("back_html", ""),
            default_color=template_data.get("default_color", False),
            default_double_sided=template_data.get("default_double_sided", True),
            required_variables=template_data.get("required_variables", {}),
            is_active=True,
            is_system_template=True
        )

        db.add(template)
        created_count += 1

    try:
        db.commit()
        print(f"✓ Seeded {created_count} direct mail templates for agent {agent_id}")
    except Exception as e:
        db.rollback()
        print(f"✗ Failed to seed templates: {e}")

    return created_count

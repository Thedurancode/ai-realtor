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
# TEMPLATE REGISTRY
# =========================================================================

TEMPLATES = {
    "just_sold": JUST_SOLD_TEMPLATE,
    "open_house": OPEN_HOUSE_TEMPLATE,
    "market_update": MARKET_UPDATE_TEMPLATE,
    "new_listing": NEW_LISTING_TEMPLATE,
    "price_reduction": PRICE_REDUCTION_TEMPLATE,
    "hello": HELLO_FARMING_TEMPLATE
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
            return f"{{{{{key}}}}"

    safe_vars = SafeDict(variables)
    return template.render(**safe_vars)

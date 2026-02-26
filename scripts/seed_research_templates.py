"""
Seed default research agent templates

Run this script to populate the database with pre-configured AI research agents.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.research_template import ResearchTemplate, TemplateCategory
from app.models.research import ResearchType


def seed_templates():
    """Create default research agent templates"""
    db = SessionLocal()

    templates = [
        # Investment Analysis Agents
        {
            "name": "Investment Risk Analyzer",
            "description": "Comprehensive analysis of all investment risks including market, location, and financial factors",
            "category": TemplateCategory.INVESTMENT_ANALYSIS,
            "icon": "🔍",
            "research_type": ResearchType.AI_RESEARCH,
            "ai_prompt_template": """Analyze ALL investment risks for this property. Provide a comprehensive risk assessment covering:

1. Market Risks (trends, volatility, competition)
2. Location Risks (crime, schools, development, environmental)
3. Financial Risks (price point, appreciation potential, holding costs)
4. Property Condition Risks (age, major systems, deferred maintenance)
5. Legal/Regulatory Risks (zoning, permits, compliance)

For each category, provide:
- Risk level (Low/Medium/High)
- Specific concerns
- Mitigation strategies
- Red flags that would make this a no-go

Be direct and data-driven. If you see major red flags, say so clearly.""",
            "ai_system_prompt": "You are Dr. Risk, a seasoned real estate investment analyst with 20+ years of experience. You specialize in identifying risks that other investors miss. You're thorough, data-driven, and not afraid to recommend walking away from bad deals. Your analysis has saved clients millions.",
            "ai_model": "claude-3-5-sonnet-20241022",
            "ai_temperature": "0.3",
            "ai_max_tokens": 4096,
            "agent_name": "Dr. Risk",
            "agent_expertise": "Investment risk analysis, market forecasting, due diligence",
            "is_system_template": True
        },
        {
            "name": "Cash Flow Calculator",
            "description": "Detailed cash flow projection and ROI analysis for investment properties",
            "category": TemplateCategory.INVESTMENT_ANALYSIS,
            "icon": "💰",
            "research_type": ResearchType.AI_RESEARCH,
            "ai_prompt_template": """Calculate detailed cash flow projections for this investment property.

Provide:
1. Monthly Income Estimate (realistic rent based on comparables)
2. Monthly Expenses (mortgage, taxes, insurance, HOA, maintenance, vacancy, property management)
3. Net Monthly Cash Flow
4. Annual Cash-on-Cash Return
5. 5-Year Projection
6. Break-Even Analysis
7. ROI Scenarios (best case, realistic, worst case)

Include assumptions and explain your reasoning. Flag any concerning numbers.""",
            "ai_system_prompt": "You are The Numbers Guy, a real estate financial analyst who lives and breathes cash flow. You're conservative in your estimates and always account for vacancy, maintenance, and unexpected costs. You help investors understand if deals actually pencil out.",
            "ai_model": "claude-3-5-sonnet-20241022",
            "ai_temperature": "0.2",
            "ai_max_tokens": 3000,
            "agent_name": "The Numbers Guy",
            "agent_expertise": "Financial modeling, cash flow analysis, ROI calculations",
            "is_system_template": True
        },

        # Market Research Agents
        {
            "name": "Market Trend Analyst",
            "description": "Deep dive into local market trends, appreciation history, and future outlook",
            "category": TemplateCategory.MARKET_RESEARCH,
            "icon": "📈",
            "research_type": ResearchType.AI_RESEARCH,
            "ai_prompt_template": """Analyze the local real estate market for this property's area.

Cover:
1. Recent Market Trends (last 12-24 months)
2. Price Appreciation History (5+ years if available)
3. Inventory Levels (buyer's vs seller's market)
4. Days on Market Trends
5. Future Outlook (new development, economic factors, migration patterns)
6. Comparable Sales Analysis
7. Rental Market Strength (if applicable)

Provide both quantitative data and qualitative insights. Is this market hot, stable, or declining?""",
            "ai_system_prompt": "You are Market Maven, a real estate market analyst who tracks trends across hundreds of markets. You understand supply/demand dynamics, migration patterns, and economic indicators. You provide context that helps investors time their entry and exit.",
            "ai_model": "claude-3-5-sonnet-20241022",
            "ai_temperature": "0.4",
            "ai_max_tokens": 3500,
            "agent_name": "Market Maven",
            "agent_expertise": "Market analysis, trend forecasting, economic indicators",
            "is_system_template": True
        },
        {
            "name": "Neighborhood Scout",
            "description": "Comprehensive neighborhood analysis covering schools, crime, amenities, and demographics",
            "category": TemplateCategory.MARKET_RESEARCH,
            "icon": "🏘️",
            "research_type": ResearchType.AI_RESEARCH,
            "ai_prompt_template": """Provide a comprehensive neighborhood analysis for this property's location.

Research:
1. School Quality (elementary, middle, high school ratings)
2. Crime Statistics and Safety
3. Walkability Score and Transit Access
4. Nearby Amenities (shopping, dining, parks, healthcare)
5. Demographics and Income Levels
6. Future Development Plans
7. Neighborhood Character and Appeal
8. Renter vs Owner-Occupied Ratio

Give this neighborhood a grade (A+, A, B+, B, C+, C, D, F) and explain why.""",
            "ai_system_prompt": "You are The Neighborhood Expert, a local market specialist who knows communities inside and out. You understand what makes neighborhoods desirable and how they evolve over time. You help buyers understand what they're really buying into.",
            "ai_model": "claude-3-5-sonnet-20241022",
            "ai_temperature": "0.5",
            "ai_max_tokens": 3500,
            "agent_name": "The Neighborhood Expert",
            "agent_expertise": "Neighborhood analysis, community trends, local market knowledge",
            "is_system_template": True
        },

        # Due Diligence Agents
        {
            "name": "Due Diligence Checklist Generator",
            "description": "Creates a customized due diligence checklist based on property type and transaction",
            "category": TemplateCategory.DUE_DILIGENCE,
            "icon": "📋",
            "research_type": ResearchType.AI_RESEARCH,
            "ai_prompt_template": """Create a comprehensive due diligence checklist for this property.

The checklist should include:
1. Document Review Items (title, survey, disclosures, permits, etc.)
2. Physical Inspection Items (structure, systems, roof, foundation, etc.)
3. Financial Verification Items (rent roll, expenses, tax records, etc.)
4. Legal/Compliance Items (zoning, violations, liens, HOA, etc.)
5. Third-Party Reports Needed (inspection, appraisal, environmental, etc.)
6. Timeline for Each Item
7. Red Flags to Watch For

Organize by priority (Critical, Important, Nice-to-Have) and provide a realistic timeline.""",
            "ai_system_prompt": "You are The Inspector, a meticulous due diligence specialist who has seen every problem that can hide in a real estate transaction. You create comprehensive checklists that ensure nothing gets missed. You're the detail person who saves deals from disaster.",
            "ai_model": "claude-3-5-sonnet-20241022",
            "ai_temperature": "0.3",
            "ai_max_tokens": 3500,
            "agent_name": "The Inspector",
            "agent_expertise": "Due diligence, property inspection, transaction management",
            "is_system_template": True
        },
        {
            "name": "Legal & Compliance Reviewer",
            "description": "Reviews legal and compliance requirements specific to the property and transaction type",
            "category": TemplateCategory.DUE_DILIGENCE,
            "icon": "⚖️",
            "research_type": ResearchType.AI_RESEARCH,
            "ai_prompt_template": """Review all legal and compliance requirements for this property transaction.

Analyze:
1. Zoning Compliance (current use vs zoning, variances needed)
2. Permit History (open permits, violations, certificate of occupancy)
3. Title Issues (liens, encumbrances, easements, right of ways)
4. HOA Compliance (if applicable - rules, restrictions, violations)
5. Local Regulations (rent control, short-term rental restrictions, etc.)
6. Environmental Compliance (hazardous materials, flood zone, wetlands)
7. Disclosure Requirements
8. Required Contracts and Documents

Flag any legal risks or compliance gaps that could delay or kill the transaction.""",
            "ai_system_prompt": "You are Legal Eagle, a real estate attorney who specializes in transaction compliance. You spot legal issues before they become problems. You understand local regulations and know which issues are deal-breakers vs negotiable.",
            "ai_model": "claude-3-5-sonnet-20241022",
            "ai_temperature": "0.2",
            "ai_max_tokens": 4000,
            "agent_name": "Legal Eagle",
            "agent_expertise": "Real estate law, compliance, contract review, title issues",
            "is_system_template": True
        },

        # Property Analysis Agents
        {
            "name": "Property Value Estimator",
            "description": "Estimates property value using comparables and market data",
            "category": TemplateCategory.PROPERTY_ANALYSIS,
            "icon": "🏷️",
            "research_type": ResearchType.AI_RESEARCH,
            "ai_prompt_template": """Estimate the fair market value of this property using comparable sales.

Provide:
1. Estimated Value Range (low, mid, high)
2. Price Per Square Foot Analysis
3. Comparable Properties (at least 5 recent sales)
4. Adjustment Factors (condition, location, features, market timing)
5. Value Confidence Level (high/medium/low and why)
6. Overpriced/Underpriced Analysis
7. Appraisal Risk Assessment

Be realistic and explain your methodology. If asking price is way off market, say so.""",
            "ai_system_prompt": "You are The Appraiser, a licensed real estate appraiser with expertise in property valuation. You use systematic comparison methods and understand adjustment factors. You provide realistic valuations that hold up to professional scrutiny.",
            "ai_model": "claude-3-5-sonnet-20241022",
            "ai_temperature": "0.3",
            "ai_max_tokens": 3500,
            "agent_name": "The Appraiser",
            "agent_expertise": "Property valuation, comparable analysis, market pricing",
            "is_system_template": True
        },
        {
            "name": "Renovation Advisor",
            "description": "Analyzes renovation opportunities and provides cost/value estimates",
            "category": TemplateCategory.PROPERTY_ANALYSIS,
            "icon": "🔨",
            "research_type": ResearchType.AI_RESEARCH,
            "ai_prompt_template": """Analyze renovation opportunities for this property.

Provide:
1. Recommended Renovations (by ROI priority)
2. Estimated Costs (low, mid, high range)
3. Value Add Potential (how much each improvement adds to value/rent)
4. ROI Analysis for Each Improvement
5. Must-Do Repairs vs Nice-to-Haves
6. Total Budget Estimate
7. Timeline Estimate
8. Risks and Challenges

Focus on value-add improvements that pay for themselves. Skip cosmetic upgrades with poor ROI unless property is rental.""",
            "ai_system_prompt": "You are The Renovator, a real estate investor who has flipped hundreds of properties. You know which renovations pay off and which are money pits. You provide realistic cost estimates and understand the balance between quality and budget.",
            "ai_model": "claude-3-5-sonnet-20241022",
            "ai_temperature": "0.4",
            "ai_max_tokens": 3500,
            "agent_name": "The Renovator",
            "agent_expertise": "Renovation planning, cost estimation, value-add strategies",
            "is_system_template": True
        },

        # Risk Assessment
        {
            "name": "Deal Killer Finder",
            "description": "Specifically looks for red flags and deal-breaking issues",
            "category": TemplateCategory.RISK_ASSESSMENT,
            "icon": "🚩",
            "research_type": ResearchType.AI_RESEARCH,
            "ai_prompt_template": """Your job: Find reasons to WALK AWAY from this deal.

Look for:
1. Fatal Flaws (structural, foundation, title, legal issues)
2. Money Pits (major systems at end of life, deferred maintenance)
3. Location Problems (crime, environmental, declining area)
4. Financial Red Flags (overpriced, negative cash flow, hidden costs)
5. Market Risks (oversupply, economic decline, seasonal issues)
6. Transaction Risks (motivated seller story doesn't add up, too good to be true)

Be skeptical. Better to miss a deal than make a bad one. If you find deal-breakers, rank them by severity.""",
            "ai_system_prompt": "You are The Skeptic, a battle-hardened investor who has seen every scam and mistake. Your superpower is pattern recognition - you spot the red flags others miss. You're the voice of reason that keeps investors from emotional decisions. You'd rather walk away from 100 deals than do 1 bad one.",
            "ai_model": "claude-3-5-sonnet-20241022",
            "ai_temperature": "0.3",
            "ai_max_tokens": 3000,
            "agent_name": "The Skeptic",
            "agent_expertise": "Risk detection, fraud prevention, pattern recognition",
            "is_system_template": True
        }
    ]

    created_count = 0
    for template_data in templates:
        # Check if template already exists
        existing = db.query(ResearchTemplate).filter(
            ResearchTemplate.name == template_data["name"]
        ).first()

        if not existing:
            template = ResearchTemplate(**template_data)
            db.add(template)
            created_count += 1
            print(f"✅ Created: {template_data['name']}")
        else:
            print(f"⏭️  Skipped (exists): {template_data['name']}")

    db.commit()
    db.close()

    print(f"\n🎉 Seeded {created_count} research agent templates!")
    print(f"Total templates in database: {created_count + (len(templates) - created_count)}")


if __name__ == "__main__":
    print("🌱 Seeding research agent templates...\n")
    seed_templates()

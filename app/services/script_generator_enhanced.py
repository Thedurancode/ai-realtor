"""Enhanced Script Generator Service

AI-powered video script generation using Claude Sonnet 4 via OpenRouter.
Generates professional property video scripts with multiple sections.
"""
import logging
import json
from typing import Dict, Optional
import httpx
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class ScriptGeneratorService:
    """
    Enhanced script generator using Claude AI via OpenRouter.

    Generates professional video scripts for:
    - Property tours
    - Agent introductions
    - Market updates
    - Just sold announcements
    - New listings

    Supports multiple styles: luxury, friendly, professional
    """

    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'openrouter_api_key', None)
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://ai-realtor.com",
                "X-Title": "AI Realtor Video Generator"
            }
        )

    async def generate_property_script(
        self,
        property_data: Dict,
        style: str = "luxury",
        duration: int = 60
    ) -> Dict:
        """
        Generate complete property video script.

        Args:
            property_data: Property details dict
                {
                    "address": "123 Main St",
                    "city": "Miami",
                    "price": 850000,
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "square_feet": 2000,
                    "description": "...",
                    "property_type": "house"
                }
            style: Video style (luxury, friendly, professional)
            duration: Target duration in seconds

        Returns:
            {
                "agent_intro": "Hi, I'm Agent Name...",
                "property_highlights": "This stunning property features...",
                "call_to_action": "Contact me today at...",
                "estimated_duration": 60,
                "word_count": 150
            }
        """
        logger.info(f"Generating {style} property script for {property_data.get('address', 'property')}")

        word_count = int(duration * 1.5)  # ~150 words per minute

        style_guidance = self._get_style_guidance(style)

        prompt = f"""You are an expert real estate video scriptwriter. Generate a {style} video script (~{word_count} words, {duration} seconds) for this property.

PROPERTY DETAILS:
- Address: {property_data.get('address', 'N/A')}
- City: {property_data.get('city', 'N/A')}
- Price: ${property_data.get('price', 0):,}
- Bedrooms: {property_data.get('bedrooms', 'N/A')}
- Bathrooms: {property_data.get('bathrooms', 'N/A')}
- Square Feet: {property_data.get('square_feet', 'N/A')}
- Property Type: {property_data.get('property_type', 'N/A')}
- Description: {(property_data.get('description') or 'Beautiful property awaiting your discovery')[:300]}

AGENT INFORMATION:
- Agent Name: {property_data.get('agent_name', 'your agent')}
- Company: {property_data.get('agent_company', 'Emprezario Inc')}
- Contact: {property_data.get('agent_phone', 'contact me for details')}

STYLE GUIDANCE: {style_guidance}

SCRIPT STRUCTURE:
1. **Agent Intro (15 seconds)**: Warm introduction using "{property_data.get('agent_name', 'your agent')}" and "{property_data.get('agent_company', 'Emprezario Inc')}", plus property teaser
2. **Property Highlights (30-35 seconds)**: Key features, room details, unique selling points, benefits
3. **Call to Action (10 seconds)**: Clear contact info using "{property_data.get('agent_phone', 'contact me for details')}" and next steps

REQUIREMENTS:
- Total word count: ~{word_count} words
- Use natural, conversational language
- Include specific property details
- Create emotional connection
- End with clear call-to-action
- Return ONLY valid JSON (no markdown formatting)

JSON FORMAT:
{{
    "agent_intro": "Agent introduction script here...",
    "property_highlights": "Property description script here...",
    "call_to_action": "Contact info and CTA here...",
    "estimated_duration": {duration},
    "word_count": {word_count}
}}

Generate the script now:"""

        try:
            # Use OpenRouter API (OpenAI-compatible format)
            response = await self.client.post(
                self.OPENROUTER_API_URL,
                json={
                    "model": "anthropic/claude-sonnet-4",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            data = response.json()

            # Validate response structure
            if not data:
                raise Exception("Empty response from OpenRouter API")

            if "choices" not in data:
                logger.error(f"Response missing 'choices': {data}")
                raise Exception("Invalid API response format - missing 'choices'")

            if not data["choices"]:
                raise Exception("Empty choices array in API response")

            if "message" not in data["choices"][0]:
                logger.error(f"Choice missing 'message': {data['choices'][0]}")
                raise Exception("Invalid API response format - missing 'message'")

            if "content" not in data["choices"][0]["message"]:
                logger.error(f"Message missing 'content': {data['choices'][0]['message']}")
                raise Exception("Invalid API response format - missing 'content'")

            script_text = data["choices"][0]["message"]["content"]

            # Clean up any markdown code blocks
            if "```json" in script_text:
                script_text = script_text.split("```json")[1].split("```")[0].strip()
            elif "```" in script_text:
                script_text = script_text.split("```")[1].split("```")[0].strip()

            script_data = json.loads(script_text)

            logger.info(f"Script generated: {script_data.get('word_count', 0)} words")

            return script_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            if 'script_text' in locals():
                logger.error(f"Response text: {script_text[:500]}")
            raise Exception(f"Invalid JSON in script generation: {str(e)}")
        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            raise

    async def generate_agent_intro_script(
        self,
        agent_data: Dict,
        style: str = "professional"
    ) -> Dict:
        """
        Generate agent introduction script.

        Args:
            agent_data: Agent details
                {
                    "name": "Jane Smith",
                    "company": "Emprezario Inc",
                    "specialty": "luxury real estate",
                    "city": "Miami"
                }
            style: Script style

        Returns:
            {
                "script": "Hi, I'm Jane Smith...",
                "duration": 25,
                "word_count": 60
            }
        """
        logger.info(f"Generating {style} agent intro script for {agent_data.get('name')}")

        style_guidance = self._get_style_guidance(style)

        prompt = f"""Generate a {style} agent introduction script (20-30 seconds, ~50-70 words) for:

AGENT: {agent_data.get('name')}
COMPANY: {agent_data.get('company', 'Emprezario Inc')}
SPECIALTY: {agent_data.get('specialty', 'luxury real estate')}
LOCATION: {agent_data.get('city', 'Miami')}

STYLE: {style_guidance}

The script should:
- Establish trust and expertise
- Mention the company
- Hint at the property tour coming up
- Be warm and inviting

Return JSON format:
{{
    "script": "Your script here...",
    "duration": 25,
    "word_count": 60
}}

Generate the script:"""

        try:
            response = await self.client.post(
                self.OPENROUTER_API_URL,
                json={
                    "model": "anthropic/claude-sonnet-4",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            data = response.json()

            script_text = data["choices"][0]["message"]["content"]

            # Clean up markdown
            if "```json" in script_text:
                script_text = script_text.split("```json")[1].split("```")[0].strip()
            elif "```" in script_text:
                script_text = script_text.split("```")[1].split("```")[0].strip()

            return json.loads(script_text)

        except Exception as e:
            logger.error(f"Agent intro script generation failed: {str(e)}")
            raise

    async def generate_market_update_script(
        self,
        market_data: Dict,
        style: str = "professional"
    ) -> Dict:
        """
        Generate market update video script.

        Args:
            market_data: Market statistics
                {
                    "city": "Miami",
                    "avg_price": 750000,
                    "price_change": "+5%",
                    "days_on_market": 45,
                    "inventory": "low"
                }
            style: Script style

        Returns:
            Complete script with intro, data, and CTA
        """
        logger.info(f"Generating market update script for {market_data.get('city')}")

        style_guidance = self._get_style_guidance(style)

        prompt = f"""Generate a {style} market update video script (45-60 seconds) for:

MARKET DATA:
- City: {market_data.get('city')}
- Average Price: ${market_data.get('avg_price', 0):,}
- Price Change: {market_data.get('price_change', 'N/A')}
- Days on Market: {market_data.get('days_on_market', 'N/A')}
- Inventory: {market_data.get('inventory', 'N/A')}

STYLE: {style_guidance}

The script should:
- Present data clearly and confidently
- Explain what it means for buyers/sellers
- Create urgency or opportunity
- End with clear CTA

Return JSON format:
{{
    "intro": "Hook and market overview...",
    "data_presentation": "Key statistics and insights...",
    "call_to_action": "Contact CTA...",
    "duration": 60
}}

Generate the script:"""

        try:
            response = await self.client.post(
                self.OPENROUTER_API_URL,
                json={
                    "model": "anthropic/claude-sonnet-4",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            data = response.json()

            script_text = data["choices"][0]["message"]["content"]

            if "```json" in script_text:
                script_text = script_text.split("```json")[1].split("```")[0].strip()
            elif "```" in script_text:
                script_text = script_text.split("```")[1].split("```")[0].strip()

            return json.loads(script_text)

        except Exception as e:
            logger.error(f"Market update script generation failed: {str(e)}")
            raise

    def _get_style_guidance(self, style: str) -> str:
        """Get style-specific guidance for script generation."""

        styles = {
            "luxury": """
- Sophisticated and elegant language
- Emphasize exclusivity and premium features
- Use words like: stunning, exceptional, unparalleled, exquisite
- Create aspirational feeling
- Appeal to discerning buyers
- Confident and polished tone
""",
            "friendly": """
- Warm and approachable language
- Focus on lifestyle and comfort
- Use words like: welcoming, perfect, cozy, ideal
- Create emotional connection
- Family-oriented appeal
- Conversational and inviting tone
""",
            "professional": """
- Confident and informative language
- Focus on value and investment
- Use words like: exceptional, opportunity, prime, strategic
- Appeal to rational buyers
- Business-oriented
- Clear and direct tone
"""
        }

        return styles.get(style, styles["luxury"])

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# ============================================================================
# Helper Functions
# ============================================================================

async def generate_video_script(
    property_data: Dict,
    style: str = "luxury",
    duration: int = 60
) -> Dict:
    """
    Convenience function to generate property video script.

    Args:
        property_data: Property details
        style: Video style
        duration: Target duration

    Returns:
        Complete script with all sections
    """
    generator = ScriptGeneratorService()
    return await generator.generate_property_script(property_data, style, duration)

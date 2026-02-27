"""
AI Website Generator Service

Generates landing page content using Claude AI based on property data
"""
import os
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.zillow_enrichment import ZillowEnrichment
from app.services.website_templates import WebsiteTemplates


class WebsiteGeneratorService:
    """AI-powered landing page content generator"""

    def __init__(self, db: Session):
        self.db = db
        self.templates = WebsiteTemplates()

    async def generate_website_content(
        self,
        property_obj: Property,
        template: str = "modern"
    ) -> Dict:
        """
        Generate complete landing page content using AI

        Analyzes:
        - Property details (address, price, features)
        - Zillow enrichment data (photos, description, zestimate)
        - Market data (comps, neighborhood info)
        - Agent brand info
        """
        # Gather property data
        property_data = self._gather_property_data(property_obj)

        # Get template structure
        template_structure = self.templates.get_template_structure(template)

        # Generate AI content for each section
        content = {
            "template": template,
            "theme": self._generate_theme(template),
            "sections": {}
        }

        # Generate hero section
        content["sections"]["hero"] = await self._generate_hero_section(property_data)

        # Generate about section
        content["sections"]["about"] = await self._generate_about_section(property_data)

        # Generate features section
        content["sections"]["features"] = await self._generate_features_section(property_data)

        # Generate gallery section
        content["sections"]["gallery"] = await self._generate_gallery_section(property_data)

        # generate contact section
        content["sections"]["contact"] = await self._generate_contact_section(property_data)

        # Generate CTA section
        content["sections"]["cta"] = await self._generate_cta_section(property_data)

        # Generate SEO metadata
        content["seo"] = await self._generate_seo_metadata(property_data)

        return content

    def _gather_property_data(self, property_obj: Property) -> Dict:
        """Gather all relevant property data"""
        data = {
            "id": property_obj.id,
            "address": property_obj.address,
            "city": property_obj.city,
            "state": property_obj.state,
            "zip_code": property_obj.zip_code,
            "price": property_obj.price,
            "bedrooms": property_obj.bedrooms,
            "bathrooms": property_obj.bathrooms,
            "square_footage": property_obj.square_footage,
            "property_type": property_obj.property_type.value,
            "status": property_obj.status.value,
            "description": property_obj.description,
            "year_built": getattr(property_obj, 'year_built', None),
            "lot_size": getattr(property_obj, 'lot_size', None),
            "agent_id": property_obj.agent_id
        }

        # Get Zillow enrichment if available
        enrichment = self.db.query(ZillowEnrichment).filter(
            ZillowEnrichment.property_id == property_obj.id
        ).first()

        if enrichment:
            data["zillow"] = {
                "description": enrichment.description,
                "photos": enrichment.photos[:10] if enrichment.photos else [],
                "zestimate": enrichment.zestimate,
                "rent_zestimate": enrichment.rent_zestimate,
                "tax_assessment": enrichment.tax_assessment,
                "year_built": enrichment.year_built,
                "lot_size": enrichment.lot_size,
                "living_area": enrichment.living_area,
                "bedrooms": enrichment.bedrooms,
                "bathrooms": enrichment.bathrooms,
                "rooms": enrichment.rooms,
            }

        return data

    async def _generate_hero_section(self, property_data: Dict) -> Dict:
        """Generate hero section with headline, subheadline, CTA"""
        # In production, this would call Claude AI API
        # For now, generate template-based content

        price_formatted = f"${property_data['price']:,}" if property_data.get('price') else "Price Upon Request"

        headlines = {
            "modern": f"Stunning {property_data['city']} Property",
            "luxury": f"Luxury Living in {property_data['city']}",
            "minimal": f"{property_data['address']}"
        }

        subheadlines = {
            "modern": f"{property_data['bedrooms']} Bed, {property_data['bathrooms']} Bath Premium Property",
            "luxury": f"Exquisite {property_data['bedrooms']}BR, {property_data['bathrooms']}BA Residence",
            "minimal": f"{property_data['bedrooms']} Bedrooms • {property_data['bathrooms']} Baths"
        }

        zestimate = property_data.get("zillow", {}).get("zestimate")
        if zestimate:
            price_note = f"Zestimate: ${zestimate:,}"
        else:
            price_note = price_formatted

        return {
            "headline": headlines["modern"],
            "subheadline": subheadlines["modern"],
            "price_display": price_formatted,
            "price_note": price_note,
            "primary_cta": "Schedule a Showing",
            "secondary_cta": "Download Brochure",
            "background_image": property_data.get("zillow", {}).get("photos", [None])[0] if property_data.get("zillow", {}).get("photos") else None,
            "overlay": True
        }

    async def _generate_about_section(self, property_data: Dict) -> Dict:
        """Generate about/description section"""
        description = property_data.get("zillow", {}).get(
            "description",
            f"Beautiful property located at {property_data['address']} in {property_data['city']}, {property_data['state']}. "
            f"This {property_data['property_type'].value} features {property_data['bedrooms']} bedrooms and "
            f"{property_data['bathrooms']} bathrooms with {property_data['square_footage']:,} square feet of living space."
        )

        features = self._extract_key_features(property_data)

        return {
            "title": "About This Property",
            "description": description[:500] + "..." if len(description) > 500 else description,
            "features": features,
            "highlights": self._generate_highlights(property_data)
        }

    async def _generate_features_section(self, property_data: Dict) -> Dict:
        """Generate features section"""
        features = self._extract_key_features(property_data)

        return {
            "title": "Property Features",
            "features": features[:12],  # Limit to 12 features
            "layout": "grid"  # grid or list
        }

    async def _generate_gallery_section(self, property_data: Dict) -> Dict:
        """Generate photo gallery section"""
        photos = property_data.get("zillow", {}).get("photos", [])

        gallery_images = []
        for i, photo_url in enumerate(photos[:12]):  # Max 12 photos
            gallery_images.append({
                "url": photo_url,
                "thumbnail": photo_url,
                "caption": f"Photo {i+1}",
                "alt": f"{property_data['address']} - Photo {i+1}"
            })

        return {
            "title": "Property Gallery",
            "images": gallery_images,
            "layout": "masonry"  # masonry, grid, or slider
        }

    async def _generate_contact_section(self, property_data: Dict) -> Dict:
        """Generate contact form section"""
        return {
            "title": "Interested? Let's Talk!",
            "subtitle": f"Schedule a private showing of {property_data['address']}",
            "form_fields": [
                {"name": "name", "label": "Your Name", "type": "text", "required": True},
                {"name": "email", "label": "Email Address", "type": "email", "required": True},
                {"name": "phone", "label": "Phone Number", "type": "tel", "required": False},
                {"name": "message", "label": "Message (Optional)", "type": "textarea", "required": False},
            ],
            "submit_button": "Send Message",
            "contact_methods": {
                "phone": True,
                "email": True,
                "text": True
            }
        }

    async def _generate_cta_section(self, property_data: Dict) -> Dict:
        """Generate call-to-action section"""
        return {
            "headline": "Ready to See This Property?",
            "subheadline": f"Schedule your private showing today. {property_data['bedrooms']}BR/{property_data['bathrooms']}BA waiting for you.",
            "primary_cta": {
                "text": "Schedule Showing",
                "action": "contact"
            },
            "secondary_cta": {
                "text": "View Virtual Tour",
                "action": "gallery"
            },
            "trust_badges": [
                {"icon": "✓", "text": "Licensed Agent"},
                {"icon": "🔒", "text": "Secure Form"},
                {"icon": "⚡", "text": "Quick Response"}
            ]
        }

    async def _generate_seo_metadata(self, property_data: Dict) -> Dict:
        """Generate SEO metadata"""
        city_state = f"{property_data['city']}, {property_data['state']}"
        price_str = f"${property_data['price']:,}" if property_data.get('price') else "Price Upon Request"

        return {
            "title": f"{property_data['address']} | {property_data['bedrooms']}BR/{property_data['bathrooms']}BA | {city_state}",
            "description": f"View this {property_data['property_type'].value} at {property_data['address']}, {city_state}. "
                         f"{property_data['bedrooms']} bedrooms, {property_data['bathrooms']} bathrooms, "
                         f"{property_data['square_footage']:,} sq ft. {price_str}.",
            "keywords": [
                f"{city_state} real estate",
                f"{property_data['city']} property",
                f"{property_data['property_type'].value} for sale",
                f"{property_data['bedrooms']} bedroom property",
                f"{property_data['bathrooms']} bathroom property",
                "luxury real estate",
                "property for sale",
                f"{property_data['address']}"
            ],
            "og_image": property_data.get("zillow", {}).get("photos", [None])[0],
            "twitter_card": "summary_large_image"
        }

    def _generate_theme(self, template: str) -> Dict:
        """Generate theme (colors, fonts) for template"""
        themes = {
            "modern": {
                "primary_color": "#3b82f6",
                "secondary_color": "#1e40af",
                "accent_color": "#10b981",
                "background_color": "#ffffff",
                "text_color": "#1f2937",
                "font": "Inter",
                "border_radius": "8px",
                "shadow": "medium"
            },
            "luxury": {
                "primary_color": "#b45309",
                "secondary_color": "#d97706",
                "accent_color": "#f59e0b",
                "background_color": "#fafafa",
                "text_color": "#78350f",
                "font": "Playfair Display",
                "border_radius": "4px",
                "shadow": "light"
            },
            "minimal": {
                "primary_color": "#111827",
                "secondary_color": "#374151",
                "accent_color": "#6b7280",
                "background_color": "#ffffff",
                "text_color": "#111827",
                "font": "system-ui",
                "border_radius": "0px",
                "shadow": "none"
            }
        }

        return themes.get(template, themes["modern"])

    def _extract_key_features(self, property_data: Dict) -> list:
        """Extract key features from property data"""
        features = []

        # Basic features
        if property_data.get("bedrooms"):
            features.append(f"{property_data['bedrooms']} Bedrooms")
        if property_data.get("bathrooms"):
            features.append(f"{property_data['bathrooms']} Bathrooms")
        if property_data.get("square_footage"):
            features.append(f"{property_data['square_footage']:,} Sq Ft")

        # Additional features from enrichment
        enrichment = property_data.get("zillow", {})
        if enrichment.get("year_built"):
            features.append(f"Built in {enrichment['year_built']}")
        if enrichment.get("lot_size"):
            features.append(f"{enrichment['lot_size']:,} Sq Ft Lot")

        # Type-specific features
        property_type = property_data.get("property_type", "").lower()
        if "condo" in property_type or "apartment" in property_type:
            features.extend([
                "Secure Building",
                "Elevator Access",
                "Common Areas"
            ])
        elif "house" in property_type:
            features.extend([
                "Private Yard",
                "Garage",
                "Driveway"
            ])

        # Add generic features if list is short
        if len(features) < 6:
            features.extend([
                "Modern Design",
                "Updated Kitchen",
                "Hardwood Floors",
                "Natural Light",
                "Storage Space",
                "Central HVAC"
            ])

        return features

    def _generate_highlights(self, property_data: Dict) -> list:
        """Generate property highlights"""
        highlights = []

        if property_data.get("price"):
            highlights.append({
                "icon": "💰",
                "title": "Competitive Price",
                "description": f"Priced at ${property_data['price']:,} in {property_data['city']}"
            })

        zestimate = property_data.get("zillow", {}).get("zestimate")
        if zestimate:
            diff = zestimate - property_data.get("price", 0)
            if diff > 0:
                highlights.append({
                    "icon": "📈",
                    "title": "Below Zestimate",
                    "description": f"${zestimate:,} Zestimate (${diff:,} above asking)"
                })

        highlights.append({
            "icon": "📍",
            "title": "Prime Location",
            "description": f"Desirable {property_data['city']} neighborhood"
        })

        return highlights

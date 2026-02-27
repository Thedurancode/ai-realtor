"""
Lob.com Direct Mail API Service

Handles all communication with Lob's API for sending postcards, letters, and checks.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from jinja2 import Template

from app.config import settings
from app.schemas.direct_mail import (
    AddressSchema,
    PostcardSize,
    LetterSize,
    MailType,
    MailStatus
)


class LobClient:
    """
    Lob.com API Client for Physical Mail Automation

    API Docs: https://lob.com/docs/api
    """

    # Lob API Base URL
    BASE_URL = "https://api.lob.com/v1"

    # Lob API version
    API_VERSION = "2024-01-01"

    # Mailpiece status mapping from Lob to internal
    STATUS_MAPPING = {
        "draft": MailStatus.DRAFT,
        "scheduled": MailStatus.SCHEDULED,
        "processing": MailStatus.PROCESSING,
        "mailed": MailStatus.MAILED,
        "in_transit": MailStatus.IN_TRANSIT,
        "delivered": MailStatus.DELIVERED,
        "canceled": MailStatus.CANCELLED,
        "failed": MailStatus.FAILED,
    }

    def __init__(self, api_key: str = None, test_mode: bool = None):
        """
        Initialize Lob client

        Args:
            api_key: Lob API key (defaults to settings.lob_api_key)
            test_mode: If True, uses test mode (no actual mail sent, defaults to settings.lob_test_mode)
        """
        self.api_key = api_key or settings.lob_api_key
        self.test_mode = test_mode if test_mode is not None else settings.lob_test_mode

        if not self.api_key:
            raise ValueError("LOB_API_KEY must be set in environment or passed to constructor")

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Lob-Version": self.API_VERSION,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    # ==========================================================================
    # ADDRESS VERIFICATION
    # ==========================================================================

    async def verify_address(
        self,
        address: Dict[str, str],
        secondary_line: str = ""
    ) -> Dict[str, Any]:
        """
        Verify and standardize a US address

        Args:
            address: Dictionary with address components
            secondary_line: Optional secondary address line

        Returns:
            Verified address with Lob's standardized format
        """
        payload = {
            "recipient": address.get("name", ""),
            "primary_line": address.get("address_line1", ""),
            "secondary_line": address.get("address_line2") or secondary_line,
            "city": address.get("address_city", ""),
            "state": address.get("address_state", ""),
            "zip_code": address.get("address_zip", "")
        }

        response = await self.client.post("/us_verifications", json=payload)
        response.raise_for_status()

        return response.json()

    async def verify_address_batch(
        self,
        addresses: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Verify multiple addresses

        Args:
            addresses: List of address dictionaries

        Returns:
            List of verified addresses
        """
        results = []
        for address in addresses:
            try:
                verified = await self.verify_address(address)
                results.append(verified)
            except Exception as e:
                results.append({
                    "error": str(e),
                    "original_address": address
                })
        return results

    # ==========================================================================
    # POSTCARDS
    # ==========================================================================

    async def create_postcard(
        self,
        to_address: Dict[str, str],
        from_address: Dict[str, str],
        front_html: str,
        back_html: str = None,
        size: str = "4x6",
        merge_variables: Dict[str, Any] = None,
        send_after: datetime = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send a postcard

        Args:
            to_address: Recipient address
            from_address: Sender address
            front_html: HTML for front of postcard
            back_html: HTML for back of postcard
            size: Postcard size (4x6, 6x9, 6x11)
            merge_variables: Variables to merge into HTML templates
            send_after: Schedule for future sending
            metadata: Additional metadata

        Returns:
            Lob postcard response
        """
        # Format addresses for Lob API
        to_lob = self._format_address(to_address)
        from_lob = self._format_address(from_address)

        payload = {
            "to": to_lob,
            "from": from_lob,
            "front": front_html,
            "size": size
        }

        if back_html:
            payload["back"] = back_html

        if merge_variables:
            payload["merge_variables"] = merge_variables

        if send_after:
            payload["send_after"] = send_after.isoformat()

        if metadata:
            payload["metadata"] = metadata

        if self.test_mode:
            payload["test_mode"] = True

        response = await self.client.post("/postcards", json=payload)
        response.raise_for_status()

        return response.json()

    async def get_postcard(self, postcard_id: str) -> Dict[str, Any]:
        """Retrieve a postcard by ID"""
        response = await self.client.get(f"/postcards/{postcard_id}")
        response.raise_for_status()
        return response.json()

    async def list_postcards(
        self,
        limit: int = 10,
        offset: int = 0,
        status: str = None
    ) -> Dict[str, Any]:
        """List all postcards"""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        response = await self.client.get("/postcards", params=params)
        response.raise_for_status()
        return response.json()

    async def cancel_postcard(self, postcard_id: str) -> Dict[str, Any]:
        """Cancel a postcard (before it's processed for mailing)"""
        response = await self.client.delete(f"/postcards/{postcard_id}")
        response.raise_for_status()
        return response.json()

    # ==========================================================================
    # LETTERS
    # ==========================================================================

    async def create_letter(
        self,
        to_address: Dict[str, str],
        from_address: Dict[str, str],
        file_url: str,
        color: bool = False,
        double_sided: bool = True,
        certified_mail: bool = False,
        return_envelope: bool = False,
        size: str = "letter",
        send_after: datetime = None,
        metadata: Dict[str, Any] = None,
        merge_variables: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send a letter

        Args:
            to_address: Recipient address
            from_address: Sender address
            file_url: URL to PDF file
            color: Color printing (default: false)
            double_sided: Double-sided printing (default: true)
            certified_mail: Send via certified mail
            return_envelope: Include return envelope
            size: Letter size (letter, legal, a4)
            send_after: Schedule for future sending
            metadata: Additional metadata
            merge_variables: Variables for template merging

        Returns:
            Lob letter response
        """
        # Format addresses for Lob API
        to_lob = self._format_address(to_address)
        from_lob = self._format_address(from_address)

        payload = {
            "to": to_lob,
            "from": from_lob,
            "file": file_url,
            "color": color,
            "double_sided": double_sided,
            "certified_mail": certified_mail,
            "return_envelope": return_envelope,
            "size": size
        }

        if send_after:
            payload["send_after"] = send_after.isoformat()

        if metadata:
            payload["metadata"] = metadata

        if merge_variables:
            payload["merge_variables"] = merge_variables

        if self.test_mode:
            payload["test_mode"] = True

        response = await self.client.post("/letters", json=payload)
        response.raise_for_status()

        return response.json()

    async def get_letter(self, letter_id: str) -> Dict[str, Any]:
        """Retrieve a letter by ID"""
        response = await self.client.get(f"/letters/{letter_id}")
        response.raise_for_status()
        return response.json()

    async def list_letters(
        self,
        limit: int = 10,
        offset: int = 0,
        status: str = None
    ) -> Dict[str, Any]:
        """List all letters"""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        response = await self.client.get("/letters", params=params)
        response.raise_for_status()
        return response.json()

    async def cancel_letter(self, letter_id: str) -> Dict[str, Any]:
        """Cancel a letter (before it's processed for mailing)"""
        response = await self.client.delete(f"/letters/{letter_id}")
        response.raise_for_status()
        return response.json()

    # ==========================================================================
    # CHECKS
    # ==========================================================================

    async def create_check(
        self,
        to_address: Dict[str, str],
        from_address: Dict[str, str],
        bank_account: str,
        amount: float,
        check_number: str = None,
        memo: str = None,
        logo: str = None,
        mail_class: str = "first_class",
        send_after: datetime = None
    ) -> Dict[str, Any]:
        """
        Send a check

        Args:
            to_address: Recipient address
            from_address: Sender address
            bank_account: Lob bank account ID
            amount: Check amount
            check_number: Optional check number
            memo: Optional memo line
            logo: Optional logo URL
            mail_class: USPS mail class
            send_after: Schedule for future sending

        Returns:
            Lob check response
        """
        # Format addresses for Lob API
        to_lob = self._format_address(to_address)
        from_lob = self._format_address(from_address)

        payload = {
            "to": to_lob,
            "from": from_lob,
            "bank_account": bank_account,
            "amount": amount,
            "mail_class": mail_class
        }

        if check_number:
            payload["check_number"] = check_number

        if memo:
            payload["memo"] = memo

        if logo:
            payload["logo"] = logo

        if send_after:
            payload["send_after"] = send_after.isoformat()

        if self.test_mode:
            payload["test_mode"] = True

        response = await self.client.post("/checks", json=payload)
        response.raise_for_status()

        return response.json()

    # ==========================================================================
    # MAILPIECES (Generic tracking)
    # ==========================================================================

    async def get_mailpiece(self, mailpiece_id: str) -> Dict[str, Any]:
        """
        Get status of any mailpiece (postcard, letter, or check)

        Args:
            mailpiece_id: Lob mailpiece ID

        Returns:
            Mailpiece details with tracking
        """
        response = await self.client.get(f"/mailpieces/{mailpiece_id}")
        response.raise_for_status()
        return response.json()

    async def list_mailpieces(
        self,
        limit: int = 10,
        offset: int = 0,
        status: str = None,
        mail_type: str = None
    ) -> Dict[str, Any]:
        """
        List all mailpieces

        Args:
            limit: Number of results
            offset: Pagination offset
            status: Filter by status
            mail_type: Filter by type (postcards, letters, checks)

        Returns:
            List of mailpieces
        """
        params = {"limit": limit, "offset": offset}

        if status:
            params["status"] = status
        if mail_type:
            params["mail_type"] = mail_type

        response = await self.client.get("/mailpieces", params=params)
        response.raise_for_status()
        return response.json()

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def _format_address(self, address: Dict[str, str]) -> Dict[str, str]:
        """
        Format address dictionary for Lob API

        Args:
            address: Address dict with keys like name, address_line1, city, etc.

        Returns:
            Lob-formatted address dict
        """
        return {
            "name": address.get("name", ""),
            "company": address.get("company", ""),
            "address_line1": address.get("address_line1", ""),
            "address_line2": address.get("address_line2", ""),
            "address_city": address.get("address_city", ""),
            "address_state": address.get("address_state", ""),
            "address_zip": address.get("address_zip", ""),
            "address_country": address.get("address_country", "US")
        }

    @staticmethod
    def map_lob_status(lob_status: str) -> MailStatus:
        """Map Lob status to internal MailStatus enum"""
        return LobClient.STATUS_MAPPING.get(
            lob_status.lower(),
            MailStatus.PROCESSING
        )

    @staticmethod
    def render_template(template_html: str, variables: Dict[str, Any]) -> str:
        """
        Render HTML template with variables

        Args:
            template_html: HTML template with {{variable}} placeholders
            variables: Variables to merge into template

        Returns:
            Rendered HTML
        """
        template = Template(template_html)
        return template.render(**variables)


class DirectMailService:
    """
    High-level service for direct mail operations
    Integrates LobClient with database operations
    """

    def __init__(self, db_session, api_key: str = None):
        """
        Initialize direct mail service

        Args:
            db_session: SQLAlchemy database session
            api_key: Optional Lob API key
        """
        self.db = db_session
        self.lob_client = LobClient(api_key=api_key)

    async def send_property_postcard(
        self,
        property_id: int,
        template_name: str,
        to_address: Dict[str, str],
        from_address: Dict[str, str] = None,
        size: str = "4x6",
        agent_id: int = None
    ) -> Dict[str, Any]:
        """
        Send a postcard for a property

        Args:
            property_id: Property ID
            template_name: Template to use
            to_address: Recipient address
            from_address: Sender address (uses agent default if None)
            size: Postcard size
            agent_id: Agent ID

        Returns:
            Created direct mail record
        """
        # Import here to avoid circular imports
        from app.models import Property, Agent
        from app.templates.direct_mail import get_template, render_template

        # Get property details
        property = self.db.query(Property).filter(Property.id == property_id).first()
        if not property:
            raise ValueError(f"Property {property_id} not found")

        # Get agent details for return address
        if agent_id:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if agent and not from_address:
                from_address = {
                    "name": agent.full_name or "Real Estate Agent",
                    "address_line1": agent.office_address or "123 Main St",
                    "address_city": agent.office_city or "Anytown",
                    "address_state": agent.office_state or "CA",
                    "address_zip": agent.office_zip or "90210"
                }

        # Get and render template
        template = get_template(template_name)
        front_html = render_template(
            template["front_html"],
            {
                "property_address": property.full_address,
                "property_price": f"${property.price:,.0f}" if property.price else "",
                "property_bedrooms": property.bedrooms or 0,
                "property_bathrooms": property.bathrooms or 0,
                "property_sqft": property.square_footage or 0,
                "property_photo": property.primary_photo_url or "",
                "agent_name": from_address["name"],
                "agent_phone": agent.phone if agent else "",
                "agent_email": agent.email if agent else ""
            }
        )

        # Send via Lob
        result = await self.lob_client.create_postcard(
            to_address=to_address,
            from_address=from_address,
            front_html=front_html,
            back_html=template.get("back_html", ""),
            size=size
        )

        return result

    async def close(self):
        """Clean up resources"""
        await self.lob_client.close()

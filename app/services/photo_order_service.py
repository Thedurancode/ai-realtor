"""
Property Photo Ordering Service

Integrates with ProxyPics and other photography service providers
to order professional property photography.

Supported Providers:
- ProxyPics (https://proxypics.com) - Primary
- BoxBrownie (https://boxbrownie.com) - Photo editing & virtual staging
- PhotoUp - Real estate photo editing
- Manual - Direct photographer arrangement
"""

import os
import httpx
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.photo_order import (
    PhotoOrder, PhotoOrderItem, PhotoOrderDeliverable, PhotoOrderTemplate,
    PhotoProvider, PhotoOrderStatus, PhotoServiceType
)
from app.models.property import Property
from app.schemas.photo_order import (
    PhotoOrderCreate, PhotoOrderUpdate, PhotoOrderItemCreate,
    PhotoOrderTemplateCreate, PhotoOrderVoiceSummary
)

logger = logging.getLogger(__name__)


# =============================================================================
# PROVIDER API CLIENTS
# =============================================================================

class ProxyPicsClient:
    """
    ProxyPics API Client

    Official API documentation:
    - Live API: https://api.proxypics.com/api/v3
    - Sandbox: https://sandbox.proxypics.com/api/v3
    - Sandbox web app: https://sandbox-app.proxypics.com

    Authentication:
    - API key via `x-api-key` header or `api_key` query parameter
    - Generate keys from Profile page → Integrations

    Two platforms:
    - Crowdsource: Available to any photo taker
    - Direct: Assigned to specific person by phone number
    """

    # ProxyPics webhook event types
    WEBHOOK_EVENTS = {
        "PHOTO_REQUEST_ADDED": "ProxyPicsEvents::PhotoDelivery::PhotoRequestAdded",
        "PHOTO_REQUEST_UNASSIGNED": "ProxyPicsEvents::PhotoDelivery::PhotoRequestUnassigned",
        "PHOTO_REQUEST_ASSIGNED": "ProxyPicsEvents::PhotoDelivery::PhotoRequestAssigned",
        "UPLOAD_STARTED": "ProxyPicsEvents::PhotoDelivery::PhotoRequestUploadStarted",
        "APPOINTMENT_SCHEDULED": "ProxyPicsEvents::PhotoDelivery::AppointmentScheduled",
        "PHOTO_REQUEST_CANCELED": "ProxyPicsEvents::PhotoDelivery::PhotoRequestCanceled",
        "PHOTO_REQUEST_COMPLETED": "ProxyPicsEvents::PhotoDelivery::PhotoRequestCompleted",
        "PHOTO_REQUEST_FULFILLED": "ProxyPicsEvents::PhotoDelivery::PhotoRequestReportGenerated",
        "EXPIRED": "ProxyPicsEvents::PhotoDelivery::PhotoRequestExpired",
        "ON_HOLD": "ProxyPicsEvents::PhotoDelivery::PhotoRequestOnHold",
    }

    # Status mapping from ProxyPics to our internal status
    STATUS_MAPPING = {
        "unassigned": PhotoOrderStatus.PENDING,
        "assigned": PhotoOrderStatus.CONFIRMED,
        "upload_started": PhotoOrderStatus.UPLOADING,
        "completed": PhotoOrderStatus.REVIEW,
        "fulfilled": PhotoOrderStatus.COMPLETED,
        "expired": PhotoOrderStatus.FAILED,
        "canceled": PhotoOrderStatus.CANCELLED,
    }

    def __init__(self):
        self.api_key = os.getenv("PROXYPICS_API_KEY")
        # Default to sandbox for testing
        self.base_url = os.getenv(
            "PROXYPICS_API_URL",
            "https://sandbox.proxypics.com/api/v3/"
        )
        self.timeout = 30.0

    async def create_photo_request(
        self,
        address: str,
        template_token: Optional[str] = None,
        photo_request_platform: str = "crowdsource",
        expires_at: Optional[str] = None,
        property_owner_phone: Optional[str] = None,
        direct_due_date: Optional[str] = None,
        external_id: Optional[str] = None,
        additional_notes: Optional[str] = None,
        loan_number: Optional[str] = None,
        price_boost: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a ProxyPics photo request

        Args:
            address: Property address (will be geocoded)
            template_token: Predefined template token (recommended)
            photo_request_platform: "crowdsource" or "direct"
            expires_at: ISO8601 datetime when request expires (24h default)
            property_owner_phone: Required for Direct platform
            direct_due_date: Required for Direct platform
            external_id: Your external ID for tracking
            additional_notes: Notes for photographer
            loan_number: Loan number
            price_boost: Extra cents to encourage photo takers

        Returns:
            Created PhotoRequest object
        """
        if not self.api_key:
            logger.warning("ProxyPics API key not configured, returning mock response")
            return self._mock_photo_request(address, external_id)

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "address": address,
            "photo_request_platform": photo_request_platform
        }

        # Add optional fields
        if template_token:
            payload["template_token"] = template_token
        if expires_at:
            payload["expires_at"] = expires_at
        if property_owner_phone:
            payload["property_owner_phone"] = property_owner_phone
        if direct_due_date:
            payload["direct_due_date"] = direct_due_date
        if external_id:
            payload["external_id"] = external_id
        if additional_notes:
            payload["additional_notes"] = additional_notes
        if loan_number:
            payload["loan_number"] = loan_number
        if price_boost:
            payload["price_boost"] = price_boost

        # Add any additional fields
        payload.update(kwargs)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/photo_requests",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"ProxyPics API error: {e}")
            raise

    async def get_photo_request(
        self,
        photo_request_id: str
    ) -> Dict[str, Any]:
        """Get details of a specific photo request"""
        if not self.api_key:
            return self._mock_photo_request("Mock Address", photo_request_id)

        headers = {
            "x-api-key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/photo_requests/{photo_request_id}",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"ProxyPics API error: {e}")
            raise

    async def list_photo_requests(
        self,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """List photo requests with pagination"""
        if not self.api_key:
            return {"data": [], "meta": {"pagination": {"total": 0}}}

        headers = {
            "x-api-key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/photo_requests",
                    params={"page": page, "per_page": per_page},
                    headers=headers
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"ProxyPics API error: {e}")
            raise

    async def cancel_photo_request(
        self,
        photo_request_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a photo request

        If status is 'unassigned', it will be cancelled immediately.
        Otherwise, support team is notified to handle cancellation.
        """
        if not self.api_key:
            return {"id": photo_request_id, "status": "canceled"}

        headers = {
            "x-api-key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/photo_requests/{photo_request_id}",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"ProxyPics API error: {e}")
            raise

    async def approve_photo_request(
        self,
        photo_request_id: str
    ) -> Dict[str, Any]:
        """
        Approve a completed photo request

        Approved jobs get fulfilled after payment confirmation.
        Report is generated automatically and webhook is triggered.
        """
        if not self.api_key:
            return {"id": photo_request_id, "status": "approved"}

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/photo_requests/{photo_request_id}/approve",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"ProxyPics API error: {e}")
            raise

    async def reject_photo_request(
        self,
        photo_request_id: str,
        reason: str = "other",
        clarification: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reject a completed photo request

        Reasons: unspecified, blurry_photo, wrong_direction, incorrect_property,
                people_in_photo, property_not_visible, other
        """
        if not self.api_key:
            return {"id": photo_request_id, "status": "rejected"}

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {"reason": reason}
        if clarification:
            payload["clarification"] = clarification

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/photo_requests/{photo_request_id}/reject",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"ProxyPics API error: {e}")
            raise

    async def extend_photo_request(
        self,
        photo_request_id: str,
        expires_at: str
    ) -> Dict[str, Any]:
        """
        Extend an expired photo request

        For Crowdsource: Updates expires_at and makes request available again
        For Direct: Updates assignment expires_at and resets to pending
        """
        if not self.api_key:
            return {"id": photo_request_id, "status": "extended"}

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/photo_requests/{photo_request_id}/extend",
                    json={"expires_at": expires_at},
                    headers=headers
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"ProxyPics API error: {e}")
            raise

    def _mock_photo_request(
        self,
        address: str,
        external_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock photo request for testing without API key"""
        return {
            "id": f"MOCK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "address": address,
            "city": "Mock City",
            "state": "MC",
            "zip": "12345",
            "status": "unassigned",
            "cost": 15000,  # cents ($150)
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "external_id": external_id,
            "download_photos_url": None,
            "download_report_url": None,
            "photo_request_platform": "crowdsource"
        }


class BoxBrownieClient:
    """
    BoxBrownie API Client

    For photo editing, virtual staging, twilight conversion, etc.
    """

    def __init__(self):
        self.api_key = os.getenv("BOXBROWNIE_API_KEY")
        self.base_url = os.getenv(
            "BOXBROWNIE_API_URL",
            "https://api.boxbrownie.com/api/v2/"
        )

    async def submit_editing_job(
        self,
        image_urls: List[str],
        services: List[str],
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit photo editing job to BoxBrownie"""
        # Implementation when API docs become available
        return {"job_id": "mock-job-id", "status": "pending"}


# =============================================================================
# PHOTO ORDER SERVICE
# =============================================================================

class PhotoOrderService:
    """
    Main service for managing property photo orders

    Handles:
    - Creating orders from properties
    - Submitting to providers (ProxyPics, BoxBrownie, etc.)
    - Tracking order status
    - Processing deliverables
    - Voice-ready summaries
    """

    def __init__(self, db: Session):
        self.db = db
        self.proxypics_client = ProxyPicsClient()
        self.boxbrownie_client = BoxBrownieClient()

    def create_order(
        self,
        order_data: PhotoOrderCreate,
        property: Property,
        agent_id: int
    ) -> PhotoOrder:
        """Create a new photo order from a property"""
        # Use property address if not specified
        shoot_address = order_data.shoot_address or property.address
        shoot_city = order_data.shoot_city or property.city
        shoot_state = order_data.shoot_state or property.state
        shoot_zip = order_data.shoot_zip or property.zip_code

        # Create order
        order = PhotoOrder(
            property_id=order_data.property_id,
            agent_id=agent_id,
            provider=order_data.provider,
            order_status=PhotoOrderStatus.DRAFT,
            requested_date=order_data.requested_date,
            time_slot_preference=order_data.time_slot_preference,
            shoot_address=shoot_address,
            shoot_city=shoot_city,
            shoot_state=shoot_state,
            shoot_zip=shoot_zip,
            special_instructions=order_data.special_instructions,
            contact_name=order_data.contact_name,
            contact_phone=order_data.contact_phone,
            contact_email=order_data.contact_email,
            services_requested=order_data.services,
            rooms_count=order_data.rooms_count,
            square_footage=order_data.square_footage or property.square_feet,
            estimated_cost=self._estimate_cost(order_data.services)
        )

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        # Create order items
        for service in order_data.services:
            item = PhotoOrderItem(
                order_id=order.id,
                service_type=service.get("service_type", "basic_editing"),
                service_name=service.get("service_name", service.get("service_type", "Service")),
                description=service.get("description"),
                quantity=service.get("quantity", 1),
                room_name=service.get("room_name"),
                floor=service.get("floor"),
                enhancement_options=service.get("enhancement_options"),
                unit_price=service.get("unit_price")
            )
            self.db.add(item)

        self.db.commit()
        return order

    async def submit_order(
        self,
        order_id: int,
        confirm: bool = True
    ) -> PhotoOrder:
        """Submit order to the provider"""
        order = self.db.query(PhotoOrder).filter(PhotoOrder.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if not confirm:
            return order

        # Prepare provider-specific request
        provider_request = self._prepare_provider_request(order)

        try:
            # Submit to provider
            if order.provider == PhotoProvider.PROXYPICS:
                # Determine platform type (crowdsource or direct)
                platform = "crowdsource"
                if order.contact_phone:
                    platform = "direct"

                response = await self.proxypics_client.create_photo_request(
                    address=order.shoot_address,
                    template_token=None,  # Could be set from order services
                    photo_request_platform=platform,
                    expires_at=order.requested_date.isoformat() if order.requested_date else None,
                    property_owner_phone=order.contact_phone if platform == "direct" else None,
                    external_id=str(order.id),
                    additional_notes=order.special_instructions,
                    price_boost=int(order.estimated_cost * 100) if order.estimated_cost else None
                )

                # Map ProxyPics response to our format
                order.provider_order_id = response.get("id")
                order.order_status = PhotoOrderStatus.PENDING
                order.submitted_at = datetime.utcnow()
                order.provider_response = response

                # Cost is in cents from ProxyPics
                if response.get("cost"):
                    order.estimated_cost = response["cost"] / 100  # Convert cents to dollars
                if response.get("expires_at"):
                    order.estimated_completion = datetime.fromisoformat(response["expires_at"])

            elif order.provider == PhotoProvider.BOXBROWNIE:
                response = await self.boxbrownie_client.submit_editing_job(
                    image_urls=provider_request.get("image_urls", []),
                    services=provider_request.get("services", []),
                    instructions=provider_request.get("instructions")
                )
                order.provider_order_id = response.get("job_id")
                order.order_status = PhotoOrderStatus.PENDING
                order.submitted_at = datetime.utcnow()
            else:
                # Manual orders don't need provider submission
                response = {"order_id": f"MANUAL-{order_id}", "status": "confirmed"}
                order.provider_order_id = response.get("order_id")
                order.order_status = PhotoOrderStatus.CONFIRMED
                order.submitted_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(order)

            return order

        except Exception as e:
            logger.error(f"Failed to submit order {order_id}: {e}")
            order.order_status = PhotoOrderStatus.FAILED
            self.db.commit()
            raise

    def get_order_status(self, order_id: int) -> Dict[str, Any]:
        """Get current status of an order"""
        order = self.db.query(PhotoOrder).filter(PhotoOrder.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        return {
            "order_id": order.id,
            "status": order.order_status.value,
            "provider": order.provider.value,
            "provider_order_id": order.provider_order_id,
            "scheduled_at": order.scheduled_at.isoformat() if order.scheduled_at else None,
            "estimated_completion": order.estimated_completion.isoformat() if order.estimated_completion else None,
            "delivery_count": order.delivery_count,
            "photographer_assigned": order.photographer_assigned
        }

    async def sync_order_status(self, order_id: int) -> PhotoOrder:
        """Sync order status with provider"""
        order = self.db.query(PhotoOrder).filter(PhotoOrder.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.provider == PhotoProvider.MANUAL:
            return order

        try:
            if order.provider == PhotoProvider.PROXYPICS:
                # Get photo request from ProxyPics
                photo_request = await self.proxypics_client.get_photo_request(
                    order.provider_order_id
                )

                # Map ProxyPics status to our internal status
                proxypics_status = photo_request.get("status")
                internal_status = ProxyPicsClient.STATUS_MAPPING.get(proxypics_status)

                if internal_status:
                    order.order_status = internal_status

                    # Set timestamps based on status
                    if internal_status == PhotoOrderStatus.CONFIRMED and not order.confirmed_at:
                        order.confirmed_at = datetime.utcnow()
                    elif internal_status == PhotoOrderStatus.COMPLETED and not order.completed_at:
                        order.completed_at = datetime.utcnow()

                        # Fetch deliverables if available
                        if photo_request.get("download_photos_url"):
                            await self._fetch_deliverables_from_proxy_pics(order, photo_request)

                    elif internal_status == PhotoOrderStatus.REVIEW:
                        # Photos are ready for review
                        if photo_request.get("download_photos_url"):
                            await self._fetch_deliverables_from_proxy_pics(order, photo_request)

                # Update cost if provided (in cents)
                if photo_request.get("cost"):
                    order.actual_cost = photo_request["cost"] / 100

                # Store full response
                order.provider_response = photo_request

                self.db.commit()
                self.db.refresh(order)

                return order

            elif order.provider == PhotoProvider.BOXBROWNIE:
                # TODO: Implement BoxBrownie status sync
                pass

            return order

        except Exception as e:
            logger.error(f"Failed to sync order {order_id}: {e}")
            raise
            self.db.refresh(order)

            return order

        except Exception as e:
            logger.error(f"Failed to sync order {order_id}: {e}")
            raise

    async def _fetch_deliverables_from_proxy_pics(
        self,
        order: PhotoOrder,
        photo_request: Dict[str, Any]
    ):
        """Fetch and process deliverables from ProxyPics photo request"""
        try:
            download_url = photo_request.get("download_photos_url")
            report_url = photo_request.get("download_report_url")

            if download_url:
                # Create a deliverable entry for the ZIP file
                deliverable = PhotoOrderDeliverable(
                    order_id=order.id,
                    file_name=f"photos_{order.provider_order_id}.zip",
                    file_url=download_url,
                    file_type="archive",
                    file_format="zip",
                    processing_status="ready",
                    sequence=0
                )
                self.db.add(deliverable)

            # TODO: Individual photos would need to be fetched from the ZIP
            # This could be done by downloading and extracting the ZIP file
            # For now, we'll create placeholder entries based on the order's services

            if order.services_requested:
                seq = 1
                for service in order.services_requested:
                    service_type = service.get("service_type", "photo")
                    quantity = service.get("quantity", 1)

                    # Create placeholder deliverables for each service
                    for i in range(quantity):
                        deliverable = PhotoOrderDeliverable(
                            order_id=order.id,
                            file_name=f"{service_type}_{i + 1}.jpg",
                            file_url=download_url or "",
                            file_type="photo",
                            file_format="jpg",
                            room_name=service.get("room_name"),
                            sequence=seq,
                            processing_status="pending"  # Will be processed when ZIP is downloaded
                        )
                        self.db.add(deliverable)
                        seq += 1

            order.delivery_url = download_url
            order.delivery_count = seq - 1
            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to fetch deliverables for order {order.id}: {e}")

    def cancel_order(self, order_id: int, reason: Optional[str] = None) -> PhotoOrder:
        """Cancel an order"""
        order = self.db.query(PhotoOrder).filter(PhotoOrder.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Can only cancel draft, pending, or confirmed orders
        if order.order_status not in [
            PhotoOrderStatus.DRAFT,
            PhotoOrderStatus.PENDING,
            PhotoOrderStatus.CONFIRMED
        ]:
            raise ValueError(f"Cannot cancel order in status {order.order_status.value}")

        # If submitted to provider, cancel with provider
        if order.provider_order_id and order.provider == PhotoProvider.PROXYPICS:
            # Note: This is async, but we're in a sync method
            # In production, you'd want to handle this properly
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a task
                    asyncio.create_task(
                        self.proxypics_client.cancel_photo_request(order.provider_order_id)
                    )
                else:
                    # Run the async coroutine
                    loop.run_until_complete(
                        self.proxypics_client.cancel_photo_request(order.provider_order_id)
                    )
            except Exception as e:
                logger.warning(f"Failed to cancel with ProxyPics: {e}")

        order.order_status = PhotoOrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        order.cancellation_reason = reason

        self.db.commit()
        self.db.refresh(order)
        return order

    def get_voice_summary(self, order_id: int) -> PhotoOrderVoiceSummary:
        """Generate voice-friendly summary of order"""
        order = self.db.query(PhotoOrder).filter(PhotoOrder.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        property_obj = self.db.query(Property).filter(Property.id == order.property_id).first()
        property_address = property_obj.address if property_obj else "Unknown"

        # Build natural language summary
        status_messages = {
            "draft": "is being prepared",
            "pending": "has been submitted",
            "confirmed": f"is scheduled for {order.scheduled_at.strftime('%B %d at %I:%M %p') if order.scheduled_at else 'an upcoming date'}",
            "in_progress": "is currently being photographed",
            "uploading": "photos are being uploaded",
            "review": "photos are ready for review",
            "completed": "is complete",
            "cancelled": "has been cancelled"
        }

        base_summary = f"Photo order {order.id} for {property_address} {status_messages.get(order.order_status.value, 'has unknown status')}"

        if order.photographer_assigned:
            base_summary += f". Photographer: {order.photographer_assigned}"

        if order.delivery_count > 0:
            base_summary += f". {order.delivery_count} photos delivered"

        return PhotoOrderVoiceSummary(
            order_id=order.id,
            property_address=property_address,
            status=order.order_status.value,
            scheduled_date=order.scheduled_at.isoformat() if order.scheduled_at else None,
            photographer=order.photographer_assigned,
            services_count=len(order.services_requested) if order.services_requested else 0,
            photos_delivered=order.delivery_count,
            estimated_cost=f"${order.estimated_cost:.2f}" if order.estimated_cost else None,
            voice_summary=base_summary
        )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _prepare_provider_request(self, order: PhotoOrder) -> Dict[str, Any]:
        """Prepare provider-specific API request"""
        return {
            "property_address": {
                "street": order.shoot_address,
                "city": order.shoot_city,
                "state": order.shoot_state,
                "zip": order.shoot_zip,
                "lat": order.shoot_lat,
                "lng": order.shoot_lng
            },
            "requested_date": order.requested_date.isoformat() if order.requested_date else None,
            "time_slot_preference": order.time_slot_preference,
            "services": order.services_requested,
            "special_instructions": order.special_instructions,
            "contact": {
                "name": order.contact_name,
                "phone": order.contact_phone,
                "email": order.contact_email
            } if order.contact_name else None,
            "property_details": {
                "rooms_count": order.rooms_count,
                "square_footage": order.square_footage
            }
        }

    def _estimate_cost(self, services: List[Dict[str, Any]]) -> Optional[float]:
        """Estimate cost based on services requested"""
        # Base pricing (can be overridden with actual provider pricing)
        pricing = {
            "hdr_interior": 15.0,
            "exterior_day": 10.0,
            "exterior_twilight": 20.0,
            "aerial_drone": 50.0,
            "panoramic_360": 25.0,
            "virtual_tour_3d": 100.0,
            "walkthrough_video": 75.0,
            "aerial_video": 100.0,
            "virtual_staging": 30.0,
            "twilight_conversion": 15.0,
            "object_removal": 10.0,
            "sky_replacement": 8.0,
            "floor_plan": 40.0,
            "basic_editing": 5.0,
            "advanced_editing": 15.0
        }

        total = 0.0
        for service in services:
            service_type = service.get("service_type", "basic_editing")
            quantity = service.get("quantity", 1)
            unit_price = service.get("unit_price") or pricing.get(service_type, 10.0)
            total += unit_price * quantity

        return total if total > 0 else None


# =============================================================================
# TEMPLATE SERVICE
# =============================================================================

class PhotoOrderTemplateService:
    """Service for managing reusable photo order templates"""

    def __init__(self, db: Session):
        self.db = db

    def create_template(
        self,
        template_data: PhotoOrderTemplateCreate,
        agent_id: int
    ) -> PhotoOrderTemplate:
        """Create a new order template"""
        template = PhotoOrderTemplate(
            agent_id=agent_id,
            template_name=template_data.template_name,
            description=template_data.description,
            services=template_data.services,
            base_price=template_data.base_price,
            property_types=template_data.property_types,
            tags=template_data.tags,
            is_active=template_data.is_active
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_templates_for_property(
        self,
        agent_id: int,
        property_type: str
    ) -> List[PhotoOrderTemplate]:
        """Get applicable templates for a property type"""
        return (
            self.db.query(PhotoOrderTemplate)
            .filter(
                PhotoOrderTemplate.agent_id == agent_id,
                PhotoOrderTemplate.is_active == True
            )
            .all()
        )  # Can filter by property_type if stored as JSON

    def apply_template(
        self,
        template_id: int,
        property_id: int
    ) -> Dict[str, Any]:
        """Apply a template to create an order"""
        template = (
            self.db.query(PhotoOrderTemplate)
            .filter(PhotoOrderTemplate.id == template_id)
            .first()
        )

        if not template:
            raise ValueError(f"Template {template_id} not found")

        return {
            "property_id": property_id,
            "services": template.services,
            "estimated_cost": template.base_price
        }

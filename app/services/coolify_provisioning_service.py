"""Coolify instance provisioning service.

Handles automatic Coolify instance creation for product purchases.
"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.config import settings
from app.database import SessionLocal, get_db
from sqlalchemy.orm import Session
from app.models.product import Product, UserProduct, AutoProvision

logger = logging.getLogger(__name__)


class CoolifyProvisioningService:
    """Service for auto-provisioning Coolify instances."""

    def __init__(self):
        self.coolify_api_base = getattr(settings, "COOLIFY_API_BASE", None)
        self.coolify_api_key = getattr(settings, "COOLIFY_API_KEY", None)
        self.timeout = httpx.Timeout(30.0)

    async def provision_instance(
        self,
        product_slug: str,
        environment_vars: Dict[str, Any],
    ):
        """Launch a new Coolify instance for a product.

        Args:
            product_slug: Product slug to provision
            environment_vars: Environment variables to pass to instance

        Returns:
            instance_id: Coolify instance ID

        Raises:
            httpx.HTTPStatusError: If API call fails
            Exception: If provision fails
        """
        if not self.coolify_api_base or not self.coolify_api_key:
            logger.warning("Coolify API not configured - auto-provisioning disabled")
            raise Exception("Coolify API not configured")

        logger.info(f"Provisioning Coolify instance for product: {product_slug}")

        url = f"{self.coolify_api_base}/instances"
        headers = {
            "Authorization": f"Bearer {self.coolify_api_key}",
            "Content-Type": "application/json"
        }

        # Build instance payload
        payload = {
            "name": f"AI Realtor - {product_slug}",
            "slug": product_slug,
            "environment": {
                **environment_vars,
            },
            "region": "us-east-1",
            "tier": "starter",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()

                instance_data = response.json()
                instance_id = instance_data.get("id")

                logger.info(f"Successfully created Coolify instance: {instance_id}")
                return instance_id

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to provision Coolify instance: {e}")
            logger.error(f"Response: {e.response.text}")
            raise Exception(f"Failed to provision Coolify instance: {str(e)}")

        except Exception as e:
            logger.error(f"Error provisioning Coolify instance: {e}")
            raise Exception(f"Failed to provision Coolify instance: {str(e)}")


coolify_service = CoolifyProvisioningService()

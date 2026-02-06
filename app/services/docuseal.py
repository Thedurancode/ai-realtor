"""
DocuSeal API integration service for document signing.

API Documentation: https://www.docuseal.com/docs/api
"""
import httpx
from typing import Optional, Dict, Any, List
from app.config import settings


class DocuSealClient:
    """Client for interacting with DocuSeal API."""

    def __init__(self):
        self.api_key = settings.docuseal_api_key
        self.base_url = settings.docuseal_api_url
        self.headers = {
            "X-Auth-Token": self.api_key,
            "Content-Type": "application/json",
        }

    async def create_submission(
        self,
        template_id: str,
        submitters: List[Dict[str, str]],
        send_email: bool = True,
        order: str = "random",
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a submission and send contract for signature.

        Args:
            template_id: DocuSeal template ID
            submitters: List of submitters with email and role
                Example: [{"email": "john@example.com", "role": "Signer"}]
            send_email: Whether to send email notification
            order: "random" for parallel signing, "preserved" for sequential
            message: Custom email message

        Returns:
            Submission response with submission_id and URLs
        """
        url = f"{self.base_url}/submissions"

        payload = {
            "template_id": template_id,
            "send_email": send_email,
            "order": order,
            "submitters": submitters,
        }

        # Self-hosted DocuSeal expects message as object, not string
        # Skip message for now to ensure compatibility
        # if message:
        #     payload["message"] = message

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()

            # Handle both cloud and self-hosted response formats
            # Cloud returns: {"id": X, "submitters": [...], "submission_url": "..."}
            # Self-hosted returns: [{submitter1}, {submitter2}, ...]
            if isinstance(result, list) and len(result) > 0:
                # Self-hosted format - normalize to cloud format
                first_submitter = result[0]
                return {
                    "id": first_submitter.get("submission_id"),
                    "submission_url": first_submitter.get("embed_src"),
                    "submitters": result
                }

            return result

    async def get_submission(self, submission_id: str) -> Dict[str, Any]:
        """
        Get submission details and status.

        Args:
            submission_id: DocuSeal submission ID

        Returns:
            Submission details including status and submitter info
        """
        url = f"{self.base_url}/submissions/{submission_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def list_submissions(
        self,
        template_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        List all submissions.

        Args:
            template_id: Filter by template ID
            limit: Number of results to return

        Returns:
            List of submissions
        """
        url = f"{self.base_url}/submissions"
        params = {"limit": limit}

        if template_id:
            params["template_id"] = template_id

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def archive_submission(self, submission_id: str) -> Dict[str, Any]:
        """
        Archive (cancel) a submission.

        Args:
            submission_id: DocuSeal submission ID

        Returns:
            Archived submission details
        """
        url = f"{self.base_url}/submissions/{submission_id}/archive"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_templates(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all available templates.

        Args:
            limit: Number of templates to return

        Returns:
            List of templates
        """
        from app.services.cache import docuseal_cache

        cache_key = f"templates:{limit}"
        cached = docuseal_cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/templates"
        params = {"limit": limit}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()

            # Handle both self-hosted (returns {"data": [...]})
            # and cloud (returns [...]) response formats
            if isinstance(result, dict) and "data" in result:
                templates = result["data"]
            else:
                templates = result

            docuseal_cache.set(cache_key, templates, ttl_seconds=86400)  # 24 hours
            return templates


# Global DocuSeal client instance
docuseal_client = DocuSealClient()

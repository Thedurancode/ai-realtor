"""
Resend email service for sending contract notifications.

Resend Documentation: https://resend.com/docs
"""
import resend
from typing import Optional, Dict, Any, List
from app.config import settings


class ResendEmailService:
    """Service for sending emails via Resend."""

    def __init__(self):
        self.api_key = settings.resend_api_key
        self.from_email = settings.from_email
        self.from_name = settings.from_name

        if self.api_key:
            resend.api_key = self.api_key

    def send_contract_notification(
        self,
        to_email: str,
        to_name: str,
        contract_name: str,
        property_address: str,
        docuseal_url: str,
        role: str,
        signing_order: Optional[int] = None,
        is_sequential: bool = False,
        custom_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send contract signing notification email.

        Args:
            to_email: Recipient email
            to_name: Recipient name
            contract_name: Name of the contract
            property_address: Property address
            docuseal_url: DocuSeal signing URL
            role: Signer's role (Owner, Lawyer, Agent, etc.)
            signing_order: Order number if sequential
            is_sequential: Whether this is sequential signing
            custom_message: Optional custom message

        Returns:
            Resend response with email ID
        """
        subject = f"Signature Required: {contract_name} - {property_address}"

        # Build order message
        order_text = ""
        if is_sequential and signing_order:
            if signing_order == 1:
                order_text = "You're the first signer."
            else:
                order_text = f"You're signer #{signing_order}. You'll receive another email when it's your turn to sign."

        # Build HTML email
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contract Signature Request</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f8f9fa;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8f9fa; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 48px 40px 40px 40px; text-align: left; border-bottom: 1px solid #e9ecef;">
                            <h1 style="margin: 0 0 8px 0; color: #1a1a1a; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">
                                Signature Required
                            </h1>
                            <p style="margin: 0; color: #6c757d; font-size: 15px; font-weight: 400;">
                                {self.from_name}
                            </p>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 24px 0; color: #495057; font-size: 16px; line-height: 1.6;">
                                Hi <strong style="color: #1a1a1a;">{to_name}</strong>,
                            </p>

                            <p style="margin: 0 0 28px 0; color: #495057; font-size: 16px; line-height: 1.6;">
                                You've been requested to sign the following document as <strong style="color: #1a1a1a;">{role}</strong>:
                            </p>

                            <!-- Contract Details Box -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8f9fa; border-radius: 12px; margin: 0 0 28px 0; border: 1px solid #e9ecef;">
                                <tr>
                                    <td style="padding: 24px;">
                                        <p style="margin: 0 0 4px 0; color: #868e96; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">
                                            Document
                                        </p>
                                        <p style="margin: 0 0 16px 0; color: #1a1a1a; font-size: 20px; font-weight: 600; line-height: 1.3;">
                                            {contract_name}
                                        </p>
                                        <p style="margin: 0 0 4px 0; color: #868e96; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">
                                            Property
                                        </p>
                                        <p style="margin: 0; color: #495057; font-size: 16px; line-height: 1.5;">
                                            {property_address}
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            {f'<div style="margin: 0 0 28px 0; padding: 16px 20px; background-color: #fff8e1; border-radius: 8px; border-left: 4px solid #ffd54f;"><p style="margin: 0; color: #5f5000; font-size: 14px; line-height: 1.6;"><strong style="color: #3e2723;">Signing Order:</strong> {order_text}</p></div>' if order_text else ''}

                            {f'<div style="margin: 0 0 28px 0; padding: 16px 20px; background-color: #f1f8ff; border-radius: 8px; border-left: 4px solid #0969da;"><p style="margin: 0; color: #0a3069; font-size: 15px; line-height: 1.6;">{custom_message}</p></div>' if custom_message else ''}

                            <!-- CTA Button -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 32px 0 24px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{docuseal_url}" style="display: inline-block; padding: 16px 48px; background-color: #1a1a1a; color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: 600; letter-spacing: 0.3px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); transition: all 0.2s;">
                                            Review & Sign →
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 24px 0 0 0; color: #868e96; font-size: 14px; line-height: 1.6; text-align: center;">
                                Questions? Contact the sender for assistance.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 40px; text-align: center; background-color: #fafbfc; border-radius: 0 0 16px 16px; border-top: 1px solid #e9ecef;">
                            <p style="margin: 0 0 8px 0; color: #868e96; font-size: 13px; font-weight: 500;">
                                {self.from_name}
                            </p>
                            <p style="margin: 0; color: #adb5bd; font-size: 12px;">
                                Powered by DocuSeal
                            </p>
                        </td>
                    </tr>
                </table>

                <!-- Security Notice -->
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="margin-top: 24px;">
                    <tr>
                        <td align="center" style="padding: 0 20px;">
                            <p style="margin: 0; color: #adb5bd; font-size: 12px; line-height: 1.6;">
                                This email contains a secure signing link. Always verify the sender before proceeding.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        # Plain text fallback
        text_content = f"""
Hi {to_name},

You've been requested to sign the following document as {role}:

Contract: {contract_name}
Property: {property_address}

{order_text if order_text else ''}

{f"Message: {custom_message}" if custom_message else ""}

Click here to review and sign: {docuseal_url}

---
Powered by DocuSeal & {self.from_name}
This is an automated message.
"""

        try:
            params = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": text_content,
            }

            response = resend.Emails.send(params)
            return {"success": True, "email_id": response.get("id"), "to": to_email}

        except Exception as e:
            return {"success": False, "error": str(e), "to": to_email}

    def send_multi_party_notification(
        self,
        submitters: List[Dict[str, Any]],
        contract_name: str,
        property_address: str,
        is_sequential: bool = False,
        custom_message: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send notifications to multiple submitters.

        Args:
            submitters: List of submitters with name, email, role, docuseal_url, signing_order
            contract_name: Name of the contract
            property_address: Property address
            is_sequential: Whether signing is sequential
            custom_message: Optional custom message

        Returns:
            List of send results
        """
        import time
        results = []

        for i, submitter in enumerate(submitters):
            result = self.send_contract_notification(
                to_email=submitter["email"],
                to_name=submitter["name"],
                contract_name=contract_name,
                property_address=property_address,
                docuseal_url=submitter["docuseal_url"],
                role=submitter["role"],
                signing_order=submitter.get("signing_order"),
                is_sequential=is_sequential,
                custom_message=custom_message,
            )
            results.append(result)

            # Add delay to respect Resend rate limit (2 emails/second)
            if i < len(submitters) - 1:  # Don't delay after last email
                time.sleep(0.6)  # 600ms delay = ~1.6 emails/second

        return results


# Global Resend email service instance
resend_service = ResendEmailService()

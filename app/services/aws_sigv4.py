"""AWS Signature Version 4 Signer

For signing requests to services using AWS Signature Version 4.
Required for D-ID API which uses AWS API Gateway.
"""
import hashlib
import hmac
import datetime
from urllib.parse import urlparse, quote


class AWSSignerV4:
    """AWS Signature Version 4 request signer."""

    def __init__(self, access_key: str, secret_key: str, region: str = "us-east-1", service: str = "execute-api"):
        """
        Initialize AWS SigV4 signer.

        Args:
            access_key: AWS access key ID (or D-ID username)
            secret_key: AWS secret access key (or D-ID API key)
            region: AWS region (default us-east-1)
            service: AWS service name (default execute-api for API Gateway)
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.service = service

    def _sign(self, key: bytes, msg: str) -> bytes:
        """Generate HMAC-SHA256 signature."""
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    def _get_signature_key(self, date_stamp: str) -> bytes:
        """
        Generate signature key.

        Key derivation order:
        kDate = HMAC("AWS4" + SecretKey, Date)
        kRegion = HMAC(kDate, Region)
        kService = HMAC(kRegion, Service)
        kSigning = HMAC(kService, "aws4_request")
        """
        k_date = self._sign(("AWS4" + self.secret_key).encode('utf-8'), date_stamp)
        k_region = self._sign(k_date, self.region)
        k_service = self._sign(k_region, self.service)
        k_signing = self._sign(k_service, "aws4_request")
        return k_signing

    def sign_request(
        self,
        method: str,
        url: str,
        headers: dict,
        body: str = ""
    ) -> dict:
        """
        Sign an HTTP request with AWS Signature Version 4.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL
            headers: Existing headers dict
            body: Request body (empty string for GET)

        Returns:
            Headers dict with added Authorization and X-Amz-Date headers
        """
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        endpoint = parsed_url.path
        query = parsed_url.query

        # Current timestamp
        now = datetime.datetime.utcnow()
        amz_date = now.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = now.strftime('%Y%m%d')

        # Canonical request
        canonical_uri = endpoint or '/'
        canonical_querystring = query

        # Headers must be sorted alphabetically
        canonical_headers = ''
        signed_headers = ''
        if headers:
            sorted_headers = sorted([(k.lower(), v) for k, v in headers.items()])
            canonical_headers = '\n'.join([f"{k}:{v}" for k, v in sorted_headers]) + '\n'
            signed_headers = ';'.join([k for k, v in sorted_headers])

        # Add host header
        canonical_headers += f"host:{host}\n"
        signed_headers = signed_headers + ';host' if signed_headers else 'host'

        # Add x-amz-date header
        canonical_headers += f"x-amz-date:{amz_date}\n"
        signed_headers += ';x-amz-date'

        # Payload hash
        payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()

        # Canonical request
        canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

        # Create string to sign
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"
        string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

        # Calculate signature
        signing_key = self._get_signature_key(date_stamp)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

        # Create authorization header
        authorization_header = (
            f"{algorithm} Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        # Add headers to request
        signed_headers = headers.copy() if headers else {}
        signed_headers['Authorization'] = authorization_header
        signed_headers['x-amz-date'] = amz_date

        return signed_headers


# For D-ID, we need to use the API key as the secret key
# The access key might be the email or a default value
def create_did_signer(did_api_key: str, region: str = "us-east-1") -> AWSSignerV4:
    """
    Create an AWS SigV4 signer for D-ID API.

    D-ID uses AWS API Gateway which requires SigV4.

    Args:
        did_api_key: D-ID API key (format: email:secret or just secret)
        region: AWS region (default us-east-1, try us-east-2, eu-west-1 if fails)

    Returns:
        AWSSignerV4 instance configured for D-ID
    """
    # Parse the key if it contains email:secret format
    if ':' in did_api_key:
        email_part, secret_part = did_api_key.split(':', 1)
        # Use the secret part as both access key and secret key
        # D-ID's API key serves as both for their AWS gateway
        access_key = secret_part
        secret_key = secret_part
    else:
        # Use the key directly as both access and secret
        access_key = did_api_key
        secret_key = did_api_key

    # D-ID uses AWS API Gateway, region may vary
    return AWSSignerV4(
        access_key=access_key,
        secret_key=secret_key,
        region=region,
        service="execute-api"
    )

"""Credential Scrubbing Service.

Inspired by ZeroClaw's credential scrubbing, this module automatically
redacts sensitive information from tool outputs, logs, and conversation
history to prevent accidental exposure of secrets.

Supported patterns:
- API keys: sk-ant-xxx, AKIAxxx, etc.
- Passwords: password":"xxx", "pass":"xxx"
- Tokens: Bearer xxx, token":"xxx
- Secrets: secret":"xxx", SECRET=xxx
- SSNs: 123-45-6789, 123 45 6789
- Credit cards: 1234 5678 9012 3456
- Email addresses: user@example.com (optional)
- Phone numbers: +1-415-555-1234 (optional)
- IP addresses: 192.168.1.1 (optional)

Usage:
    from app.services.credential_scrubbing import scrub_credentials

    raw_output = 'API key: sk-ant-1234567890abcdef'
    clean_output = scrub_credentials(raw_output)
    # Result: 'API key: ***REDACTED***'

    # Or keep partial for debugging
    clean_output = scrub_credentials(raw_output, keep_chars=4)
    # Result: 'API key: sk-ant-***abcdef'
"""

import re
import json
from typing import Any, Dict, List, Optional, Union


class CredentialScrubber:
    """Automatically redact sensitive information from text."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize credential scrubber with configuration.

        Args:
            config: Configuration dictionary with keys:
                - redaction_string: String to replace sensitive data with (default: "***REDACTED***")
                - keep_chars: Number of leading/trailing chars to keep (default: 0)
                - scrub_email: Whether to scrub email addresses (default: True)
                - scrub_phone: Whether to scrub phone numbers (default: True)
                - scrub_ip: Whether to scrub IP addresses (default: True)
                - custom_patterns: List of custom regex patterns (default: [])
        """
        self.config = config or {}
        self.redaction_string = self.config.get("redaction_string", "***REDACTED***")
        self.keep_chars = self.config.get("keep_chars", 0)
        self.scrub_email = self.config.get("scrub_email", True)
        self.scrub_phone = self.config.get("scrub_phone", True)
        self.scrub_ip = self.config.get("scrub_ip", True)
        self.custom_patterns = self.config.get("custom_patterns", [])

        # Compile regex patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile all regex patterns for performance."""

        # API Keys
        self.api_key_patterns = [
            # Anthropic Claude: sk-ant-xxx
            re.compile(r'(sk-ant-[\w-]{20,})', re.IGNORECASE),
            # OpenAI: sk-xxx
            re.compile(r'(sk-[\w]{20,})', re.IGNORECASE),
            # AWS: AKIAxxx
            re.compile(r'(AKIA[0-9A-Z]{16})', re.IGNORECASE),
            # Google: ya29.xxx
            re.compile(r'(ya29\.[\w-]+)', re.IGNORECASE),
            # Generic API key: api_key":"xxx", API_KEY=xxx
            re.compile(r'(["\']?api[_-]?key["\']?\s*[:=]\s*["\']?)([\w-]+)(["\']?)', re.IGNORECASE),
            # Generic: key=xxx, secret=xxx
            re.compile(r'(["\']?(?:key|secret|token)["\']?\s*[:=]\s*["\']?)([\w-]+)(["\']?)', re.IGNORECASE),
        ]

        # Passwords
        self.password_patterns = [
            # JSON: "password":"xxx"
            re.compile(r'(["\']?password["\']?\s*:\s*["\'])([^"\']+)(["\'])', re.IGNORECASE),
            # Form: password=xxx
            re.compile(r'(["\']?password["\']?\s*=\s*["\']?)([^"\'\s]+)(["\']?)', re.IGNORECASE),
            # Pass: pass=xxx, pass":"xxx"
            re.compile(r'(["\']?pass["\']?\s*[:=]\s*["\']?)([^"\'\s]+)(["\']?)', re.IGNORECASE),
        ]

        # Tokens
        self.token_patterns = [
            # Bearer token
            re.compile(r'(Bearer\s+)([\w\.-]+)', re.IGNORECASE),
            # Authorization: token xxx
            re.compile(r'(["\']?token["\']?\s*[:=]\s*["\']?)([\w\.-]+)(["\']?)', re.IGNORECASE),
            # JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
            re.compile(r'(eyJ[\w-]+\.[\w-]+\.[\w-]+)'),
        ]

        # SSNs (Social Security Numbers)
        self.ssn_patterns = [
            # Format: 123-45-6789
            re.compile(r'(\b\d{3}-\d{2}-\d{4}\b)'),
            # Format: 123 45 6789
            re.compile(r'(\b\d{3}\s\d{2}\s\d{4}\b)'),
            # Format: 123456789
            re.compile(r'(\b\d{9}\b)'),
        ]

        # Credit Cards
        self.credit_card_patterns = [
            # Format: 1234 5678 9012 3456
            re.compile(r'(\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b)'),
            # Format: 1234-5678-9012-3456
            re.compile(r'(\b\d{4}-\d{4}-\d{4}-\d{4}\b)'),
            # Format: 1234567890123456
            re.compile(r'(\b(?:\d[ -]*?){13,16}\b)'),
        ]

        # Email addresses (optional)
        self.email_pattern = re.compile(r'([\w\.-]+@[\w\.-]+\.\w+)') if self.scrub_email else None

        # Phone numbers (optional)
        self.phone_patterns = [
            # Format: +1-415-555-1234
            re.compile(r'(\+?\d{1,3}[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4})'),
            # Format: (415) 555-1234
            re.compile(r'(\(\d{3}\)\s*\d{3}-\d{4})'),
            # Format: 415-555-1234
            re.compile(r'(\d{3}-\d{3}-\d{4})'),
        ] if self.scrub_phone else []

        # IP addresses (optional)
        self.ip_pattern = re.compile(r'(\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)') if self.scrub_ip else None

        # Custom patterns
        self.custom_regex_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.custom_patterns
        ]

    def _redact_match(self, match: re.Match) -> str:
        """Redact a regex match with optional character preservation.

        Args:
            match: Regex match object

        Returns:
            Redacted string
        """
        full_match = match.group(0)

        if self.keep_chars > 0:
            # Keep leading and trailing characters
            if len(full_match) <= self.keep_chars * 2:
                # Too short to redact
                return full_match
            else:
                leading = full_match[:self.keep_chars]
                trailing = full_match[-self.keep_chars:]
                return f"{leading}{self.redaction_string}{trailing}"
        else:
            # Full redaction
            return self.redaction_string

    def _redact_match_keep_context(self, match: re.Match, context_groups: List[int] = None) -> str:
        """Redact match but preserve context (key names, etc.).

        Args:
            match: Regex match object
            context_groups: List of group indices to preserve

        Returns:
            Redacted string with context preserved
        """
        if context_groups:
            # Preserve specified groups
            result = ""
            last_end = 0
            for i in range(1, len(match.groups()) + 1):
                if match.start(i) > last_end:
                    result += match.group(0)[last_end:match.start(i)]
                if i in context_groups:
                    # Keep context
                    result += match.group(i)
                else:
                    # Redact sensitive value
                    value = match.group(i)
                    if self.keep_chars > 0 and len(value) > self.keep_chars * 2:
                        result += f"{value[:self.keep_chars]}{self.redaction_string}{value[-self.keep_chars:]}"
                    else:
                        result += self.redaction_string
                last_end = match.end(i)
            if last_end < len(match.group(0)):
                result += match.group(0)[last_end:]
            return result
        else:
            return self._redact_match(match)

    def scrub(self, text: str) -> str:
        """Scrub sensitive information from text.

        Args:
            text: Input text that may contain sensitive information

        Returns:
            Text with sensitive information redacted
        """
        if not text:
            return text

        result = text

        # Scrub API keys
        for pattern in self.api_key_patterns:
            result = pattern.sub(self._redact_match_keep_context, result)

        # Scrub passwords
        for pattern in self.password_patterns:
            result = pattern.sub(
                lambda m: self._redact_match_keep_context(m, context_groups=[1, 3]),
                result
            )

        # Scrub tokens
        for pattern in self.token_patterns:
            result = pattern.sub(
                lambda m: self._redact_match_keep_context(m, context_groups=[1]),
                result
            )

        # Scrub SSNs
        for pattern in self.ssn_patterns:
            result = pattern.sub(self._redact_match, result)

        # Scrub credit cards
        for pattern in self.credit_card_patterns:
            result = pattern.sub(self._redact_match, result)

        # Scrub emails
        if self.email_pattern:
            result = self.email_pattern.sub(
                lambda m: f"{m.group(1)[:3]}{self.redaction_string}",
                result
            )

        # Scrub phone numbers
        for pattern in self.phone_patterns:
            result = pattern.sub(self._redact_match, result)

        # Scrub IP addresses
        if self.ip_pattern:
            result = self.ip_pattern.sub(self._redact_match, result)

        # Scrub custom patterns
        for pattern in self.custom_regex_patterns:
            result = pattern.sub(self._redact_match, result)

        return result

    def scrub_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively scrub dictionary values.

        Args:
            data: Dictionary that may contain sensitive information

        Returns:
            Dictionary with sensitive values redacted
        """
        if not isinstance(data, dict):
            return data

        scrubbed = {}
        for key, value in data.items():
            # Check if key looks sensitive
            if any(sensitive in key.lower() for sensitive in [
                "password", "token", "api_key", "secret", "key",
                "ssn", "social_security", "credit_card", "account_number"
            ]):
                # Redact entire value
                if isinstance(value, str):
                    scrubbed[key] = self.redaction_string
                elif isinstance(value, (dict, list)):
                    scrubbed[key] = self.redaction_string
                else:
                    scrubbed[key] = self.redaction_string
            elif isinstance(value, str):
                # Scrub string values
                scrubbed[key] = self.scrub(value)
            elif isinstance(value, dict):
                # Recursively scrub nested dicts
                scrubbed[key] = self.scrub_dict(value)
            elif isinstance(value, list):
                # Recursively scrub lists
                scrubbed[key] = self.scrub_list(value)
            else:
                # Keep other types as-is
                scrubbed[key] = value

        return scrubbed

    def scrub_list(self, data: List[Any]) -> List[Any]:
        """Recursively scrub list values.

        Args:
            data: List that may contain sensitive information

        Returns:
            List with sensitive values redacted
        """
        if not isinstance(data, list):
            return data

        scrubbed = []
        for item in data:
            if isinstance(item, str):
                scrubbed.append(self.scrub(item))
            elif isinstance(item, dict):
                scrubbed.append(self.scrub_dict(item))
            elif isinstance(item, list):
                scrubbed.append(self.scrub_list(item))
            else:
                scrubbed.append(item)

        return scrubbed

    def scrub_json(self, json_str: str) -> str:
        """Parse, scrub, and re-serialize JSON string.

        Args:
            json_str: JSON string that may contain sensitive information

        Returns:
            Scrubbed JSON string

        Raises:
            json.JSONDecodeError: If json_str is not valid JSON
        """
        data = json.loads(json_str)
        scrubbed = self.scrub_dict(data)
        return json.dumps(scrubbed, indent=2)

    def scrub_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Scrub a log entry (conversation history, audit log, etc.).

        Args:
            log_entry: Log entry dictionary

        Returns:
            Scrubbed log entry
        """
        scrubbed = {}

        for key, value in log_entry.items():
            if key in ["input", "output", "result", "response"]:
                # Scrub these fields
                if isinstance(value, str):
                    scrubbed[key] = self.scrub(value)
                elif isinstance(value, dict):
                    scrubbed[key] = self.scrub_dict(value)
                elif isinstance(value, list):
                    scrubbed[key] = self.scrub_list(value)
                else:
                    scrubbed[key] = value
            else:
                # Keep other fields as-is
                scrubbed[key] = value

        return scrubbed


# Global singleton instance
default_scrubber = CredentialScrubber()


def scrub_credentials(
    data: Union[str, Dict, List],
    config: Optional[Dict] = None
) -> Union[str, Dict, List]:
    """Convenience function to scrub sensitive information.

    Args:
        data: String, dictionary, or list to scrub
        config: Optional configuration for scrubber

    Returns:
        Scrubbed data with same type as input

    Examples:
        >>> scrub_credentials("API key: sk-ant-1234567890")
        'API key: ***REDACTED***'

        >>> scrub_credentials({"api_key": "sk-ant-1234567890", "name": "test"})
        {'api_key': '***REDACTED***', 'name': 'test'}

        >>> scrub_credentials("API key: sk-ant-1234567890", config={"keep_chars": 4})
        'API key: sk-ant-***7890'
    """
    if config:
        scrubber = CredentialScrubber(config)
    else:
        scrubber = default_scrubber

    if isinstance(data, str):
        return scrubber.scrub(data)
    elif isinstance(data, dict):
        return scrubber.scrub_dict(data)
    elif isinstance(data, list):
        return scrubber.scrub_list(data)
    else:
        return data

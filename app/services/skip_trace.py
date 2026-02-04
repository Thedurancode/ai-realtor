import random
import hashlib
from typing import Any
import httpx
from app.config import settings


class RapidAPISkipTraceService:
    """
    Real skip trace service using RapidAPI Skip Tracing API.
    """

    def __init__(self):
        self.api_key = settings.rapidapi_key
        self.api_host = settings.skip_trace_api_host
        self.base_url = f"https://{self.api_host}"

    async def skip_trace(
        self, address: str, city: str, state: str, zip_code: str
    ) -> dict[str, Any]:
        """
        Perform skip trace using RapidAPI.
        Returns owner contact information for the given address.
        """
        headers = {
            "x-rapidapi-host": self.api_host,
            "x-rapidapi-key": self.api_key,
        }

        # Step 1: Search by address to get person IDs
        citystatezip = f"{city}, {state} {zip_code}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search/byaddress",
                params={
                    "street": address,
                    "citystatezip": citystatezip,
                    "page": 1
                },
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            search_result = response.json()

        people = search_result.get("PeopleDetails", [])

        if not people:
            # No results found, return empty data
            return {
                "owner_name": "Unknown Owner",
                "owner_first_name": None,
                "owner_last_name": None,
                "phone_numbers": [],
                "emails": [],
                "mailing_address": None,
                "mailing_city": None,
                "mailing_state": None,
                "mailing_zip": None,
                "raw_response": search_result,
            }

        # Get the first person (most likely current owner)
        primary_person = people[0]
        person_id = primary_person.get("Person ID")
        truepeoplesearch_link = primary_person.get("Link", "")

        # Note: This API tier provides basic info only
        # Phone numbers and emails require visiting the TruePeopleSearch link
        # or upgrading to a premium skip trace API
        phone_numbers = []
        emails = []

        # Store the link for manual lookup if needed
        if truepeoplesearch_link:
            # Add a note about where to find contact info
            phone_numbers.append({
                "number": "Visit link for details",
                "type": "info",
                "status": "link_available",
                "link": truepeoplesearch_link
            })

        # Parse name
        full_name = primary_person.get("Name", "Unknown Owner")
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0] if len(name_parts) > 0 else None
        last_name = name_parts[1] if len(name_parts) > 1 else None

        # Check if they used to live elsewhere (different mailing address)
        used_to_live = primary_person.get("Used to live in", "")
        mailing_address = None
        mailing_city = None
        mailing_state = None
        mailing_zip = None

        # If current address doesn't match, they might have different mailing
        current_location = primary_person.get("Lives in", "")
        if current_location and f"{city}, {state}" not in current_location:
            mailing_city = city
            mailing_state = state
            mailing_zip = zip_code

        # Add useful info from API as email placeholders
        age = primary_person.get("Age")
        related_to = primary_person.get("Related to", "")

        # Add informational "emails" with useful data
        if truepeoplesearch_link:
            emails.append({
                "email": f"Age: {age}, Related: {related_to[:30]}...",
                "type": "info"
            })

        return {
            "owner_name": full_name,
            "owner_first_name": first_name,
            "owner_last_name": last_name,
            "phone_numbers": phone_numbers,
            "emails": emails,
            "mailing_address": mailing_address,
            "mailing_city": mailing_city,
            "mailing_state": mailing_state,
            "mailing_zip": mailing_zip,
            "raw_response": {
                "search_result": search_result,
                "person_count": len(people),
                "primary_person": primary_person,
                "truepeoplesearch_link": truepeoplesearch_link,
                "age": age,
                "current_location": current_location,
                "used_to_live": used_to_live,
                "related_to": related_to
            },
        }


class MockSkipTraceService:
    """
    Mock skip trace service that generates realistic-looking owner data.
    Replace with real API integration (BatchSkipTracing, SkipGenie, etc.) later.
    """

    # Sample data for generating mock responses
    FIRST_NAMES = [
        "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
        "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy"
    ]

    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson"
    ]

    EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "aol.com", "icloud.com"]

    def _generate_seed(self, address: str, city: str, state: str) -> int:
        """Generate consistent seed from address for reproducible mock data."""
        seed_string = f"{address}{city}{state}".lower()
        return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)

    def _generate_phone(self, seed: int, index: int) -> str:
        """Generate a realistic phone number."""
        random.seed(seed + index)
        area_code = random.randint(200, 999)
        prefix = random.randint(200, 999)
        line = random.randint(1000, 9999)
        return f"({area_code}) {prefix}-{line}"

    def _generate_email(self, first_name: str, last_name: str, seed: int) -> str:
        """Generate a realistic email."""
        random.seed(seed)
        domain = random.choice(self.EMAIL_DOMAINS)
        formats = [
            f"{first_name.lower()}.{last_name.lower()}@{domain}",
            f"{first_name.lower()}{last_name.lower()}@{domain}",
            f"{first_name[0].lower()}{last_name.lower()}@{domain}",
            f"{first_name.lower()}{random.randint(1, 99)}@{domain}",
        ]
        return random.choice(formats)

    async def skip_trace(
        self, address: str, city: str, state: str, zip_code: str
    ) -> dict[str, Any]:
        """
        Perform a mock skip trace lookup.
        Returns owner contact information for the given address.

        In production, replace this with actual API call to:
        - BatchSkipTracing API
        - SkipGenie API
        - REI Skip Trace API
        - etc.
        """
        seed = self._generate_seed(address, city, state)
        random.seed(seed)

        first_name = random.choice(self.FIRST_NAMES)
        last_name = random.choice(self.LAST_NAMES)
        owner_name = f"{first_name} {last_name}"

        # Generate 1-3 phone numbers
        num_phones = random.randint(1, 3)
        phone_types = ["mobile", "landline", "work"]
        phone_numbers = []
        for i in range(num_phones):
            phone_numbers.append({
                "number": self._generate_phone(seed, i),
                "type": phone_types[i] if i < len(phone_types) else "other",
                "status": random.choice(["valid", "valid", "valid", "unknown"]),  # 75% valid
            })

        # Generate 1-2 emails
        num_emails = random.randint(1, 2)
        emails = []
        for i in range(num_emails):
            emails.append({
                "email": self._generate_email(first_name, last_name, seed + i),
                "type": "personal" if i == 0 else "secondary",
            })

        # 30% chance mailing address is different from property
        mailing_address = None
        mailing_city = None
        mailing_state = None
        mailing_zip = None

        if random.random() < 0.3:
            mailing_address = f"{random.randint(100, 9999)} {random.choice(['Oak', 'Maple', 'Cedar', 'Pine', 'Elm'])} {random.choice(['St', 'Ave', 'Dr', 'Ln'])}"
            mailing_city = city  # Keep same city for simplicity
            mailing_state = state
            mailing_zip = zip_code

        return {
            "owner_name": owner_name,
            "owner_first_name": first_name,
            "owner_last_name": last_name,
            "phone_numbers": phone_numbers,
            "emails": emails,
            "mailing_address": mailing_address,
            "mailing_city": mailing_city,
            "mailing_state": mailing_state,
            "mailing_zip": mailing_zip,
            "raw_response": {
                "source": "mock_service",
                "confidence": random.uniform(0.85, 0.99),
            },
        }


skip_trace_service = RapidAPISkipTraceService()

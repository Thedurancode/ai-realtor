import httpx
from app.config import settings


class GooglePlacesService:
    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    def __init__(self):
        self.api_key = settings.google_places_api_key

    async def autocomplete(
        self, input_text: str, types: str = "address", country: str = "us"
    ) -> list[dict]:
        """
        Get address suggestions from Google Places Autocomplete.
        Returns a list of predictions with place_id and description.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/autocomplete/json",
                params={
                    "input": input_text,
                    "types": types,
                    "components": f"country:{country}",
                    "key": self.api_key,
                },
            )
            data = response.json()

            if data.get("status") != "OK":
                return []

            return [
                {
                    "place_id": p["place_id"],
                    "description": p["description"],
                    "main_text": p["structured_formatting"]["main_text"],
                    "secondary_text": p["structured_formatting"].get(
                        "secondary_text", ""
                    ),
                }
                for p in data.get("predictions", [])
            ]

    async def get_place_details(self, place_id: str) -> dict | None:
        """
        Get full address details from a place_id.
        Returns parsed address components.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/details/json",
                params={
                    "place_id": place_id,
                    "fields": "formatted_address,address_components,geometry",
                    "key": self.api_key,
                },
            )
            data = response.json()

            if data.get("status") != "OK":
                return None

            result = data.get("result", {})
            components = {
                c["types"][0]: c["long_name"]
                for c in result.get("address_components", [])
            }

            return {
                "formatted_address": result.get("formatted_address", ""),
                "street_number": components.get("street_number", ""),
                "street": components.get("route", ""),
                "city": components.get("locality", "")
                or components.get("sublocality", ""),
                "state": components.get("administrative_area_level_1", ""),
                "zip_code": components.get("postal_code", ""),
                "country": components.get("country", ""),
                "lat": result.get("geometry", {}).get("location", {}).get("lat"),
                "lng": result.get("geometry", {}).get("location", {}).get("lng"),
            }


google_places_service = GooglePlacesService()

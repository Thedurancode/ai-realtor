from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_places_api_key: str = ""
    docuseal_api_key: str = ""
    docuseal_api_url: str = "https://api.docuseal.com"
    resend_api_key: str = ""
    from_email: str = "noreply@yourdomain.com"
    from_name: str = "Real Estate Contracts"
    rapidapi_key: str = ""
    skip_trace_api_host: str = "skip-tracing-working-api.p.rapidapi.com"
    zillow_api_host: str = "private-zillow.p.rapidapi.com"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

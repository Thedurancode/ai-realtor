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
    exa_api_key: str = ""
    exa_base_url: str = "https://api.exa.ai"
    exa_search_type: str = "auto"
    exa_timeout_seconds: int = 20

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

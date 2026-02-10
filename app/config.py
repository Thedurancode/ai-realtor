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
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    rentcast_api_key: str = ""
    exa_api_key: str = ""
    exa_base_url: str = "https://api.exa.ai"
    exa_search_type: str = "auto"
    exa_timeout_seconds: int = 20
    vapi_api_key: str = ""
    vapi_phone_number_id: str = ""
    vapi_webhook_secret: str = ""
    campaign_worker_enabled: bool = True
    campaign_worker_interval_seconds: int = 15
    campaign_worker_max_calls_per_tick: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

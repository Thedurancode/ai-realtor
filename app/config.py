from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_places_api_key: str = ""
    docuseal_api_key: str = ""
    docuseal_api_url: str = "https://api.docuseal.com"
    resend_api_key: str = ""
    resend_from_email: str = "notifications@ai-realtor.com"
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
    daily_digest_enabled: bool = True
    daily_digest_hour: int = 8

    # Remotion Rendering
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    worker_concurrency: int = 1

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    aws_s3_bucket: str = "ai-realtor-renders"

    # Lob.com Direct Mail
    lob_api_key: str = ""
    lob_webhook_secret: str = ""
    lob_test_mode: bool = False

    # Enhanced Video Generation
    heygen_api_key: str = ""  # HeyGen API for avatar videos
    did_api_key: str = ""  # D-ID API for talking head videos
    replicate_api_key: str = ""  # Replicate API for PixVerse footage
    elevenlabs_api_key: str = ""  # ElevenLabs for text-to-speech
    openrouter_api_key: str = ""  # OpenRouter for Claude AI script generation

    # CORS Configuration
    cors_origins: str = "http://localhost:3025,http://localhost:3000,http://localhost:8000"

    # Customer Portal JWT Secret
    portal_jwt_secret: str = "change-this-in-production-use-a-strong-random-secret"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

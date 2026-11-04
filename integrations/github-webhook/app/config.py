"""Settings come from environment variables, checked by Pydantic.

Why env vars: the same code runs on a laptop, in CI and in a container;
only the environment changes. Secrets never live in the code or in Git.
"""

import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    github_webhook_secret: str = Field(default="", description="Shared secret set on the GitHub webhook")
    log_level: str = Field(default="INFO")
    # Day 19: Port API access (optional until the weekend, when the receiver writes to Port)
    port_client_id: str = Field(default="")
    port_client_secret: str = Field(default="")
    port_api_url: str = Field(default="https://api.port.io/v1")
    # Day 19: how long we remember a delivery ID, and how many we keep
    dedupe_ttl_seconds: int = Field(default=3600, ge=60)
    dedupe_max_entries: int = Field(default=10000, ge=100)


def get_settings() -> Settings:
    """Read the environment every time it is called (so tests can change it)."""
    return Settings(
        github_webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET", ""),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        port_client_id=os.getenv("PORT_CLIENT_ID", ""),
        port_client_secret=os.getenv("PORT_CLIENT_SECRET", ""),
        port_api_url=os.getenv("PORT_API_URL", "https://api.port.io/v1"),
        dedupe_ttl_seconds=int(os.getenv("DEDUPE_TTL_SECONDS", "3600")),
        dedupe_max_entries=int(os.getenv("DEDUPE_MAX_ENTRIES", "10000")),
    )

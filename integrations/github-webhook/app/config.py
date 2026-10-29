"""Settings come from environment variables, checked by Pydantic.

Why env vars: the same code runs on a laptop, in CI and in a container;
only the environment changes. Secrets never live in the code or in Git.
"""

import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    github_webhook_secret: str = Field(default="", description="Shared secret set on the GitHub webhook")
    log_level: str = Field(default="INFO")


def get_settings() -> Settings:
    """Read the environment every time it is called (so tests can change it)."""
    return Settings(
        github_webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET", ""),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )

"""Pydantic models: only the fields we care about from a GitHub pull_request event.

GitHub sends a very large JSON. Pydantic keeps the fields we declare, checks their
types, and ignores the rest. If a required field is missing we get a clear error.
"""

from pydantic import BaseModel


class User(BaseModel):
    login: str


class Repository(BaseModel):
    full_name: str


class PullRequest(BaseModel):
    number: int
    title: str
    state: str
    html_url: str
    merged: bool = False
    user: User


class PullRequestEvent(BaseModel):
    action: str
    pull_request: PullRequest
    repository: Repository

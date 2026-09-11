"""PyGithub-backed GitHub service."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, Any

from github import Auth, Github

from .base import Service

if TYPE_CHECKING:
    from github.AuthenticatedUser import AuthenticatedUser
    from github.NamedUser import NamedUser
    from github.Organization import Organization
    from github.PaginatedList import PaginatedList
    from github.RateLimitOverview import RateLimitOverview
    from github.Repository import Repository, RepositorySearchResult

DEFAULT_BASE_URL = "https://api.github.com"
DEFAULT_TIMEOUT = 15


@dataclass(frozen=True, slots=True)
class GithubSettings:
    """Settings loaded from the ``[services.github]`` configuration section."""

    token: str | None = None
    base_url: str = DEFAULT_BASE_URL
    timeout: int = DEFAULT_TIMEOUT

    @classmethod
    def from_mapping(cls, config: Mapping[str, Any]) -> GithubSettings:
        """Validate a raw configuration mapping."""
        unknown_keys = set(config) - {"token", "base_url", "timeout"}
        if unknown_keys:
            names = ", ".join(sorted(unknown_keys))
            raise ValueError(f"Unknown GitHub setting(s): {names}")

        token_value = config.get("token")
        token = str(token_value).strip() if token_value is not None else None

        base_url_value = config.get("base_url", DEFAULT_BASE_URL)
        base_url = str(base_url_value).strip()
        if not base_url:
            raise ValueError("GitHub base_url must not be empty")

        timeout = int(config.get("timeout", DEFAULT_TIMEOUT))
        if timeout <= 0:
            raise ValueError("GitHub timeout must be greater than zero")

        return cls(token=token or None, base_url=base_url, timeout=timeout)


class GithubClient(Service):
    """Expose common PyGithub operations through a test-friendly facade."""

    def __init__(self, github_client: Github) -> None:
        self._github_client = github_client

    @property
    def raw_client(self) -> Github:
        """Return the underlying PyGithub client for advanced use cases."""
        return self._github_client

    def get_authenticated_user(self) -> AuthenticatedUser:
        """Return the user associated with the configured token."""
        return self._github_client.get_user()

    def get_user(self, login: str) -> NamedUser:
        """Return a GitHub user by login."""
        return self._github_client.get_user(login)

    def get_repo(self, full_name_or_id: int | str) -> Repository:
        """Return a repository by ``owner/name`` or numeric identifier."""
        return self._github_client.get_repo(full_name_or_id)

    def get_organization(self, org: str) -> Organization:
        """Return an organization by login."""
        return self._github_client.get_organization(org)

    def get_rate_limit(self) -> RateLimitOverview:
        """Return the current GitHub API rate-limit overview."""
        return self._github_client.get_rate_limit()

    def search_repositories(
        self,
        query: str,
        **qualifiers: Any,
    ) -> PaginatedList[RepositorySearchResult]:
        """Search repositories using the GitHub search API."""
        return self._github_client.search_repositories(query, **qualifiers)

    def close(self) -> None:
        """Close the underlying HTTP connections."""
        self._github_client.close()

    def __getattr__(self, name: str) -> Any:
        """Delegate other attributes and methods to PyGithub."""
        return getattr(self._github_client, name)

    def __enter__(self) -> GithubClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def build_github_client(config: Mapping[str, Any]) -> GithubClient:
    """Build a configured GitHub service."""
    settings = GithubSettings.from_mapping(config)
    client_kwargs: dict[str, Any] = {
        "base_url": settings.base_url,
        "timeout": settings.timeout,
    }
    if settings.token:
        client_kwargs["auth"] = Auth.Token(settings.token)

    github_client = Github(**client_kwargs)
    return GithubClient(github_client)

"""
API package for aircloudhome.

Architecture:
    Three-layer data flow: Entities → Coordinator → API Client.
    Only the coordinator should call the API client. Entities must never
    import or call the API client directly.

Exception hierarchy:
    AirCloudHomeApiClientError (base)
    ├── AirCloudHomeApiClientCommunicationError (network/timeout)
    ├── AirCloudHomeApiClientAuthenticationError (401/403)
    └── AirCloudHomeApiClientAccountLockedError (423, too many failed sign-ins)

Coordinator exception mapping:
    ApiClientAuthenticationError → ConfigEntryAuthFailed (triggers reauth)
    ApiClientCommunicationError → UpdateFailed (auto-retry)
    ApiClientAccountLockedError → UpdateFailed (auto-retry, no reauth)
    ApiClientError             → UpdateFailed (auto-retry)
"""

from .client import (
    API_BASE_URLS,
    AirCloudHomeApiClient,
    AirCloudHomeApiClientAccountLockedError,
    AirCloudHomeApiClientAuthenticationError,
    AirCloudHomeApiClientCommunicationError,
    AirCloudHomeApiClientError,
    AirCloudHomeRegion,
)

__all__ = [
    "API_BASE_URLS",
    "AirCloudHomeApiClient",
    "AirCloudHomeApiClientAccountLockedError",
    "AirCloudHomeApiClientAuthenticationError",
    "AirCloudHomeApiClientCommunicationError",
    "AirCloudHomeApiClientError",
    "AirCloudHomeRegion",
]

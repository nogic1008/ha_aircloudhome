"""
API package for aircloudhome.

Architecture:
    Three-layer data flow: Entities → Coordinator → API Client.
    Only the coordinator should call the API client. Entities must never
    import or call the API client directly.

Exception hierarchy:
    AirCloudHomeApiClientError (base)
    ├── AirCloudHomeApiClientCommunicationError (network/timeout)
    └── AirCloudHomeApiClientAuthenticationError (401/403)

Coordinator exception mapping:
    ApiClientAuthenticationError → ConfigEntryAuthFailed (triggers reauth)
    ApiClientCommunicationError → UpdateFailed (auto-retry)
    ApiClientError             → UpdateFailed (auto-retry)
"""

from .client import (
    AirCloudHomeApiClient,
    AirCloudHomeApiClientAuthenticationError,
    AirCloudHomeApiClientCommunicationError,
    AirCloudHomeApiClientError,
)

__all__ = [
    "AirCloudHomeApiClient",
    "AirCloudHomeApiClientAuthenticationError",
    "AirCloudHomeApiClientCommunicationError",
    "AirCloudHomeApiClientError",
]

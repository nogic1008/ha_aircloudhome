"""
Config flow schemas.

Schemas for the main configuration flow steps:
- User setup
- Reconfiguration
- Reauthentication

When this file grows too large (>300 lines), consider splitting into:
- user.py: User setup schemas
- reauth.py: Reauthentication schemas
- reconfigure.py: Reconfiguration schemas
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from custom_components.aircloudhome.api import AirCloudHomeRegion
from custom_components.aircloudhome.const import CONF_REGION
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector

REGION_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[region.value for region in AirCloudHomeRegion],
        mode=selector.SelectSelectorMode.LIST,
        translation_key=CONF_REGION,
    ),
)


def get_user_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """
    Get schema for user step (initial setup).

    Args:
        defaults: Optional dictionary of default values to pre-populate the form.

    Returns:
        Voluptuous schema for user credentials input.

    """
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_REGION,
                default=defaults.get(CONF_REGION, AirCloudHomeRegion.JAPAN.value),
            ): REGION_SELECTOR,
            vol.Required(
                CONF_USERNAME,
                default=defaults.get(CONF_USERNAME, vol.UNDEFINED),
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                ),
            ),
            vol.Required(CONF_PASSWORD): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.PASSWORD,
                ),
            ),
        },
    )


def get_reconfigure_schema(email: str, region: str) -> vol.Schema:
    """
    Get schema for reconfigure step.

    Args:
        email: Current email to pre-fill in the form.
        region: Current cloud region to preselect in the form.

    Returns:
        Voluptuous schema for reconfiguration.

    """
    return vol.Schema(
        {
            vol.Required(CONF_REGION, default=region): REGION_SELECTOR,
            vol.Required(
                CONF_USERNAME,
                default=email,
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                ),
            ),
            vol.Required(
                CONF_PASSWORD,
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.PASSWORD,
                ),
            ),
        },
    )


def get_reauth_schema(email: str) -> vol.Schema:
    """
    Get schema for reauthentication step.

    Args:
        email: Current email to pre-fill in the form.

    Returns:
        Voluptuous schema for reauthentication.

    """
    return vol.Schema(
        {
            vol.Required(
                CONF_USERNAME,
                default=email,
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                ),
            ),
            vol.Required(
                CONF_PASSWORD,
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.PASSWORD,
                ),
            ),
        },
    )


__all__ = [
    "get_reauth_schema",
    "get_reconfigure_schema",
    "get_user_schema",
]

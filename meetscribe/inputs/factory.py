"""
Factory for INPUT layer providers.
"""

from typing import Dict, Any

from ..core.providers import InputProvider


def get_input_provider(provider_name: str, config: Dict[str, Any]) -> InputProvider:
    """
    Get INPUT provider by name.

    Args:
        provider_name: Provider identifier (discord, zoom, meet, etc.)
        config: Provider configuration

    Returns:
        InputProvider instance

    Raises:
        ValueError: If provider is not supported
    """
    providers = {
        'discord': 'meetscribe.inputs.discord_provider.DiscordProvider',
        'zoom': 'meetscribe.inputs.zoom_provider.ZoomProvider',
        'meet': 'meetscribe.inputs.meet_provider.MeetProvider',
        'proctap': 'meetscribe.inputs.proctap_provider.ProcTapProvider',
        'obs': 'meetscribe.inputs.obs_provider.OBSProvider',
    }

    if provider_name not in providers:
        raise ValueError(f"Unsupported input provider: {provider_name}")

    # For MVP, raise NotImplementedError
    # Providers will be implemented in future versions
    raise NotImplementedError(f"Provider '{provider_name}' not yet implemented")

"""
Factory for INPUT layer providers.
"""

from typing import Dict, Any

from ..core.providers import InputProvider


def get_input_provider(provider_name: str, config: Dict[str, Any]) -> InputProvider:
    """
    Get INPUT provider by name.

    Args:
        provider_name: Provider identifier (file, discord, zoom, meet, webrtc, obs, etc.)
        config: Provider configuration

    Returns:
        InputProvider instance

    Raises:
        ValueError: If provider is not supported
    """
    # Normalize provider name
    provider = provider_name.lower().replace('_', '-').replace(' ', '-')

    # Map provider names to classes
    if provider == 'file':
        from .file_provider import FileProvider
        return FileProvider(config)
    elif provider == 'zip':
        from .zip_provider import ZipProvider
        return ZipProvider(config)
    elif provider in ('meet', 'google-meet', 'gmeet'):
        from .google_meet_provider import GoogleMeetProvider
        return GoogleMeetProvider(config)
    elif provider in ('discord', 'discord-bot'):
        from .discord_provider import DiscordBotProvider
        return DiscordBotProvider(config)
    elif provider == 'webrtc':
        from .webrtc_provider import WebRTCProvider
        return WebRTCProvider(config)
    elif provider == 'obs':
        from .obs_provider import OBSProvider
        return OBSProvider(config)
    elif provider == 'zoom':
        raise NotImplementedError("Zoom provider not yet implemented")
    elif provider == 'proctap':
        raise NotImplementedError("ProcTap provider not yet implemented")
    else:
        raise ValueError(f"Unsupported input provider: {provider_name}")

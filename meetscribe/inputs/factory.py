"""
Factory for INPUT layer providers.
"""

from typing import Dict, Any

from ..core.providers import InputProvider


def get_input_provider(provider_name: str, config: Dict[str, Any]) -> InputProvider:
    """
    Get INPUT provider by name.

    Args:
        provider_name: Provider identifier (file, discord, zoom, meet, etc.)
        config: Provider configuration

    Returns:
        InputProvider instance

    Raises:
        ValueError: If provider is not supported
    """
    # Map provider names to classes
    if provider_name == 'file':
        from .file_provider import FileProvider
        return FileProvider(config)
    elif provider_name == 'discord':
        raise NotImplementedError("Discord provider not yet implemented")
    elif provider_name == 'zoom':
        raise NotImplementedError("Zoom provider not yet implemented")
    elif provider_name == 'meet':
        raise NotImplementedError("Meet provider not yet implemented")
    elif provider_name == 'proctap':
        raise NotImplementedError("ProcTap provider not yet implemented")
    elif provider_name == 'obs':
        raise NotImplementedError("OBS provider not yet implemented")
    else:
        raise ValueError(f"Unsupported input provider: {provider_name}")

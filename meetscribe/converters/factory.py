"""
Factory for CONVERT layer providers.
"""

from typing import Dict, Any

from ..core.providers import ConvertProvider


def get_converter(engine_name: str, config: Dict[str, Any]) -> ConvertProvider:
    """
    Get CONVERT provider by name.

    Args:
        engine_name: Engine identifier (passthrough, whisper, gemini, etc.)
        config: Converter configuration

    Returns:
        ConvertProvider instance

    Raises:
        ValueError: If engine is not supported
    """
    # Map engine names to classes
    if engine_name == 'passthrough':
        from .passthrough_converter import PassthroughConverter
        return PassthroughConverter(config)
    elif engine_name == 'whisper':
        raise NotImplementedError("Whisper converter not yet implemented")
    elif engine_name == 'faster-whisper':
        raise NotImplementedError("Faster-whisper converter not yet implemented")
    elif engine_name == 'gemini':
        raise NotImplementedError("Gemini converter not yet implemented")
    else:
        raise ValueError(f"Unsupported converter engine: {engine_name}")

"""
Factory for CONVERT layer providers.
"""

from typing import Dict, Any

from ..core.providers import ConvertProvider


def get_converter(engine_name: str, config: Dict[str, Any]) -> ConvertProvider:
    """
    Get CONVERT provider by name.

    Args:
        engine_name: Engine identifier (whisper, gemini, passthrough, etc.)
        config: Converter configuration

    Returns:
        ConvertProvider instance

    Raises:
        ValueError: If engine is not supported
    """
    engines = {
        'whisper': 'meetscribe.converters.whisper_converter.WhisperConverter',
        'faster-whisper': 'meetscribe.converters.faster_whisper_converter.FasterWhisperConverter',
        'gemini': 'meetscribe.converters.gemini_converter.GeminiConverter',
        'passthrough': 'meetscribe.converters.passthrough_converter.PassthroughConverter',
    }

    if engine_name not in engines:
        raise ValueError(f"Unsupported converter engine: {engine_name}")

    # For MVP, raise NotImplementedError
    # Converters will be implemented in future versions
    raise NotImplementedError(f"Converter '{engine_name}' not yet implemented")

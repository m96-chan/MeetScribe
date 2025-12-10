"""
Factory for CONVERT layer providers.
"""

from typing import Dict, Any

from ..core.providers import ConvertProvider


def get_converter(engine_name: str, config: Dict[str, Any]) -> ConvertProvider:
    """
    Get CONVERT provider by name.

    Args:
        engine_name: Engine identifier (passthrough, whisper, whisper-api,
                     faster-whisper, gemini, deepgram, etc.)
        config: Converter configuration

    Returns:
        ConvertProvider instance

    Raises:
        ValueError: If engine is not supported
    """
    # Normalize engine name
    engine = engine_name.lower().replace("_", "-")

    # Map engine names to classes
    if engine == "passthrough":
        from .passthrough_converter import PassthroughConverter

        return PassthroughConverter(config)
    elif engine in ("whisper", "whisper-api"):
        from .whisper_converter import WhisperAPIConverter

        return WhisperAPIConverter(config)
    elif engine == "faster-whisper":
        from .faster_whisper_converter import FasterWhisperConverter

        return FasterWhisperConverter(config)
    elif engine in ("gemini", "gemini-audio"):
        from .gemini_converter import GeminiAudioConverter

        return GeminiAudioConverter(config)
    elif engine == "deepgram":
        from .deepgram_converter import DeepgramConverter

        return DeepgramConverter(config)
    else:
        raise ValueError(f"Unsupported converter engine: {engine_name}")

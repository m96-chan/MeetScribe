"""
Factory for LLM layer providers.
"""

from typing import Dict, Any

from ..core.providers import LLMProvider


def get_llm_provider(engine_name: str, config: Dict[str, Any]) -> LLMProvider:
    """
    Get LLM provider by name.

    Args:
        engine_name: Engine identifier (notebooklm, chatgpt, claude, gemini)
        config: LLM configuration

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If engine is not supported
    """
    # Map engine names to classes
    if engine_name == 'notebooklm':
        from .notebooklm_provider import NotebookLMProvider
        return NotebookLMProvider(config)
    elif engine_name == 'chatgpt':
        raise NotImplementedError("ChatGPT provider not yet implemented")
    elif engine_name == 'claude':
        raise NotImplementedError("Claude provider not yet implemented")
    elif engine_name == 'gemini':
        raise NotImplementedError("Gemini provider not yet implemented")
    else:
        raise ValueError(f"Unsupported LLM engine: {engine_name}")

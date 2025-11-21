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
    engines = {
        'notebooklm': 'meetscribe.llm.notebooklm_provider.NotebookLMProvider',
        'chatgpt': 'meetscribe.llm.chatgpt_provider.ChatGPTProvider',
        'claude': 'meetscribe.llm.claude_provider.ClaudeProvider',
        'gemini': 'meetscribe.llm.gemini_provider.GeminiProvider',
    }

    if engine_name not in engines:
        raise ValueError(f"Unsupported LLM engine: {engine_name}")

    # For MVP, raise NotImplementedError
    # LLM providers will be implemented in future versions
    raise NotImplementedError(f"LLM provider '{engine_name}' not yet implemented")

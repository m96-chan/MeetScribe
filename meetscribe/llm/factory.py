"""
Factory for LLM layer providers.
"""

from typing import Dict, Any

from ..core.providers import LLMProvider


def get_llm_provider(engine_name: str, config: Dict[str, Any]) -> LLMProvider:
    """
    Get LLM provider by name.

    Args:
        engine_name: Engine identifier (notebooklm, chatgpt, claude, gemini, gpt, openai)
        config: LLM configuration

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If engine is not supported
    """
    # Normalize engine name
    engine = engine_name.lower().replace("_", "-").replace(" ", "-")

    # Map engine names to classes
    if engine == "notebooklm":
        from .notebooklm_provider import NotebookLMProvider

        return NotebookLMProvider(config)
    elif engine in ("chatgpt", "gpt", "openai", "gpt-4", "gpt-3.5"):
        from .chatgpt_provider import ChatGPTProvider

        return ChatGPTProvider(config)
    elif engine in ("claude", "anthropic", "claude-3"):
        from .claude_provider import ClaudeProvider

        return ClaudeProvider(config)
    elif engine in ("gemini", "google", "bard"):
        from .gemini_provider import GeminiProvider

        return GeminiProvider(config)
    else:
        raise ValueError(f"Unsupported LLM engine: {engine_name}")

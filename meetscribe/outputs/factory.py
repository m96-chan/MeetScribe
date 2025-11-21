"""
Factory for OUTPUT layer renderers.
"""

from typing import Dict, Any

from ..core.providers import OutputRenderer


def get_output_renderer(format_name: str, config: Dict[str, Any]) -> OutputRenderer:
    """
    Get OUTPUT renderer by name.

    Args:
        format_name: Format identifier (url, markdown, json, pdf, docs)
        config: Renderer configuration

    Returns:
        OutputRenderer instance

    Raises:
        ValueError: If format is not supported
    """
    # Map format names to classes
    if format_name == 'url':
        from .url_renderer import URLRenderer
        return URLRenderer(config)
    elif format_name == 'markdown':
        raise NotImplementedError("Markdown renderer not yet implemented")
    elif format_name == 'json':
        raise NotImplementedError("JSON renderer not yet implemented")
    elif format_name == 'pdf':
        raise NotImplementedError("PDF renderer not yet implemented")
    elif format_name == 'docs':
        raise NotImplementedError("Google Docs renderer not yet implemented")
    else:
        raise ValueError(f"Unsupported output format: {format_name}")

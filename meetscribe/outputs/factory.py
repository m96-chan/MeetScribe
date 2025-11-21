"""
Factory for OUTPUT layer renderers.
"""

from typing import Dict, Any

from ..core.providers import OutputRenderer


def get_output_renderer(format_name: str, config: Dict[str, Any]) -> OutputRenderer:
    """
    Get OUTPUT renderer by name.

    Args:
        format_name: Format identifier (markdown, json, pdf, docs, notebooklm)
        config: Renderer configuration

    Returns:
        OutputRenderer instance

    Raises:
        ValueError: If format is not supported
    """
    formats = {
        'markdown': 'meetscribe.outputs.markdown_renderer.MarkdownRenderer',
        'json': 'meetscribe.outputs.json_renderer.JSONRenderer',
        'pdf': 'meetscribe.outputs.pdf_renderer.PDFRenderer',
        'docs': 'meetscribe.outputs.docs_renderer.DocsRenderer',
        'notebooklm': 'meetscribe.outputs.notebooklm_renderer.NotebookLMRenderer',
    }

    if format_name not in formats:
        raise ValueError(f"Unsupported output format: {format_name}")

    # For MVP, raise NotImplementedError
    # Renderers will be implemented in future versions
    raise NotImplementedError(f"Output renderer '{format_name}' not yet implemented")

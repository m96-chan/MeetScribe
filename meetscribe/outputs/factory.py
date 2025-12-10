"""
Factory for OUTPUT layer renderers.
"""

from typing import Dict, Any, List

from ..core.providers import OutputRenderer


def get_output_renderer(format_name: str, config: Dict[str, Any]) -> OutputRenderer:
    """
    Get OUTPUT renderer by name.

    Args:
        format_name: Format identifier (url, markdown, json, pdf, docs, sheets, webhook)
        config: Renderer configuration

    Returns:
        OutputRenderer instance

    Raises:
        ValueError: If format is not supported
    """
    # Normalize format name
    fmt = format_name.lower().replace("_", "-").replace(" ", "-")

    # Map format names to classes
    if fmt == "url":
        from .url_renderer import URLRenderer

        return URLRenderer(config)
    elif fmt in ("markdown", "md"):
        from .markdown_renderer import MarkdownRenderer

        return MarkdownRenderer(config)
    elif fmt == "json":
        from .json_renderer import JSONRenderer

        return JSONRenderer(config)
    elif fmt == "pdf":
        from .pdf_renderer import PDFRenderer

        return PDFRenderer(config)
    elif fmt in ("docs", "google-docs", "gdocs"):
        from .google_docs_renderer import GoogleDocsRenderer

        return GoogleDocsRenderer(config)
    elif fmt in ("sheets", "google-sheets", "spreadsheet", "gsheets"):
        from .google_sheets_renderer import GoogleSheetsRenderer

        return GoogleSheetsRenderer(config)
    elif fmt in ("webhook", "discord-webhook", "discord"):
        from .discord_webhook_renderer import DiscordWebhookRenderer

        return DiscordWebhookRenderer(config)
    else:
        raise ValueError(f"Unsupported output format: {format_name}")


def get_multiple_renderers(formats: List[Dict[str, Any]]) -> List[OutputRenderer]:
    """
    Get multiple OUTPUT renderers.

    Args:
        formats: List of format configurations, each with 'format' and optional params

    Returns:
        List of OutputRenderer instances
    """
    renderers = []
    for fmt_config in formats:
        format_name = fmt_config.get("format")
        if not format_name:
            raise ValueError("Each output format must specify 'format' key")
        renderer = get_output_renderer(format_name, fmt_config)
        renderers.append(renderer)
    return renderers

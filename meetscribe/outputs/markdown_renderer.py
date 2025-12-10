"""
Markdown OUTPUT renderer for MeetScribe.

Generates formatted Markdown meeting minutes.
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import logging

from ..core.providers import OutputRenderer
from ..core.models import Minutes


logger = logging.getLogger(__name__)


class MarkdownRenderer(OutputRenderer):
    """
    Markdown OUTPUT renderer.

    Generates beautifully formatted Markdown meeting minutes.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Markdown renderer.

        Config params:
            output_dir: Directory to save output (default: ./meetings)
            filename_template: Template for filename (default: minutes.md)
            include_metadata: Include metadata section (default: True)
            include_toc: Include table of contents (default: True)
            template: Custom template name (default: 'default')
            language: Output language (default: 'en')
        """
        super().__init__(config)
        self.output_dir = Path(config.get("output_dir", "./meetings"))
        self.filename_template = config.get("filename_template", "minutes.md")
        self.include_metadata = config.get("include_metadata", True)
        self.include_toc = config.get("include_toc", True)
        self.template = config.get("template", "default")
        self.language = config.get("language", "en")

    def render(self, minutes: Minutes, meeting_id: str) -> str:
        """
        Render minutes to Markdown file.

        Args:
            minutes: Minutes object
            meeting_id: Meeting identifier

        Returns:
            Path to generated Markdown file
        """
        logger.info(f"Rendering Markdown output for {meeting_id}")

        # Generate content
        content = self._generate_markdown(minutes, meeting_id)

        # Create output directory
        meeting_dir = self.output_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)

        # Write file
        output_path = meeting_dir / self.filename_template
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Markdown saved to: {output_path}")
        return str(output_path)

    def _generate_markdown(self, minutes: Minutes, meeting_id: str) -> str:
        """Generate Markdown content."""
        lines = []

        # Title
        title = minutes.metadata.get("title", f"Meeting Minutes: {meeting_id}")
        lines.append(f"# {title}")
        lines.append("")

        # Metadata section
        if self.include_metadata:
            lines.extend(self._generate_metadata(minutes, meeting_id))
            lines.append("")

        # Table of Contents
        if self.include_toc:
            lines.extend(self._generate_toc(minutes))
            lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(minutes.summary)
        lines.append("")

        # Key Points
        if minutes.key_points:
            lines.append("## Key Points")
            lines.append("")
            for point in minutes.key_points:
                lines.append(f"- {point}")
            lines.append("")

        # Participants
        if minutes.participants:
            lines.append("## Participants")
            lines.append("")
            for participant in minutes.participants:
                lines.append(f"- {participant}")
            lines.append("")

        # Decisions
        if minutes.decisions:
            lines.append("## Decisions")
            lines.append("")
            for i, decision in enumerate(minutes.decisions, 1):
                lines.append(f"### Decision {i}")
                lines.append("")
                lines.append(f"**Description:** {decision.description}")
                if decision.responsible:
                    lines.append(f"**Responsible:** {decision.responsible}")
                if decision.deadline:
                    lines.append(f"**Deadline:** {decision.deadline}")
                lines.append("")

        # Action Items
        if minutes.action_items:
            lines.append("## Action Items")
            lines.append("")
            lines.append("| # | Description | Assignee | Deadline | Priority |")
            lines.append("|---|-------------|----------|----------|----------|")
            for i, item in enumerate(minutes.action_items, 1):
                assignee = item.assignee or "-"
                deadline = item.deadline or "-"
                priority = item.priority or "-"
                lines.append(f"| {i} | {item.description} | {assignee} | {deadline} | {priority} |")
            lines.append("")

        # NotebookLM URL
        if minutes.url:
            lines.append("## Additional Resources")
            lines.append("")
            lines.append(f"- [NotebookLM Notebook]({minutes.url})")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(
            f"*Generated by MeetScribe at {minutes.generated_at.strftime('%Y-%m-%d %H:%M:%S')}*"
        )

        return "\n".join(lines)

    def _generate_metadata(self, minutes: Minutes, meeting_id: str) -> list:
        """Generate metadata section."""
        lines = []
        lines.append("| Property | Value |")
        lines.append("|----------|-------|")
        lines.append(f"| Meeting ID | `{meeting_id}` |")
        lines.append(f"| Generated | {minutes.generated_at.strftime('%Y-%m-%d %H:%M:%S')} |")

        if "llm_engine" in minutes.metadata:
            lines.append(f"| LLM Engine | {minutes.metadata['llm_engine']} |")
        if "duration" in minutes.metadata:
            lines.append(f"| Duration | {minutes.metadata['duration']} min |")

        return lines

    def _generate_toc(self, minutes: Minutes) -> list:
        """Generate table of contents."""
        lines = []
        lines.append("## Table of Contents")
        lines.append("")
        lines.append("- [Summary](#summary)")
        if minutes.key_points:
            lines.append("- [Key Points](#key-points)")
        if minutes.participants:
            lines.append("- [Participants](#participants)")
        if minutes.decisions:
            lines.append("- [Decisions](#decisions)")
        if minutes.action_items:
            lines.append("- [Action Items](#action-items)")
        if minutes.url:
            lines.append("- [Additional Resources](#additional-resources)")
        return lines

    def validate_config(self) -> bool:
        """Validate renderer configuration."""
        return True

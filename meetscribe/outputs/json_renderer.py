"""
JSON OUTPUT renderer for MeetScribe.

Generates structured JSON meeting minutes.
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import json
import logging

from ..core.providers import OutputRenderer
from ..core.models import Minutes


logger = logging.getLogger(__name__)


class JSONRenderer(OutputRenderer):
    """
    JSON OUTPUT renderer.

    Generates structured JSON meeting minutes for machine consumption.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize JSON renderer.

        Config params:
            output_dir: Directory to save output (default: ./meetings)
            filename_template: Template for filename (default: minutes.json)
            indent: JSON indentation (default: 2)
            include_metadata: Include full metadata (default: True)
            schema_version: JSON schema version (default: "1.0")
        """
        super().__init__(config)
        self.output_dir = Path(config.get("output_dir", "./meetings"))
        self.filename_template = config.get("filename_template", "minutes.json")
        self.indent = config.get("indent", 2)
        self.include_metadata = config.get("include_metadata", True)
        self.schema_version = config.get("schema_version", "1.0")

    def render(self, minutes: Minutes, meeting_id: str) -> str:
        """
        Render minutes to JSON file.

        Args:
            minutes: Minutes object
            meeting_id: Meeting identifier

        Returns:
            Path to generated JSON file
        """
        logger.info(f"Rendering JSON output for {meeting_id}")

        # Generate JSON structure
        data = self._generate_json(minutes, meeting_id)

        # Create output directory
        meeting_dir = self.output_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)

        # Write file
        output_path = meeting_dir / self.filename_template
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=self.indent, ensure_ascii=False, default=str)

        logger.info(f"JSON saved to: {output_path}")
        return str(output_path)

    def _generate_json(self, minutes: Minutes, meeting_id: str) -> Dict[str, Any]:
        """Generate JSON structure."""
        data = {
            "$schema_version": self.schema_version,
            "meeting_id": meeting_id,
            "generated_at": minutes.generated_at.isoformat(),
            "summary": minutes.summary,
            "key_points": minutes.key_points,
            "participants": minutes.participants,
            "decisions": [
                {"description": d.description, "responsible": d.responsible, "deadline": d.deadline}
                for d in minutes.decisions
            ],
            "action_items": [
                {
                    "description": a.description,
                    "assignee": a.assignee,
                    "deadline": a.deadline,
                    "priority": a.priority,
                }
                for a in minutes.action_items
            ],
        }

        # Add URL if present
        if minutes.url:
            data["notebooklm_url"] = minutes.url

        # Add metadata if requested
        if self.include_metadata:
            data["metadata"] = minutes.metadata

        # Add statistics
        data["statistics"] = {
            "total_decisions": len(minutes.decisions),
            "total_action_items": len(minutes.action_items),
            "total_key_points": len(minutes.key_points),
            "total_participants": len(minutes.participants),
        }

        return data

    def validate_config(self) -> bool:
        """Validate renderer configuration."""
        if self.indent < 0:
            raise ValueError("indent must be non-negative")
        return True

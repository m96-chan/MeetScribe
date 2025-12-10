"""
Discord Webhook OUTPUT renderer for MeetScribe.

Posts meeting minutes to Discord channels via webhooks.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.models import Minutes
from ..core.providers import OutputRenderer

logger = logging.getLogger(__name__)


class DiscordWebhookRenderer(OutputRenderer):
    """
    Discord Webhook OUTPUT renderer.

    Posts meeting minutes to Discord channels using webhooks.
    """

    # Discord embed limits
    MAX_TITLE_LENGTH = 256
    MAX_DESCRIPTION_LENGTH = 4096
    MAX_FIELD_NAME_LENGTH = 256
    MAX_FIELD_VALUE_LENGTH = 1024
    MAX_FIELDS = 25
    MAX_EMBED_TOTAL = 6000

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Discord Webhook renderer.

        Config params:
            webhook_url: Discord webhook URL (or from DISCORD_WEBHOOK_URL env)
            username: Bot username for messages (default: "MeetScribe")
            avatar_url: Bot avatar URL
            color: Embed color (hex, default: 0x5865F2)
            include_action_items: Include action items in embed
            include_decisions: Include decisions in embed
            mention_roles: List of role IDs to mention
            mention_users: List of user IDs to mention
            output_dir: Directory for local backup
        """
        super().__init__(config)

        self.webhook_url = config.get("webhook_url") or os.getenv("DISCORD_WEBHOOK_URL")
        self.username = config.get("username", "MeetScribe")
        self.avatar_url = config.get("avatar_url")
        self.color = config.get("color", 0x5865F2)  # Discord blurple
        self.include_action_items = config.get("include_action_items", True)
        self.include_decisions = config.get("include_decisions", True)
        self.mention_roles = config.get("mention_roles", [])
        self.mention_users = config.get("mention_users", [])
        self.output_dir = Path(config.get("output_dir", "./meetings"))

        # Check for requests library
        self._http_available = self._check_http_library()

    def _check_http_library(self) -> bool:
        """Check if HTTP library is available."""
        try:
            import requests

            return True
        except ImportError:
            try:
                import httpx

                return True
            except ImportError:
                logger.warning(
                    "No HTTP library available. Run: pip install requests\n" "Running in mock mode."
                )
                return False

    def render(self, minutes: Minutes, meeting_id: str) -> str:
        """
        Render minutes to Discord webhook.

        Args:
            minutes: Minutes object
            meeting_id: Meeting identifier

        Returns:
            Message ID or local backup path
        """
        logger.info(f"Rendering Discord webhook output for {meeting_id}")

        # Build webhook payload
        payload = self._build_payload(minutes, meeting_id)

        # Send to webhook
        if self.webhook_url and self._http_available:
            result = self._send_webhook(payload)
        else:
            result = self._save_mock_output(minutes, meeting_id, payload)

        logger.info(f"Discord webhook result: {result}")
        return result

    def _build_payload(self, minutes: Minutes, meeting_id: str) -> Dict[str, Any]:
        """Build Discord webhook payload."""
        # Build mentions
        mentions = []
        for role_id in self.mention_roles:
            mentions.append(f"<@&{role_id}>")
        for user_id in self.mention_users:
            mentions.append(f"<@{user_id}>")

        content = " ".join(mentions) if mentions else None

        # Build main embed
        main_embed = self._build_main_embed(minutes, meeting_id)

        # Build additional embeds
        embeds = [main_embed]

        if self.include_action_items and minutes.action_items:
            action_embed = self._build_action_items_embed(minutes)
            if action_embed:
                embeds.append(action_embed)

        if self.include_decisions and minutes.decisions:
            decisions_embed = self._build_decisions_embed(minutes)
            if decisions_embed:
                embeds.append(decisions_embed)

        # Build payload
        payload = {
            "username": self.username,
            "embeds": embeds,
        }

        if content:
            payload["content"] = content

        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url

        return payload

    def _build_main_embed(self, minutes: Minutes, meeting_id: str) -> Dict[str, Any]:
        """Build main summary embed."""
        # Truncate summary if needed
        summary = minutes.summary
        if len(summary) > self.MAX_DESCRIPTION_LENGTH:
            summary = summary[: self.MAX_DESCRIPTION_LENGTH - 3] + "..."

        embed = {
            "title": self._truncate(f"Meeting Minutes: {meeting_id}", self.MAX_TITLE_LENGTH),
            "description": summary,
            "color": self.color,
            "timestamp": minutes.generated_at.isoformat(),
            "footer": {"text": "Generated by MeetScribe"},
        }

        # Add fields
        fields = []

        # Key points (if space allows)
        if minutes.key_points:
            key_points_text = "\n".join(f"• {p}" for p in minutes.key_points[:5])
            if len(minutes.key_points) > 5:
                key_points_text += f"\n... and {len(minutes.key_points) - 5} more"
            fields.append(
                {
                    "name": "Key Points",
                    "value": self._truncate(key_points_text, self.MAX_FIELD_VALUE_LENGTH),
                    "inline": False,
                }
            )

        # Participants
        if minutes.participants:
            participants_text = ", ".join(minutes.participants[:10])
            if len(minutes.participants) > 10:
                participants_text += f" +{len(minutes.participants) - 10} more"
            fields.append(
                {
                    "name": "Participants",
                    "value": self._truncate(participants_text, self.MAX_FIELD_VALUE_LENGTH),
                    "inline": True,
                }
            )

        # Statistics
        stats = []
        if minutes.action_items:
            stats.append(f"📋 {len(minutes.action_items)} action items")
        if minutes.decisions:
            stats.append(f"✅ {len(minutes.decisions)} decisions")
        if stats:
            fields.append({"name": "Summary", "value": "\n".join(stats), "inline": True})

        # NotebookLM URL
        if minutes.url:
            fields.append(
                {
                    "name": "Resources",
                    "value": f"[View in NotebookLM]({minutes.url})",
                    "inline": True,
                }
            )

        embed["fields"] = fields[: self.MAX_FIELDS]

        return embed

    def _build_action_items_embed(self, minutes: Minutes) -> Optional[Dict[str, Any]]:
        """Build action items embed."""
        if not minutes.action_items:
            return None

        lines = []
        for i, item in enumerate(minutes.action_items[:10], 1):
            line = f"**{i}.** {item.description}"
            if item.assignee:
                line += f" → {item.assignee}"
            if item.deadline:
                line += f" (Due: {item.deadline})"
            if item.priority:
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    item.priority.lower(), "⚪"
                )
                line += f" {priority_emoji}"
            lines.append(line)

        if len(minutes.action_items) > 10:
            lines.append(f"... and {len(minutes.action_items) - 10} more items")

        description = "\n".join(lines)
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            description = description[: self.MAX_DESCRIPTION_LENGTH - 3] + "..."

        return {
            "title": "📋 Action Items",
            "description": description,
            "color": 0xFFA500,  # Orange
        }

    def _build_decisions_embed(self, minutes: Minutes) -> Optional[Dict[str, Any]]:
        """Build decisions embed."""
        if not minutes.decisions:
            return None

        lines = []
        for i, decision in enumerate(minutes.decisions[:10], 1):
            line = f"**{i}.** {decision.description}"
            if decision.responsible:
                line += f" → {decision.responsible}"
            if decision.deadline:
                line += f" (Deadline: {decision.deadline})"
            lines.append(line)

        if len(minutes.decisions) > 10:
            lines.append(f"... and {len(minutes.decisions) - 10} more decisions")

        description = "\n".join(lines)
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            description = description[: self.MAX_DESCRIPTION_LENGTH - 3] + "..."

        return {
            "title": "✅ Decisions",
            "description": description,
            "color": 0x00FF00,  # Green
        }

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def _send_webhook(self, payload: Dict[str, Any]) -> str:
        """Send payload to Discord webhook."""
        try:
            import requests

            response = requests.post(
                self.webhook_url, json=payload, headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            # Discord returns empty body on success
            if response.status_code == 204:
                return "Message sent successfully"

            # If wait=true was used, we get the message object
            if response.content:
                data = response.json()
                return data.get("id", "Message sent")

            return "Message sent"

        except ImportError:
            try:
                import httpx

                with httpx.Client() as client:
                    response = client.post(
                        self.webhook_url, json=payload, headers={"Content-Type": "application/json"}
                    )
                    response.raise_for_status()
                    return "Message sent successfully"
            except Exception as e:
                logger.error(f"Failed to send webhook: {e}")
                raise

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            raise

    def _save_mock_output(self, minutes: Minutes, meeting_id: str, payload: Dict[str, Any]) -> str:
        """Save mock output when webhook not available."""
        logger.info(f"[MOCK] Saving Discord webhook payload for {meeting_id}")

        meeting_dir = self.output_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)

        output_path = meeting_dir / "discord_webhook_payload.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

        return str(output_path)

    def validate_config(self) -> bool:
        """Validate renderer configuration."""
        if not self.webhook_url:
            logger.warning("No webhook URL configured - running in mock mode")
        return True

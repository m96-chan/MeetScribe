"""
ChatGPT LLM provider for MeetScribe.

Uses OpenAI's GPT models for meeting minutes generation.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
import json

from ..core.providers import LLMProvider
from ..core.models import Transcript, Minutes, Decision, ActionItem


logger = logging.getLogger(__name__)


class ChatGPTProvider(LLMProvider):
    """
    ChatGPT LLM provider.

    Uses OpenAI's GPT models to generate meeting minutes from transcripts.
    """

    # Default system prompt for meeting minutes
    DEFAULT_SYSTEM_PROMPT = """You are an expert meeting assistant. Analyze the provided meeting transcript and generate structured meeting minutes.

Your output must be a valid JSON object with the following structure:
{
    "summary": "A concise 2-3 paragraph summary of the meeting",
    "key_points": ["List of key discussion points"],
    "decisions": [
        {"description": "Decision made", "responsible": "Person responsible", "deadline": "Deadline if mentioned"}
    ],
    "action_items": [
        {"description": "Action item", "assignee": "Person assigned", "deadline": "Due date", "priority": "high/medium/low"}
    ],
    "participants": ["List of participants mentioned"]
}

Be thorough but concise. Extract all actionable items and decisions."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ChatGPT provider.

        Config params:
            api_key: OpenAI API key (or from OPENAI_API_KEY env)
            model: Model name (gpt-4, gpt-4-turbo, gpt-3.5-turbo)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum response tokens
            system_prompt: Custom system prompt
            response_format: Response format (json_object, text)
        """
        super().__init__(config)

        self.api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        self.model = config.get('model', 'gpt-4-turbo')
        self.temperature = config.get('temperature', 0.3)
        self.max_tokens = config.get('max_tokens', 4096)
        self.system_prompt = config.get('system_prompt', self.DEFAULT_SYSTEM_PROMPT)
        self.response_format = config.get('response_format', 'json_object')

        # Initialize client
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize OpenAI client."""
        if not self.api_key:
            logger.warning("No OpenAI API key - running in mock mode")
            return

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"OpenAI client initialized with model: {self.model}")
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")

    def generate_minutes(self, transcript: Transcript) -> Minutes:
        """
        Generate meeting minutes using ChatGPT.

        Args:
            transcript: Transcript object

        Returns:
            Minutes object
        """
        meeting_id = transcript.meeting_info.meeting_id
        logger.info(f"Generating minutes for {meeting_id} using ChatGPT ({self.model})")

        # Get transcript text
        text = transcript.get_full_text()
        if not text:
            raise ValueError("Transcript has no text content")

        # Generate minutes
        if self.client:
            result = self._generate_with_api(text, transcript)
        else:
            result = self._mock_generation(transcript)

        # Parse result
        minutes = self._parse_result(result, transcript)

        logger.info(f"Minutes generated: {len(minutes.action_items)} action items, "
                    f"{len(minutes.decisions)} decisions")
        return minutes

    def _generate_with_api(self, text: str, transcript: Transcript) -> Dict[str, Any]:
        """Generate using actual API."""
        logger.info(f"Calling ChatGPT API ({self.model})")

        # Build messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Please analyze this meeting transcript and generate minutes:\n\n{text}"}
        ]

        # Add meeting context if available
        if transcript.meeting_info.participants:
            context = f"\nKnown participants: {', '.join(transcript.meeting_info.participants)}"
            messages[1]["content"] += context

        # Call API
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if self.response_format == 'json_object':
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)

        # Parse response
        content = response.choices[0].message.content

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Response is not valid JSON, attempting to parse")
            return self._extract_json_from_text(content)

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response."""
        import re

        # Try to find JSON block
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback: create structured response from text
        return {
            'summary': text,
            'key_points': [],
            'decisions': [],
            'action_items': [],
            'participants': []
        }

    def _mock_generation(self, transcript: Transcript) -> Dict[str, Any]:
        """Generate mock minutes for testing."""
        logger.info("[MOCK] Generating mock minutes")

        return {
            'summary': (
                "This is a mock meeting summary generated by the ChatGPT provider in PoC mode. "
                "In production, this would contain an AI-generated summary of the meeting discussion. "
                "The meeting covered project updates, timeline reviews, and task assignments."
            ),
            'key_points': [
                "Discussed project timeline and milestones",
                "Reviewed current progress on deliverables",
                "Identified blockers and proposed solutions",
                "Agreed on next steps and responsibilities"
            ],
            'decisions': [
                {
                    'description': 'Approved the proposed implementation approach',
                    'responsible': 'Team Lead',
                    'deadline': '2025-12-15'
                },
                {
                    'description': 'Decided to increase testing coverage',
                    'responsible': 'QA Team',
                    'deadline': None
                }
            ],
            'action_items': [
                {
                    'description': 'Complete initial implementation',
                    'assignee': 'Developer 1',
                    'deadline': '2025-12-10',
                    'priority': 'high'
                },
                {
                    'description': 'Review and update documentation',
                    'assignee': 'Developer 2',
                    'deadline': '2025-12-12',
                    'priority': 'medium'
                },
                {
                    'description': 'Set up test environment',
                    'assignee': 'DevOps',
                    'deadline': '2025-12-08',
                    'priority': 'high'
                }
            ],
            'participants': transcript.meeting_info.participants or ['Participant 1', 'Participant 2']
        }

    def _parse_result(self, result: Dict[str, Any], transcript: Transcript) -> Minutes:
        """Parse API result into Minutes object."""
        return Minutes(
            meeting_id=transcript.meeting_info.meeting_id,
            summary=result.get('summary', ''),
            decisions=[
                Decision(
                    description=d.get('description', ''),
                    responsible=d.get('responsible'),
                    deadline=d.get('deadline')
                )
                for d in result.get('decisions', [])
            ],
            action_items=[
                ActionItem(
                    description=a.get('description', ''),
                    assignee=a.get('assignee'),
                    deadline=a.get('deadline'),
                    priority=a.get('priority')
                )
                for a in result.get('action_items', [])
            ],
            key_points=result.get('key_points', []),
            participants=result.get('participants', transcript.meeting_info.participants),
            metadata={
                'llm_engine': 'chatgpt',
                'model': self.model,
                'temperature': self.temperature,
            }
        )

    def validate_config(self) -> bool:
        """Validate configuration."""
        if not self.api_key:
            logger.warning("No API key - running in mock mode")

        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature must be between 0 and 2")

        return True

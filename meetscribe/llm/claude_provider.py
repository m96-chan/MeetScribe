"""
Claude LLM provider for MeetScribe.

Uses Anthropic's Claude models for meeting minutes generation.
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


class ClaudeProvider(LLMProvider):
    """
    Claude LLM provider.

    Uses Anthropic's Claude models to generate meeting minutes.
    """

    # Default system prompt
    DEFAULT_SYSTEM_PROMPT = """You are an expert meeting assistant tasked with analyzing meeting transcripts and generating structured meeting minutes.

Analyze the provided transcript carefully and extract:
1. A comprehensive summary (2-3 paragraphs)
2. Key discussion points
3. Decisions made (with responsible parties and deadlines if mentioned)
4. Action items (with assignees, deadlines, and priority levels)
5. List of participants

Respond with a valid JSON object in this exact format:
{
    "summary": "string",
    "key_points": ["string"],
    "decisions": [{"description": "string", "responsible": "string or null", "deadline": "string or null"}],
    "action_items": [{"description": "string", "assignee": "string or null", "deadline": "string or null", "priority": "high|medium|low|null"}],
    "participants": ["string"]
}

Be precise and thorough. Focus on actionable insights."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Claude provider.

        Config params:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env)
            model: Model name (claude-3-opus, claude-3-sonnet, claude-3-haiku)
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (0-1)
            system_prompt: Custom system prompt
        """
        super().__init__(config)

        self.api_key = config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        self.model = config.get('model', 'claude-3-sonnet-20240229')
        self.max_tokens = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.3)
        self.system_prompt = config.get('system_prompt', self.DEFAULT_SYSTEM_PROMPT)

        # Initialize client
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize Anthropic client."""
        if not self.api_key:
            logger.warning("No Anthropic API key - running in mock mode")
            return

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Anthropic client initialized with model: {self.model}")
        except ImportError:
            logger.error("anthropic package not installed. Run: pip install anthropic")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")

    def generate_minutes(self, transcript: Transcript) -> Minutes:
        """
        Generate meeting minutes using Claude.

        Args:
            transcript: Transcript object

        Returns:
            Minutes object
        """
        meeting_id = transcript.meeting_info.meeting_id
        logger.info(f"Generating minutes for {meeting_id} using Claude ({self.model})")

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
        logger.info(f"Calling Claude API ({self.model})")

        # Build user message
        user_message = f"Please analyze this meeting transcript and generate structured minutes:\n\n{text}"

        # Add context
        if transcript.meeting_info.participants:
            user_message += f"\n\nKnown participants: {', '.join(transcript.meeting_info.participants)}"

        # Call API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Extract content
        content = response.content[0].text

        # Parse JSON
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

        # Fallback
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
                "This is a mock meeting summary generated by the Claude provider in PoC mode. "
                "Claude excels at structured analysis and would provide detailed insights here. "
                "The meeting focused on project planning, resource allocation, and timeline adjustments."
            ),
            'key_points': [
                "Reviewed project milestones and deliverables",
                "Discussed resource constraints and solutions",
                "Evaluated risk factors and mitigation strategies",
                "Planned next sprint activities"
            ],
            'decisions': [
                {
                    'description': 'Extend project timeline by two weeks',
                    'responsible': 'Project Manager',
                    'deadline': '2025-12-20'
                },
                {
                    'description': 'Allocate additional resources to critical path',
                    'responsible': 'Resource Manager',
                    'deadline': None
                }
            ],
            'action_items': [
                {
                    'description': 'Update project schedule',
                    'assignee': 'Project Manager',
                    'deadline': '2025-12-10',
                    'priority': 'high'
                },
                {
                    'description': 'Conduct risk assessment review',
                    'assignee': 'Risk Analyst',
                    'deadline': '2025-12-15',
                    'priority': 'medium'
                },
                {
                    'description': 'Prepare stakeholder communication',
                    'assignee': 'Communications Lead',
                    'deadline': '2025-12-11',
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
                'llm_engine': 'claude',
                'model': self.model,
                'temperature': self.temperature,
            }
        )

    def validate_config(self) -> bool:
        """Validate configuration."""
        if not self.api_key:
            logger.warning("No API key - running in mock mode")

        if self.temperature < 0 or self.temperature > 1:
            raise ValueError("temperature must be between 0 and 1")

        return True

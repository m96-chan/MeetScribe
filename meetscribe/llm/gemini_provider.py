"""
Gemini LLM provider for MeetScribe.

Uses Google's Gemini models for meeting minutes generation.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from ..core.models import ActionItem, Decision, Minutes, Transcript
from ..core.providers import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Gemini LLM provider.

    Uses Google's Gemini models to generate meeting minutes.
    Supports both text and audio input processing.
    """

    # Default system prompt
    DEFAULT_SYSTEM_PROMPT = """You are an expert meeting assistant. Analyze the provided meeting transcript and generate comprehensive, well-structured meeting minutes.

Your response must be a valid JSON object with this structure:
{
    "summary": "A 2-3 paragraph executive summary of the meeting",
    "key_points": ["Array of key discussion points"],
    "decisions": [
        {"description": "Decision description", "responsible": "Person responsible or null", "deadline": "Deadline or null"}
    ],
    "action_items": [
        {"description": "Action item", "assignee": "Assignee or null", "deadline": "Deadline or null", "priority": "high/medium/low or null"}
    ],
    "participants": ["List of participants mentioned"]
}

Be thorough and accurate. Focus on extracting actionable insights."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Gemini provider.

        Config params:
            api_key: Gemini API key (or from GEMINI_API_KEY env)
            model: Model name (gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash-exp)
            temperature: Sampling temperature (0-1)
            max_output_tokens: Maximum response tokens
            system_prompt: Custom system prompt
            process_audio_directly: Process audio file directly (default: False)
        """
        super().__init__(config)

        self.api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
        self.model = config.get("model", "gemini-1.5-flash")
        self.temperature = config.get("temperature", 0.3)
        self.max_output_tokens = config.get("max_output_tokens", 8192)
        self.system_prompt = config.get("system_prompt", self.DEFAULT_SYSTEM_PROMPT)
        self.process_audio_directly = config.get("process_audio_directly", False)

        # Initialize client
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize Gemini client."""
        if not self.api_key:
            logger.warning("No Gemini API key - running in mock mode")
            return

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
            logger.info(f"Gemini client initialized with model: {self.model}")
        except ImportError:
            logger.error("google-generativeai not installed. Run: pip install google-generativeai")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")

    def generate_minutes(self, transcript: Transcript) -> Minutes:
        """
        Generate meeting minutes using Gemini.

        Args:
            transcript: Transcript object

        Returns:
            Minutes object
        """
        meeting_id = transcript.meeting_info.meeting_id
        logger.info(f"Generating minutes for {meeting_id} using Gemini ({self.model})")

        # Decide processing mode
        if self.process_audio_directly and transcript.audio_path and transcript.audio_path.exists():
            result = self._generate_from_audio(transcript)
        else:
            # Get transcript text
            text = transcript.get_full_text()
            if not text:
                raise ValueError("Transcript has no text content")

            if self.client:
                result = self._generate_with_api(text, transcript)
            else:
                result = self._mock_generation(transcript)

        # Parse result
        minutes = self._parse_result(result, transcript)

        logger.info(
            f"Minutes generated: {len(minutes.action_items)} action items, "
            f"{len(minutes.decisions)} decisions"
        )
        return minutes

    def _generate_with_api(self, text: str, transcript: Transcript) -> Dict[str, Any]:
        """Generate using text API."""
        import google.generativeai as genai

        logger.info(f"Calling Gemini API ({self.model})")

        # Build prompt
        prompt = f"{self.system_prompt}\n\nMeeting Transcript:\n{text}"

        if transcript.meeting_info.participants:
            prompt += f"\n\nKnown participants: {', '.join(transcript.meeting_info.participants)}"

        # Configure generation
        gen_config = genai.GenerationConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            response_mime_type="application/json",
        )

        # Generate
        response = self.client.generate_content(prompt, generation_config=gen_config)

        # Parse response
        content = response.text

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Response is not valid JSON, attempting to parse")
            return self._extract_json_from_text(content)

    def _generate_from_audio(self, transcript: Transcript) -> Dict[str, Any]:
        """Generate directly from audio file."""
        import google.generativeai as genai

        logger.info(f"Processing audio directly with Gemini ({self.model})")

        audio_path = transcript.audio_path

        # Upload audio file
        audio_file = genai.upload_file(
            path=str(audio_path), mime_type=self._get_mime_type(audio_path)
        )

        # Build prompt
        prompt = f"""Analyze this meeting audio recording and generate structured meeting minutes.

{self.system_prompt}

Please listen to the audio carefully and extract all key information."""

        # Configure generation
        gen_config = genai.GenerationConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            response_mime_type="application/json",
        )

        # Generate
        response = self.client.generate_content([prompt, audio_file], generation_config=gen_config)

        # Clean up uploaded file
        try:
            genai.delete_file(audio_file.name)
        except Exception:
            pass

        # Parse response
        content = response.text

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._extract_json_from_text(content)

    def _get_mime_type(self, audio_path: Path) -> str:
        """Get MIME type for audio file."""
        mime_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
            ".webm": "audio/webm",
        }
        return mime_types.get(audio_path.suffix.lower(), "audio/mpeg")

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response."""
        import re

        # Try to find JSON block
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback
        return {
            "summary": text,
            "key_points": [],
            "decisions": [],
            "action_items": [],
            "participants": [],
        }

    def _mock_generation(self, transcript: Transcript) -> Dict[str, Any]:
        """Generate mock minutes for testing."""
        logger.info("[MOCK] Generating mock minutes")

        return {
            "summary": (
                "This is a mock meeting summary generated by the Gemini provider in PoC mode. "
                "Gemini's multimodal capabilities would provide comprehensive analysis here. "
                "The meeting addressed strategic planning, operational updates, and team coordination."
            ),
            "key_points": [
                "Reviewed Q4 strategic objectives",
                "Discussed operational efficiency improvements",
                "Addressed team capacity and workload distribution",
                "Planned upcoming product releases",
            ],
            "decisions": [
                {
                    "description": "Approve new product feature roadmap",
                    "responsible": "Product Manager",
                    "deadline": "2025-12-15",
                },
                {
                    "description": "Implement weekly status sync meetings",
                    "responsible": "Team Lead",
                    "deadline": None,
                },
            ],
            "action_items": [
                {
                    "description": "Finalize Q4 objectives document",
                    "assignee": "Strategy Team",
                    "deadline": "2025-12-12",
                    "priority": "high",
                },
                {
                    "description": "Prepare capacity planning report",
                    "assignee": "Operations",
                    "deadline": "2025-12-15",
                    "priority": "medium",
                },
                {
                    "description": "Schedule cross-team coordination session",
                    "assignee": "Project Manager",
                    "deadline": "2025-12-10",
                    "priority": "medium",
                },
            ],
            "participants": transcript.meeting_info.participants
            or ["Participant 1", "Participant 2"],
        }

    def _parse_result(self, result: Dict[str, Any], transcript: Transcript) -> Minutes:
        """Parse API result into Minutes object."""
        return Minutes(
            meeting_id=transcript.meeting_info.meeting_id,
            summary=result.get("summary", ""),
            decisions=[
                Decision(
                    description=d.get("description", ""),
                    responsible=d.get("responsible"),
                    deadline=d.get("deadline"),
                )
                for d in result.get("decisions", [])
            ],
            action_items=[
                ActionItem(
                    description=a.get("description", ""),
                    assignee=a.get("assignee"),
                    deadline=a.get("deadline"),
                    priority=a.get("priority"),
                )
                for a in result.get("action_items", [])
            ],
            key_points=result.get("key_points", []),
            participants=result.get("participants", transcript.meeting_info.participants),
            metadata={
                "llm_engine": "gemini",
                "model": self.model,
                "temperature": self.temperature,
                "audio_processing": self.process_audio_directly,
            },
        )

    def validate_config(self) -> bool:
        """Validate configuration."""
        if not self.api_key:
            logger.warning("No API key - running in mock mode")

        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature must be between 0 and 2")

        return True

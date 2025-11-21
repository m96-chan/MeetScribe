"""
Base provider interfaces for all pipeline layers.

These abstract classes define the contract for each pipeline stage.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

from .models import Transcript, Minutes


class InputProvider(ABC):
    """
    Base class for INPUT layer providers.

    Handles acquisition of raw meeting data from various sources.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize input provider.

        Args:
            config: Provider-specific configuration
        """
        self.config = config

    @abstractmethod
    def record(self, meeting_id: str) -> Path:
        """
        Record or fetch audio for a meeting.

        Args:
            meeting_id: Meeting identifier

        Returns:
            Path to recorded audio file

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError

    def validate_config(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if config is valid

        Raises:
            ValueError: If config is invalid
        """
        return True


class ConvertProvider(ABC):
    """
    Base class for CONVERT layer providers.

    Transforms raw audio into LLM-usable format.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize converter.

        Args:
            config: Converter-specific configuration
        """
        self.config = config

    @abstractmethod
    def transcribe(self, audio_path: Path, meeting_id: str) -> Transcript:
        """
        Convert audio to transcript.

        Args:
            audio_path: Path to audio file
            meeting_id: Meeting identifier

        Returns:
            Transcript object with text/segments/metadata

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError

    def validate_config(self) -> bool:
        """
        Validate converter configuration.

        Returns:
            True if config is valid

        Raises:
            ValueError: If config is invalid
        """
        return True


class LLMProvider(ABC):
    """
    Base class for LLM layer providers.

    Generates structured meeting minutes from transcripts.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM provider.

        Args:
            config: LLM-specific configuration
        """
        self.config = config

    @abstractmethod
    def generate_minutes(self, transcript: Transcript) -> Minutes:
        """
        Generate meeting minutes from transcript.

        Args:
            transcript: Transcript object

        Returns:
            Minutes object with summary/decisions/action_items

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError

    def validate_config(self) -> bool:
        """
        Validate LLM configuration.

        Returns:
            True if config is valid

        Raises:
            ValueError: If config is invalid
        """
        return True


class OutputRenderer(ABC):
    """
    Base class for OUTPUT layer renderers.

    Creates final user-facing artifacts.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize output renderer.

        Args:
            config: Renderer-specific configuration
        """
        self.config = config

    @abstractmethod
    def render(self, minutes: Minutes, meeting_id: str) -> str:
        """
        Render minutes to final output format.

        Args:
            minutes: Minutes object
            meeting_id: Meeting identifier

        Returns:
            Path to output file or URL

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError

    def validate_config(self) -> bool:
        """
        Validate renderer configuration.

        Returns:
            True if config is valid

        Raises:
            ValueError: If config is invalid
        """
        return True

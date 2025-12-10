"""
Pipeline runner for MeetScribe.

Orchestrates the full INPUT → CONVERT → LLM → OUTPUT pipeline.
"""

import logging
from pathlib import Path
from typing import Optional

from .config import PipelineConfig
from .models import Minutes, Transcript
from .providers import ConvertProvider, InputProvider, LLMProvider, OutputRenderer

logger = logging.getLogger(__name__)


class PipelineRunner:
    """
    Orchestrates the full MeetScribe pipeline.

    Executes: INPUT → CONVERT → LLM → OUTPUT
    """

    def __init__(self, config: PipelineConfig):
        """
        Initialize pipeline runner.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.input_provider: Optional[InputProvider] = None
        self.converter: Optional[ConvertProvider] = None
        self.llm_provider: Optional[LLMProvider] = None
        self.output_renderer: Optional[OutputRenderer] = None

    def setup(self):
        """
        Initialize all pipeline components based on config.

        Raises:
            ValueError: If any component initialization fails
        """
        logger.info("Setting up pipeline components...")

        # Import providers dynamically based on config
        self._setup_input_provider()
        self._setup_converter()
        self._setup_llm_provider()
        self._setup_output_renderer()

        logger.info("Pipeline setup complete")

    def _setup_input_provider(self):
        """Initialize INPUT layer provider."""
        provider_name = self.config.input.provider
        logger.info(f"Setting up INPUT provider: {provider_name}")

        # Dynamic import will be implemented in provider modules
        # For now, we create a placeholder
        from ..inputs.factory import get_input_provider

        self.input_provider = get_input_provider(provider_name, self.config.input.params)

    def _setup_converter(self):
        """Initialize CONVERT layer provider."""
        engine_name = self.config.convert.engine
        logger.info(f"Setting up CONVERT engine: {engine_name}")

        from ..converters.factory import get_converter

        self.converter = get_converter(engine_name, self.config.convert.params)

    def _setup_llm_provider(self):
        """Initialize LLM layer provider."""
        engine_name = self.config.llm.engine
        logger.info(f"Setting up LLM engine: {engine_name}")

        from ..llm.factory import get_llm_provider

        self.llm_provider = get_llm_provider(engine_name, self.config.llm.params)

    def _setup_output_renderer(self):
        """Initialize OUTPUT layer renderer."""
        format_name = self.config.output.format
        logger.info(f"Setting up OUTPUT renderer: {format_name}")

        from ..outputs.factory import get_output_renderer

        self.output_renderer = get_output_renderer(format_name, self.config.output.params)

    def run(self, meeting_id: str) -> str:
        """
        Execute full pipeline for a meeting.

        Args:
            meeting_id: Meeting identifier

        Returns:
            Path to final output or URL

        Raises:
            RuntimeError: If pipeline execution fails
        """
        logger.info(f"Starting pipeline for meeting: {meeting_id}")

        try:
            # Stage 1: INPUT - Record/fetch audio
            logger.info("Stage 1/4: INPUT - Recording audio...")
            audio_path = self.input_provider.record(meeting_id)
            logger.info(f"Audio recorded: {audio_path}")

            # Stage 2: CONVERT - Transcribe audio
            logger.info("Stage 2/4: CONVERT - Transcribing audio...")
            transcript = self.converter.transcribe(audio_path, meeting_id)
            logger.info(f"Transcription complete: {len(transcript.get_full_text())} chars")

            # Stage 3: LLM - Generate minutes
            logger.info("Stage 3/4: LLM - Generating minutes...")
            minutes = self.llm_provider.generate_minutes(transcript)
            logger.info(f"Minutes generated: {len(minutes.summary)} chars")

            # Stage 4: OUTPUT - Render final output
            logger.info("Stage 4/4: OUTPUT - Rendering output...")
            output_path = self.output_renderer.render(minutes, meeting_id)
            logger.info(f"Output rendered: {output_path}")

            # Optional: Cleanup raw audio
            if self.config.cleanup_audio and audio_path.exists():
                logger.info(f"Cleaning up raw audio: {audio_path}")
                audio_path.unlink()

            logger.info(f"Pipeline complete: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise RuntimeError(f"Pipeline execution failed: {e}") from e

    def validate(self) -> bool:
        """
        Validate all pipeline components.

        Returns:
            True if all components are valid

        Raises:
            ValueError: If any component is invalid
        """
        logger.info("Validating pipeline components...")

        if not self.input_provider.validate_config():
            raise ValueError("INPUT provider config is invalid")

        if not self.converter.validate_config():
            raise ValueError("CONVERT provider config is invalid")

        if not self.llm_provider.validate_config():
            raise ValueError("LLM provider config is invalid")

        if not self.output_renderer.validate_config():
            raise ValueError("OUTPUT renderer config is invalid")

        logger.info("All components validated successfully")
        return True

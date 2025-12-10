"""
OBS Recording INPUT provider for MeetScribe.

Monitors OBS recording output directory and uses recorded files.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
import json
import time

from ..core.providers import InputProvider
from ..core.meeting_id import generate_meeting_id_from_file


logger = logging.getLogger(__name__)


class OBSProvider(InputProvider):
    """
    OBS Recording INPUT provider.

    Monitors OBS recording directory and uses recorded files.
    Can also control OBS via websocket.
    """

    # Common OBS recording formats
    SUPPORTED_FORMATS = [".mkv", ".mp4", ".flv", ".mov", ".ts", ".m3u8"]

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OBS provider.

        Config params:
            recording_dir: OBS recording output directory
            pattern: Glob pattern for finding recordings
            watch_mode: Watch for new files (default: False)
            watch_timeout: Timeout for watching in seconds
            use_websocket: Use OBS websocket for control
            websocket_host: OBS websocket host
            websocket_port: OBS websocket port
            websocket_password: OBS websocket password
            output_dir: Working directory for processed files
            extract_audio: Extract audio from video (default: True)
            audio_format: Output audio format (default: mp3)
        """
        super().__init__(config)

        self.recording_dir = Path(config.get("recording_dir", os.path.expanduser("~/Videos")))
        self.pattern = config.get("pattern", "*.mkv")
        self.watch_mode = config.get("watch_mode", False)
        self.watch_timeout = config.get("watch_timeout", 300)
        self.use_websocket = config.get("use_websocket", False)
        self.websocket_host = config.get("websocket_host", "localhost")
        self.websocket_port = config.get("websocket_port", 4455)
        self.websocket_password = config.get("websocket_password")
        self.output_dir = Path(config.get("output_dir", "./recordings"))
        self.extract_audio = config.get("extract_audio", True)
        self.audio_format = config.get("audio_format", "mp3")

        # OBS websocket client
        self._obs_client = None

    def record(self, meeting_id: str) -> Path:
        """
        Get recording from OBS.

        Args:
            meeting_id: Meeting identifier

        Returns:
            Path to audio/video file
        """
        logger.info(f"Getting OBS recording for {meeting_id}")

        if self.use_websocket:
            return self._record_via_websocket(meeting_id)
        elif self.watch_mode:
            return self._watch_for_recording(meeting_id)
        else:
            return self._get_latest_recording(meeting_id)

    def _get_latest_recording(self, meeting_id: str) -> Path:
        """Get the latest recording from directory."""
        recordings = self._find_recordings()

        if not recordings:
            raise FileNotFoundError(f"No recordings found in {self.recording_dir}")

        # Get most recent
        latest = max(recordings, key=lambda p: p.stat().st_mtime)
        logger.info(f"Found recording: {latest}")

        # Process if needed
        return self._process_recording(latest, meeting_id)

    def _find_recordings(self) -> List[Path]:
        """Find all recordings in directory."""
        recordings = []

        for pattern in [self.pattern] if self.pattern else ["*"]:
            recordings.extend(self.recording_dir.glob(pattern))

        # Filter by supported formats
        recordings = [
            r for r in recordings if r.is_file() and r.suffix.lower() in self.SUPPORTED_FORMATS
        ]

        return sorted(recordings, key=lambda p: p.stat().st_mtime, reverse=True)

    def _watch_for_recording(self, meeting_id: str) -> Path:
        """Watch for new recording to appear."""
        logger.info(f"Watching for new recording in {self.recording_dir}")

        # Get existing files
        existing = set(str(p) for p in self._find_recordings())

        start_time = time.time()
        while time.time() - start_time < self.watch_timeout:
            current = self._find_recordings()

            # Check for new files
            for recording in current:
                if str(recording) not in existing:
                    # Wait for file to stop growing
                    if self._wait_for_file_complete(recording):
                        logger.info(f"New recording detected: {recording}")
                        return self._process_recording(recording, meeting_id)

            time.sleep(2)

        raise TimeoutError(f"No new recording found within {self.watch_timeout} seconds")

    def _wait_for_file_complete(self, file_path: Path, timeout: int = 60) -> bool:
        """Wait for file to stop growing (recording complete)."""
        last_size = 0
        stable_count = 0

        start_time = time.time()
        while time.time() - start_time < timeout:
            current_size = file_path.stat().st_size
            if current_size == last_size and current_size > 0:
                stable_count += 1
                if stable_count >= 3:
                    return True
            else:
                stable_count = 0
                last_size = current_size
            time.sleep(1)

        return False

    def _record_via_websocket(self, meeting_id: str) -> Path:
        """Control OBS via websocket to start/stop recording."""
        try:
            from obswebsocket import obsws, requests as obs_requests

            # Connect to OBS
            ws = obsws(self.websocket_host, self.websocket_port, self.websocket_password)
            ws.connect()

            logger.info("Connected to OBS websocket")

            # Get current recording status
            status = ws.call(obs_requests.GetRecordStatus())

            if not status.getOutputActive():
                # Start recording
                ws.call(obs_requests.StartRecord())
                logger.info("Started OBS recording")

                # Wait for recording to complete (user must stop it)
                # or implement auto-stop after duration

            # Get recording path
            record_directory = ws.call(obs_requests.GetRecordDirectory())
            recording_path = Path(record_directory.getRecordDirectory())

            ws.disconnect()

            # Find the recording
            return self._get_latest_recording(meeting_id)

        except ImportError:
            logger.error("obs-websocket-py not installed. Run: pip install obs-websocket-py")
            return self._create_mock_recording(meeting_id)
        except Exception as e:
            logger.error(f"OBS websocket error: {e}")
            return self._get_latest_recording(meeting_id)

    def _process_recording(self, recording_path: Path, meeting_id: str) -> Path:
        """Process recording (extract audio if needed)."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / meeting_id
        output_path.mkdir(parents=True, exist_ok=True)

        if self.extract_audio:
            audio_path = output_path / f"audio.{self.audio_format}"
            self._extract_audio(recording_path, audio_path)
            return audio_path
        else:
            # Copy video file
            import shutil

            dest = output_path / recording_path.name
            shutil.copy2(recording_path, dest)
            return dest

    def _extract_audio(self, video_path: Path, audio_path: Path):
        """Extract audio from video file."""
        logger.info(f"Extracting audio from {video_path}")

        try:
            from pydub import AudioSegment

            # Load video/audio
            audio = AudioSegment.from_file(str(video_path))

            # Export audio
            audio.export(str(audio_path), format=self.audio_format)
            logger.info(f"Audio extracted to: {audio_path}")

        except ImportError:
            logger.warning("pydub not installed. Run: pip install pydub")
            # Try ffmpeg directly
            self._extract_audio_ffmpeg(video_path, audio_path)
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise

    def _extract_audio_ffmpeg(self, video_path: Path, audio_path: Path):
        """Extract audio using ffmpeg directly."""
        import subprocess

        try:
            cmd = [
                "ffmpeg",
                "-i",
                str(video_path),
                "-vn",
                "-acodec",
                "libmp3lame",
                "-y",
                str(audio_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Audio extracted via ffmpeg: {audio_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg failed: {e}")
            raise
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg.")
            raise

    def _create_mock_recording(self, meeting_id: str) -> Path:
        """Create mock recording for testing."""
        logger.info(f"[MOCK] Creating mock OBS recording for {meeting_id}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / meeting_id
        output_path.mkdir(parents=True, exist_ok=True)

        mock_file = output_path / "mock_obs_recording.txt"
        with open(mock_file, "w") as f:
            f.write(f"Mock OBS recording for {meeting_id}\n")
            f.write("This is a placeholder file.\n")
            f.write("Configure OBS recording directory to use actual recordings.\n")

        return mock_file

    def list_recordings(self) -> List[Dict[str, Any]]:
        """List available recordings."""
        recordings = self._find_recordings()
        return [
            {
                "path": str(r),
                "name": r.name,
                "size": r.stat().st_size,
                "modified": datetime.fromtimestamp(r.stat().st_mtime).isoformat(),
            }
            for r in recordings
        ]

    def validate_config(self) -> bool:
        """Validate provider configuration."""
        if not self.recording_dir.exists():
            logger.warning(f"Recording directory not found: {self.recording_dir}")

        if self.use_websocket and not self.websocket_password:
            logger.warning("OBS websocket password not configured")

        return True

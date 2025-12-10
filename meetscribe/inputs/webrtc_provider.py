"""
WebRTC Stream INPUT provider for MeetScribe.

Captures audio from WebRTC streams.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.providers import InputProvider

logger = logging.getLogger(__name__)


class WebRTCProvider(InputProvider):
    """
    WebRTC Stream INPUT provider.

    Captures audio from WebRTC streams for transcription.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize WebRTC provider.

        Config params:
            stream_url: WebRTC stream URL or signaling server
            ice_servers: List of ICE servers for WebRTC
            output_dir: Directory for recordings
            recording_format: Output format (wav, mp3)
            max_duration: Maximum recording duration in seconds
            auto_reconnect: Auto-reconnect on disconnect
            stun_servers: List of STUN servers
            turn_servers: List of TURN servers with credentials
        """
        super().__init__(config)

        self.stream_url = config.get("stream_url")
        self.ice_servers = config.get("ice_servers", [{"urls": "stun:stun.l.google.com:19302"}])
        self.output_dir = Path(config.get("output_dir", "./recordings"))
        self.recording_format = config.get("recording_format", "wav")
        self.max_duration = config.get("max_duration", 14400)  # 4 hours
        self.auto_reconnect = config.get("auto_reconnect", True)
        self.stun_servers = config.get("stun_servers", [])
        self.turn_servers = config.get("turn_servers", [])

        # Recording state
        self._is_recording = False
        self._audio_data = []

    def record(self, meeting_id: str) -> Path:
        """
        Record from WebRTC stream.

        Args:
            meeting_id: Meeting identifier

        Returns:
            Path to recorded audio file
        """
        logger.info(f"Starting WebRTC recording for {meeting_id}")

        if not self.stream_url:
            logger.warning("No stream URL configured - running in mock mode")
            return self._create_mock_recording(meeting_id)

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        audio_path = loop.run_until_complete(self._record_stream(meeting_id))
        return audio_path

    async def _record_stream(self, meeting_id: str) -> Path:
        """Async recording implementation."""
        try:
            from aiortc import RTCPeerConnection, RTCSessionDescription
            from aiortc.contrib.media import MediaRecorder

            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_file = self.output_dir / f"{meeting_id}.{self.recording_format}"

            # Create peer connection
            pc = RTCPeerConnection(configuration={"iceServers": self._build_ice_servers()})

            # Create recorder
            recorder = MediaRecorder(str(output_file))

            @pc.on("track")
            async def on_track(track):
                if track.kind == "audio":
                    logger.info("Received audio track")
                    recorder.addTrack(track)

            @pc.on("connectionstatechange")
            async def on_connectionstatechange():
                logger.info(f"Connection state: {pc.connectionState}")
                if pc.connectionState == "connected":
                    self._is_recording = True
                    await recorder.start()
                elif pc.connectionState in ("failed", "closed"):
                    self._is_recording = False
                    await recorder.stop()

            # Connect to signaling server and establish connection
            # This is a simplified implementation - real WebRTC requires signaling
            offer = await self._get_offer_from_signaling()
            if offer:
                await pc.setRemoteDescription(RTCSessionDescription(**offer))
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                await self._send_answer_to_signaling(pc.localDescription)

            # Wait for recording to complete
            await asyncio.sleep(self.max_duration)

            # Cleanup
            await recorder.stop()
            await pc.close()

            return output_file

        except ImportError:
            logger.error("aiortc not installed. Run: pip install aiortc")
            return self._create_mock_recording(meeting_id)
        except Exception as e:
            logger.error(f"WebRTC recording failed: {e}")
            return self._create_mock_recording(meeting_id)

    def _build_ice_servers(self) -> List[Dict]:
        """Build ICE server configuration."""
        servers = list(self.ice_servers)

        # Add STUN servers
        for stun in self.stun_servers:
            servers.append({"urls": f"stun:{stun}"})

        # Add TURN servers
        for turn in self.turn_servers:
            servers.append(
                {
                    "urls": f"turn:{turn['host']}",
                    "username": turn.get("username"),
                    "credential": turn.get("credential"),
                }
            )

        return servers

    async def _get_offer_from_signaling(self) -> Optional[Dict]:
        """Get offer from signaling server."""
        # This is a placeholder - real implementation depends on signaling protocol
        logger.info("Connecting to signaling server...")

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.stream_url}/offer") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Failed to get offer: {e}")

        return None

    async def _send_answer_to_signaling(self, answer) -> bool:
        """Send answer to signaling server."""
        logger.info("Sending answer to signaling server...")

        try:
            import aiohttp

            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    f"{self.stream_url}/answer", json={"sdp": answer.sdp, "type": answer.type}
                ) as response,
            ):
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to send answer: {e}")

        return False

    def _create_mock_recording(self, meeting_id: str) -> Path:
        """Create mock recording for testing."""
        logger.info(f"[MOCK] Creating mock WebRTC recording for {meeting_id}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / meeting_id
        output_path.mkdir(parents=True, exist_ok=True)

        mock_file = output_path / "mock_webrtc_recording.txt"
        with open(mock_file, "w") as f:
            f.write(f"Mock WebRTC recording for {meeting_id}\n")
            f.write("This is a placeholder file.\n")
            f.write("Configure stream_url to capture actual WebRTC streams.\n")

        # Save metadata
        meta_file = output_path / "webrtc_metadata.json"
        metadata = {
            "meeting_id": meeting_id,
            "source": "webrtc",
            "mock": True,
            "stream_url": self.stream_url,
            "created_at": datetime.now().isoformat(),
        }
        with open(meta_file, "w") as f:
            json.dump(metadata, f, indent=2)

        return mock_file

    def stop_recording(self):
        """Stop current recording."""
        self._is_recording = False
        logger.info("Recording stopped")

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording

    def validate_config(self) -> bool:
        """Validate provider configuration."""
        if not self.stream_url:
            logger.warning("No stream URL configured - running in mock mode")
        return True

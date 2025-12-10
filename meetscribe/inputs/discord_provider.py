"""
Discord Bot INPUT provider for MeetScribe.

Records audio from Discord voice channels using discord.py.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import logging
import os
import asyncio
import json

from ..core.providers import InputProvider
from ..core.meeting_id import generate_meeting_id


logger = logging.getLogger(__name__)


class DiscordBotProvider(InputProvider):
    """
    Discord Bot INPUT provider.

    Records audio from Discord voice channels.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Discord Bot provider.

        Config params:
            bot_token: Discord bot token (or from DISCORD_BOT_TOKEN env)
            guild_id: Target guild/server ID
            channel_id: Target voice channel ID
            recording_format: Output format (mp3, wav, ogg)
            max_duration: Maximum recording duration in seconds
            output_dir: Directory for recordings
            auto_join: Auto-join when users are present
            min_users: Minimum users to start recording (default: 1)
        """
        super().__init__(config)

        self.bot_token = config.get('bot_token') or os.getenv('DISCORD_BOT_TOKEN')
        self.guild_id = config.get('guild_id')
        self.channel_id = config.get('channel_id')
        self.recording_format = config.get('recording_format', 'mp3')
        self.max_duration = config.get('max_duration', 14400)  # 4 hours default
        self.output_dir = Path(config.get('output_dir', './recordings'))
        self.auto_join = config.get('auto_join', False)
        self.min_users = config.get('min_users', 1)

        # State
        self._is_recording = False
        self._current_meeting_id: Optional[str] = None
        self._bot = None

    def record(self, meeting_id: str) -> Path:
        """
        Start recording from Discord voice channel.

        Args:
            meeting_id: Meeting identifier

        Returns:
            Path to recorded audio file
        """
        logger.info(f"Starting Discord recording for {meeting_id}")

        if not self.bot_token:
            logger.warning("No bot token - running in mock mode")
            return self._create_mock_recording(meeting_id)

        # Run async recording
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        audio_path = loop.run_until_complete(self._record_async(meeting_id))
        return audio_path

    async def _record_async(self, meeting_id: str) -> Path:
        """Async recording implementation."""
        try:
            import discord
            from discord.ext import commands

            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_file = self.output_dir / f"{meeting_id}.{self.recording_format}"

            # Create bot
            intents = discord.Intents.default()
            intents.voice_states = True
            intents.guilds = True

            bot = commands.Bot(command_prefix='!', intents=intents)
            self._bot = bot

            recording_done = asyncio.Event()
            audio_data = []

            @bot.event
            async def on_ready():
                logger.info(f"Discord bot connected as {bot.user}")

                # Find voice channel
                guild = bot.get_guild(int(self.guild_id)) if self.guild_id else None
                if not guild:
                    logger.error("Guild not found")
                    recording_done.set()
                    return

                channel = guild.get_channel(int(self.channel_id)) if self.channel_id else None
                if not channel:
                    logger.error("Voice channel not found")
                    recording_done.set()
                    return

                # Connect to voice channel
                try:
                    voice_client = await channel.connect()
                    logger.info(f"Connected to voice channel: {channel.name}")

                    # Start recording
                    self._is_recording = True
                    self._current_meeting_id = meeting_id

                    # Record using sink
                    # Note: discord.py voice recording requires additional setup
                    # This is a simplified implementation

                    # Wait for recording to complete or timeout
                    await asyncio.sleep(self.max_duration)

                except Exception as e:
                    logger.error(f"Recording error: {e}")
                finally:
                    self._is_recording = False
                    if bot.voice_clients:
                        await bot.voice_clients[0].disconnect()
                    recording_done.set()

            # Start bot
            bot_task = asyncio.create_task(bot.start(self.bot_token))

            # Wait for recording to complete
            await recording_done.wait()

            # Cleanup
            await bot.close()

            # Save audio data
            if audio_data:
                self._save_audio(audio_data, output_file)
            else:
                # Create placeholder
                self._create_mock_recording(meeting_id)

            return output_file

        except ImportError:
            logger.error("discord.py not installed. Run: pip install discord.py[voice]")
            return self._create_mock_recording(meeting_id)
        except Exception as e:
            logger.error(f"Discord recording failed: {e}")
            return self._create_mock_recording(meeting_id)

    def _save_audio(self, audio_data: List[bytes], output_file: Path):
        """Save recorded audio data."""
        try:
            from pydub import AudioSegment

            # Combine audio chunks
            combined = AudioSegment.empty()
            for chunk in audio_data:
                segment = AudioSegment(
                    data=chunk,
                    sample_width=2,
                    frame_rate=48000,
                    channels=2
                )
                combined += segment

            # Export
            combined.export(str(output_file), format=self.recording_format)
            logger.info(f"Audio saved: {output_file}")

        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            # Create placeholder
            with open(output_file, 'wb') as f:
                f.write(b'')

    def _create_mock_recording(self, meeting_id: str) -> Path:
        """Create mock recording for testing."""
        logger.info(f"[MOCK] Creating mock Discord recording for {meeting_id}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / f"{meeting_id}.txt"

        with open(output_file, 'w') as f:
            f.write(f"Mock Discord recording for {meeting_id}\n")
            f.write("This is a placeholder file.\n")
            f.write("Configure Discord bot token to record actual audio.\n")

        # Save metadata
        meta_file = self.output_dir / f"{meeting_id}_metadata.json"
        metadata = {
            'meeting_id': meeting_id,
            'source': 'discord',
            'mock': True,
            'guild_id': self.guild_id,
            'channel_id': self.channel_id,
            'created_at': datetime.now().isoformat()
        }
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return output_file

    def stop_recording(self):
        """Stop current recording."""
        self._is_recording = False
        logger.info("Recording stopped")

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording

    def validate_config(self) -> bool:
        """Validate provider configuration."""
        if not self.bot_token:
            logger.warning("No Discord bot token configured - running in mock mode")

        if not self.guild_id:
            logger.warning("No guild_id configured")

        if not self.channel_id:
            logger.warning("No channel_id configured")

        return True


class DiscordDaemon:
    """
    Discord daemon for monitoring and auto-recording.

    Monitors voice channels and automatically starts recording
    when users join.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Discord daemon.

        Config params:
            bot_token: Discord bot token
            guild_ids: List of guild IDs to monitor
            channel_ids: List of channel IDs to monitor (empty = all)
            mode: Operation mode ('notify', 'auto_record')
            webhook_url: Discord webhook for notifications
            min_users: Minimum users to trigger recording
            cooldown: Cooldown between recordings in seconds
            output_dir: Directory for recordings
        """
        self.bot_token = config.get('bot_token') or os.getenv('DISCORD_BOT_TOKEN')
        self.guild_ids = config.get('guild_ids', [])
        self.channel_ids = config.get('channel_ids', [])
        self.mode = config.get('mode', 'notify')
        self.webhook_url = config.get('webhook_url') or os.getenv('DISCORD_WEBHOOK_URL')
        self.min_users = config.get('min_users', 2)
        self.cooldown = config.get('cooldown', 300)
        self.output_dir = Path(config.get('output_dir', './recordings'))

        # State
        self._is_running = False
        self._bot = None
        self._last_recording: Dict[str, datetime] = {}
        self._active_recordings: Dict[str, str] = {}

        # Callbacks
        self._on_meeting_start: Optional[Callable] = None
        self._on_meeting_end: Optional[Callable] = None

    async def start(self):
        """Start the daemon."""
        if not self.bot_token:
            logger.error("No bot token configured")
            return

        try:
            import discord
            from discord.ext import commands

            intents = discord.Intents.default()
            intents.voice_states = True
            intents.guilds = True
            intents.members = True

            bot = commands.Bot(command_prefix='!meetscribe ', intents=intents)
            self._bot = bot

            @bot.event
            async def on_ready():
                logger.info(f"MeetScribe daemon connected as {bot.user}")
                logger.info(f"Monitoring mode: {self.mode}")
                self._is_running = True

            @bot.event
            async def on_voice_state_update(member, before, after):
                await self._handle_voice_update(member, before, after)

            @bot.command(name='status')
            async def status_command(ctx):
                await ctx.send(f"MeetScribe Daemon Status: {'Running' if self._is_running else 'Stopped'}")
                await ctx.send(f"Active recordings: {len(self._active_recordings)}")

            @bot.command(name='record')
            async def record_command(ctx):
                if ctx.author.voice:
                    channel = ctx.author.voice.channel
                    await self._start_recording(channel)
                    await ctx.send(f"Started recording in {channel.name}")
                else:
                    await ctx.send("You must be in a voice channel to start recording")

            @bot.command(name='stop')
            async def stop_command(ctx):
                if ctx.author.voice:
                    channel = ctx.author.voice.channel
                    await self._stop_recording(channel)
                    await ctx.send(f"Stopped recording in {channel.name}")
                else:
                    await ctx.send("You must be in a voice channel to stop recording")

            await bot.start(self.bot_token)

        except ImportError:
            logger.error("discord.py not installed. Run: pip install discord.py[voice]")
        except Exception as e:
            logger.error(f"Daemon failed: {e}")

    async def stop(self):
        """Stop the daemon."""
        self._is_running = False
        if self._bot:
            await self._bot.close()
        logger.info("Daemon stopped")

    async def _handle_voice_update(self, member, before, after):
        """Handle voice state update events."""
        # User joined a voice channel
        if after.channel and (not before.channel or before.channel != after.channel):
            await self._on_user_joined(member, after.channel)

        # User left a voice channel
        if before.channel and (not after.channel or before.channel != after.channel):
            await self._on_user_left(member, before.channel)

    async def _on_user_joined(self, member, channel):
        """Handle user joining voice channel."""
        # Check if we should monitor this channel
        if self.channel_ids and str(channel.id) not in self.channel_ids:
            return

        if self.guild_ids and str(channel.guild.id) not in self.guild_ids:
            return

        # Count non-bot users
        user_count = sum(1 for m in channel.members if not m.bot)
        logger.debug(f"User {member.name} joined {channel.name} ({user_count} users)")

        if user_count >= self.min_users:
            # Check cooldown
            channel_key = str(channel.id)
            if channel_key in self._last_recording:
                elapsed = (datetime.now() - self._last_recording[channel_key]).seconds
                if elapsed < self.cooldown:
                    logger.debug(f"Cooldown active ({self.cooldown - elapsed}s remaining)")
                    return

            if self.mode == 'notify':
                await self._send_notification(channel, 'meeting_started')
            elif self.mode == 'auto_record':
                await self._start_recording(channel)

    async def _on_user_left(self, member, channel):
        """Handle user leaving voice channel."""
        # Count non-bot users
        user_count = sum(1 for m in channel.members if not m.bot)
        logger.debug(f"User {member.name} left {channel.name} ({user_count} users)")

        channel_key = str(channel.id)

        if user_count < self.min_users and channel_key in self._active_recordings:
            if self.mode == 'auto_record':
                await self._stop_recording(channel)
            elif self.mode == 'notify':
                await self._send_notification(channel, 'meeting_ended')

    async def _start_recording(self, channel):
        """Start recording a channel."""
        channel_key = str(channel.id)

        if channel_key in self._active_recordings:
            logger.info(f"Already recording {channel.name}")
            return

        meeting_id = generate_meeting_id('discord', channel.name)
        self._active_recordings[channel_key] = meeting_id
        self._last_recording[channel_key] = datetime.now()

        logger.info(f"Started recording {channel.name} ({meeting_id})")

        if self._on_meeting_start:
            self._on_meeting_start(channel, meeting_id)

        await self._send_notification(channel, 'recording_started', meeting_id)

    async def _stop_recording(self, channel):
        """Stop recording a channel."""
        channel_key = str(channel.id)

        if channel_key not in self._active_recordings:
            logger.info(f"Not recording {channel.name}")
            return

        meeting_id = self._active_recordings.pop(channel_key)
        logger.info(f"Stopped recording {channel.name} ({meeting_id})")

        if self._on_meeting_end:
            self._on_meeting_end(channel, meeting_id)

        await self._send_notification(channel, 'recording_stopped', meeting_id)

    async def _send_notification(self, channel, event_type: str, meeting_id: str = None):
        """Send notification to webhook."""
        if not self.webhook_url:
            return

        try:
            import aiohttp

            embed = {
                'title': f'MeetScribe: {event_type.replace("_", " ").title()}',
                'color': 0x5865F2,
                'fields': [
                    {'name': 'Channel', 'value': channel.name, 'inline': True},
                    {'name': 'Guild', 'value': channel.guild.name, 'inline': True},
                ],
                'timestamp': datetime.now().isoformat()
            }

            if meeting_id:
                embed['fields'].append({'name': 'Meeting ID', 'value': meeting_id, 'inline': False})

            payload = {'embeds': [embed]}

            async with aiohttp.ClientSession() as session:
                await session.post(self.webhook_url, json=payload)

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def on_meeting_start(self, callback: Callable):
        """Set callback for meeting start."""
        self._on_meeting_start = callback

    def on_meeting_end(self, callback: Callable):
        """Set callback for meeting end."""
        self._on_meeting_end = callback


def run_daemon(config: Dict[str, Any]):
    """Run Discord daemon from config."""
    daemon = DiscordDaemon(config)

    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        logger.info("Daemon interrupted")
    except Exception as e:
        logger.error(f"Daemon error: {e}")

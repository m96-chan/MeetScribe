"""
Tests for meetscribe.cli module.

Tests command-line interface functionality.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestCmdRun:
    """Tests for cmd_run function."""

    def test_cmd_run_success(self, tmp_path):
        """Test successful pipeline run."""
        from meetscribe.cli import cmd_run

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
input:
  provider: file
  params:
    audio_path: test.mp3
convert:
  engine: passthrough
llm:
  engine: notebooklm
  params:
    api_key: test
output:
  format: markdown
  params:
    output_dir: ./output
working_dir: ./meetings
"""
        )

        args = MagicMock()
        args.config = str(config_file)
        args.meeting_id = "test-meeting-id"
        args.channel = None

        with patch("meetscribe.cli.PipelineRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.run.return_value = "/output/result.md"
            mock_runner_class.return_value = mock_runner

            cmd_run(args)

            mock_runner.setup.assert_called_once()
            mock_runner.validate.assert_called_once()
            mock_runner.run.assert_called_once_with("test-meeting-id")

    def test_cmd_run_generates_meeting_id(self, tmp_path):
        """Test that meeting ID is generated when not provided."""
        from meetscribe.cli import cmd_run

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
input:
  provider: file
  params:
    audio_path: test.mp3
convert:
  engine: passthrough
llm:
  engine: notebooklm
  params:
    api_key: test
output:
  format: markdown
  params:
    output_dir: ./output
working_dir: ./meetings
"""
        )

        args = MagicMock()
        args.config = str(config_file)
        args.meeting_id = None
        args.channel = "test-channel"

        with patch("meetscribe.cli.PipelineRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.run.return_value = "/output/result.md"
            mock_runner_class.return_value = mock_runner

            with patch("meetscribe.cli.generate_meeting_id") as mock_gen:
                mock_gen.return_value = "generated-meeting-id"

                cmd_run(args)

                mock_gen.assert_called_once()
                mock_runner.run.assert_called_once_with("generated-meeting-id")


class TestCmdDaemon:
    """Tests for cmd_daemon function."""

    def test_cmd_daemon_loads_config(self, tmp_path):
        """Test that daemon command loads config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
input:
  provider: discord
  params:
    bot_token: test
convert:
  engine: passthrough
llm:
  engine: notebooklm
  params:
    api_key: test
output:
  format: markdown
  params:
    output_dir: ./output
working_dir: ./meetings
daemon:
  enabled: true
"""
        )

        args = MagicMock()
        args.config = str(config_file)

        # Test that load_config is called
        with patch("meetscribe.cli.load_config") as mock_load:
            mock_config = MagicMock()
            mock_load.return_value = mock_config

            # Patch the daemon import to avoid actual execution
            mock_daemon_module = MagicMock()
            mock_daemon_class = MagicMock()
            mock_daemon_module.DiscordDaemon = mock_daemon_class

            with patch.dict("sys.modules", {"meetscribe.daemon": mock_daemon_module}):
                try:
                    from meetscribe.cli import cmd_daemon

                    cmd_daemon(args)
                except Exception:
                    pass  # Daemon might fail but we just want to verify config loading

                mock_load.assert_called_once()


class TestCmdInit:
    """Tests for cmd_init function."""

    def test_cmd_init_discord(self, tmp_path, monkeypatch):
        """Test initializing Discord configuration."""
        from meetscribe.cli import cmd_init

        monkeypatch.chdir(tmp_path)

        args = MagicMock()
        args.provider = "discord"

        cmd_init(args)

        config_file = tmp_path / "config_discord.yaml"
        assert config_file.exists()
        content = config_file.read_text()
        assert "discord" in content.lower()
        assert "bot_token" in content

    def test_cmd_init_zoom(self, tmp_path, monkeypatch):
        """Test initializing Zoom configuration."""
        from meetscribe.cli import cmd_init

        monkeypatch.chdir(tmp_path)

        args = MagicMock()
        args.provider = "zoom"

        cmd_init(args)

        config_file = tmp_path / "config_zoom.yaml"
        assert config_file.exists()
        content = config_file.read_text()
        assert "zoom" in content.lower()

    def test_cmd_init_meet(self, tmp_path, monkeypatch):
        """Test initializing Google Meet configuration."""
        from meetscribe.cli import cmd_init

        monkeypatch.chdir(tmp_path)

        args = MagicMock()
        args.provider = "meet"

        cmd_init(args)

        config_file = tmp_path / "config_meet.yaml"
        assert config_file.exists()

    def test_cmd_init_proctap(self, tmp_path, monkeypatch):
        """Test initializing ProcTap configuration."""
        from meetscribe.cli import cmd_init

        monkeypatch.chdir(tmp_path)

        args = MagicMock()
        args.provider = "proctap"

        cmd_init(args)

        config_file = tmp_path / "config_proctap.yaml"
        assert config_file.exists()

    def test_cmd_init_obs(self, tmp_path, monkeypatch):
        """Test initializing OBS configuration."""
        from meetscribe.cli import cmd_init

        monkeypatch.chdir(tmp_path)

        args = MagicMock()
        args.provider = "obs"

        cmd_init(args)

        config_file = tmp_path / "config_obs.yaml"
        assert config_file.exists()


class TestMain:
    """Tests for main function."""

    def test_main_no_command(self, capsys):
        """Test main with no command shows help."""
        from meetscribe.cli import main

        with patch("sys.argv", ["meetscribe"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_main_run_command(self, tmp_path):
        """Test main with run command."""
        from meetscribe.cli import main

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
input:
  provider: file
  params:
    audio_path: test.mp3
convert:
  engine: passthrough
llm:
  engine: notebooklm
  params:
    api_key: test
output:
  format: markdown
  params:
    output_dir: ./output
working_dir: ./meetings
"""
        )

        with patch("sys.argv", ["meetscribe", "run", "--config", str(config_file)]):
            with patch("meetscribe.cli.PipelineRunner") as mock_runner_class:
                mock_runner = MagicMock()
                mock_runner.run.return_value = "/output/result.md"
                mock_runner_class.return_value = mock_runner

                main()

                mock_runner.run.assert_called_once()

    def test_main_init_command(self, tmp_path, monkeypatch):
        """Test main with init command."""
        from meetscribe.cli import main

        monkeypatch.chdir(tmp_path)

        with patch("sys.argv", ["meetscribe", "init", "discord"]):
            main()

            assert (tmp_path / "config_discord.yaml").exists()

    def test_main_command_failure(self, tmp_path, capsys):
        """Test main handles command failure."""
        from meetscribe.cli import main

        with patch("sys.argv", ["meetscribe", "run", "--config", "nonexistent.yaml"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_main_run_with_meeting_id(self, tmp_path):
        """Test main with run command and meeting ID."""
        from meetscribe.cli import main

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
input:
  provider: file
  params:
    audio_path: test.mp3
convert:
  engine: passthrough
llm:
  engine: notebooklm
  params:
    api_key: test
output:
  format: markdown
  params:
    output_dir: ./output
working_dir: ./meetings
"""
        )

        with patch(
            "sys.argv",
            ["meetscribe", "run", "--config", str(config_file), "--meeting-id", "custom-id"],
        ):
            with patch("meetscribe.cli.PipelineRunner") as mock_runner_class:
                mock_runner = MagicMock()
                mock_runner.run.return_value = "/output/result.md"
                mock_runner_class.return_value = mock_runner

                main()

                mock_runner.run.assert_called_once_with("custom-id")

    def test_main_run_with_channel(self, tmp_path):
        """Test main with run command and channel option."""
        from meetscribe.cli import main

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
input:
  provider: discord
  params:
    bot_token: test
convert:
  engine: passthrough
llm:
  engine: notebooklm
  params:
    api_key: test
output:
  format: markdown
  params:
    output_dir: ./output
working_dir: ./meetings
"""
        )

        with patch(
            "sys.argv",
            ["meetscribe", "run", "--config", str(config_file), "--channel", "test-channel"],
        ):
            with patch("meetscribe.cli.PipelineRunner") as mock_runner_class:
                mock_runner = MagicMock()
                mock_runner.run.return_value = "/output/result.md"
                mock_runner_class.return_value = mock_runner

                with patch("meetscribe.cli.generate_meeting_id") as mock_gen:
                    mock_gen.return_value = "generated-id"

                    main()

                    # Verify channel was passed to generate_meeting_id
                    call_kwargs = mock_gen.call_args[1]
                    assert call_kwargs["channel_or_pid"] == "test-channel"

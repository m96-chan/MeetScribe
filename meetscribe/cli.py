"""
Command-line interface for MeetScribe.

Commands:
- run: Execute pipeline for a meeting
- daemon: Monitor Discord for meetings
- init: Initialize provider configurations
"""

import argparse
import logging
import sys
from pathlib import Path

from .core.config import load_config
from .core.runner import PipelineRunner
from .core.meeting_id import generate_meeting_id


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def cmd_run(args):
    """
    Execute pipeline for a meeting.

    Args:
        args: Parsed command-line arguments
    """
    logger.info(f"Loading config: {args.config}")
    config = load_config(Path(args.config))

    logger.info("Initializing pipeline...")
    runner = PipelineRunner(config)
    runner.setup()
    runner.validate()

    # Generate meeting ID if not provided
    meeting_id = args.meeting_id
    if not meeting_id:
        meeting_id = generate_meeting_id(
            source=config.input.provider, channel_or_pid=args.channel or "default"
        )
        logger.info(f"Generated meeting ID: {meeting_id}")

    # Run pipeline
    logger.info(f"Starting pipeline for: {meeting_id}")
    output = runner.run(meeting_id)

    logger.info(f"Pipeline complete!")
    logger.info(f"Output: {output}")
    print(f"\nSuccess! Output available at:\n{output}")


def cmd_daemon(args):
    """
    Run Discord monitoring daemon.

    Args:
        args: Parsed command-line arguments
    """
    logger.info(f"Loading config: {args.config}")
    config = load_config(Path(args.config))

    logger.info("Starting Discord daemon...")
    from .daemon import DiscordDaemon

    daemon = DiscordDaemon(config)
    daemon.start()


def cmd_init(args):
    """
    Initialize provider configuration.

    Args:
        args: Parsed command-line arguments
    """
    provider = args.provider
    logger.info(f"Initializing {provider} configuration...")

    from .init_templates import get_init_template

    template = get_init_template(provider)
    output_path = Path(f"config_{provider}.yaml")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(template)

    logger.info(f"Configuration template created: {output_path}")
    print(f"\nConfiguration template created: {output_path}")
    print(f"Please edit this file with your credentials and settings.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MeetScribe - Multi-source AI Meeting Pipeline", prog="meetscribe"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Execute pipeline for a meeting")
    run_parser.add_argument("--config", required=True, help="Path to pipeline config YAML")
    run_parser.add_argument("--meeting-id", help="Meeting ID (auto-generated if not provided)")
    run_parser.add_argument(
        "--channel", help="Channel ID or name (used for auto-generated meeting ID)"
    )
    run_parser.set_defaults(func=cmd_run)

    # Daemon command
    daemon_parser = subparsers.add_parser("daemon", help="Run Discord monitoring daemon")
    daemon_parser.add_argument("--config", required=True, help="Path to daemon config YAML")
    daemon_parser.set_defaults(func=cmd_daemon)

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize provider configuration")
    init_parser.add_argument(
        "provider",
        choices=["discord", "zoom", "meet", "proctap", "obs"],
        help="Provider to initialize",
    )
    init_parser.set_defaults(func=cmd_init)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

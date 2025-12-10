"""
PoC pipeline test script.

Tests the entire pipeline without requiring pytest.
"""

import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add meetscribe to path
sys.path.insert(0, str(Path(__file__).parent))

from meetscribe.core.config import load_config
from meetscribe.core.runner import PipelineRunner
from meetscribe.core.meeting_id import generate_meeting_id


def test_poc_pipeline():
    """Test PoC pipeline end-to-end."""
    print("=" * 80)
    print("MeetScribe PoC Pipeline Test")
    print("=" * 80)
    print()

    # Check if sample audio exists
    audio_path = Path("sample_audio.mp3")
    if not audio_path.exists():
        print("Creating dummy audio file...")
        with open(audio_path, "w") as f:
            f.write("Dummy audio data for testing")
        print(f"Created: {audio_path}")
        print()

    # Load config
    config_path = Path("config.poc.yaml")
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        print("Please ensure config.poc.yaml exists in the current directory")
        return False

    print(f"Loading config: {config_path}")
    try:
        config = load_config(config_path)
        print("[OK] Config loaded successfully")
        print()
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}")
        return False

    # Initialize pipeline
    print("Initializing pipeline...")
    try:
        runner = PipelineRunner(config)
        runner.setup()
        print("[OK] Pipeline initialized successfully")
        print()
    except Exception as e:
        print(f"ERROR: Failed to initialize pipeline: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Generate meeting ID
    meeting_id = generate_meeting_id(source="file", channel_or_pid="poc_test")
    print(f"Meeting ID: {meeting_id}")
    print()

    # Run pipeline
    print("Running pipeline...")
    print("-" * 80)
    try:
        output = runner.run(meeting_id)
        print("-" * 80)
        print()
        print("[OK] Pipeline completed successfully!")
        print()
        print(f"Output: {output}")
        print()

        # Check output exists
        if Path(output).exists():
            print("[OK] Output file created successfully")
            print()
            print("Contents:")
            with open(output, "r", encoding="utf-8") as f:
                content = f.read()
                print(content)
        else:
            print(f"Note: Output location is a URL, not a file: {output}")

        return True

    except Exception as e:
        print(f"ERROR: Pipeline failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = test_poc_pipeline()
    print()
    print("=" * 80)
    if success:
        print("[SUCCESS] PoC Test PASSED")
        print("=" * 80)
        sys.exit(0)
    else:
        print("[FAILED] PoC Test FAILED")
        print("=" * 80)
        sys.exit(1)

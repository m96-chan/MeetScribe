"""
Audio processing utilities for MeetScribe.

Provides functions for audio preprocessing, analysis, and conversion.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import logging
import subprocess
import json
import os

logger = logging.getLogger(__name__)

# Supported audio formats
SUPPORTED_FORMATS = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".opus": "audio/opus",
    ".webm": "audio/webm",
    ".aac": "audio/aac",
}


def get_audio_info(audio_path: Path) -> Dict[str, Any]:
    """
    Extract detailed audio information using ffprobe.

    Args:
        audio_path: Path to audio file

    Returns:
        Dictionary containing audio metadata
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    info = {
        "path": str(audio_path),
        "filename": audio_path.name,
        "format": audio_path.suffix.lower(),
        "size_bytes": audio_path.stat().st_size,
    }

    try:
        # Use ffprobe to get detailed info
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            probe_data = json.loads(result.stdout)

            # Extract format info
            if "format" in probe_data:
                fmt = probe_data["format"]
                info["duration"] = float(fmt.get("duration", 0))
                info["bitrate"] = int(fmt.get("bit_rate", 0))
                info["format_name"] = fmt.get("format_name", "")
                info["format_long_name"] = fmt.get("format_long_name", "")

            # Extract audio stream info
            for stream in probe_data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    info["codec"] = stream.get("codec_name", "")
                    info["codec_long_name"] = stream.get("codec_long_name", "")
                    info["samplerate"] = int(stream.get("sample_rate", 0))
                    info["channels"] = stream.get("channels", 0)
                    info["channel_layout"] = stream.get("channel_layout", "")
                    info["bits_per_sample"] = stream.get("bits_per_sample", 0)
                    break

    except FileNotFoundError:
        logger.warning("ffprobe not found - using basic file info only")
    except subprocess.TimeoutExpired:
        logger.warning("ffprobe timed out")
    except json.JSONDecodeError:
        logger.warning("Failed to parse ffprobe output")
    except Exception as e:
        logger.warning(f"Error getting audio info: {e}")

    return info


def get_audio_duration(audio_path: Path) -> float:
    """
    Get audio duration in seconds.

    Args:
        audio_path: Path to audio file

    Returns:
        Duration in seconds
    """
    info = get_audio_info(audio_path)
    return info.get("duration", 0.0)


def convert_audio(
    input_path: Path,
    output_path: Path,
    output_format: str = "wav",
    samplerate: int = 16000,
    channels: int = 1,
    bitrate: Optional[str] = None,
) -> Path:
    """
    Convert audio to a different format.

    Args:
        input_path: Input audio file path
        output_path: Output file path
        output_format: Target format (wav, mp3, etc.)
        samplerate: Target sample rate
        channels: Number of channels (1=mono, 2=stereo)
        bitrate: Target bitrate (e.g., "128k")

    Returns:
        Path to converted file
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-ar",
        str(samplerate),
        "-ac",
        str(channels),
    ]

    if bitrate:
        cmd.extend(["-b:a", bitrate])

    cmd.extend(["-y", str(output_path)])  # Overwrite output file

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        logger.info(f"Converted {input_path.name} to {output_path.name}")
        return output_path

    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found - please install ffmpeg")


def normalize_audio(
    input_path: Path,
    output_path: Optional[Path] = None,
    target_lufs: float = -16.0,
    target_peak: float = -1.0,
) -> Path:
    """
    Normalize audio levels using EBU R128 loudness normalization.

    Args:
        input_path: Input audio file path
        output_path: Output file path (defaults to input with _normalized suffix)
        target_lufs: Target integrated loudness in LUFS
        target_peak: Maximum peak level in dB

    Returns:
        Path to normalized file
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_normalized{input_path.suffix}"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-af",
        f"loudnorm=I={target_lufs}:TP={target_peak}:LRA=11",
        "-y",
        str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        logger.info(f"Normalized {input_path.name} -> {output_path.name}")
        return output_path

    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found - please install ffmpeg")


def remove_silence(
    input_path: Path,
    output_path: Optional[Path] = None,
    silence_threshold: float = -50.0,
    min_silence_duration: float = 0.5,
) -> Path:
    """
    Remove silence from audio file.

    Args:
        input_path: Input audio file path
        output_path: Output file path
        silence_threshold: Silence threshold in dB
        min_silence_duration: Minimum silence duration to remove (seconds)

    Returns:
        Path to processed file
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_nosilence{input_path.suffix}"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-af",
        f"silenceremove=start_periods=1:start_silence={min_silence_duration}:"
        f"start_threshold={silence_threshold}dB:"
        f"stop_periods=-1:stop_silence={min_silence_duration}:"
        f"stop_threshold={silence_threshold}dB",
        "-y",
        str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        logger.info(f"Removed silence from {input_path.name}")
        return output_path

    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found - please install ffmpeg")


def extract_audio_from_video(
    video_path: Path,
    output_path: Optional[Path] = None,
    output_format: str = "mp3",
    samplerate: int = 44100,
    bitrate: str = "128k",
) -> Path:
    """
    Extract audio track from video file.

    Args:
        video_path: Input video file path
        output_path: Output audio file path
        output_format: Output audio format
        samplerate: Sample rate
        bitrate: Audio bitrate

    Returns:
        Path to extracted audio
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if output_path is None:
        output_path = video_path.parent / f"{video_path.stem}.{output_format}"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vn",  # No video
        "-ar",
        str(samplerate),
        "-b:a",
        bitrate,
        "-y",
        str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        logger.info(f"Extracted audio from {video_path.name} -> {output_path.name}")
        return output_path

    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found - please install ffmpeg")


def split_audio(
    input_path: Path,
    output_dir: Path,
    segment_duration: float = 300.0,  # 5 minutes
    output_format: Optional[str] = None,
) -> List[Path]:
    """
    Split audio file into segments.

    Args:
        input_path: Input audio file path
        output_dir: Output directory for segments
        segment_duration: Duration of each segment in seconds
        output_format: Output format (defaults to input format)

    Returns:
        List of paths to segments
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    if output_format is None:
        output_format = input_path.suffix.replace(".", "")

    output_pattern = str(output_dir / f"{input_path.stem}_%03d.{output_format}")

    cmd = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-f",
        "segment",
        "-segment_time",
        str(segment_duration),
        "-c",
        "copy",
        "-y",
        output_pattern,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        # Get list of created segments
        segments = sorted(output_dir.glob(f"{input_path.stem}_*.{output_format}"))
        logger.info(f"Split {input_path.name} into {len(segments)} segments")
        return segments

    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found - please install ffmpeg")


def merge_audio(
    input_paths: List[Path],
    output_path: Path,
) -> Path:
    """
    Merge multiple audio files into one.

    Args:
        input_paths: List of input audio file paths
        output_path: Output file path

    Returns:
        Path to merged file
    """
    if not input_paths:
        raise ValueError("No input files provided")

    for path in input_paths:
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create concat file
    concat_file = output_path.parent / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for path in input_paths:
            f.write(f"file '{path.absolute()}'\n")

    cmd = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        "-y",
        str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        logger.info(f"Merged {len(input_paths)} files -> {output_path.name}")
        return output_path

    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found - please install ffmpeg")
    finally:
        # Clean up concat file
        if concat_file.exists():
            concat_file.unlink()


def analyze_audio_quality(audio_path: Path) -> Dict[str, Any]:
    """
    Analyze audio quality metrics.

    Args:
        audio_path: Path to audio file

    Returns:
        Dictionary containing quality metrics
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    metrics = {
        "path": str(audio_path),
        "filename": audio_path.name,
    }

    try:
        # Get basic info
        info = get_audio_info(audio_path)
        metrics.update(info)

        # Get loudness info using ffmpeg
        result = subprocess.run(
            ["ffmpeg", "-i", str(audio_path), "-af", "ebur128=peak=true", "-f", "null", "-"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Parse loudness info from stderr
        for line in result.stderr.split("\n"):
            if "I:" in line and "LUFS" in line:
                try:
                    lufs = float(line.split("I:")[1].split("LUFS")[0].strip())
                    metrics["integrated_lufs"] = lufs
                except (ValueError, IndexError):
                    pass
            elif "Peak:" in line and "dBFS" in line:
                try:
                    peak = float(line.split("Peak:")[1].split("dBFS")[0].strip())
                    metrics["peak_dbfs"] = peak
                except (ValueError, IndexError):
                    pass

    except FileNotFoundError:
        logger.warning("ffmpeg not found - quality analysis limited")
    except subprocess.TimeoutExpired:
        logger.warning("Audio analysis timed out")
    except Exception as e:
        logger.warning(f"Error analyzing audio: {e}")

    return metrics


def is_valid_audio_format(file_path: Path) -> bool:
    """
    Check if file has a supported audio format.

    Args:
        file_path: Path to file

    Returns:
        True if format is supported
    """
    return file_path.suffix.lower() in SUPPORTED_FORMATS


def get_mime_type(file_path: Path) -> str:
    """
    Get MIME type for audio file.

    Args:
        file_path: Path to audio file

    Returns:
        MIME type string
    """
    return SUPPORTED_FORMATS.get(file_path.suffix.lower(), "application/octet-stream")

"""
Tests for meetscribe.utils.audio module.

Tests audio processing utilities including format detection,
audio info retrieval, and mock tests for ffmpeg operations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestSupportedFormats:
    """Tests for SUPPORTED_FORMATS constant."""

    def test_supported_formats_contains_common_formats(self):
        """Test that common audio formats are supported."""
        from meetscribe.utils.audio import SUPPORTED_FORMATS

        assert ".mp3" in SUPPORTED_FORMATS
        assert ".wav" in SUPPORTED_FORMATS
        assert ".m4a" in SUPPORTED_FORMATS
        assert ".flac" in SUPPORTED_FORMATS
        assert ".ogg" in SUPPORTED_FORMATS

    def test_supported_formats_has_mime_types(self):
        """Test that MIME types are defined for formats."""
        from meetscribe.utils.audio import SUPPORTED_FORMATS

        assert SUPPORTED_FORMATS[".mp3"] == "audio/mpeg"
        assert SUPPORTED_FORMATS[".wav"] == "audio/wav"


class TestIsValidAudioFormat:
    """Tests for is_valid_audio_format function."""

    def test_valid_formats(self):
        """Test that valid audio formats are recognized."""
        from meetscribe.utils.audio import is_valid_audio_format

        assert is_valid_audio_format(Path("test.mp3")) is True
        assert is_valid_audio_format(Path("test.wav")) is True
        assert is_valid_audio_format(Path("test.m4a")) is True
        assert is_valid_audio_format(Path("test.flac")) is True

    def test_invalid_formats(self):
        """Test that invalid audio formats are rejected."""
        from meetscribe.utils.audio import is_valid_audio_format

        assert is_valid_audio_format(Path("test.txt")) is False
        assert is_valid_audio_format(Path("test.pdf")) is False
        assert is_valid_audio_format(Path("test.exe")) is False

    def test_case_insensitive(self):
        """Test that format check is case insensitive."""
        from meetscribe.utils.audio import is_valid_audio_format

        assert is_valid_audio_format(Path("test.MP3")) is True
        assert is_valid_audio_format(Path("test.Wav")) is True


class TestGetMimeType:
    """Tests for get_mime_type function."""

    def test_get_mime_type_mp3(self):
        """Test getting MIME type for MP3."""
        from meetscribe.utils.audio import get_mime_type

        assert get_mime_type(Path("test.mp3")) == "audio/mpeg"

    def test_get_mime_type_wav(self):
        """Test getting MIME type for WAV."""
        from meetscribe.utils.audio import get_mime_type

        assert get_mime_type(Path("test.wav")) == "audio/wav"

    def test_get_mime_type_unknown(self):
        """Test getting MIME type for unknown format."""
        from meetscribe.utils.audio import get_mime_type

        assert get_mime_type(Path("test.unknown")) == "application/octet-stream"


class TestGetAudioInfo:
    """Tests for get_audio_info function."""

    def test_get_audio_info_file_not_found(self, tmp_path):
        """Test get_audio_info with nonexistent file."""
        from meetscribe.utils.audio import get_audio_info

        with pytest.raises(FileNotFoundError):
            get_audio_info(tmp_path / "nonexistent.mp3")

    def test_get_audio_info_basic(self, tmp_path):
        """Test get_audio_info returns basic file info."""
        from meetscribe.utils.audio import get_audio_info

        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake audio content")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ffprobe not found")

            result = get_audio_info(test_file)

            assert result["path"] == str(test_file)
            assert result["filename"] == "test.mp3"
            assert result["format"] == ".mp3"
            assert result["size_bytes"] == 18

    def test_get_audio_info_with_ffprobe(self, tmp_path):
        """Test get_audio_info with ffprobe available."""
        from meetscribe.utils.audio import get_audio_info

        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake audio content")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """{
            "format": {
                "duration": "120.5",
                "bit_rate": "128000",
                "format_name": "mp3",
                "format_long_name": "MP3 Audio"
            },
            "streams": [{
                "codec_type": "audio",
                "codec_name": "mp3",
                "sample_rate": "44100",
                "channels": 2,
                "channel_layout": "stereo"
            }]
        }"""

        with patch("subprocess.run", return_value=mock_result):
            result = get_audio_info(test_file)

            assert result["duration"] == 120.5
            assert result["bitrate"] == 128000
            assert result["codec"] == "mp3"
            assert result["samplerate"] == 44100
            assert result["channels"] == 2


class TestGetAudioDuration:
    """Tests for get_audio_duration function."""

    def test_get_audio_duration(self, tmp_path):
        """Test getting audio duration."""
        from meetscribe.utils.audio import get_audio_duration

        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake audio")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"format": {"duration": "180.0"}}'

        with patch("subprocess.run", return_value=mock_result):
            result = get_audio_duration(test_file)
            assert result == 180.0


class TestConvertAudio:
    """Tests for convert_audio function."""

    def test_convert_audio_file_not_found(self, tmp_path):
        """Test convert_audio with nonexistent input."""
        from meetscribe.utils.audio import convert_audio

        with pytest.raises(FileNotFoundError):
            convert_audio(tmp_path / "nonexistent.mp3", tmp_path / "output.wav")

    def test_convert_audio_success(self, tmp_path):
        """Test successful audio conversion."""
        from meetscribe.utils.audio import convert_audio

        input_file = tmp_path / "input.mp3"
        input_file.write_bytes(b"fake audio")
        output_file = tmp_path / "output.wav"

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = convert_audio(input_file, output_file)

            assert result == output_file
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args
            assert "-ar" in call_args
            assert "16000" in call_args

    def test_convert_audio_with_bitrate(self, tmp_path):
        """Test audio conversion with custom bitrate."""
        from meetscribe.utils.audio import convert_audio

        input_file = tmp_path / "input.mp3"
        input_file.write_bytes(b"fake audio")
        output_file = tmp_path / "output.mp3"

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            convert_audio(input_file, output_file, bitrate="192k")

            call_args = mock_run.call_args[0][0]
            assert "-b:a" in call_args
            assert "192k" in call_args

    def test_convert_audio_ffmpeg_not_found(self, tmp_path):
        """Test convert_audio when ffmpeg is not found."""
        from meetscribe.utils.audio import convert_audio

        input_file = tmp_path / "input.mp3"
        input_file.write_bytes(b"fake audio")
        output_file = tmp_path / "output.wav"

        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="ffmpeg not found"):
                convert_audio(input_file, output_file)


class TestNormalizeAudio:
    """Tests for normalize_audio function."""

    def test_normalize_audio_file_not_found(self, tmp_path):
        """Test normalize_audio with nonexistent input."""
        from meetscribe.utils.audio import normalize_audio

        with pytest.raises(FileNotFoundError):
            normalize_audio(tmp_path / "nonexistent.mp3")

    def test_normalize_audio_success(self, tmp_path):
        """Test successful audio normalization."""
        from meetscribe.utils.audio import normalize_audio

        input_file = tmp_path / "input.mp3"
        input_file.write_bytes(b"fake audio")

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            result = normalize_audio(input_file)

            assert result.name == "input_normalized.mp3"

    def test_normalize_audio_custom_output(self, tmp_path):
        """Test audio normalization with custom output path."""
        from meetscribe.utils.audio import normalize_audio

        input_file = tmp_path / "input.mp3"
        input_file.write_bytes(b"fake audio")
        output_file = tmp_path / "custom_output.mp3"

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            result = normalize_audio(input_file, output_file)

            assert result == output_file


class TestRemoveSilence:
    """Tests for remove_silence function."""

    def test_remove_silence_file_not_found(self, tmp_path):
        """Test remove_silence with nonexistent input."""
        from meetscribe.utils.audio import remove_silence

        with pytest.raises(FileNotFoundError):
            remove_silence(tmp_path / "nonexistent.mp3")

    def test_remove_silence_success(self, tmp_path):
        """Test successful silence removal."""
        from meetscribe.utils.audio import remove_silence

        input_file = tmp_path / "input.mp3"
        input_file.write_bytes(b"fake audio")

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            result = remove_silence(input_file)

            assert result.name == "input_nosilence.mp3"


class TestExtractAudioFromVideo:
    """Tests for extract_audio_from_video function."""

    def test_extract_audio_file_not_found(self, tmp_path):
        """Test extract_audio_from_video with nonexistent input."""
        from meetscribe.utils.audio import extract_audio_from_video

        with pytest.raises(FileNotFoundError):
            extract_audio_from_video(tmp_path / "nonexistent.mp4")

    def test_extract_audio_success(self, tmp_path):
        """Test successful audio extraction from video."""
        from meetscribe.utils.audio import extract_audio_from_video

        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"fake video")

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            result = extract_audio_from_video(video_file)

            assert result.name == "video.mp3"


class TestSplitAudio:
    """Tests for split_audio function."""

    def test_split_audio_file_not_found(self, tmp_path):
        """Test split_audio with nonexistent input."""
        from meetscribe.utils.audio import split_audio

        with pytest.raises(FileNotFoundError):
            split_audio(tmp_path / "nonexistent.mp3", tmp_path / "output")

    def test_split_audio_success(self, tmp_path):
        """Test successful audio splitting."""
        from meetscribe.utils.audio import split_audio

        input_file = tmp_path / "input.mp3"
        input_file.write_bytes(b"fake audio")
        output_dir = tmp_path / "output"

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            result = split_audio(input_file, output_dir)

            assert output_dir.exists()
            assert isinstance(result, list)


class TestMergeAudio:
    """Tests for merge_audio function."""

    def test_merge_audio_empty_list(self, tmp_path):
        """Test merge_audio with empty input list."""
        from meetscribe.utils.audio import merge_audio

        with pytest.raises(ValueError, match="No input files"):
            merge_audio([], tmp_path / "output.mp3")

    def test_merge_audio_file_not_found(self, tmp_path):
        """Test merge_audio with nonexistent input file."""
        from meetscribe.utils.audio import merge_audio

        with pytest.raises(FileNotFoundError):
            merge_audio([tmp_path / "nonexistent.mp3"], tmp_path / "output.mp3")

    def test_merge_audio_success(self, tmp_path):
        """Test successful audio merging."""
        from meetscribe.utils.audio import merge_audio

        file1 = tmp_path / "file1.mp3"
        file2 = tmp_path / "file2.mp3"
        file1.write_bytes(b"audio1")
        file2.write_bytes(b"audio2")
        output_file = tmp_path / "merged.mp3"

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            result = merge_audio([file1, file2], output_file)

            assert result == output_file


class TestAnalyzeAudioQuality:
    """Tests for analyze_audio_quality function."""

    def test_analyze_audio_quality_file_not_found(self, tmp_path):
        """Test analyze_audio_quality with nonexistent input."""
        from meetscribe.utils.audio import analyze_audio_quality

        with pytest.raises(FileNotFoundError):
            analyze_audio_quality(tmp_path / "nonexistent.mp3")

    def test_analyze_audio_quality_basic(self, tmp_path):
        """Test basic audio quality analysis."""
        from meetscribe.utils.audio import analyze_audio_quality

        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake audio content")

        mock_ffprobe_result = MagicMock()
        mock_ffprobe_result.returncode = 0
        mock_ffprobe_result.stdout = '{"format": {"duration": "120.0"}}'

        mock_ffmpeg_result = MagicMock()
        mock_ffmpeg_result.returncode = 0
        mock_ffmpeg_result.stderr = """
        [Parsed_ebur128] I: -16.0 LUFS
        [Parsed_ebur128] Peak: -1.0 dBFS
        """

        with patch("subprocess.run", side_effect=[mock_ffprobe_result, mock_ffmpeg_result]):
            result = analyze_audio_quality(test_file)

            assert "path" in result
            assert "filename" in result

"""
Core data models for MeetScribe pipeline.

These models unify data flow across all pipeline stages.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AudioInfo:
    """Audio technical metadata."""

    duration: float
    samplerate: int
    codec: str
    channels: int = 1
    lufs: Optional[float] = None
    peak: Optional[float] = None
    noise_level: Optional[float] = None
    silence_ratio: Optional[float] = None
    bitrate: Optional[int] = None


@dataclass
class MeetingInfo:
    """Meeting metadata."""

    meeting_id: str
    source_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    participants: List[str] = field(default_factory=list)
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Segment:
    """Transcription segment with speaker diarization."""

    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None
    language: Optional[str] = None


@dataclass
class Transcript:
    """
    Unified transcript object used throughout the pipeline.

    This is the core data structure that flows from CONVERT → LLM layer.
    """

    meeting_info: MeetingInfo
    text: Optional[str] = None
    audio_path: Optional[Path] = None
    segments: List[Segment] = field(default_factory=list)
    audio_info: Optional[AudioInfo] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_processing_step(self, step: str, details: Dict[str, Any]):
        """Add a processing step to the history."""
        self.processing_history.append(
            {"timestamp": datetime.now().isoformat(), "step": step, "details": details}
        )

    def get_full_text(self) -> str:
        """Get complete transcript text."""
        if self.text:
            return self.text
        return "\n".join(seg.text for seg in self.segments)


@dataclass
class Decision:
    """A decision made during the meeting."""

    description: str
    responsible: Optional[str] = None
    deadline: Optional[str] = None


@dataclass
class ActionItem:
    """An action item from the meeting."""

    description: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None


@dataclass
class Minutes:
    """
    Unified minutes object produced by LLM layer.

    This is the output of the LLM stage, consumed by the OUTPUT layer.
    """

    meeting_id: str
    summary: str
    decisions: List[Decision] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "meeting_id": self.meeting_id,
            "summary": self.summary,
            "decisions": [
                {"description": d.description, "responsible": d.responsible, "deadline": d.deadline}
                for d in self.decisions
            ],
            "action_items": [
                {
                    "description": a.description,
                    "assignee": a.assignee,
                    "deadline": a.deadline,
                    "priority": a.priority,
                }
                for a in self.action_items
            ],
            "key_points": self.key_points,
            "participants": self.participants,
            "url": self.url,
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat(),
        }

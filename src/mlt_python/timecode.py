"""Timecode utility functions for MLT XML library.

Handles conversion between HH:MM:SS:FF timecode format and frame numbers,
using the profile's frame rate for accurate conversion.
"""

from dataclasses import dataclass
from typing import Union


@dataclass
class Timecode:
    """Represents a timecode in HH:MM:SS:FF format with frame rate awareness."""

    hours: int
    minutes: int
    seconds: int
    frames: int
    fps: float

    def __post_init__(self) -> None:
        """Validate timecode components."""
        if self.fps <= 0:
            raise ValueError(f"FPS must be positive, got {self.fps}")
        if self.frames >= int(self.fps):
            raise ValueError(
                f"Frames ({self.frames}) must be less than FPS ({self.fps})"
            )
        if self.seconds >= 60 or self.minutes >= 60 or self.hours < 0:
            raise ValueError("Invalid time component")
        if any(v < 0 for v in (self.minutes, self.seconds, self.frames)):
            raise ValueError("Time components cannot be negative")

    @classmethod
    def from_string(cls, timecode_str: str, fps: float) -> "Timecode":
        """Parse a timecode string (HH:MM:SS:FF) into a Timecode object.

        Args:
            timecode_str: Timecode in HH:MM:SS:FF format
            fps: Frames per second for frame calculation

        Returns:
            Timecode object

        Raises:
            ValueError: If timecode format is invalid
        """
        parts = timecode_str.split(":")
        if len(parts) != 4:
            raise ValueError(
                f"Invalid timecode format: {timecode_str}. Expected HH:MM:SS:FF"
            )

        try:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            frames = int(parts[3])
        except ValueError as e:
            raise ValueError(f"Invalid timecode component in {timecode_str}: {e}")

        return cls(hours, minutes, seconds, frames, fps)

    @classmethod
    def from_frames(cls, frames: int, fps: float) -> "Timecode":
        """Convert frame number to Timecode.

        Args:
            frames: Frame number (0-based)
            fps: Frames per second

        Returns:
            Timecode object
        """
        if frames < 0:
            raise ValueError(f"Frame number cannot be negative: {frames}")

        total_seconds = frames / fps
        hours = int(total_seconds // 3600)
        remaining = total_seconds % 3600
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        frame_part = int(frames % int(fps))

        return cls(hours, minutes, seconds, frame_part, fps)

    @classmethod
    def from_seconds(cls, seconds: float, fps: float) -> "Timecode":
        """Convert float seconds to Timecode.

        Args:
            seconds: Seconds
            fps: Frames per second

        Returns:
            Timecode object
        """
        return cls.from_frames(int(round(seconds * fps)), fps)


    def to_frames(self) -> int:
        """Convert timecode to absolute frame number.

        Returns:
            Frame number (0-based)
        """
        total_seconds = self.hours * 3600 + self.minutes * 60 + self.seconds
        return int(total_seconds * self.fps) + self.frames

    def to_seconds(self) -> float:
        """Convert timecode to floating-point seconds.

        Returns:
            Seconds
        """
        total_seconds = self.hours * 3600 + self.minutes * 60 + self.seconds
        return total_seconds + self.frames / self.fps

    def to_string(self) -> str:
        """Convert to HH:MM:SS:FF string format.

        Returns:
            Timecode string
        """
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}:{self.frames:02d}"

    def __str__(self) -> str:
        return self.to_string()

    def __add__(self, other: Union["Timecode", int]) -> "Timecode":
        """Add two timecodes or add frames to timecode."""
        if isinstance(other, Timecode):
            if self.fps != other.fps:
                raise ValueError("Cannot add timecodes with different FPS")
            return Timecode.from_frames(self.to_frames() + other.to_frames(), self.fps)
        elif isinstance(other, int):
            return Timecode.from_frames(self.to_frames() + other, self.fps)
        raise TypeError(f"Cannot add {type(other)} to Timecode")

    def __sub__(self, other: Union["Timecode", int]) -> "Timecode":
        """Subtract two timecodes or subtract frames from timecode."""
        if isinstance(other, Timecode):
            if self.fps != other.fps:
                raise ValueError("Cannot subtract timecodes with different FPS")
            return Timecode.from_frames(self.to_frames() - other.to_frames(), self.fps)
        elif isinstance(other, int):
            return Timecode.from_frames(self.to_frames() - other, self.fps)
        raise TypeError(f"Cannot subtract {type(other)} from Timecode")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timecode):
            return False
        return self.to_frames() == other.to_frames() and self.fps == other.fps

    def __lt__(self, other: "Timecode") -> bool:
        if self.fps != other.fps:
            raise ValueError("Cannot compare timecodes with different FPS")
        return self.to_frames() < other.to_frames()

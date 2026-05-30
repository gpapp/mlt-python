"""Timecode utility functions for MLT XML library.

Handles conversion between time formats and float seconds.
All internal storage uses float seconds; timecode strings are
only used at the XML serialization boundary.

Supports both HH:MM:SS.mmm and HH:MM:SS:FF formats on input,
but always outputs HH:MM:SS.mmm format (FPS-independent).
"""

from dataclasses import dataclass
from typing import Union


@dataclass
class Timecode:
    """Represents a time value independent of frame rate.

    Stores time as hours, minutes, seconds and milliseconds.
    No frame rate awareness — FPS is not needed for time-based calculations.
    """

    hours: int
    minutes: int
    seconds: int
    milliseconds: int

    def __post_init__(self) -> None:
        """Validate timecode components."""
        if self.milliseconds >= 1000:
            raise ValueError(
                f"Milliseconds ({self.milliseconds}) must be less than 1000"
            )
        if self.seconds >= 60 or self.minutes >= 60 or self.hours < 0:
            raise ValueError("Invalid time component")
        if any(v < 0 for v in (self.minutes, self.seconds, self.milliseconds)):
            raise ValueError("Time components cannot be negative")

    @classmethod
    def from_string(cls, timecode_str: str) -> "Timecode":
        """Parse a timecode string into a Timecode object.

        Supports two formats:
        - HH:MM:SS.mmm  (milliseconds, preferred)
        - HH:MM:SS:FF   (frames, FPS assumed to be irrelevant — uses 0 ms)

        Args:
            timecode_str: Timecode string

        Returns:
            Timecode object

        Raises:
            ValueError: If timecode format is invalid
        """
        parts = timecode_str.split(":")

        if len(parts) == 4 and "." in parts[3]:
            # HH:MM:SS.mmm format with colons
            try:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                millis_str = parts[3]
                if "." in millis_str:
                    # Overflow seconds: SS.mmm format spread across parts
                    sec_parts = millis_str.split(".")
                    seconds = int(sec_parts[0])
                    milliseconds = int(sec_parts[1].ljust(3, "0")[:3])
                else:
                    milliseconds = int(millis_str)
                return cls(hours, minutes, seconds, milliseconds)
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid timecode format: {timecode_str}: {e}")

        if len(parts) == 3 and "." in parts[2]:
            # HH:MM:SS.mmm format
            try:
                hours = int(parts[0])
                minutes = int(parts[1])
                sec_parts = parts[2].split(".")
                seconds = int(sec_parts[0])
                milliseconds = int(sec_parts[1].ljust(3, "0")[:3])
                return cls(hours, minutes, seconds, milliseconds)
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid timecode format: {timecode_str}: {e}")

        if len(parts) == 4:
            # HH:MM:SS:FF format (frames) — ignore frame value
            try:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                return cls(hours, minutes, seconds, 0)
            except ValueError as e:
                raise ValueError(f"Invalid timecode format: {timecode_str}: {e}")

        raise ValueError(
            f"Invalid timecode format: {timecode_str}. "
            f"Expected HH:MM:SS.mmm or HH:MM:SS:FF"
        )

    @classmethod
    def from_seconds(cls, seconds: float) -> "Timecode":
        """Convert float seconds to Timecode.

        Args:
            seconds: Seconds (float)

        Returns:
            Timecode object
        """
        if seconds < 0:
            raise ValueError(f"Seconds cannot be negative: {seconds}")

        total_ms = int(round(seconds * 1000))
        hours = total_ms // 3600000
        remaining = total_ms % 3600000
        minutes = remaining // 60000
        remaining = remaining % 60000
        secs = remaining // 1000
        ms = remaining % 1000

        return cls(hours, minutes, secs, ms)

    def to_seconds(self) -> float:
        """Convert timecode to floating-point seconds.

        Returns:
            Seconds
        """
        total = self.hours * 3600 + self.minutes * 60 + self.seconds
        return total + self.milliseconds / 1000.0

    def to_string(self) -> str:
        """Convert to HH:MM:SS.mmm string format.

        Returns:
            Timecode string
        """
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}.{self.milliseconds:03d}"

    def __str__(self) -> str:
        return self.to_string()

    def __add__(self, other: Union["Timecode", float]) -> "Timecode":
        """Add two timecodes or add seconds to timecode."""
        if isinstance(other, Timecode):
            return Timecode.from_seconds(self.to_seconds() + other.to_seconds())
        elif isinstance(other, (int, float)):
            return Timecode.from_seconds(self.to_seconds() + float(other))
        raise TypeError(f"Cannot add {type(other)} to Timecode")

    def __sub__(self, other: Union["Timecode", float]) -> "Timecode":
        """Subtract two timecodes or subtract seconds from timecode."""
        if isinstance(other, Timecode):
            return Timecode.from_seconds(self.to_seconds() - other.to_seconds())
        elif isinstance(other, (int, float)):
            return Timecode.from_seconds(self.to_seconds() - float(other))
        raise TypeError(f"Cannot subtract {type(other)} from Timecode")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timecode):
            return False
        return abs(self.to_seconds() - other.to_seconds()) < 0.0005

    def __lt__(self, other: "Timecode") -> bool:
        return self.to_seconds() < other.to_seconds()

    def __le__(self, other: "Timecode") -> bool:
        return self.to_seconds() <= other.to_seconds()

    def __gt__(self, other: "Timecode") -> bool:
        return self.to_seconds() > other.to_seconds()

    def __ge__(self, other: "Timecode") -> bool:
        return self.to_seconds() >= other.to_seconds()

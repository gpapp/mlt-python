"""Clip class for MLT XML library.

Represents a clip entry in a playlist. Clips reference producers with
specific in/out points to define which portion of the media to use.
All time positions are stored as timecode strings (HH:MM:SS:FF).
"""

from typing import TYPE_CHECKING
from .timecode import Timecode
from xml.etree import ElementTree as ET

if TYPE_CHECKING:
    from .filter import Filter


class Clip:
    """Represents a clip entry in an MLT playlist.

    A clip references a producer with specific in/out points to define
    the portion of the media that appears in the timeline.

    Attributes:
        producer_id: ID of the producer this clip references
        in_point: Start timecode (HH:MM:SS:FF) within the producer
        out_point: End timecode (HH:MM:SS:FF) within the producer (inclusive)
        properties: Additional MLT properties for this clip entry
        filters: List of filters attached to this clip
    """

    def __init__(
        self,
        producer_id: str,
        in_point: str | None = None,
        out_point: str | None = None,
        properties: dict[str, str] | None = None,
        filters: list["Filter"] | None = None,
    ) -> None:
        """Initialize a Clip.

        Args:
            producer_id: ID of the producer to reference
            in_point: Start timecode (HH:MM:SS:FF). Defaults to None (start of media).
            out_point: End timecode (HH:MM:SS:FF, inclusive). Defaults to None.
            properties: Additional MLT properties for the entry element
            filters: Optional initial filters
        """
        self.producer_id = producer_id
        self.in_point = in_point
        self.out_point = out_point
        self.properties: dict[str, str] = properties or {}
        self.filters: list["Filter"] = filters or []

    @classmethod
    def from_timecode(
        cls,
        producer_id: str,
        start_time: str,
        end_time: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
        properties: dict[str, str] | None = None,
        filters: list["Filter"] | None = None,
    ) -> "Clip":
        """Create a clip using timecode format (HH:MM:SS:FF).

        Args:
            producer_id: ID of the producer to reference
            start_time: Start timecode (HH:MM:SS:FF)
            end_time: End timecode (HH:MM:SS:FF), exclusive
            duration: Duration timecode (alternative to end)
            fps: Frames per second for timecode conversion
            properties: Additional MLT properties
            filters: Optional initial filters

        Returns:
            Clip object
        """
        if end_time is not None:
            end_tc = Timecode.from_string(end_time, fps)
            end_frames = end_tc.to_frames() - 1  # MLT out is inclusive
            out_point = str(Timecode.from_frames(end_frames, fps))
        elif duration is not None:
            start_tc = Timecode.from_string(start_time, fps)
            dur_tc = Timecode.from_string(duration, fps)
            out_frames = start_tc.to_frames() + dur_tc.to_frames() - 1
            out_point = str(Timecode.from_frames(out_frames, fps))
        else:
            out_point = None

        return cls(
            producer_id=producer_id,
            in_point=start_time,
            out_point=out_point,
            properties=properties,
            filters=filters,
        )

    def get_duration_frames(self, fps: float) -> int | None:
        """Get the clip duration in frames.

        Args:
            fps: Frames per second for timecode conversion

        Returns:
            Duration in frames, or None if out_point not set
        """
        if self.out_point is None or self.in_point is None:
            return None
        in_f = Timecode.from_string(self.in_point, fps).to_frames()
        out_f = Timecode.from_string(self.out_point, fps).to_frames()
        return out_f - in_f + 1

    def get_duration_timecode(self, fps: float) -> str | None:
        """Get the clip duration as a timecode string.

        Args:
            fps: Frames per second

        Returns:
            Duration in HH:MM:SS:FF format, or None
        """
        duration = self.get_duration_frames(fps)
        if duration is None:
            return None
        return str(Timecode.from_frames(duration, fps))

    def to_xml(self, fps: float | None = None) -> ET.Element:
        """Generate XML element for this clip entry.

        Timecode strings are output directly as ``in`` and ``out`` attributes.
        The ``fps`` parameter is accepted for API compatibility but not used,
        since timecodes are already stored as strings.

        Args:
            fps: Ignored (timecodes stored as strings).

        Returns:
            XML Element representing the entry
        """
        attrs: dict[str, str] = {"producer": self.producer_id}
        if self.in_point is not None:
            attrs["in"] = self.in_point
        if self.out_point is not None:
            attrs["out"] = self.out_point

        elem = ET.Element("entry", attrs)

        for name, value in self.properties.items():
            prop = ET.SubElement(elem, "property", {"name": name})
            prop.text = value

        for filter_obj in self.filters:
            elem.append(filter_obj.to_xml())

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> "Clip":
        """Parse a clip from an XML entry element.

        Handles timecode strings (HH:MM:SS:FF), timestamp strings
        (HH:MM:SS.mmm), and raw frame numbers.

        Args:
            elem: XML Element representing an entry

        Returns:
            Clip object
        """
        producer_id = elem.get("producer", "")
        in_str = elem.get("in", "0")
        out_str = elem.get("out")

        in_point = _parse_time_str(in_str)
        out_point = _parse_time_str(out_str) if out_str is not None else None

        properties: dict[str, str] = {}
        for prop in elem.findall("property"):
            name = prop.get("name", "")
            if name:
                properties[name] = prop.text or ""

        return cls(
            producer_id=producer_id,
            in_point=in_point,
            out_point=out_point,
            properties=properties,
        )

    def __repr__(self) -> str:
        return f"Clip(producer='{self.producer_id}', in={self.in_point}, out={self.out_point})"


def _parse_time_str(s: str) -> str:
    """Normalise a time string to HH:MM:SS:FF if possible.

    - If already HH:MM:SS:FF, return as-is.
    - If HH:MM:SS.mmm, convert to HH:MM:SS:FF at 30 fps (fallback).
    - If bare integer, convert to timecode at 30 fps.

    .. note::
        The 30 fps fallback for ambiguous formats is used only during
        XML *loading*; when building projects programmatically all
        timecodes should be passed as HH:MM:SS:FF directly.
    """
    if ":" not in s:
        try:
            return str(Timecode.from_frames(int(s), 30.0))
        except ValueError:
            return s
    parts = s.split(":")
    if len(parts) == 4:
        return s
    if len(parts) == 3 and "." in parts[2]:
        try:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            total_frames = int(round((hours * 3600 + minutes * 60 + seconds) * 30.0))
            return str(Timecode.from_frames(total_frames, 30.0))
        except (ValueError, IndexError):
            pass
    return s


class Blank:
    """Represents a blank space in a playlist.

    Attributes:
        length: Duration as a timecode string (HH:MM:SS:FF)
    """

    def __init__(self, length: str) -> None:
        """Initialize a Blank.

        Args:
            length: Duration as a timecode string (HH:MM:SS:FF)
        """
        self.length = length

    @classmethod
    def from_timecode(cls, timecode: str, fps: float = 30.0) -> "Blank":
        """Create a blank from timecode duration.

        Args:
            timecode: Duration in HH:MM:SS:FF format
            fps: Frames per second (not used for storage, only validation)

        Returns:
            Blank object
        """
        _ = Timecode.from_string(timecode, fps)
        return cls(length=timecode)

    @classmethod
    def from_seconds(cls, seconds: float, fps: float = 30.0) -> "Blank":
        """Create a blank from a duration in seconds.

        Args:
            seconds: Duration in seconds
            fps: Frames per second

        Returns:
            Blank object
        """
        return cls(length=str(Timecode.from_seconds(seconds, fps)))

    def get_duration_frames(self, fps: float) -> int:
        """Get the blank duration in frames.

        Args:
            fps: Frames per second

        Returns:
            Duration in frames
        """
        return Timecode.from_string(self.length, fps).to_frames()

    def to_xml(self, fps: float = 30.0) -> ET.Element:
        """Generate XML element for this blank.

        The MLT XML format requires ``length`` in frames, so the
        stored timecode is converted using the given FPS.

        Args:
            fps: Frames per second for timecode-to-frame conversion

        Returns:
            XML Element representing the blank
        """
        frames = Timecode.from_string(self.length, fps).to_frames()
        return ET.Element("blank", {"length": str(frames)})

    @classmethod
    def from_xml(cls, elem: ET.Element) -> "Blank":
        """Parse a blank from XML element.

        Args:
            elem: XML Element representing a blank

        Returns:
            Blank object
        """
        frame_len = int(elem.get("length", "0"))
        return cls(length=str(Timecode.from_frames(frame_len, 30.0)))

    def __repr__(self) -> str:
        return f"Blank(length={self.length})"

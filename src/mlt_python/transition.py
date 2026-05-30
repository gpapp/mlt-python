"""Transition class for MLT XML library.

Represents MLT transitions between tracks (video wipes, audio mixes, etc.).
Transitions work between two tracks (a_track and b_track) over a time range.
In/out points are stored as float seconds internally.
"""

from typing import Optional
from xml.etree import ElementTree as ET

from .timecode import Timecode


class Transition:
    """Represents an MLT transition between tracks.

    Transitions blend or combine video/audio from two tracks (a_track and b_track)
    over a specified time range. Common transitions include luma (video wipes),
    mix (audio crossfade), and composite.

    Attributes:
        id: Unique identifier for the transition
        mlt_service: MLT transition service (luma, mix, composite, etc.)
        a_track: Source track index (background)
        b_track: Destination track index (foreground)
        in_point: Start time in seconds
        out_point: End time in seconds (inclusive)
        properties: Transition-specific properties
    """

    def __init__(
        self,
        mlt_service: str,
        a_track: int = 0,
        b_track: int = 1,
        id: str | None = None,
        in_point: float | None = None,
        out_point: float | None = None,
        properties: dict[str, str] | None = None,
    ) -> None:
        """Initialize a Transition.

        Args:
            mlt_service: MLT transition service name
            a_track: Source track index (default: 0)
            b_track: Destination track index (default: 1)
            id: Unique identifier (auto-generated if None)
            in_point: Start time in seconds
            out_point: End time in seconds (inclusive)
            properties: Transition-specific properties
        """
        self.id = id
        self.mlt_service = mlt_service
        self.a_track = a_track
        self.b_track = b_track
        self.in_point = in_point
        self.out_point = out_point
        self.properties: dict[str, str] = properties or {}

        if "mlt_service" not in self.properties:
            self.properties["mlt_service"] = mlt_service

    @classmethod
    def from_timecode(
        cls,
        mlt_service: str,
        a_track: int = 0,
        b_track: int = 1,
        start: float | None = None,
        end: float | None = None,
        duration: float | None = None,
        properties: dict[str, str] | None = None,
    ) -> "Transition":
        """Create a transition using float seconds.

        Args:
            mlt_service: MLT transition service name
            a_track: Source track index
            b_track: Destination track index
            start: Start time in seconds
            end: End time in seconds, exclusive
            duration: Duration in seconds (alternative to end)
            properties: Additional properties

        Returns:
            Transition object
        """
        in_point = None
        out_point = None

        if start is not None:
            in_point = start

        if end is not None:
            out_point = end  # end is exclusive, out is inclusive
        elif duration is not None and in_point is not None:
            out_point = in_point + duration

        return cls(
            mlt_service=mlt_service,
            a_track=a_track,
            b_track=b_track,
            in_point=in_point,
            out_point=out_point,
            properties=properties,
        )

    def set_property(self, name: str, value: str) -> None:
        """Set a transition property.

        Args:
            name: Property name
            value: Property value
        """
        self.properties[name] = value

    def get_property(self, name: str, default: str | None = None) -> str | None:
        """Get a transition property value.

        Args:
            name: Property name
            default: Default value if not found

        Returns:
            Property value or default
        """
        return self.properties.get(name, default)

    def to_xml(self, fps: float | None = None) -> ET.Element:
        """Generate XML element for this transition.

        In/out points are serialised as HH:MM:SS.mmm timecode strings.

        Args:
            fps: Ignored (timecodes are FPS-independent).

        Returns:
            XML Element representing the transition
        """
        attrs: dict[str, str] = {
            "a_track": str(self.a_track),
            "b_track": str(self.b_track),
        }

        if self.id:
            attrs["id"] = self.id
        if self.in_point is not None:
            attrs["in"] = str(Timecode.from_seconds(self.in_point))
        if self.out_point is not None:
            attrs["out"] = str(Timecode.from_seconds(self.out_point))

        elem = ET.Element("transition", attrs)

        for name, value in self.properties.items():
            prop = ET.SubElement(elem, "property", {"name": name})
            prop.text = value

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> "Transition":
        """Parse a transition from XML element.

        Args:
            elem: XML Element representing a transition

        Returns:
            Transition object
        """
        id = elem.get("id")
        mlt_service = elem.get("mlt_service", "")
        a_track = int(elem.get("a_track", "0"))
        b_track = int(elem.get("b_track", "1"))
        in_str = elem.get("in")
        out_str = elem.get("out")

        in_point = _parse_time_str(in_str) if in_str else None
        out_point = _parse_time_str(out_str) if out_str else None

        properties: dict[str, str] = {}
        for prop in elem.findall("property"):
            name = prop.get("name", "")
            if name:
                properties[name] = prop.text or ""

        if not mlt_service and "mlt_service" in properties:
            mlt_service = properties["mlt_service"]

        return cls(
            mlt_service=mlt_service,
            a_track=a_track,
            b_track=b_track,
            id=id,
            in_point=in_point,
            out_point=out_point,
            properties=properties,
        )

    def __repr__(self) -> str:
        return f"Transition(service='{self.mlt_service}', a={self.a_track}, b={self.b_track})"


def _parse_time_str(s: str) -> float:
    if ":" not in s:
        try:
            return float(s)
        except ValueError:
            return 0.0
    parts = s.split(":")
    if len(parts) == 4 and "." in parts[3]:
        try:
            hours = int(parts[0])
            minutes = int(parts[1])
            sec_parts = parts[3].split(".")
            seconds = int(sec_parts[0])
            ms = int(sec_parts[1].ljust(3, "0")[:3])
            return hours * 3600 + minutes * 60 + seconds + ms / 1000.0
        except (ValueError, IndexError):
            pass
    if len(parts) == 3 and "." in parts[2]:
        try:
            hours = int(parts[0])
            minutes = int(parts[1])
            sec_parts = parts[2].split(".")
            seconds = int(sec_parts[0])
            ms = int(sec_parts[1].ljust(3, "0")[:3])
            return hours * 3600 + minutes * 60 + seconds + ms / 1000.0
        except (ValueError, IndexError):
            pass
    if len(parts) == 4:
        try:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            pass
    if len(parts) == 3:
        try:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            pass
    return 0.0


class Transitions:
    """Factory class for common MLT transitions."""

    @staticmethod
    def luma(
        a_track: int = 0,
        b_track: int = 1,
        start: float | None = None,
        end: float | None = None,
        duration: float | None = None,
        reverse: bool = False,
    ) -> Transition:
        """Create a luma (video wipe) transition."""
        t = Transition.from_timecode(
            mlt_service="luma",
            a_track=a_track,
            b_track=b_track,
            start=start,
            end=end,
            duration=duration,
        )
        if reverse:
            t.set_property("reverse", "1")
        return t

    @staticmethod
    def mix(
        a_track: int = 0,
        b_track: int = 1,
        start: float | None = None,
        end: float | None = None,
        duration: float | None = None,
        start_level: float = 0.0,
        end_level: float = 1.0,
        kdenlive_audio: bool = False,
    ) -> Transition:
        """Create an audio mix transition."""
        t = Transition.from_timecode(
            mlt_service="mix",
            a_track=a_track,
            b_track=b_track,
            start=start,
            end=end,
            duration=duration,
        )
        t.set_property("start", str(start_level))
        t.set_property("end", str(end_level))
        if kdenlive_audio:
            t.set_property("always_active", "1")
            t.set_property("accepts_blanks", "1")
            t.set_property("sum", "1")
            t.set_property("kdenlive_id", "mix")
        return t

    @staticmethod
    def qtblend(
        a_track: int = 0,
        b_track: int = 1,
        start: float | None = None,
        end: float | None = None,
        duration: float | None = None,
    ) -> Transition:
        """Create a qtblend transition."""
        t = Transition.from_timecode(
            mlt_service="qtblend",
            a_track=a_track,
            b_track=b_track,
            start=start,
            end=end,
            duration=duration,
        )
        t.set_property("compositing", "0")
        t.set_property("distort", "0")
        t.set_property("rotate_center", "0")
        t.set_property("always_active", "1")
        t.set_property("kdenlive_id", "qtblend")
        return t

    @staticmethod
    def composite(
        a_track: int = 0,
        b_track: int = 1,
        start: float | None = None,
        end: float | None = None,
        duration: float | None = None,
        geometry: str = "0%/0%:100%x100%",
    ) -> Transition:
        """Create a composite transition."""
        t = Transition.from_timecode(
            mlt_service="composite",
            a_track=a_track,
            b_track=b_track,
            start=start,
            end=end,
            duration=duration,
        )
        t.set_property("geometry", geometry)
        return t

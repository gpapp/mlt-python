"""Transition class for MLT XML library.

Represents MLT transitions between tracks (video wipes, audio mixes, etc.).
Transitions work between two tracks (a_track and b_track) over a time range.
In/out points are stored as timecode strings (HH:MM:SS:FF).
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
        in_point: Start timecode
        out_point: End timecode (inclusive)
        properties: Transition-specific properties
    """

    def __init__(
        self,
        mlt_service: str,
        a_track: int = 0,
        b_track: int = 1,
        id: str | None = None,
        in_point: str | None = None,
        out_point: str | None = None,
        properties: dict[str, str] | None = None,
    ) -> None:
        """Initialize a Transition.

        Args:
            mlt_service: MLT transition service name
            a_track: Source track index (default: 0)
            b_track: Destination track index (default: 1)
            id: Unique identifier (auto-generated if None)
            in_point: Start timecode (HH:MM:SS:FF)
            out_point: End timecode (HH:MM:SS:FF, inclusive)
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
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
        properties: dict[str, str] | None = None,
    ) -> "Transition":
        """Create a transition using timecode format (HH:MM:SS:FF).

        Args:
            mlt_service: MLT transition service name
            a_track: Source track index
            b_track: Destination track index
            start: Start timecode (HH:MM:SS:FF)
            end: End timecode (HH:MM:SS:FF), exclusive
            duration: Duration timecode (alternative to end)
            fps: Frames per second
            properties: Additional properties

        Returns:
            Transition object
        """
        in_point = None
        out_point = None

        if start is not None:
            in_point = start

        if end is not None:
            end_tc = Timecode.from_string(end, fps)
            end_frames = end_tc.to_frames() - 1  # MLT out is inclusive
            out_point = str(Timecode.from_frames(end_frames, fps))
        elif duration is not None and in_point is not None:
            in_tc = Timecode.from_string(in_point, fps)
            dur_tc = Timecode.from_string(duration, fps)
            out_frames = in_tc.to_frames() + dur_tc.to_frames() - 1
            out_point = str(Timecode.from_frames(out_frames, fps))

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

    def to_xml(self) -> ET.Element:
        """Generate XML element for this transition.

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
            attrs["in"] = self.in_point
        if self.out_point is not None:
            attrs["out"] = self.out_point

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
        in_point = elem.get("in")
        out_point = elem.get("out")

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


class Transitions:
    """Factory class for common MLT transitions."""

    @staticmethod
    def luma(
        a_track: int = 0,
        b_track: int = 1,
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
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
            fps=fps,
        )
        if reverse:
            t.set_property("reverse", "1")
        return t

    @staticmethod
    def mix(
        a_track: int = 0,
        b_track: int = 1,
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
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
            fps=fps,
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
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
    ) -> Transition:
        """Create a qtblend transition."""
        t = Transition.from_timecode(
            mlt_service="qtblend",
            a_track=a_track,
            b_track=b_track,
            start=start,
            end=end,
            duration=duration,
            fps=fps,
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
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
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
            fps=fps,
        )
        t.set_property("geometry", geometry)
        return t

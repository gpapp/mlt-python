"""Filter class for MLT XML library.

Represents MLT filters/effects that can be applied to producers,
playlists, or tracks. Filters modify the audio or video stream.
In/out points are stored as timecode strings (HH:MM:SS:FF).
"""

from typing import Optional
from xml.etree import ElementTree as ET

from .timecode import Timecode


class Filter:
    """Represents an MLT filter (effect).

    Filters are applied to modify audio or video streams. They can be
    applied to specific tracks, producers, or globally.

    Attributes:
        id: Unique identifier for the filter
        mlt_service: MLT filter service name (e.g., "greyscale", "volume")
        track: Track index this filter applies to (None = all tracks)
        in_point: Start timecode for filter application
        out_point: End timecode for filter application (inclusive)
        properties: Filter-specific properties
    """

    def __init__(
        self,
        mlt_service: str,
        id: str | None = None,
        track: int | None = None,
        in_point: str | None = None,
        out_point: str | None = None,
        properties: dict[str, str] | None = None,
    ) -> None:
        """Initialize a Filter.

        Args:
            mlt_service: MLT filter service name
            id: Unique identifier (auto-generated if None)
            track: Track index (0-based, None = all)
            in_point: Start timecode (HH:MM:SS:FF)
            out_point: End timecode (HH:MM:SS:FF, inclusive)
            properties: Filter-specific properties
        """
        self.id = id
        self.mlt_service = mlt_service
        self.track = track
        self.in_point = in_point
        self.out_point = out_point
        self.properties: dict[str, str] = properties or {}

        if "mlt_service" not in self.properties:
            self.properties["mlt_service"] = mlt_service

    @classmethod
    def from_timecode(
        cls,
        mlt_service: str,
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
        track: int | None = None,
        properties: dict[str, str] | None = None,
    ) -> "Filter":
        """Create a filter using timecode format (HH:MM:SS:FF).

        Args:
            mlt_service: MLT filter service name
            start: Start timecode (HH:MM:SS:FF)
            end: End timecode (HH:MM:SS:FF), exclusive
            duration: Duration timecode (alternative to end)
            fps: Frames per second
            track: Track index
            properties: Additional properties

        Returns:
            Filter object
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
            track=track,
            in_point=in_point,
            out_point=out_point,
            properties=properties,
        )

    def set_property(self, name: str, value: str) -> None:
        """Set a filter property.

        Args:
            name: Property name
            value: Property value
        """
        self.properties[name] = value

    def get_property(self, name: str, default: str | None = None) -> str | None:
        """Get a filter property value.

        Args:
            name: Property name
            default: Default value if not found

        Returns:
            Property value or default
        """
        return self.properties.get(name, default)

    def to_xml(self) -> ET.Element:
        """Generate XML element for this filter.

        In/out points are serialised as frame numbers (MLT XML convention
        for filters).

        Returns:
            XML Element representing the filter
        """
        attrs: dict[str, str] = {}

        if self.id:
            attrs["id"] = self.id
        if self.track is not None:
            attrs["track"] = str(self.track)
        if self.in_point is not None:
            attrs["in"] = self.in_point
        if self.out_point is not None:
            attrs["out"] = self.out_point

        elem = ET.Element("filter", attrs)

        for name, value in self.properties.items():
            prop = ET.SubElement(elem, "property", {"name": name})
            prop.text = value

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> "Filter":
        """Parse a filter from XML element.

        Args:
            elem: XML Element representing a filter

        Returns:
            Filter object
        """
        id = elem.get("id")
        mlt_service = elem.get("mlt_service", "")
        track = int(elem.get("track", "0")) if elem.get("track") else None
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
            id=id,
            track=track,
            in_point=in_point,
            out_point=out_point,
            properties=properties,
        )

    def __repr__(self) -> str:
        return f"Filter(service='{self.mlt_service}', track={self.track})"


class Filters:
    """Factory class for common MLT filters."""

    @staticmethod
    def greyscale(
        track: int | None = None,
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
    ) -> Filter:
        """Create a greyscale filter."""
        return Filter.from_timecode(
            mlt_service="greyscale",
            start=start,
            end=end,
            duration=duration,
            fps=fps,
            track=track,
        )

    @staticmethod
    def volume(
        level: float = 1.0,
        track: int | None = None,
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
    ) -> Filter:
        """Create a volume filter."""
        f = Filter.from_timecode(
            mlt_service="volume",
            start=start,
            end=end,
            duration=duration,
            fps=fps,
            track=track,
        )
        f.set_property("level", str(level))
        return f

    @staticmethod
    def watermark(
        resource: str,
        track: int | None = None,
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
    ) -> Filter:
        """Create a watermark filter."""
        f = Filter.from_timecode(
            mlt_service="watermark",
            start=start,
            end=end,
            duration=duration,
            fps=fps,
            track=track,
        )
        f.set_property("resource", resource)
        return f

    @staticmethod
    def subtitle(
        resource: str,
        track: int | None = None,
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
        geometry: str = "20%/80%:60%x20%:100",
        font_family: str = "Sans",
        font_size: str = "48",
        font_colour: str = "0xffffffff",
    ) -> Filter:
        """Create a subtitle filter."""
        f = Filter.from_timecode(
            mlt_service="subtitle",
            start=start,
            end=end,
            duration=duration,
            fps=fps,
            track=track,
        )
        f.set_property("resource", resource)
        f.set_property("geometry", geometry)
        f.set_property("family", font_family)
        f.set_property("size", font_size)
        f.set_property("fgcolour", font_colour)
        return f

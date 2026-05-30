"""Clip class for MLT XML library.

Represents a clip entry in a playlist. Clips reference producers with
specific in/out points to define which portion of the media to use.
"""

from typing import TYPE_CHECKING
from .timecode import Timecode
from xml.etree import ElementTree as ET

from .timecode import Timecode

if TYPE_CHECKING:
    from .filter import Filter


class Clip:
    """Represents a clip entry in an MLT playlist.

    A clip references a producer with specific in/out points to define
    the portion of the media that appears in the timeline.

    Attributes:
        producer_id: ID of the producer this clip references
        in_point: Start frame within the producer
        out_point: End frame within the producer (inclusive)
        properties: Additional MLT properties for this clip entry
        filters: List of filters attached to this clip
    """

    def __init__(
        self,
        producer_id: str,
        in_point: int = 0,
        out_point: int | None = None,
        length: int | None = None,
        properties: dict[str, str] | None = None,
        filters: list["Filter"] | None = None,
    ) -> None:
        """Initialize a Clip.

        Args:
            producer_id: ID of the producer to reference
            in_point: Start frame (default: 0)
            out_point: End frame (inclusive). If None and length not provided,
                       use producer's full length
            length: Length in frames (alternative to out_point)
            properties: Additional MLT properties for the entry element
            filters: Optional initial filters
        """
        self.producer_id = producer_id
        self.in_point = in_point
        self.properties: dict[str, str] = properties or {}
        self.filters: list["Filter"] = filters or []

        if out_point is not None:
            self.out_point = out_point
        elif length is not None:
            self.out_point = in_point + length - 1
        else:
            self.out_point = None

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
        start_tc = Timecode.from_string(start_time, fps)
        in_point = start_tc.to_frames()

        if end_time is not None:
            end_tc = Timecode.from_string(end_time, fps)
            out_point = end_tc.to_frames() - 1  # MLT out is inclusive
        elif duration is not None:
            dur_tc = Timecode.from_string(duration, fps)
            out_point = in_point + dur_tc.to_frames() - 1
        else:
            out_point = None

        return cls(
            producer_id=producer_id,
            in_point=in_point,
            out_point=out_point,
            properties=properties,
            filters=filters,
        )

    def get_duration_frames(self) -> int | None:
        """Get the clip duration in frames.

        Returns:
            Duration in frames, or None if out_point not set
        """
        if self.out_point is None:
            return None
        return self.out_point - self.in_point + 1

    def get_duration_timecode(self, fps: float) -> str | None:
        """Get the clip duration as a timecode string.

        Args:
            fps: Frames per second

        Returns:
            Duration in HH:MM:SS:FF format, or None
        """
        duration = self.get_duration_frames()
        if duration is None:
            return None
        return str(Timecode.from_frames(duration, fps))

    def to_xml(self, fps: float | None = None) -> ET.Element:
        """Generate XML element for this clip entry.

        Args:
            fps: Optional frames per second for timecode conversion.
                 If provided, 'in' and 'out' will be timecodes.

        Returns:
            XML Element representing the entry
        """
        attrs: dict[str, str] = {"producer": self.producer_id}
        if self.in_point is not None:
            if fps:
                attrs["in"] = Timecode.from_frames(self.in_point, fps).to_string()
            else:
                attrs["in"] = str(self.in_point)
        if self.out_point is not None:
            if fps:
                attrs["out"] = Timecode.from_frames(self.out_point, fps).to_string()
            else:
                attrs["out"] = str(self.out_point)

        elem = ET.Element("entry", attrs)

        # Add properties
        for name, value in self.properties.items():
            prop = ET.SubElement(elem, "property", {"name": name})
            prop.text = value

        # Add filters
        for filter_obj in self.filters:
            elem.append(filter_obj.to_xml())

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> "Clip":
        """Parse a clip from an XML entry element.

        Args:
            elem: XML Element representing an entry

        Returns:
            Clip object
        """
        producer_id = elem.get("producer", "")
        
        # Handle both timecode strings (HH:MM:SS:FF) and raw frame numbers
        # Also handle timestamp format (HH:MM:SS.mmm)
        in_str = elem.get("in", "0")
        in_point = None
        if ":" in in_str:
            parts = in_str.split(":")
            if len(parts) == 4:
                # HH:MM:SS:FF format
                in_point = Timecode.from_string(in_str, 30.0).to_frames()
            elif len(parts) == 3 and "." in parts[2]:
                # HH:MM:SS.mmm format (timestamp)
                try:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = float(parts[2])
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                    in_point = int(total_seconds * 30.0)  # Assume 30 fps
                except (ValueError, IndexError):
                    in_point = 0
        else:
            try:
                in_point = int(in_str)
            except ValueError:
                in_point = 0
            
        out_str = elem.get("out")
        out_point = None
        if out_str:
            if ":" in out_str:
                parts = out_str.split(":")
                if len(parts) == 4:
                    out_point = Timecode.from_string(out_str, 30.0).to_frames()
                elif len(parts) == 3 and "." in parts[2]:
                    try:
                        hours = int(parts[0])
                        minutes = int(parts[1])
                        seconds = float(parts[2])
                        total_seconds = hours * 3600 + minutes * 60 + seconds
                        out_point = int(total_seconds * 30.0)
                    except (ValueError, IndexError):
                        out_point = None
            else:
                try:
                    out_point = int(out_str)
                except ValueError:
                    out_point = None

        # Parse properties
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


class Blank:
    """Represents a blank space in a playlist.

    Attributes:
        length: Length of the blank in frames
    """

    def __init__(self, length: int) -> None:
        """Initialize a Blank.

        Args:
            length: Length in frames
        """
        self.length = length

    @classmethod
    def from_timecode(cls, timecode: str, fps: float = 30.0) -> "Blank":
        """Create a blank from timecode duration.

        Args:
            timecode: Duration in HH:MM:SS:FF format
            fps: Frames per second

        Returns:
            Blank object
        """
        tc = Timecode.from_string(timecode, fps)
        return cls(length=tc.to_frames())

    def to_xml(self) -> ET.Element:
        """Generate XML element for this blank.

        Returns:
            XML Element representing the blank
        """
        return ET.Element("blank", {"length": str(self.length)})

    @classmethod
    def from_xml(cls, elem: ET.Element) -> "Blank":
        """Parse a blank from XML element.

        Args:
            elem: XML Element representing a blank

        Returns:
            Blank object
        """
        length = int(elem.get("length", "0"))
        return cls(length=length)

    def __repr__(self) -> str:
        return f"Blank(length={self.length})"

"""Playlist/Track class for MLT XML library.

Represents a playlist in MLT, which acts as a track in the timeline.
A playlist contains clips (entries) and blanks in a specific order.
All time positions are stored as float seconds internally.
"""

from typing import Optional
from xml.etree import ElementTree as ET

from .clip import Clip, Blank, _parse_time_str
from .timecode import Timecode


class Playlist:
    """Represents an MLT playlist (track) in the timeline.

    A playlist is a sequence of clips and blanks. In the context of a
    multitrack/tractor setup, each playlist corresponds to one track
    (video track, audio track, etc.).

    Attributes:
        id: Unique identifier for the playlist
        clips: List of Clip and Blank objects in order
        properties: Additional MLT properties for the playlist
    """

    def __init__(
        self,
        id: str,
        clips: list[Clip | Blank] | None = None,
        properties: dict[str, str] | None = None,
        filters: list["Filter"] | None = None,
    ) -> None:
        """Initialize a Playlist.

        Args:
            id: Unique identifier (e.g., "playlist0", "video_track")
            clips: Initial list of clips and blanks
            properties: Additional MLT properties
            filters: Initial list of filters
        """
        self.id = id
        self.clips: list[Clip | Blank] = clips or []
        self.properties: dict[str, str] = properties or {}
        self.filters: list["Filter"] = filters or []

    def add_clip(
        self,
        producer_id: str,
        in_point: float | None = None,
        out_point: float | None = None,
        end: float | None = None,
        duration: float | None = None,
        position: int | None = None,
        fps: float = 25.0,
    ) -> Clip:
        """Add a clip to the playlist using float seconds.

        Exactly one of ``out_point``, ``end``, or ``duration`` must be
        provided (or ``out_point`` alone for an open-ended clip).

        Args:
            producer_id: ID of the producer to reference
            in_point: Start time in seconds. Defaults to 0.0.
            out_point: End time in seconds, **inclusive**.
            end: End time in seconds, **exclusive**.
            duration: Duration in seconds.
            position: Insert position (default: append to end).
            fps: Video frame rate for inclusive-out conversion (default 25.0).

        Returns:
            The created Clip object
        """
        if in_point is None:
            in_point = 0.0

        if out_point is None:
            if end is not None:
                out_point = max(0.0, end - 1.0 / fps)
            elif duration is not None:
                out_point = in_point + duration - 1.0 / fps

        clip = Clip(producer_id, in_point=in_point, out_point=out_point)

        if position is None:
            self.clips.append(clip)
        else:
            self.clips.insert(position, clip)

        return clip

    def add_blank(
        self,
        duration: float,
        position: int | None = None,
    ) -> Blank:
        """Add a blank space to the playlist.

        Args:
            duration: Duration in seconds
            position: Insert position (default: append)

        Returns:
            The created Blank object
        """
        blank = Blank(duration)
        if position is None:
            self.clips.append(blank)
        else:
            self.clips.insert(position, blank)
        return blank

    def remove_clip(self, position: int) -> Clip | Blank | None:
        """Remove a clip/blank at the specified position.

        Args:
            position: Index of the clip/blank to remove

        Returns:
            The removed Clip/Blank, or None if invalid position
        """
        if 0 <= position < len(self.clips):
            return self.clips.pop(position)
        return None

    def clear(self) -> None:
        """Remove all clips from the playlist."""
        self.clips.clear()

    def get_duration(self) -> float:
        """Get the total duration of the playlist in seconds.

        Returns:
            Total duration in seconds
        """
        duration = 0.0
        for item in self.clips:
            if isinstance(item, Clip):
                d = item.get_duration()
                if d is not None:
                    duration += d
            elif isinstance(item, Blank):
                duration += item.length
        return duration

    def get_property(self, name: str, default: str | None = None) -> str | None:
        """Get an MLT property value.

        Args:
            name: Property name
            default: Default value if property doesn't exist

        Returns:
            Property value or default
        """
        return self.properties.get(name, default)

    def set_property(self, name: str, value: str) -> None:
        """Set an MLT property on the playlist.

        Args:
            name: Property name
            value: Property value
        """
        self.properties[name] = value

    def add_filter(self, filter_obj: "Filter") -> None:
        """Add a filter to the playlist.

        Args:
            filter_obj: Filter object to add
        """
        self.filters.append(filter_obj)

    def to_xml(self, producer_to_chain: dict[str, str] | None = None, fps: float | None = None) -> ET.Element:
        """Generate XML element for this playlist.

        Args:
            producer_to_chain: Optional mapping from producer ID to chain ID.
                              If provided, clip references will use chain IDs.
            fps: Frames per second (passed to ``Blank.to_xml`` for blank
                 length conversion).

        Returns:
            XML Element representing the playlist
        """
        elem = ET.Element("playlist", {"id": self.id})

        for name, value in self.properties.items():
            prop = ET.SubElement(elem, "property", {"name": name})
            prop.text = value

        for item in self.clips:
            if isinstance(item, Clip):
                xml_elem = item.to_xml()
                if producer_to_chain and item.producer_id in producer_to_chain:
                    xml_elem.set("producer", producer_to_chain[item.producer_id])
            else:
                xml_elem = item.to_xml(fps=fps or 30.0)
            elem.append(xml_elem)

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, fps: float = 30.0) -> "Playlist":
        """Parse a playlist from XML element.

        Args:
            elem: XML Element representing a playlist
            fps: Frames per second for blank length frame-to-seconds conversion

        Returns:
            Playlist object
        """
        id = elem.get("id", "")
        properties: dict[str, str] = {}
        clips: list[Clip | Blank] = []

        for child in elem:
            if child.tag == "property":
                name = child.get("name", "")
                if name:
                    properties[name] = child.text or ""
            elif child.tag == "entry":
                clips.append(Clip.from_xml(child))
            elif child.tag == "blank":
                clips.append(Blank.from_xml(child, fps=fps))

        return cls(id=id, clips=clips, properties=properties)

    def __repr__(self) -> str:
        return f"Playlist(id='{self.id}', clips={len(self.clips)})"

"""Playlist/Track class for MLT XML library.

Represents a playlist in MLT, which acts as a track in the timeline.
A playlist contains clips (entries) and blanks in a specific order.
All time positions are stored as timecode strings (HH:MM:SS:FF).
"""

from typing import Optional
from xml.etree import ElementTree as ET

from .clip import Clip, Blank
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
        in_point: str | None = None,
        out_point: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        position: int | None = None,
        fps: float = 30.0,
    ) -> Clip:
        """Add a clip to the playlist using timecodes.

        Exactly one of ``out_point``, ``end``, or ``duration`` must be
        provided (or ``out_point`` alone for an open-ended clip).

        Args:
            producer_id: ID of the producer to reference
            in_point: Start timecode (HH:MM:SS:FF). Defaults to ``00:00:00:00``.
            out_point: End timecode (HH:MM:SS:FF), **inclusive**.
            end: End timecode (HH:MM:SS:FF), **exclusive** (1 frame beyond last).
            duration: Duration timecode (HH:MM:SS:FF).
            position: Insert position (default: append to end).
            fps: Frames per second (required when ``end`` or ``duration`` is used).

        Returns:
            The created Clip object
        """
        if in_point is None:
            in_point = "00:00:00:00"

        if out_point is None:
            if end is not None:
                end_f = Timecode.from_string(end, fps).to_frames()
                out_f = max(0, end_f - 1)
                out_point = str(Timecode.from_frames(out_f, fps))
            elif duration is not None:
                in_f = Timecode.from_string(in_point, fps).to_frames()
                dur_f = Timecode.from_string(duration, fps).to_frames()
                out_f = in_f + dur_f - 1
                out_point = str(Timecode.from_frames(out_f, fps))

        clip = Clip(producer_id, in_point=in_point, out_point=out_point)

        if position is None:
            self.clips.append(clip)
        else:
            self.clips.insert(position, clip)

        return clip

    def add_blank(
        self,
        timecode: str,
        position: int | None = None,
        fps: float = 30.0,
    ) -> Blank:
        """Add a blank space to the playlist using a timecode duration.

        Args:
            timecode: Duration in HH:MM:SS:FF format
            position: Insert position (default: append)
            fps: Frames per second (for validation only)

        Returns:
            The created Blank object
        """
        _ = Timecode.from_string(timecode, fps)  # validate
        blank = Blank(timecode)
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

    def get_duration_frames(self, fps: float = 30.0) -> int:
        """Get the total duration of the playlist in frames.

        Args:
            fps: Frames per second for timecode conversion

        Returns:
            Total duration in frames
        """
        duration = 0
        for item in self.clips:
            if isinstance(item, Clip):
                if item.in_point is not None and item.out_point is not None:
                    in_f = Timecode.from_string(item.in_point, fps).to_frames()
                    out_f = Timecode.from_string(item.out_point, fps).to_frames()
                    duration += out_f - in_f + 1
            elif isinstance(item, Blank):
                duration += Timecode.from_string(item.length, fps).to_frames()
        return duration

    def get_duration_timecode(self, fps: float) -> str:
        """Get the total duration as a timecode string.

        Args:
            fps: Frames per second

        Returns:
            Duration in HH:MM:SS:FF format
        """
        return str(Timecode.from_frames(self.get_duration_frames(fps), fps))

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
    def from_xml(cls, elem: ET.Element) -> "Playlist":
        """Parse a playlist from XML element.

        Args:
            elem: XML Element representing a playlist

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
                clips.append(Blank.from_xml(child))

        return cls(id=id, clips=clips, properties=properties)

    def __repr__(self) -> str:
        return f"Playlist(id='{self.id}', clips={len(self.clips)})"

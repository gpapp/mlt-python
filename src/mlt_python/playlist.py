"""Playlist/Track class for MLT XML library.

Represents a playlist in MLT, which acts as a track in the timeline.
A playlist contains clips (entries) and blanks in a specific order.
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
    ) -> None:
        """Initialize a Playlist.

        Args:
            id: Unique identifier (e.g., "playlist0", "video_track")
            clips: Initial list of clips and blanks
            properties: Additional MLT properties
        """
        self.id = id
        self.clips: list[Clip | Blank] = clips or []
        self.properties: dict[str, str] = properties or {}

    def add_clip(
        self,
        producer_id: str,
        in_point: int = 0,
        out_point: int | None = None,
        length: int | None = None,
        position: int | None = None,
    ) -> Clip:
        """Add a clip to the playlist.

        Args:
            producer_id: ID of the producer to reference
            in_point: Start frame within the producer
            out_point: End frame (inclusive). If None and length not provided,
                       uses producer's full length
            length: Length in frames (alternative to out_point)
            position: Insert position (default: append to end)

        Returns:
            The created Clip object
        """
        if out_point is not None:
            clip = Clip(producer_id, in_point, out_point)
        elif length is not None:
            clip = Clip(producer_id, in_point, in_point + length - 1)
        else:
            clip = Clip(producer_id, in_point)

        if position is None:
            self.clips.append(clip)
        else:
            self.clips.insert(position, clip)

        return clip

    def add_clip_timecode(
        self,
        producer_id: str,
        start: str,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
        position: int | None = None,
    ) -> Clip:
        """Add a clip using timecode format (HH:MM:SS:FF).

        Args:
            producer_id: ID of the producer to reference
            start: Start timecode (HH:MM:SS:FF)
            end: End timecode (HH:MM:SS:FF), exclusive
            duration: Duration timecode (alternative to end)
            fps: Frames per second for conversion
            position: Insert position (default: append)

        Returns:
            The created Clip object
        """
        clip = Clip.from_timecode(
            producer_id=producer_id,
            start_time=start,
            end_time=end,
            duration=duration,
            fps=fps,
        )

        if position is None:
            self.clips.append(clip)
        else:
            self.clips.insert(position, clip)

        return clip

    def add_blank(self, length: int, position: int | None = None) -> Blank:
        """Add a blank space to the playlist.

        Args:
            length: Length in frames
            position: Insert position (default: append)

        Returns:
            The created Blank object
        """
        blank = Blank(length)
        if position is None:
            self.clips.append(blank)
        else:
            self.clips.insert(position, blank)
        return blank

    def add_blank_timecode(
        self,
        timecode: str,
        fps: float = 30.0,
        position: int | None = None,
    ) -> Blank:
        """Add a blank using timecode duration.

        Args:
            timecode: Duration in HH:MM:SS:FF format
            fps: Frames per second
            position: Insert position (default: append)

        Returns:
            The created Blank object
        """
        blank = Blank.from_timecode(timecode, fps)
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

    def get_duration_frames(self) -> int:
        """Get the total duration of the playlist in frames.

        Returns:
            Total duration in frames
        """
        duration = 0
        for item in self.clips:
            if isinstance(item, Clip):
                if item.out_point is not None:
                    duration += item.out_point - item.in_point + 1
                else:
                    # If no out_point, assume 0 length for now
                    pass
            elif isinstance(item, Blank):
                duration += item.length
        return duration

    def get_duration_timecode(self, fps: float) -> str:
        """Get the total duration as a timecode string.

        Args:
            fps: Frames per second

        Returns:
            Duration in HH:MM:SS:FF format
        """
        return str(Timecode.from_frames(self.get_duration_frames(), fps))

    def set_property(self, name: str, value: str) -> None:
        """Set an MLT property on the playlist.

        Args:
            name: Property name
            value: Property value
        """
        self.properties[name] = value

    def to_xml(self, producer_to_chain: dict[str, str] | None = None, fps: float | None = None) -> ET.Element:
        """Generate XML element for this playlist.

        Args:
            producer_to_chain: Optional mapping from producer ID to chain ID.
                             If provided, clip references will use chain IDs.
            fps: Optional frames per second for timecode conversion.

        Returns:
            XML Element representing the playlist
        """
        elem = ET.Element("playlist", {"id": self.id})

        # Add properties
        for name, value in self.properties.items():
            prop = ET.SubElement(elem, "property", {"name": name})
            prop.text = value

        # Add clips and blanks
        for item in self.clips:
            if isinstance(item, Clip):
                xml_elem = item.to_xml(fps=fps)
                if producer_to_chain and item.producer_id in producer_to_chain:
                    xml_elem.set("producer", producer_to_chain[item.producer_id])
            else:
                xml_elem = item.to_xml()
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

        # Parse properties and entries
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

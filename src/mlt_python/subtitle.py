"""Subtitle support for MLT XML library.

Handles external SRT subtitle files and their integration into MLT XML
via the subtitle filter (filter_subtitle).
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from xml.etree import ElementTree as ET

from .timecode import Timecode
from .clip import _parse_time_str


@dataclass
class SubtitleItem:
    """Represents a single subtitle entry."""

    start_time: str  # HH:MM:SS,mmm format from SRT
    end_time: str  # HH:MM:SS,mmm format from SRT
    text: str
    index: int = 0

    def to_srt_string(self) -> str:
        """Convert to SRT format string.

        Returns:
            SRT-formatted string for this subtitle
        """
        return f"{self.index}\n{self.start_time} --> {self.end_time}\n{self.text}\n"

    @property
    def start_seconds(self) -> float:
        """Get start time in seconds.

        Returns:
            Start time in seconds
        """
        return self._timecode_to_seconds(self.start_time)

    @property
    def end_seconds(self) -> float:
        """Get end time in seconds.

        Returns:
            End time in seconds
        """
        return self._timecode_to_seconds(self.end_time)

    @staticmethod
    def _timecode_to_seconds(timecode: str) -> float:
        """Convert HH:MM:SS,mmm to seconds.

        Args:
            timecode: Time in HH:MM:SS,mmm format

        Returns:
            Time in seconds
        """
        parts = timecode.replace(",", ":").split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        milliseconds = int(parts[3])
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0


class SubtitleTrack:
    """Represents a subtitle track using an external SRT file.

    This creates a filter that references an external SRT file,
    which MLT's subtitle filter will load and display.

    Attributes:
        resource: Path to the SRT file
        track: Track index this subtitle applies to
        start_time: Start time in seconds for subtitle display
        end_time: End time in seconds for subtitle display (optional)
        properties: Additional filter properties (geometry, font, etc.)
    """

    def __init__(
        self,
        resource: str,
        track: int = 0,
        start_time: float | None = None,
        end_time: float | None = None,
        properties: dict[str, str] | None = None,
    ) -> None:
        """Initialize a SubtitleTrack.

        Args:
            resource: Path to SRT file
            track: Track index
            start_time: Start time in seconds (optional)
            end_time: End time in seconds (optional)
            properties: Additional filter properties
        """
        self.resource = resource
        self.track = track
        self.start_time = start_time
        self.end_time = end_time
        self.properties: dict[str, str] = properties or {}

        # Set defaults for subtitle filter
        if "mlt_service" not in self.properties:
            self.properties["mlt_service"] = "subtitle"
        if "resource" not in self.properties:
            self.properties["resource"] = resource
        if "geometry" not in self.properties:
            self.properties["geometry"] = "20%/80%:60%x20%:100"
        if "family" not in self.properties:
            self.properties["family"] = "Sans"
        if "size" not in self.properties:
            self.properties["size"] = "48"
        if "fgcolour" not in self.properties:
            self.properties["fgcolour"] = "0xffffffff"

    @classmethod
    def from_timecode(
        cls,
        srt_file: str,
        track: int = 0,
        start: float | None = None,
        end: float | None = None,
        duration: float | None = None,
        font_family: str = "Sans",
        font_size: str = "48",
        font_colour: str = "0xffffffff",
    ) -> "SubtitleTrack":
        """Create a subtitle track using float seconds.

        Args:
            srt_file: Path to SRT file
            track: Track index
            start: Start time in seconds
            end: End time in seconds, exclusive
            duration: Duration in seconds (alternative to end)
            font_family: Font family
            font_size: Font size
            font_colour: Font colour (hex with alpha)

        Returns:
            SubtitleTrack object
        """
        start_time = start
        end_time = None

        if end is not None:
            end_time = end
        elif duration is not None and start_time is not None:
            end_time = start_time + duration

        properties = {
            "family": font_family,
            "size": font_size,
            "fgcolour": font_colour,
        }

        return cls(
            resource=srt_file,
            track=track,
            start_time=start_time,
            end_time=end_time,
            properties=properties,
        )

    def to_filter_xml(self) -> ET.Element:
        """Generate XML element for the subtitle filter.

        Returns:
            XML Element representing the subtitle filter
        """
        attrs: dict[str, str] = {"mlt_service": "subtitle"}
        if self.track is not None:
            attrs["track"] = str(self.track)
        if self.start_time is not None:
            attrs["in"] = str(Timecode.from_seconds(self.start_time))
        if self.end_time is not None:
            attrs["out"] = str(Timecode.from_seconds(self.end_time))

        elem = ET.Element("filter", attrs)

        # Add all properties
        for name, value in self.properties.items():
            prop = ET.SubElement(elem, "property", {"name": name})
            prop.text = value

        return elem


class SRTFile:
    """Utility class for reading and writing SRT subtitle files."""

    @staticmethod
    def parse(srt_path: str) -> list[SubtitleItem]:
        """Parse an SRT file.

        Args:
            srt_path: Path to SRT file

        Returns:
            List of SubtitleItem objects

        Raises:
            FileNotFoundError: If SRT file doesn't exist
            ValueError: If SRT format is invalid
        """
        if not os.path.exists(srt_path):
            raise FileNotFoundError(f"SRT file not found: {srt_path}")

        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        return SRTFile._parse_content(content)

    @staticmethod
    def _parse_content(content: str) -> list[SubtitleItem]:
        """Parse SRT content string.

        Args:
            content: SRT file content

        Returns:
            List of SubtitleItem objects
        """
        items: list[SubtitleItem] = []
        blocks = content.strip().split("\n\n")

        for block in blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            if len(lines) < 3:
                continue

            try:
                index = int(lines[0])
                time_line = lines[1]
                text_lines = lines[2:]

                # Parse time line: 00:00:10,500 --> 00:00:13,250
                if "-->" not in time_line:
                    continue

                times = time_line.split(" --> ")
                if len(times) != 2:
                    continue

                start_time = times[0].strip()
                end_time = times[1].strip()
                text = "\n".join(text_lines)

                items.append(
                    SubtitleItem(
                        start_time=start_time,
                        end_time=end_time,
                        text=text,
                        index=index,
                    )
                )
            except (ValueError, IndexError):
                continue

        return items

    @staticmethod
    def write(srt_path: str, items: list[SubtitleItem]) -> None:
        """Write subtitles to an SRT file.

        Args:
            srt_path: Path to output SRT file
            items: List of SubtitleItem objects
        """
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, item in enumerate(items, 1):
                item.index = i
                f.write(item.to_srt_string())
                if i < len(items):
                    f.write("\n")

    @staticmethod
    def create_from_dict(
        subtitles: list[dict[str, str | int]],
        srt_path: str,
    ) -> list[SubtitleItem]:
        """Create an SRT file from a list of dictionaries.

        Args:
            subtitles: List of dicts with 'start', 'end', 'text' keys
                       Time format: HH:MM:SS,mmm
            srt_path: Path to output SRT file

        Returns:
            List of SubtitleItem objects
        """
        items: list[SubtitleItem] = []
        for i, sub in enumerate(subtitles, 1):
            item = SubtitleItem(
                start_time=str(sub.get("start", "00:00:00,000")),
                end_time=str(sub.get("end", "00:00:00,000")),
                text=str(sub.get("text", "")),
                index=i,
            )
            items.append(item)

        SRTFile.write(srt_path, items)
        return items

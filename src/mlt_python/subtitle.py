"""Subtitle support for MLT XML library.

Handles external SRT subtitle files and their integration into MLT XML
via the subtitle filter (filter_subtitle).
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from xml.etree import ElementTree as ET

from .timecode import Timecode


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
    def start_ms(self) -> int:
        """Get start time in milliseconds.

        Returns:
            Start time in ms
        """
        return self._timecode_to_ms(self.start_time)

    @property
    def end_ms(self) -> int:
        """Get end time in milliseconds.

        Returns:
            End time in ms
        """
        return self._timecode_to_ms(self.end_time)

    @staticmethod
    def _timecode_to_ms(timecode: str) -> int:
        """Convert HH:MM:SS,mmm to milliseconds.

        Args:
            timecode: Time in HH:MM:SS,mmm format

        Returns:
            Time in milliseconds
        """
        parts = timecode.replace(",", ":").split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        milliseconds = int(parts[3])
        return ((hours * 3600 + minutes * 60 + seconds) * 1000) + milliseconds


class SubtitleTrack:
    """Represents a subtitle track using an external SRT file.

    This creates a filter that references an external SRT file,
    which MLT's subtitle filter will load and display.

    Attributes:
        resource: Path to the SRT file
        track: Track index this subtitle applies to
        start_frame: Start frame for subtitle display
        end_frame: End frame for subtitle display (optional)
        properties: Additional filter properties (geometry, font, etc.)
    """

    def __init__(
        self,
        resource: str,
        track: int = 0,
        start_frame: int | None = None,
        end_frame: int | None = None,
        properties: dict[str, str] | None = None,
    ) -> None:
        """Initialize a SubtitleTrack.

        Args:
            resource: Path to SRT file
            track: Track index
            start_frame: Start frame (optional)
            end_frame: End frame (optional)
            properties: Additional filter properties
        """
        self.resource = resource
        self.track = track
        self.start_frame = start_frame
        self.end_frame = end_frame
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
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        fps: float = 30.0,
        font_family: str = "Sans",
        font_size: str = "48",
        font_colour: str = "0xffffffff",
    ) -> "SubtitleTrack":
        """Create a subtitle track using timecode format.

        Args:
            srt_file: Path to SRT file
            track: Track index
            start: Start timecode (HH:MM:SS:FF)
            end: End timecode (HH:MM:SS:FF)
            duration: Duration timecode (alternative to end)
            fps: Frames per second
            font_family: Font family
            font_size: Font size
            font_colour: Font colour (hex with alpha)

        Returns:
            SubtitleTrack object
        """
        start_frame = None
        end_frame = None

        if start is not None:
            start_tc = Timecode.from_string(start, fps)
            start_frame = start_tc.to_frames()

        if end is not None:
            end_tc = Timecode.from_string(end, fps)
            end_frame = end_tc.to_frames() - 1  # MLT out is inclusive
        elif duration is not None and start_frame is not None:
            dur_tc = Timecode.from_string(duration, fps)
            end_frame = start_frame + dur_tc.to_frames() - 1

        properties = {
            "family": font_family,
            "size": font_size,
            "fgcolour": font_colour,
        }

        return cls(
            resource=srt_file,
            track=track,
            start_frame=start_frame,
            end_frame=end_frame,
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
        if self.start_frame is not None:
            attrs["in"] = str(self.start_frame)
        if self.end_frame is not None:
            attrs["out"] = str(self.end_frame)

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

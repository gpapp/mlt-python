"""Marker support for MLT XML / Kdenlive.

Kdenlive stores markers in two places:
- ``kdenlive:markers`` property on a chain/producer – clip markers visible in
  the clip monitor.
- ``kdenlive:sequenceproperties.guides`` property on the main sequence tractor –
  timeline guides visible on the timeline ruler.

Both use the same JSON array format::

    [
        {"comment": "Label", "duration": <frames>, "pos": <frames>, "type": <0-8>}
    ]

``pos`` and ``duration`` are stored as float seconds internally but serialised
as frame numbers in the Kdenlive JSON format (requiring FPS at serialisation).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .timecode import Timecode


@dataclass
class Marker:
    """A single Kdenlive marker / guide.

    Args:
        pos: Position in seconds (absolute, within the clip or sequence).
        comment: Label text shown in Kdenlive.
        marker_type: Colour category index (0–8).  Defaults to 0 (purple).
        duration: Length of the marker region in seconds.  0 means a simple
            point marker with no region.
    """

    pos: float
    comment: str = "Marker"
    marker_type: int = 0
    duration: float = 0.0

    # ------------------------------------------------------------------ #
    # Construction helpers                                                 #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_timecode(
        cls,
        pos: str,
        comment: str = "Marker",
        marker_type: int = 0,
        duration: str | None = None,
    ) -> "Marker":
        """Create a marker using HH:MM:SS.mmm timecodes.

        Args:
            pos: Position timecode (HH:MM:SS.mmm or HH:MM:SS:FF).
            comment: Marker label.
            marker_type: Colour category (0–8).
            duration: Optional duration timecode.  ``None`` → point marker
                (duration = 0).

        Returns:
            Marker instance.
        """
        pos_seconds = Timecode.from_string(pos).to_seconds()
        dur_seconds = 0.0
        if duration is not None:
            dur_seconds = Timecode.from_string(duration).to_seconds()
        return cls(pos=pos_seconds, comment=comment, marker_type=marker_type, duration=dur_seconds)

    @classmethod
    def from_dict(cls, data: dict, fps: float = 30.0) -> "Marker":
        """Deserialise from a Kdenlive JSON marker dict.

        Args:
            data: Kdenlive marker dict with integer frame pos/duration.
            fps: Frames per second for frame-to-seconds conversion.

        Returns:
            Marker instance.
        """
        return cls(
            pos=int(data["pos"]) / fps,
            comment=str(data.get("comment", "Marker")),
            marker_type=int(data.get("type", 0)),
            duration=int(data.get("duration", 0)) / fps,
        )

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #

    def to_dict(self, fps: float = 30.0) -> dict:
        """Serialise to Kdenlive marker dict (frame-based).

        Kdenlive's JSON format uses integer frames for pos and duration.

        Args:
            fps: Frames per second for seconds-to-frames conversion.

        Returns:
            Marker dict with frame integers.
        """
        return {
            "comment": self.comment,
            "duration": int(round(self.duration * fps)),
            "pos": int(round(self.pos * fps)),
            "type": self.marker_type,
        }

    def pos_timecode(self) -> str:
        """Return position as HH:MM:SS.mmm timecode string."""
        return str(Timecode.from_seconds(self.pos))

    def duration_timecode(self) -> str:
        """Return duration as HH:MM:SS.mmm timecode string."""
        return str(Timecode.from_seconds(self.duration))


def markers_to_json(markers: list[Marker], fps: float = 30.0) -> str:
    """Serialise a list of markers to the Kdenlive JSON property value.

    Args:
        markers: List of Marker objects.
        fps: Frames per second for frame conversion.

    Returns:
        JSON string.
    """
    items = [m.to_dict(fps=fps) for m in markers]
    return json.dumps(items, indent=4)


def markers_from_json(json_str: str, fps: float = 30.0) -> list[Marker]:
    """Deserialise a Kdenlive JSON property value to a list of markers.

    Args:
        json_str: JSON string with frame-based marker data.
        fps: Frames per second for frame-to-seconds conversion.

    Returns:
        List of Marker objects.
    """
    data = json.loads(json_str)
    return [Marker.from_dict(d, fps=fps) for d in data]

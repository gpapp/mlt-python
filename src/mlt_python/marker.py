"""Marker support for MLT XML / Kdenlive.

Kdenlive stores markers in two places:
- ``kdenlive:markers`` property on a chain/producer – clip markers visible in
  the clip monitor.
- ``kdenlive:sequenceproperties.guides`` property on the main sequence tractor –
  timeline guides visible on the timeline ruler.

Both use the same JSON array format::

    [
        {"comment": "Label", "duration": <frames>, "pos": <frame>, "type": <0-8>}
    ]

``pos`` and ``duration`` are absolute frame numbers relative to the clip or
sequence timeline respectively.  ``type`` maps to one of the nine built-in
Kdenlive guide colour categories (0 = purple, 1 = blue, …).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .timecode import Timecode


@dataclass
class Marker:
    """A single Kdenlive marker / guide.

    Args:
        pos: Position in frames (absolute, within the clip or sequence).
        comment: Label text shown in Kdenlive.
        marker_type: Colour category index (0–8).  Defaults to 0 (purple).
        duration: Length of the marker region in frames.  0 means a simple
            point marker with no region.
    """

    pos: int
    comment: str = "Marker"
    marker_type: int = 0
    duration: int = 0

    # ------------------------------------------------------------------ #
    # Construction helpers                                                 #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_timecode(
        cls,
        pos: str,
        fps: float,
        comment: str = "Marker",
        marker_type: int = 0,
        duration: str | None = None,
    ) -> "Marker":
        """Create a marker using HH:MM:SS:FF timecodes.

        Args:
            pos: Position timecode (HH:MM:SS:FF).
            fps: Frames per second of the project profile.
            comment: Marker label.
            marker_type: Colour category (0–8).
            duration: Optional duration timecode.  ``None`` → point marker
                (duration = 0).

        Returns:
            Marker instance.
        """
        pos_frames = Timecode.from_string(pos, fps).to_frames()
        dur_frames = 0
        if duration is not None:
            dur_frames = Timecode.from_string(duration, fps).to_frames()
        return cls(pos=pos_frames, comment=comment, marker_type=marker_type, duration=dur_frames)

    @classmethod
    def from_dict(cls, data: dict) -> "Marker":
        """Deserialise from a Kdenlive JSON marker dict."""
        return cls(
            pos=int(data["pos"]),
            comment=str(data.get("comment", "Marker")),
            marker_type=int(data.get("type", 0)),
            duration=int(data.get("duration", 0)),
        )

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        """Serialise to Kdenlive marker dict."""
        return {
            "comment": self.comment,
            "duration": self.duration,
            "pos": self.pos,
            "type": self.marker_type,
        }

    def pos_timecode(self, fps: float) -> str:
        """Return position as HH:MM:SS:FF timecode string."""
        return str(Timecode.from_frames(self.pos, fps))

    def duration_timecode(self, fps: float) -> str:
        """Return duration as HH:MM:SS:FF timecode string."""
        return str(Timecode.from_frames(self.duration, fps))


def markers_to_json(markers: list[Marker]) -> str:
    """Serialise a list of markers to the Kdenlive JSON property value."""
    items = [m.to_dict() for m in markers]
    return json.dumps(items, indent=4)


def markers_from_json(json_str: str) -> list[Marker]:
    """Deserialise a Kdenlive JSON property value to a list of markers."""
    data = json.loads(json_str)
    return [Marker.from_dict(d) for d in data]

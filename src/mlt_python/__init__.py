"""MLT XML Library for Kdenlive.

A pure Python library for creating, modifying, and parsing MLT XML files
compatible with Kdenlive. Provides a high-level API that uses timecodes
(HH:MM:SS:FF) for all operations.

Example usage:
    from mlt_python import MLTProject, Profile

    # Create a new project
    project = MLTProject(profile="hd1080_30")

    # Add media to bin
    video = project.add_producer("video.mp4", id="vid1")

    # Add a video track and audio track
    video_track = project.add_track("video", id="playlist0")
    audio_track = project.add_track("audio", id="playlist1")

    # Add clips using timecodes
    project.add_clip("playlist0", "vid1", start="00:00:00:00", duration="00:00:10:00")

    # Add subtitles from SRT file
    project.add_subtitle("subtitles.srt", track=0, start="00:00:00:00")

    # Save to file
    project.save("project.kdenlive.xml")
"""

from .project import MLTProject
from .profile import Profile
from .producer import Producer
from .playlist import Playlist
from .clip import Clip, Blank
from .filter import Filter, Filters
from .transition import Transition, Transitions
from .subtitle import SubtitleTrack, SubtitleItem, SRTFile
from .timecode import Timecode
from .kdenlive import KdenliveProperties, KdenliveMetadata
from .marker import Marker, markers_to_json, markers_from_json

__version__ = "0.1.0"
__all__ = [
    "MLTProject",
    "Profile",
    "Producer",
    "Playlist",
    "Clip",
    "Blank",
    "Filter",
    "Filters",
    "Transition",
    "Transitions",
    "SubtitleTrack",
    "SubtitleItem",
    "SRTFile",
    "Timecode",
    "KdenliveProperties",
    "KdenliveMetadata",
    "Marker",
    "markers_to_json",
    "markers_from_json",
]

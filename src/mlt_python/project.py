"""MLTProject class for MLT XML library.

Main class for creating, modifying, and saving MLT XML files
compatible with Kdenlive. Provides a high-level API that uses
timecodes (HH:MM:SS:FF) for all operations.
"""

from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET
from xml.dom import minidom
import uuid

from .profile import Profile
from .producer import Producer
from .playlist import Playlist
from .clip import Clip, Blank
from .filter import Filter, Filters
from .transition import Transition, Transitions
from .subtitle import SubtitleTrack, SRTFile
from .timecode import Timecode
from .kdenlive import KdenliveProperties
from .marker import Marker, markers_to_json, markers_from_json


class MLTProject:
    """Main project class for MLT XML manipulation.

    This class provides the primary API for creating and modifying
    MLT XML files. It handles timecode-to-frame conversion and
    provides methods to add/modify/delete media, tracks, clips,
    filters, transitions, and subtitles.

    Attributes:
        profile: Video profile (fps, resolution, etc.)
        producers: Dictionary of producers (media bin items)
        playlists: Dictionary of playlists (tracks)
        filters: List of global filters
        transitions: List of transitions
        tractor_id: ID of the main tractor
        kdenlive: Kdenlive-specific properties
        version: MLT XML version
    """

    def __init__(
        self,
        profile: Profile | str = "hd1080_30",
        version: str = "7.37.0",
    ) -> None:
        """Initialize an MLT project.

        Args:
            profile: Profile object or preset name (e.g., "hd1080_30")
            version: MLT XML version
        """
        if isinstance(profile, str):
            self.profile = self._get_profile_by_name(profile)
        else:
            self.profile = profile

        self.version = version
        self.producers: dict[str, Producer] = {}
        self.playlists: dict[str, Playlist] = {}
        self.filters: list[Filter] = []
        self.transitions: list[Transition] = []
        self.tractor_id: str = "tractor0"
        self.kdenlive: KdenliveProperties = KdenliveProperties()

        # Markers: clip markers keyed by producer_id; sequence guides on timeline
        self.clip_markers: dict[str, list[Marker]] = {}
        self.sequence_markers: list[Marker] = []

        # Track counter for auto-generating track IDs
        self._track_counter: int = 0
        self._producer_counter: int = 0
        self._filter_counter: int = 0
        self._chain_counter: int = 0
        self._tractor_counter: int = 0
        self.sequence_uuid: str = "{" + str(uuid.uuid4()) + "}"

    @staticmethod
    def _get_profile_by_name(name: str) -> Profile:
        """Get a profile by preset name.

        Args:
            name: Profile preset name

        Returns:
            Profile object

        Raises:
            ValueError: If preset name not found
        """
        presets = {
            "hd1080_30": Profile.hd1080_30,
            "hd1080_2997": Profile.hd1080_2997,
            "hd1080_25": Profile.hd1080_25,
            "hd1080_24": Profile.hd1080_24,
            "hd720_30": Profile.hd720_30,
            "uhd_30": Profile.uhd_30,
            "uhd_24": Profile.uhd_24,
            "sdtv_ntsc": Profile.sdtv_ntsc,
            "sdtv_pal": Profile.sdtv_pal,
        }

        if name not in presets:
            raise ValueError(f"Unknown profile preset: {name}")

        return presets[name]()

    def add_producer(
        self,
        resource: str,
        id: str | None = None,
        mlt_service: str = "avformat",
        properties: dict[str, str] | None = None,
    ) -> Producer:
        """Add a media file to the bin.

        Args:
            resource: File path or resource identifier
            id: Unique ID (auto-generated if None)
            mlt_service: MLT service type
            properties: Additional properties

        Returns:
            The created Producer object
        """
        if id is None:
            id = f"producer{self._producer_counter}"
            self._producer_counter += 1

        producer = Producer(
            id=id,
            resource=resource,
            mlt_service=mlt_service,
            properties=properties,
        )
        self.producers[id] = producer
        return producer

    def remove_producer(self, id: str) -> Producer | None:
        """Remove a producer from the bin.

        Args:
            id: Producer ID to remove

        Returns:
            Removed Producer, or None if not found
        """
        return self.producers.pop(id, None)

    def get_producer(self, id: str) -> Producer | None:
        """Get a producer by ID.

        Args:
            id: Producer ID

        Returns:
            Producer object, or None if not found
        """
        return self.producers.get(id)

    def add_track(
        self,
        track_type: str = "video",
        id: str | None = None,
    ) -> Playlist:
        """Add a new track (playlist) to the project.

        Args:
            track_type: "video" or "audio"
            id: Track ID (auto-generated if None)

        Returns:
            The created Playlist object
        """
        if id is None:
            id = f"playlist{self._track_counter}"
            self._track_counter += 1

        playlist = Playlist(id=id)
        playlist.set_property("kdenlive:track_type", track_type)
        self.playlists[id] = playlist
        return playlist

    def remove_track(self, id: str) -> Playlist | None:
        """Remove a track from the project.

        Args:
            id: Playlist ID to remove

        Returns:
            Removed Playlist, or None if not found
        """
        return self.playlists.pop(id, None)

    def add_clip(
        self,
        track_id: str,
        producer_id: str,
        start: str,
        end: str | None = None,
        duration: str | None = None,
        position: int | None = None,
    ) -> Clip:
        """Add a clip to a track using timecodes.

        Args:
            track_id: Target track/playlist ID
            producer_id: Producer ID to reference
            start: Start timecode (HH:MM:SS:FF) on the timeline
            end: End timecode (HH:MM:SS:FF), exclusive
            duration: Duration timecode (alternative to end)
            position: Position in track (default: append)

        Returns:
            The created Clip object

        Raises:
            KeyError: If track_id or producer_id not found
        """
        if track_id not in self.playlists:
            raise KeyError(f"Track not found: {track_id}")
        if producer_id not in self.producers:
            raise KeyError(f"Producer not found: {producer_id}")

        # Calculate in/out points from timecodes
        start_tc = Timecode.from_string(start, self.profile.fps)
        in_point = start_tc.to_frames()

        if end is not None:
            end_tc = Timecode.from_string(end, self.profile.fps)
            out_point = end_tc.to_frames() - 1  # MLT out is inclusive
        elif duration is not None:
            dur_tc = Timecode.from_string(duration, self.profile.fps)
            out_point = in_point + dur_tc.to_frames() - 1
        else:
            out_point = None

        clip = Clip(
            producer_id=producer_id,
            in_point=in_point,
            out_point=out_point,
        )

        playlist = self.playlists[track_id]
        if position is None:
            playlist.clips.append(clip)
        else:
            playlist.clips.insert(position, clip)

        return clip

    def remove_clip(self, track_id: str, position: int) -> Clip | Blank | None:
        """Remove a clip from a track.

        Args:
            track_id: Track/playlist ID
            position: Position of clip to remove

        Returns:
            Removed clip/blank, or None if invalid

        Raises:
            KeyError: If track_id not found
        """
        if track_id not in self.playlists:
            raise KeyError(f"Track not found: {track_id}")

        return self.playlists[track_id].remove_clip(position)

    def add_filter(
        self,
        mlt_service: str,
        track: int | None = None,
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        properties: dict[str, str] | None = None,
    ) -> Filter:
        """Add a filter to the project.

        Args:
            mlt_service: MLT filter service name
            track: Track index (None = all tracks)
            start: Start timecode
            end: End timecode
            duration: Duration timecode
            properties: Additional filter properties

        Returns:
            The created Filter object
        """
        filter_obj = Filter.from_timecode(
            mlt_service=mlt_service,
            start=start,
            end=end,
            duration=duration,
            fps=self.profile.fps,
            track=track,
            properties=properties,
        )
        self.filters.append(filter_obj)
        return filter_obj

    def add_subtitle(
        self,
        srt_file: str,
        track: int = 0,
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
    ) -> Filter:
        """Add subtitles from an SRT file.

        Args:
            srt_file: Path to SRT file
            track: Track index
            start: Start timecode
            end: End timecode
            duration: Duration timecode

        Returns:
            The created subtitle Filter object
        """
        subtitle_filter = Filters.subtitle(
            resource=srt_file,
            track=track,
            start=start,
            end=end,
            duration=duration,
            fps=self.profile.fps,
        )
        self.filters.append(subtitle_filter)
        return subtitle_filter

    def add_transition(
        self,
        mlt_service: str,
        a_track: int = 0,
        b_track: int = 1,
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        properties: dict[str, str] | None = None,
    ) -> Transition:
        """Add a transition between tracks.

        Args:
            mlt_service: MLT transition service name
            a_track: Source track index
            b_track: Destination track index
            start: Start timecode
            end: End timecode
            duration: Duration timecode
            properties: Additional transition properties

        Returns:
            The created Transition object
        """
        transition = Transition.from_timecode(
            mlt_service=mlt_service,
            a_track=a_track,
            b_track=b_track,
            start=start,
            end=end,
            duration=duration,
            fps=self.profile.fps,
            properties=properties,
        )
        self.transitions.append(transition)
        return transition

    # ------------------------------------------------------------------ #
    # Marker API                                                          #
    # ------------------------------------------------------------------ #

    def add_marker(
        self,
        pos: str,
        comment: str = "Marker",
        marker_type: int = 0,
        duration: str | None = None,
        producer_id: str | None = None,
    ) -> Marker:
        """Add a marker to the timeline (guide) or to a specific clip.

        Args:
            pos: Position timecode (HH:MM:SS:FF).
            comment: Marker label.
            marker_type: Colour category 0-8 (0=purple, 1=blue, …).
            duration: Optional region duration timecode. ``None`` = point.
            producer_id: If given, attach as a clip marker on that producer.
                         Otherwise the marker becomes a sequence/timeline guide.

        Returns:
            The created Marker.

        Raises:
            KeyError: If ``producer_id`` is given but not found.
        """
        if producer_id is not None and producer_id not in self.producers:
            raise KeyError(f"Producer not found: {producer_id}")

        marker = Marker.from_timecode(
            pos=pos,
            fps=self.profile.fps,
            comment=comment,
            marker_type=marker_type,
            duration=duration,
        )

        if producer_id is not None:
            self.clip_markers.setdefault(producer_id, []).append(marker)
        else:
            self.sequence_markers.append(marker)

        return marker

    def remove_marker(
        self,
        pos: str,
        producer_id: str | None = None,
    ) -> bool:
        """Remove a marker at a given position.

        Args:
            pos: Position timecode (HH:MM:SS:FF) to match.
            producer_id: If given, remove from clip markers; else from guides.

        Returns:
            ``True`` if a marker was removed, ``False`` if none matched.
        """
        target_frame = Timecode.from_string(pos, self.profile.fps).to_frames()

        if producer_id is not None:
            lst = self.clip_markers.get(producer_id, [])
        else:
            lst = self.sequence_markers

        for i, m in enumerate(lst):
            if m.pos == target_frame:
                lst.pop(i)
                return True
        return False

    def get_markers(
        self,
        producer_id: str | None = None,
    ) -> list[Marker]:
        """Return markers for a producer or the sequence.

        Args:
            producer_id: If given, return clip markers for that producer.
                         If ``None``, return sequence/timeline guides.

        Returns:
            List of Marker objects (copy).
        """
        if producer_id is not None:
            return list(self.clip_markers.get(producer_id, []))
        return list(self.sequence_markers)

    def clear_markers(
        self,
        producer_id: str | None = None,
    ) -> None:
        """Remove all markers for a producer or from the sequence.

        Args:
            producer_id: If given, clear clip markers for that producer.
                         If ``None``, clear sequence/timeline guides.
        """
        if producer_id is not None:
            self.clip_markers.pop(producer_id, None)
        else:
            self.sequence_markers.clear()

    def get_duration_frames(self) -> int:
        """Get the total duration of the project in frames.

        Returns:
            Total duration in frames
        """
        max_duration = 0
        for playlist in self.playlists.values():
            duration_frames = playlist.get_duration_frames()
            max_duration = max(max_duration, duration_frames)
        return max_duration

    def get_duration_timecode(self, fps: float | None = None) -> str:
        """Get the total duration as a timecode string.

        Args:
            fps: Optional frames per second (uses profile FPS if None)

        Returns:
            Duration in HH:MM:SS:FF format
        """
        fps = fps or self.profile.fps
        return str(Timecode.from_frames(self.get_duration_frames(), fps))

    def _seconds_to_timestamp(self, producer: Producer, default_seconds: int) -> str:

        """Convert producer length to timestamp format (HH:MM:SS.mmm)."""
        length_str = producer.get_property("length", str(default_seconds * 30))
        try:
            frames = int(length_str)
            fps = self.profile.fps
            total_seconds = frames / fps
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        except ValueError:
            return "00:00:00.000"

    def _get_timeline_duration(self) -> str:
        """Get the duration of the timeline in timestamp format."""
        max_duration = 0
        for playlist in self.playlists.values():
            for clip in playlist.clips:
                if clip.out_point and clip.out_point > max_duration:
                    max_duration = clip.out_point
        fps = self.profile.fps
        total_seconds = max_duration / fps if max_duration > 0 else 0
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

    def to_xml(
        self,
        kdenlive_format: bool = False,
        root_path: str | None = None,
        ) -> str:
        """Generate MLT XML string.

        Args:
            kdenlive_format: Use Kdenlive-specific format (chain elements, main_bin, etc.)
            root_path: Root path for media files (Kdenlive format only)

        Returns:
            XML string representation of the project
        """
        # Reset counters at start of XML generation
        self._filter_counter = 0
        self._chain_counter = 0
        self._tractor_counter = 0
        self._playlist_counter = 0
        self._transition_counter = 0

        # Build root attributes - order matters! LC_NUMERIC first like reference
        root_attrs: dict[str, str] = {}
        if kdenlive_format:
            root_attrs["LC_NUMERIC"] = "en_US.UTF-8"
            root_attrs["producer"] = "main_bin"
            if root_path:
                root_attrs["root"] = root_path.replace("\\", "/")
        root_attrs["version"] = self.version

        # Create root element
        root = ET.Element("mlt", root_attrs)

        # Add profile if not default
        if kdenlive_format or self.profile.name != "hd1080_30":
            profile_attrs = self.profile.to_xml_attributes()
            if kdenlive_format:
                ordered_attrs = {"colorspace": profile_attrs.pop("colorspace", "709")}
                for name, value in profile_attrs.items():
                    ordered_attrs[name] = value
                profile_attrs = ordered_attrs
                profile_name = f"atsc_{self.profile.height}p_{int(self.profile.fps)}"
            ET.SubElement(root, "profile", profile_attrs)

        # Build producer-to-chain mapping for Kdenlive format
        producer_to_chain: dict[str, str] = {}
        if kdenlive_format:
            for producer in self.producers.values():
                chain_id = f"chain{self._chain_counter}"
                producer_to_chain[producer.id] = chain_id
                chain_elem = producer.to_xml_chain(fps=self.profile.fps, chain_id=chain_id)
                # Attach clip markers if any
                clip_mkrs = self.clip_markers.get(producer.id, [])
                if clip_mkrs:
                    from xml.etree import ElementTree as _ET
                    prop = _ET.SubElement(chain_elem, "property", {"name": "kdenlive:markers"})
                    prop.text = markers_to_json(clip_mkrs)
                root.append(chain_elem)
                self._chain_counter += 1
        else:
            for producer in self.producers.values():
                if producer.filters:
                    chain_id = f"chain{self._chain_counter}"
                    chain = ET.Element("chain", {"id": chain_id, "out": self._seconds_to_timestamp(producer, 0)})
                    self._chain_counter += 1
                    for name, value in producer.properties.items():
                        prop = ET.SubElement(chain, "property", {"name": name})
                        prop.text = value.replace("\\", "/") if name == "resource" else value
                    for filter_obj in producer.filters:
                        chain.append(filter_obj.to_xml())
                    root.append(chain)
                else:
                    root.append(producer.to_xml())

        # Add playlists if not in kdenlive format
        if not kdenlive_format:
            for playlist in self.playlists.values():
                root.append(playlist.to_xml(fps=self.profile.fps))

        # Add black color producer (required by Kdenlive as base track)
        if kdenlive_format:
            main_tractor_out = self.get_duration_timecode() if self.playlists else "00:05:00.000"
            sequence_uuid = self.sequence_uuid
            black_producer = ET.SubElement(root, "producer", {"id": "producer0", "in": "00:00:00.000", "out": main_tractor_out})

            ET.SubElement(black_producer, "property", {"name": "length"}).text = "2147483647"
            ET.SubElement(black_producer, "property", {"name": "eof"}).text = "continue"
            ET.SubElement(black_producer, "property", {"name": "resource"}).text = "black"
            ET.SubElement(black_producer, "property", {"name": "aspect_ratio"}).text = "1"
            ET.SubElement(black_producer, "property", {"name": "mlt_service"}).text = "color"
            ET.SubElement(black_producer, "property", {"name": "kdenlive:playlistid"}).text = "black_track"
            ET.SubElement(black_producer, "property", {"name": "mlt_image_format"}).text = "rgba"
            ET.SubElement(black_producer, "property", {"name": "set.test_audio"}).text = "0"

            # Add main_bin playlist for Kdenlive format
            sess_uuid = str(uuid.uuid4())
            main_bin = ET.SubElement(root, "playlist", {"id": "main_bin"})
            prop = ET.SubElement(main_bin, "property", {"name": "xml_retain"})
            prop.text = "1"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:folder.-1.2"})
            prop.text = "Sequences"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:sequenceFolder"})
            prop.text = "2"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.kdenliveversion"})
            prop.text = "25.12.3"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.sessionid"})
            prop.text = sess_uuid
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.uuid"})
            prop.text = sequence_uuid
            import time
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.documentid"})
            prop.text = str(int(time.time() * 1000))
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.enableproxy"})
            prop.text = "0"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.enableexternalproxy"})
            prop.text = "0"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.generateproxy"})
            prop.text = "0"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.generateimageproxy"})
            prop.text = "0"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.version"})
            prop.text = "1.1"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.audioChannels"})
            prop.text = "2"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.binsort"})
            prop.text = "0"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.enableTimelineZone"})
            prop.text = "0"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.opensequences"})
            prop.text = sequence_uuid
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.activetimeline"})
            prop.text = sequence_uuid
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.seekOffset"})
            prop.text = "30000"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:expandedFolders"})
            prop.text = ""
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:binZoom"})
            prop.text = "4"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:extraBins"})
            prop.text = "project_bin:-1:0"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:documentnotes"})
            prop.text = ""
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:documentnotesversion"})
            prop.text = "2"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.browserurl"})
            prop.text = "C:/Users/gerge/Videos/"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.previewwextension"})
            prop.text = ""
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.previewparameters"})
            prop.text = ""
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.proxyextension"})
            prop.text = ""
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.proxyimagesize"})
            prop.text = "800"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.proxyminsize"})
            prop.text = "1000"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.proxyparams"})
            prop.text = ""
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.proxyresize"})
            prop.text = "640"
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.externalproxyparams"})
            prop.text = ""
            
            guides_categories = """[
        {
        "color": "#9b59b6",
        "comment": "Category 1",
        "index": 0
        },
        {
        "color": "#3daee9",
        "comment": "Category 2",
        "index": 1
        },
        {
        "color": "#1abc9c",
        "comment": "Category 3",
        "index": 2
        },
        {
        "color": "#1cdc9a",
        "comment": "Category 4",
        "index": 3
        },
        {
        "color": "#c9ce3b",
        "comment": "Category 5",
        "index": 4
        },
        {
        "color": "#fdbc4b",
        "comment": "Category 6",
        "index": 5
        },
        {
        "color": "#f39c1f",
        "comment": "Category 7",
        "index": 6
        },
        {
        "color": "#f47750",
        "comment": "Category 8",
        "index": 7
        },
        {
        "color": "#da4453",
        "comment": "Category 9",
        "index": 8
        }
        ]"""
            prop = ET.SubElement(main_bin, "property", {"name": "kdenlive:docproperties.guidesCategories"})
            prop.text = guides_categories

            # FINALLY add entries at the end of the playlist
            # Add entries for all producers (chains)
            for producer_id, chain_id in producer_to_chain.items():
                producer = self.producers[producer_id]
                out_frames = 0
                length = producer.properties.get("length")
                if length is not None:
                    try:
                        out_frames = int(length)
                    except ValueError:
                        pass
                
                out_tc = "00:00:00.000"
                if out_frames > 0:
                    total_seconds = out_frames / self.profile.fps
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = total_seconds % 60
                    out_tc = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
                
                ET.SubElement(main_bin, "entry", {
                    "in": "00:00:00.000",
                    "out": out_tc,
                    "producer": chain_id
                })

            # Add sequence tractor entry
            ET.SubElement(main_bin, "entry", {
                "in": "00:00:00.000",
                "out": main_tractor_out,
                "producer": sequence_uuid
            })

            # Add playlists (tracks) and tractors in alternating order (like reference)
            playlist_list = list(self.playlists.values())
            companion_map: dict[str, str] = {}
            track_type_map: dict[str, str] = {}

            # Track all used playlist IDs across loop iterations for unique companion IDs
            existing_ids = set(self.playlists.keys())

            for i, playlist in enumerate(playlist_list):
                track_type = playlist.properties.get("kdenlive:track_type", "video")
                track_type_map[playlist.id] = track_type
                playlist.properties.pop("kdenlive:track_type", None)

                # Add main playlist with chain references and FPS
                root.append(playlist.to_xml(producer_to_chain, fps=self.profile.fps))
                playlist_elem = root.find(f"playlist[@id='{playlist.id}']")
                if playlist_elem is not None and track_type == "audio":
                    prop = ET.SubElement(playlist_elem, "property", {"name": "kdenlive:audio_track"})
                    prop.text = "1"

                # Create companion playlist
                next_id = 0
                while f"playlist{next_id}" in existing_ids:
                    next_id += 1
                companion_id = f"playlist{next_id}"
                existing_ids.add(companion_id)

                companion = Playlist(id=companion_id)
                root.append(companion.to_xml())
                companion_elem = root.find(f"playlist[@id='{companion_id}']")
                if companion_elem is not None and track_type == "audio":
                    prop = ET.SubElement(companion_elem, "property", {"name": "kdenlive:audio_track"})
                    prop.text = "1"
                companion_map[playlist.id] = companion_id

                # Add tractor IMMEDIATELY after its two playlists (alternating pattern)
                tractor_attrs: dict[str, str] = {"id": f"tractor{self._tractor_counter}", "in": "00:00:00.000"}
                tractor = ET.SubElement(root, "tractor", tractor_attrs)
                self._tractor_counter += 1

                # Add track properties
                if track_type == "audio":
                    prop = ET.SubElement(tractor, "property", {"name": "kdenlive:audio_track"})
                    prop.text = "1"
                prop = ET.SubElement(tractor, "property", {"name": "kdenlive:trackheight"})
                prop.text = "64"
                prop = ET.SubElement(tractor, "property", {"name": "kdenlive:timeline_active"})
                prop.text = "1"
                prop = ET.SubElement(tractor, "property", {"name": "kdenlive:collapsed"})
                prop.text = "0"
                prop = ET.SubElement(tractor, "property", {"name": "kdenlive:thumbs_format"})
                prop.text = ""
                prop = ET.SubElement(tractor, "property", {"name": "kdenlive:audio_rec"})

                # Add track references BEFORE filters (MLT requires this order)
                hide_attr = "video" if track_type == "audio" else "audio"
                ET.SubElement(tractor, "track", {"producer": playlist.id, "hide": hide_attr})
                ET.SubElement(tractor, "track", {"producer": companion_id, "hide": hide_attr})

                # Add default audio filters - ONLY for audio tracks
                if track_type == "audio":
                    for mlt_service in ["volume", "panner", "audiolevel"]:
                        filter_elem = ET.SubElement(tractor, "filter", {"id": f"filter{self._filter_counter}"})
                        self._filter_counter += 1
                        if mlt_service == "volume":
                            prop = ET.SubElement(filter_elem, "property", {"name": "window"})
                            prop.text = "75"
                            prop = ET.SubElement(filter_elem, "property", {"name": "max_gain"})
                            prop.text = "20dB"
                            prop = ET.SubElement(filter_elem, "property", {"name": "channel_mask"})
                            prop.text = "-1"
                        elif mlt_service == "panner":
                            prop = ET.SubElement(filter_elem, "property", {"name": "channel"})
                            prop.text = "-1"
                            prop = ET.SubElement(filter_elem, "property", {"name": "start"})
                            prop.text = "0.5"
                        elif mlt_service == "audiolevel":
                            prop = ET.SubElement(filter_elem, "property", {"name": "iec_scale"})
                            prop.text = "0"
                            prop = ET.SubElement(filter_elem, "property", {"name": "dbpeak"})
                            prop.text = "1"
                        prop = ET.SubElement(filter_elem, "property", {"name": "mlt_service"})
                        prop.text = mlt_service
                        prop = ET.SubElement(filter_elem, "property", {"name": "kdenlive_id"})
                        prop.text = mlt_service
                        prop = ET.SubElement(filter_elem, "property", {"name": "internal_added"})
                        prop.text = "237"
                        prop = ET.SubElement(filter_elem, "property", {"name": "disable"})
                        prop.text = "1"

                # Add custom playlist filters
                for filter_obj in playlist.filters:
                    if not filter_obj.id:
                        filter_obj.id = f"filter{self._filter_counter}"
                        self._filter_counter += 1
                    # In Kdenlive tractors, we need to add the filter element directly
                    tractor.append(filter_obj.to_xml())



            # Create main sequence tractor with sequential ID
            sequence_id = f"tractor{self._tractor_counter}"
            sequence_uuid = self.sequence_uuid
            main_tractor_attrs: dict[str, str] = {
                "id": sequence_uuid,
                "in": "00:00:00.000",
                "out": main_tractor_out
            }

            main_tractor = ET.SubElement(root, "tractor", main_tractor_attrs)
            self._tractor_counter += 1

            # Add sequence properties
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:uuid"})
            prop.text = sequence_uuid
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:clipname"})
            prop.text = "Sequence 1"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.hasAudio"})
            prop.text = "1"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.hasVideo"})
            prop.text = "1"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.activeTrack"})
            prop.text = "2"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.tracksCount"})
            prop.text = str(len(self.playlists))
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.documentuuid"})
            prop.text = sequence_uuid
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:control_uuid"})
            prop.text = sequence_uuid
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:duration"})
            prop.text = self.get_duration_timecode()
            max_duration = self.get_duration_frames()
            maxduration_str = str(max_duration) if max_duration > 0 else "1"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:maxduration"})
            prop.text = maxduration_str

            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:producer_type"})
            prop.text = "17"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:id"})
            prop.text = "3"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:clip_type"})
            prop.text = "0"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:file_size"})
            prop.text = "0"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:folderid"})
            prop.text = "2"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.audioTarget"})
            prop.text = "1"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.disablepreview"})
            prop.text = "0"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.position"})
            prop.text = "0"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.scrollPos"})
            prop.text = "0"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.tracks"})
            prop.text = str(len(self.playlists))
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.verticalzoom"})
            prop.text = "1"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.videoTarget"})
            prop.text = "2"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.zonein"})
            prop.text = "0"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.zoneout"})
            prop.text = "75"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.zoom"})
            prop.text = "8"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.groups"})
            prop.text = "[\n]"
            prop = ET.SubElement(main_tractor, "property", {"name": "kdenlive:sequenceproperties.guides"})
            if self.sequence_markers:
                prop.text = markers_to_json(self.sequence_markers)
            else:
                prop.text = "[\n]"

            # Add tracks and transitions to main tractor
            ET.SubElement(main_tractor, "track", {"producer": "producer0"})
            
            # Keep track of track tractor IDs for references
            track_ids = list(self.playlists.keys())
            for i, track_id in enumerate(track_ids):
                # The track tractors were created in the same order as self.playlists
                # and started at tractor0.
                ET.SubElement(main_tractor, "track", {"producer": f"tractor{i}"})

            for i, track_id in enumerate(track_ids):
                track_type = self.playlists[track_id].properties.get("kdenlive:track_type", "video")
                service = "mix" if track_type == "audio" else "qtblend"
                
                transition = ET.SubElement(main_tractor, "transition", {"id": f"transition{i}"})
                ET.SubElement(transition, "property", {"name": "a_track"}).text = "0"
                ET.SubElement(transition, "property", {"name": "b_track"}).text = str(i + 1)
                ET.SubElement(transition, "property", {"name": "mlt_service"}).text = service
                ET.SubElement(transition, "property", {"name": "kdenlive_id"}).text = service
                ET.SubElement(transition, "property", {"name": "internal_added"}).text = "237"
                ET.SubElement(transition, "property", {"name": "always_active"}).text = "1"
                
                if service == "mix":
                    ET.SubElement(transition, "property", {"name": "accepts_blanks"}).text = "1"
                    ET.SubElement(transition, "property", {"name": "sum"}).text = "1"
                else:
                    ET.SubElement(transition, "property", {"name": "compositing"}).text = "0"
                    ET.SubElement(transition, "property", {"name": "distort"}).text = "0"
                    ET.SubElement(transition, "property", {"name": "rotate_center"}).text = "0"

            # Add filters at end of main tractor
            filter_elem = ET.SubElement(main_tractor, "filter", {"id": f"filter{self._filter_counter}"})
            self._filter_counter += 1
            prop = ET.SubElement(filter_elem, "property", {"name": "window"})
            prop.text = "75"
            prop = ET.SubElement(filter_elem, "property", {"name": "max_gain"})
            prop.text = "20dB"
            prop = ET.SubElement(filter_elem, "property", {"name": "channel_mask"})
            prop.text = "-1"
            prop = ET.SubElement(filter_elem, "property", {"name": "mlt_service"})
            prop.text = "volume"
            prop = ET.SubElement(filter_elem, "property", {"name": "kdenlive_id"})
            prop.text = "volume"
            prop = ET.SubElement(filter_elem, "property", {"name": "internal_added"})
            prop.text = "237"
            prop = ET.SubElement(filter_elem, "property", {"name": "disable"})
            prop.text = "1"
            filter_elem = ET.SubElement(main_tractor, "filter", {"id": f"filter{self._filter_counter}"})
            self._filter_counter += 1
            prop = ET.SubElement(filter_elem, "property", {"name": "channel"})
            prop.text = "-1"
            prop = ET.SubElement(filter_elem, "property", {"name": "mlt_service"})
            prop.text = "panner"
            prop = ET.SubElement(filter_elem, "property", {"name": "kdenlive_id"})
            prop.text = "panner"
            prop = ET.SubElement(filter_elem, "property", {"name": "internal_added"})
            prop.text = "237"
            prop = ET.SubElement(filter_elem, "property", {"name": "start"})
            prop.text = "0.5"
            prop = ET.SubElement(filter_elem, "property", {"name": "disable"})
            prop.text = "1"

            # (This block was moved up)

            # Add projectTractor tractor after main_bin
            project_tractor = ET.SubElement(root, "tractor", {
                "id": f"tractor{self._tractor_counter}",
                "in": "00:00:00.000",
                "out": main_tractor_out
            })
            self._tractor_counter += 1
            prop = ET.SubElement(project_tractor, "property", {"name": "kdenlive:projectTractor"})
            prop.text = "1"
            ET.SubElement(project_tractor, "track", {
                "in": "00:00:00.000",
                "out": main_tractor_out,
                "producer": sequence_uuid
            })
        else:
            # Standard MLT format
            # Producers are already added in the first loop
            
            # Add playlists
            for playlist in self.playlists.values():
                root.append(playlist.to_xml())
                
            # If we have filters or transitions, wrap in a tractor
            if self.filters or self.transitions:
                tractor = ET.SubElement(root, "tractor", {"id": "tractor0"})
                # Add tracks (all playlists)
                for playlist_id in self.playlists:
                    ET.SubElement(tractor, "track", {"producer": playlist_id})
                
                # Add filters
                for filter_obj in self.filters:
                    tractor.append(filter_obj.to_xml())
                
                # Add transitions
                for transition_obj in self.transitions:
                    tractor.append(transition_obj.to_xml())

        # Pretty-print XML with proper declaration
        xml_str = ET.tostring(root, encoding="utf-8").decode('utf-8')
        dom = minidom.parseString(xml_str.encode('utf-8'))
        xml_output = dom.toprettyxml(indent="  ")
        if '<?xml' in xml_output:
            xml_output = xml_output.replace('<?xml version="1.0" ?>', "<?xml version='1.0' encoding='utf-8'?>")
            xml_output = xml_output.replace('<?xml version="1.0" encoding="UTF-8"?>', "<?xml version='1.0' encoding='utf-8'?>")
        # Unescape quotes in text content (minidom escapes them but Kdenlive expects raw quotes)
        xml_output = xml_output.replace("&quot;", '"')
        return xml_output

    def save(
        self,
        file_path: str,
        kdenlive_format: bool = False,
        root_path: str | None = None,
    ) -> None:
        """Save the project to an MLT XML file.

        Args:
            file_path: Path to output file
            kdenlive_format: Use Kdenlive-specific format (.kdenlive)
            root_path: Root path for media files (Kdenlive format)
        """
        xml_content = self.to_xml(kdenlive_format=kdenlive_format, root_path=root_path)
        Path(file_path).write_text(xml_content, encoding="utf-8")

    @classmethod
    def load(cls, file_path: str) -> "MLTProject":
        """Load a project from an MLT XML file.

        Args:
            file_path: Path to MLT XML file

        Returns:
            MLTProject object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If XML is invalid
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        tree = ET.parse(file_path)
        root = tree.getroot()

        if root.tag != "mlt":
            raise ValueError("Not a valid MLT XML file")

        version = root.get("version", "7.0.0")

        profile_elem = root.find("profile")
        if profile_elem is not None:
            profile = Profile.from_xml(profile_elem.attrib)
        else:
            profile = Profile.hd1080_30()

        project = cls(profile=profile, version=version)

        for elem in root.findall("producer"):
            producer = Producer.from_xml(elem)
            project.producers[producer.id] = producer

        for elem in root.findall("playlist"):
            playlist = Playlist.from_xml(elem)
            project.playlists[playlist.id] = playlist

        for tractor in root.findall("tractor"):
            project.tractor_id = tractor.get("id", "tractor0")

            for filter_elem in tractor.findall("filter"):
                project.filters.append(Filter.from_xml(filter_elem))

            for trans_elem in tractor.findall("transition"):
                project.transitions.append(Transition.from_xml(trans_elem))

            properties: dict[str, str] = {}
            for prop in tractor.findall("property"):
                name = prop.get("name", "")
                if name.startswith("kdenlive:"):
                    properties[name] = prop.text or ""
            if properties:
                project.kdenlive = KdenliveProperties.from_xml_properties(properties)

        return project

    def __repr__(self) -> str:
        return (
            f"MLTProject(profile='{self.profile.name}', "
            f"producers={len(self.producers)}, "
            f"tracks={len(self.playlists)})"
        )

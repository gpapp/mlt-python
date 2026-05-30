"""Generate sample Kdenlive-compatible MLT XML files for testing.

This test module creates various sample project files in tests/output/
that can be opened directly in Kdenlive for manual testing.

Run with: uv run pytest tests/test_kdenlive_samples.py -v
"""

from pathlib import Path
import pytest

from mlt_python import MLTProject
from mlt_python.filter import Filter, Filters
from mlt_python.kdenlive import KdenliveMetadata

# Test data paths
TEST_DATA_DIR = Path("C:\\Users\\gerge\\source\\repos\\video-processing-tool\\test_data")
VIDEO_FILE = TEST_DATA_DIR / "2026-04-04 10-15-15_truncated.mkv"
AUDIO_1 = TEST_DATA_DIR / "2026-04-04--t08-13-10am--5e73b6ace3b63000158e6774--statler.mp3"
AUDIO_2 = TEST_DATA_DIR / "2026-04-04--t08-13-10am--615e0811aa193a007ec6f9b7--gaganetz_gmail_com.mp3"

# Output directory
OUTPUT_DIR = Path(__file__).parent / "output"


def setup_module() -> None:
    """Create output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)


def _create_base_project(name: str = "Test Project") -> MLTProject:
    """Create a base project with Kdenlive properties."""
    project = MLTProject(profile="hd1080_30")
    project.kdenlive.set_doc_property(KdenliveMetadata.DOC_VERSION, "1.1")
    project.kdenlive.set_doc_property(KdenliveMetadata.DOC_PROFILE, "hd1080_30")
    project.kdenlive.set_doc_property(KdenliveMetadata.DOC_WIDTH, "1920")
    project.kdenlive.set_doc_property(KdenliveMetadata.DOC_HEIGHT, "1080")
    project.kdenlive.set_doc_property(KdenliveMetadata.DOC_FPS, "30")
    return project


class TestSampleFiles:
    """Generate sample Kdenlive XML files for testing."""

    def test_01_empty_project(self) -> None:
        """Create an empty MLT project with empty timeline."""
        project = _create_base_project("Empty Project")
        project.add_track(track_type="audio", id="playlist0")
        project.add_track(track_type="audio", id="playlist2")
        project.add_track(track_type="video", id="playlist4")
        project.add_track(track_type="video", id="playlist6")
        output_path = OUTPUT_DIR / "01_empty.kdenlive"
        project.save(str(output_path), kdenlive_format=True, root_path=str(TEST_DATA_DIR))
        assert output_path.exists()

    def test_02_filled_bin(self) -> None:
        """Create a project with all media files in bin, empty timeline."""
        project = _create_base_project("Filled Bin Project")
        project.add_producer(str(VIDEO_FILE), id="video_producer")
        project.add_producer(str(AUDIO_1), id="audio1_producer")
        project.add_producer(str(AUDIO_2), id="audio2_producer")
        project.kdenlive.set_clip_property("video_producer", "type", KdenliveMetadata.TYPE_VIDEO)
        project.kdenlive.set_clip_property("video_producer", "name", "truncated.mkv")
        project.kdenlive.set_clip_property("audio1_producer", "type", KdenliveMetadata.TYPE_AUDIO)
        project.kdenlive.set_clip_property("audio1_producer", "name", "statler.mp3")
        project.kdenlive.set_clip_property("audio2_producer", "type", KdenliveMetadata.TYPE_AUDIO)
        project.kdenlive.set_clip_property("audio2_producer", "name", "gaganetz.mp3")
        project.add_track(track_type="audio", id="playlist0")
        project.add_track(track_type="audio", id="playlist2")
        project.add_track(track_type="video", id="playlist4")
        project.add_track(track_type="video", id="playlist6")
        output_path = OUTPUT_DIR / "02_filled_bin.kdenlive"
        project.save(str(output_path), kdenlive_format=True, root_path=str(TEST_DATA_DIR))
        assert output_path.exists()

    def test_03_audio_compression(self) -> None:
        """Create a project with compression filter on audio producers, no timeline."""
        project = _create_base_project("Audio Compression Project")
        audio1 = project.add_producer(str(AUDIO_1), id="audio1")
        audio2 = project.add_producer(str(AUDIO_2), id="audio2")
        project.kdenlive.set_clip_property("audio1", "type", KdenliveMetadata.TYPE_AUDIO)
        project.kdenlive.set_clip_property("audio1", "name", "statler.mp3")
        project.kdenlive.set_clip_property("audio2", "type", KdenliveMetadata.TYPE_AUDIO)
        project.kdenlive.set_clip_property("audio2", "name", "gaganetz.mp3")

        compressor1 = Filter(mlt_service="avfilter.compand", properties={
            "av.attacks": "0",
            "av.decays": "0.8",
            "av.soft-knee": "0.01"
        })
        audio1.add_filter(compressor1)

        loudness1 = Filter(mlt_service="dynamic_loudness", properties={
            "target_loudness": "-23",
            "window": "3"
        })
        audio1.add_filter(loudness1)

        project.add_track(track_type="audio", id="playlist0")
        project.add_track(track_type="audio", id="playlist2")
        project.add_track(track_type="video", id="playlist4")
        project.add_track(track_type="video", id="playlist6")
        output_path = OUTPUT_DIR / "03_audio_compression.kdenlive"
        project.save(str(output_path), kdenlive_format=True, root_path=str(TEST_DATA_DIR))
        assert output_path.exists()

    def test_04_video_timeline(self) -> None:
        """Create a project with video on the timeline."""
        project = _create_base_project("Video Timeline Project")
        video = project.add_producer(str(VIDEO_FILE), id="video")
        project.kdenlive.set_clip_property("video", "type", KdenliveMetadata.TYPE_VIDEO)
        project.kdenlive.set_clip_property("video", "name", "truncated.mkv")
        project.add_track(track_type="audio", id="playlist0")
        project.add_track(track_type="audio", id="playlist2")
        video_track = project.add_track(track_type="video", id="playlist4")
        project.add_track(track_type="video", id="playlist6")
        project.add_clip("playlist4", "video", start=0.0)
        output_path = OUTPUT_DIR / "04_video_timeline.kdenlive"
        project.save(str(output_path), kdenlive_format=True, root_path=str(TEST_DATA_DIR))
        assert output_path.exists()

    def test_05_audio_separate_tracks(self) -> None:
        """Create a project with audio files on separate tracks."""
        project = _create_base_project("Audio Separate Tracks Project")
        audio1 = project.add_producer(str(AUDIO_1), id="audio1")
        audio2 = project.add_producer(str(AUDIO_2), id="audio2")
        project.kdenlive.set_clip_property("audio1", "type", KdenliveMetadata.TYPE_AUDIO)
        project.kdenlive.set_clip_property("audio1", "name", "statler.mp3")
        project.kdenlive.set_clip_property("audio2", "type", KdenliveMetadata.TYPE_AUDIO)
        project.kdenlive.set_clip_property("audio2", "name", "gaganetz.mp3")
        track1 = project.add_track(track_type="audio", id="playlist0")
        track2 = project.add_track(track_type="audio", id="playlist2")
        project.add_track(track_type="video", id="playlist4")
        project.add_track(track_type="video", id="playlist6")
        project.add_clip("playlist0", "audio1", start=0.0)
        project.add_clip("playlist2", "audio2", start=0.0)
        output_path = OUTPUT_DIR / "05_audio_separate_tracks.kdenlive"
        project.save(str(output_path), kdenlive_format=True, root_path=str(TEST_DATA_DIR))
        assert output_path.exists()

    def test_06_alternating_segments(self) -> None:
        """Create a project with alternating audio segments and video on top."""
        project = _create_base_project("Alternating Segments Project")
        video = project.add_producer(str(VIDEO_FILE), id="video")
        audio1 = project.add_producer(str(AUDIO_1), id="audio1")
        audio2 = project.add_producer(str(AUDIO_2), id="audio2")
        project.kdenlive.set_clip_property("video", "type", KdenliveMetadata.TYPE_VIDEO)
        project.kdenlive.set_clip_property("video", "name", "truncated.mkv")
        project.kdenlive.set_clip_property("audio1", "type", KdenliveMetadata.TYPE_AUDIO)
        project.kdenlive.set_clip_property("audio1", "name", "statler.mp3")
        project.kdenlive.set_clip_property("audio2", "type", KdenliveMetadata.TYPE_AUDIO)
        project.kdenlive.set_clip_property("audio2", "name", "gaganetz.mp3")

        for audio_prod in [audio1, audio2]:
            audio_prod.add_filter(Filter(mlt_service="avfilter.compand", properties={
                "av.attacks": "0", "av.decays": "0.8", "av.soft-knee": "0.01"
            }))
            audio_prod.add_filter(Filter(mlt_service="dynamic_loudness", properties={
                "target_loudness": "-23", "window": "3"
            }))

        project.add_track(track_type="audio", id="playlist0")
        project.add_track(track_type="audio", id="playlist2")
        project.add_track(track_type="video", id="playlist4")
        project.add_track(track_type="video", id="playlist6")

        # Create 6 minutes of segments (alternating every minute)
        segments = [
            (0.0, 60.0),
            (60.0, 120.0),
            (120.0, 180.0),
            (180.0, 240.0),
            (240.0, 300.0),
            (300.0, 360.0),
        ]

        # Add video clip for the entire 6 minutes
        project.add_clip("playlist4", "video", start=0.0, duration=360.0)

        # Add alternating audio clips with blanks to maintain synchronization
        for i, (start, end) in enumerate(segments):
            if i % 2 == 0:
                project.add_clip("playlist0", "audio1", start=start, end=end)
                project.playlists["playlist2"].add_blank(60.0)
            else:
                project.add_clip("playlist2", "audio2", start=start, end=end)
                project.playlists["playlist0"].add_blank(60.0)

        output_path = OUTPUT_DIR / "06_alternating_segments.kdenlive"
        project.save(str(output_path), kdenlive_format=True, root_path=str(TEST_DATA_DIR))
        assert output_path.exists()

    def test_07_add_markers(self) -> None:
        """Load the file from test 6 and add markers, then save as copy."""
        input_path = OUTPUT_DIR / "06_alternating_segments.kdenlive"
        assert input_path.exists(), "test_06 output file not found"

        project = MLTProject.load(str(input_path))

        assert len(project.sequence_markers) == 0
        assert len(project.clip_markers) == 0

        # Add sequence markers (timeline guides) in seconds
        project.add_marker(60.0, comment="Minute 1", marker_type=1)
        project.add_marker(180.0, comment="Minute 3", marker_type=2)
        project.add_marker(360.0, comment="End", marker_type=3)

        # Add clip markers to audio producers
        project.add_marker(30.0, comment="Audio1 highlight", producer_id="audio1")
        project.add_marker(150.0, comment="Audio2 highlight", producer_id="audio2")

        assert len(project.sequence_markers) == 3
        assert "audio1" in project.clip_markers
        assert "audio2" in project.clip_markers
        assert len(project.clip_markers["audio1"]) == 1
        assert len(project.clip_markers["audio2"]) == 1

        output_path = OUTPUT_DIR / "07_with_markers.kdenlive"
        project.save(str(output_path), kdenlive_format=True, root_path=str(TEST_DATA_DIR))
        assert output_path.exists()

        # Load the copy and verify markers persist
        copied = MLTProject.load(str(output_path))
        assert len(copied.sequence_markers) == 3
        assert copied.sequence_markers[0].comment == "Minute 1"
        assert abs(copied.sequence_markers[0].pos - 60.0) < 0.01  # 60s at 30fps
        assert "audio1" in copied.clip_markers
        assert copied.clip_markers["audio1"][0].comment == "Audio1 highlight"
        assert "audio2" in copied.clip_markers
        assert copied.clip_markers["audio2"][0].comment == "Audio2 highlight"

    def test_filter_id_continuity(self) -> None:
        """Test that filter IDs are unique and form a continuous sequence."""
        import xml.etree.ElementTree as ET

        project = _create_base_project("Filter ID Continuity Test")

        project.add_producer(str(VIDEO_FILE), id="video1")
        project.add_producer(str(AUDIO_1), id="audio1")
        project.add_producer(str(AUDIO_2), id="audio2")

        project.add_track(track_type="audio", id="playlist0")
        project.add_track(track_type="video", id="playlist2")
        project.add_track(track_type="audio", id="playlist4")
        project.add_track(track_type="video", id="playlist6")

        project.add_clip("playlist0", "audio1", start=0.0)
        project.add_clip("playlist4", "audio2", start=0.0)
        project.add_clip("playlist2", "video1", start=0.0)

        output_path = OUTPUT_DIR / "test_filter_continuity.kdenlive"
        project.save(str(output_path), kdenlive_format=True, root_path=str(TEST_DATA_DIR))

        tree = ET.parse(output_path)
        root = tree.getroot()

        filter_ids = []
        for filter_elem in root.iter("filter"):
            filter_id_str = filter_elem.get("id", "")
            if filter_id_str.startswith("filter"):
                filter_ids.append(int(filter_id_str[6:]))

        assert len(filter_ids) == len(set(filter_ids)), \
            f"Duplicate filter IDs found! IDs: {sorted(filter_ids)}"

        filter_ids_sorted = sorted(filter_ids)
        expected = list(range(len(filter_ids_sorted)))
        assert filter_ids_sorted == expected, \
            f"Filter IDs are not continuous. Expected {expected}, got {filter_ids_sorted}"

    def test_required_kdenlive_elements(self) -> None:
        """Test that required Kdenlive elements are present."""
        import xml.etree.ElementTree as ET

        project = _create_base_project("Empty Project")
        project.add_track(track_type="audio", id="playlist0")
        project.add_track(track_type="audio", id="playlist2")
        project.add_track(track_type="video", id="playlist4")
        project.add_track(track_type="video", id="playlist6")

        output_path = OUTPUT_DIR / "01_empty.kdenlive"
        project.save(str(output_path), kdenlive_format=True, root_path=str(TEST_DATA_DIR))

        tree = ET.parse(output_path)
        root = tree.getroot()

        xml_retain_found = False
        for playlist in root.iter("playlist"):
            if playlist.get("id") == "main_bin":
                for prop in playlist.iter("property"):
                    if prop.get("name") == "xml_retain" and prop.text == "1":
                        xml_retain_found = True
                        break
        assert xml_retain_found, "Missing xml_retain property in main_bin playlist"

        entry_found = False
        for playlist in root.iter("playlist"):
            if playlist.get("id") == "main_bin":
                for entry in playlist.iter("entry"):
                    if entry.get("producer") and entry.get("in") == "00:00:00.000":
                        entry_found = True
                        break
        assert entry_found, "Missing entry element in main_bin playlist"

        project_tractor_found = False
        project_tractor_id = None
        track_with_uuid_found = False

        seq_uuid = None
        for tractor in root.iter("tractor"):
            for prop in tractor.iter("property"):
                if prop.get("name") == "kdenlive:uuid":
                    seq_uuid = prop.text
                    break
            if seq_uuid:
                break

        assert seq_uuid is not None, "Could not find sequence UUID"

        for tractor in root.iter("tractor"):
            for prop in tractor.iter("property"):
                if prop.get("name") == "kdenlive:projectTractor" and prop.text == "1":
                    project_tractor_found = True
                    project_tractor_id = tractor.get("id")
                    for track in tractor.iter("track"):
                        if track.get("producer") == seq_uuid:
                            track_with_uuid_found = True
                            break
                    break
            if project_tractor_found:
                break

        assert project_tractor_found, "Missing tractor with kdenlive:projectTractor=1"
        assert track_with_uuid_found, f"Missing track with sequence UUID {seq_uuid} in {project_tractor_id}"

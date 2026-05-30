"""Tests for project module."""

import pytest
from mlt_python.project import MLTProject
from mlt_python.profile import Profile


class TestMLTProject:
    """Test suite for MLTProject class."""

    def test_create_project(self) -> None:
        """Test basic project creation."""
        project = MLTProject(profile="hd1080_30")
        assert project.profile.name == "hd1080_30"
        assert len(project.producers) == 0
        assert len(project.playlists) == 0

    def test_add_producer(self) -> None:
        """Test adding producer to bin."""
        project = MLTProject()
        producer = project.add_producer("video.mp4", id="vid1")
        assert "vid1" in project.producers
        assert producer.resource == "video.mp4"

    def test_add_track(self) -> None:
        """Test adding tracks."""
        project = MLTProject()
        track = project.add_track("video", id="playlist0")
        assert "playlist0" in project.playlists
        assert track.id == "playlist0"

    def test_add_clip(self) -> None:
        """Test adding clip using float seconds."""
        project = MLTProject(profile="hd1080_30")
        project.add_producer("video.mp4", id="vid1")
        project.add_track("video", id="playlist0")

        project.add_clip(
            track_id="playlist0",
            producer_id="vid1",
            start=0.0,
            duration=10.0,
        )

        track = project.playlists["playlist0"]
        assert len(track.clips) == 1

    def test_add_filter(self) -> None:
        """Test adding filter."""
        project = MLTProject()
        filter_obj = project.add_filter(
            mlt_service="greyscale",
            track=0,
            start=5.0,
            duration=5.0,
        )
        assert len(project.filters) == 1
        assert filter_obj.mlt_service == "greyscale"

    def test_add_transition(self) -> None:
        """Test adding transition."""
        project = MLTProject()
        transition = project.add_transition(
            mlt_service="luma",
            a_track=0,
            b_track=1,
            start=10.0,
            duration=2.0,
        )
        assert len(project.transitions) == 1
        assert transition.mlt_service == "luma"

    def test_save_and_load(self, tmp_path) -> None:
        """Test saving and loading project."""
        project = MLTProject(profile="hd1080_30")
        project.add_producer("video.mp4", id="vid1")
        project.add_track("video", id="playlist0")
        project.add_clip("playlist0", "vid1", start=0.0, duration=10.0)

        file_path = tmp_path / "test.kdenlive.xml"
        project.save(str(file_path))

        loaded = MLTProject.load(str(file_path))
        assert loaded.profile.name == project.profile.name
        assert len(loaded.producers) == len(project.producers)
        assert len(loaded.playlists) == len(project.playlists)

    def test_add_markers_and_save_copy(self, tmp_path) -> None:
        """Test loading a project, adding markers, and saving as a copy."""
        # Create and save initial project
        project = MLTProject(profile="hd1080_30")
        project.add_producer("video.mp4", id="vid1")
        project.add_track("video", id="playlist0")
        project.add_clip("playlist0", "vid1", start=0.0, duration=10.0)

        file_path = tmp_path / "test.kdenlive.xml"
        project.save(str(file_path))

        # Load the project
        loaded = MLTProject.load(str(file_path))
        assert len(loaded.sequence_markers) == 0
        assert len(loaded.clip_markers) == 0

        # Add sequence markers (timeline guides) in seconds
        loaded.add_marker(2.0, comment="Intro starts", marker_type=1)
        loaded.add_marker(5.0, comment="Middle point", marker_type=2)

        # Add clip marker
        loaded.add_marker(1.0, comment="Clip highlight", producer_id="vid1")

        # Verify markers were added
        assert len(loaded.sequence_markers) == 2
        assert "vid1" in loaded.clip_markers
        assert len(loaded.clip_markers["vid1"]) == 1

        # Save as a copy (use kdenlive_format to save markers)
        copy_path = tmp_path / "test_with_markers.kdenlive.xml"
        loaded.save(str(copy_path), kdenlive_format=True)

        # Load the copy and verify markers persist
        copied = MLTProject.load(str(copy_path))
        assert len(copied.sequence_markers) == 2
        assert copied.sequence_markers[0].comment == "Intro starts"
        # Pos stored as seconds, at 30fps: 2s = 60 frames -> round(60/30*30)/30 = 2.0
        assert abs(copied.sequence_markers[0].pos - 2.0) < 0.01
        assert "vid1" in copied.clip_markers
        assert len(copied.clip_markers["vid1"]) == 1
        assert copied.clip_markers["vid1"][0].comment == "Clip highlight"

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

    def test_add_clip_with_timecode(self) -> None:
        """Test adding clip using timecodes."""
        project = MLTProject(profile="hd1080_30")
        project.add_producer("video.mp4", id="vid1")
        project.add_track("video", id="playlist0")

        project.add_clip(
            track_id="playlist0",
            producer_id="vid1",
            start="00:00:00:00",
            duration="00:00:10:00",
        )

        track = project.playlists["playlist0"]
        assert len(track.clips) == 1
        assert isinstance(track.clips[0], __import__("mlt_python.clip", fromlist=["Clip"]).Clip)

    def test_add_filter(self) -> None:
        """Test adding filter."""
        project = MLTProject()
        filter_obj = project.add_filter(
            mlt_service="greyscale",
            track=0,
            start="00:00:05:00",
            duration="00:00:05:00",
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
            start="00:00:10:00",
            duration="00:00:02:00",
        )
        assert len(project.transitions) == 1
        assert transition.mlt_service == "luma"

    def test_save_and_load(self, tmp_path) -> None:
        """Test saving and loading project."""
        project = MLTProject(profile="hd1080_30")
        project.add_producer("video.mp4", id="vid1")
        project.add_track("video", id="playlist0")
        project.add_clip("playlist0", "vid1", start="00:00:00:00", duration="00:00:10:00")

        file_path = tmp_path / "test.kdenlive.xml"
        project.save(str(file_path))

        loaded = MLTProject.load(str(file_path))
        assert loaded.profile.name == project.profile.name
        assert len(loaded.producers) == len(project.producers)
        assert len(loaded.playlists) == len(project.playlists)

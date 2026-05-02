"""Tests for subtitle module."""

import pytest
from mlt_python.subtitle import SubtitleItem, SRTFile, SubtitleTrack


class TestSubtitleItem:
    """Test suite for SubtitleItem class."""

    def test_create_subtitle(self) -> None:
        """Test creating a subtitle item."""
        item = SubtitleItem(
            start_time="00:00:10,500",
            end_time="00:00:13,250",
            text="Hello World",
            index=1,
        )
        assert item.start_time == "00:00:10,500"
        assert item.text == "Hello World"

    def test_to_srt_string(self) -> None:
        """Test SRT string generation."""
        item = SubtitleItem(
            start_time="00:00:10,500",
            end_time="00:00:13,250",
            text="Hello World",
            index=1,
        )
        srt = item.to_srt_string()
        assert "1" in srt
        assert "00:00:10,500 --> 00:00:13,250" in srt
        assert "Hello World" in srt


class TestSRTFile:
    """Test suite for SRTFile class."""

    def test_create_from_dict(self, tmp_path) -> None:
        """Test creating SRT file from dictionary."""
        subtitles = [
            {"start": "00:00:00,000", "end": "00:00:05,000", "text": "First subtitle"},
            {"start": "00:00:05,500", "end": "00:00:10,000", "text": "Second subtitle"},
        ]
        srt_path = str(tmp_path / "test.srt")
        items = SRTFile.create_from_dict(subtitles, srt_path)

        assert len(items) == 2
        assert items[0].text == "First subtitle"

    def test_parse_srt(self, tmp_path) -> None:
        """Test parsing SRT file."""
        srt_path = str(tmp_path / "test.srt")
        srt_content = """1
00:00:00,000 --> 00:00:05,000
First subtitle

2
00:00:05,500 --> 00:00:10,000
Second subtitle
"""
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        items = SRTFile.parse(srt_path)
        assert len(items) == 2
        assert items[0].text == "First subtitle"
        assert items[1].start_time == "00:00:05,500"


class TestSubtitleTrack:
    """Test suite for SubtitleTrack class."""

    def test_create_subtitle_track(self) -> None:
        """Test creating a subtitle track."""
        track = SubtitleTrack(
            resource="subtitles.srt",
            track=0,
            start_frame=0,
            end_frame=1000,
        )
        assert track.resource == "subtitles.srt"
        assert track.track == 0

    def test_to_filter_xml(self) -> None:
        """Test generating filter XML."""
        track = SubtitleTrack(
            resource="subtitles.srt",
            track=0,
        )
        elem = track.to_filter_xml()
        assert elem.tag == "filter"
        assert elem.get("mlt_service") == "subtitle"

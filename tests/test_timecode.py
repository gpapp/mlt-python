"""Tests for timecode module."""

import pytest
from mlt_python.timecode import Timecode


class TestTimecode:
    """Test suite for Timecode class."""

    def test_from_string(self) -> None:
        """Test parsing timecode string."""
        tc = Timecode.from_string("01:30:25:15", 30.0)
        assert tc.hours == 1
        assert tc.minutes == 30
        assert tc.seconds == 25
        assert tc.frames == 15
        assert tc.fps == 30.0

    def test_to_frames(self) -> None:
        """Test conversion to frames."""
        tc = Timecode.from_string("00:00:10:00", 30.0)
        assert tc.to_frames() == 300

        tc2 = Timecode.from_string("01:00:00:00", 30.0)
        assert tc2.to_frames() == 3600 * 30

    def test_from_frames(self) -> None:
        """Test creating timecode from frame number."""
        tc = Timecode.from_frames(300, 30.0)
        assert tc.to_string() == "00:00:10:00"

    def test_add_frames(self) -> None:
        """Test adding frames to timecode."""
        tc = Timecode.from_string("00:00:10:00", 30.0)
        tc2 = tc + 30
        assert tc2.to_string() == "00:00:11:00"

    def test_subtract_frames(self) -> None:
        """Test subtracting frames from timecode."""
        tc = Timecode.from_string("00:00:10:00", 30.0)
        tc2 = tc - 30
        assert tc2.to_string() == "00:00:09:00"

    def test_equality(self) -> None:
        """Test timecode equality."""
        tc1 = Timecode.from_string("00:00:10:00", 30.0)
        tc2 = Timecode.from_frames(300, 30.0)
        assert tc1 == tc2

    def test_invalid_format(self) -> None:
        """Test invalid timecode format."""
        with pytest.raises(ValueError):
            Timecode.from_string("invalid", 30.0)

    def test_negative_frames(self) -> None:
        """Test negative frame number."""
        with pytest.raises(ValueError):
            Timecode.from_frames(-1, 30.0)

"""Tests for timecode module."""

import pytest
from mlt_python.timecode import Timecode


class TestTimecode:
    """Test suite for Timecode class."""

    def test_from_string_mmm(self) -> None:
        """Test parsing HH:MM:SS.mmm timecode."""
        tc = Timecode.from_string("01:30:25.500")
        assert tc.hours == 1
        assert tc.minutes == 30
        assert tc.seconds == 25
        assert tc.milliseconds == 500

    def test_from_string_ff(self) -> None:
        """Test parsing HH:MM:SS:FF timecode (frame component ignored)."""
        tc = Timecode.from_string("01:30:25:15")
        assert tc.hours == 1
        assert tc.minutes == 30
        assert tc.seconds == 25
        assert tc.milliseconds == 0

    def test_from_seconds(self) -> None:
        """Test conversion from seconds."""
        tc = Timecode.from_seconds(10.0)
        assert tc.hours == 0
        assert tc.minutes == 0
        assert tc.seconds == 10
        assert tc.milliseconds == 0

    def test_from_seconds_with_ms(self) -> None:
        """Test conversion from seconds with milliseconds."""
        tc = Timecode.from_seconds(3725.750)
        assert tc.hours == 1
        assert tc.minutes == 2
        assert tc.seconds == 5
        assert tc.milliseconds == 750

    def test_to_seconds(self) -> None:
        """Test conversion to seconds."""
        tc = Timecode(0, 0, 10, 500)
        assert abs(tc.to_seconds() - 10.5) < 0.001

    def test_roundtrip(self) -> None:
        """Test seconds -> Timecode -> seconds roundtrip."""
        tc = Timecode.from_seconds(3725.750)
        assert abs(tc.to_seconds() - 3725.750) < 0.001

    def test_to_string(self) -> None:
        """Test formatting to HH:MM:SS.mmm."""
        tc = Timecode(1, 2, 5, 750)
        assert tc.to_string() == "01:02:05.750"

    def test_add(self) -> None:
        """Test adding two timecodes."""
        tc1 = Timecode.from_seconds(10.0)
        tc2 = Timecode.from_seconds(5.0)
        result = tc1 + tc2
        assert abs(result.to_seconds() - 15.0) < 0.001

    def test_add_seconds(self) -> None:
        """Test adding seconds to timecode."""
        tc = Timecode.from_seconds(10.0)
        result = tc + 5.0
        assert abs(result.to_seconds() - 15.0) < 0.001

    def test_subtract(self) -> None:
        """Test subtracting two timecodes."""
        tc1 = Timecode.from_seconds(10.0)
        tc2 = Timecode.from_seconds(3.0)
        result = tc1 - tc2
        assert abs(result.to_seconds() - 7.0) < 0.001

    def test_equality(self) -> None:
        """Test timecode equality (within 0.5ms tolerance)."""
        tc1 = Timecode.from_seconds(10.0)
        tc2 = Timecode.from_seconds(10.0)
        assert tc1 == tc2

    def test_inequality(self) -> None:
        """Test timecode inequality."""
        tc1 = Timecode.from_seconds(10.0)
        tc2 = Timecode.from_seconds(11.0)
        assert tc1 != tc2

    def test_ordering(self) -> None:
        """Test timecode ordering."""
        tc1 = Timecode.from_seconds(5.0)
        tc2 = Timecode.from_seconds(10.0)
        assert tc1 < tc2
        assert tc2 > tc1
        assert tc1 <= tc2
        assert tc2 >= tc1

    def test_invalid_format(self) -> None:
        """Test invalid timecode format."""
        with pytest.raises(ValueError):
            Timecode.from_string("invalid")

    def test_negative_seconds(self) -> None:
        """Test negative seconds raises error."""
        with pytest.raises(ValueError):
            Timecode.from_seconds(-1.0)

    def test_invalid_milliseconds(self) -> None:
        """Test milliseconds >= 1000 raises error."""
        with pytest.raises(ValueError):
            Timecode(0, 0, 0, 1000)

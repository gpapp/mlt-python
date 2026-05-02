"""Tests for profile module."""

import pytest
from mlt_python.profile import Profile


class TestProfile:
    """Test suite for Profile class."""

    def test_hd1080_30(self) -> None:
        """Test HD1080p 30fps profile."""
        p = Profile.hd1080_30()
        assert p.width == 1920
        assert p.height == 1080
        assert p.fps == 30.0
        assert p.frame_rate_num == 30
        assert p.frame_rate_den == 1

    def test_uhd_24(self) -> None:
        """Test UHD 24fps profile."""
        p = Profile.uhd_24()
        assert p.width == 3840
        assert p.height == 2160
        assert p.fps == 24.0

    def test_to_xml_attributes(self) -> None:
        """Test XML attributes generation."""
        p = Profile.hd1080_30()
        attrs = p.to_xml_attributes()
        assert attrs["width"] == "1920"
        assert attrs["height"] == "1080"
        assert attrs["frame_rate_num"] == "30"

    def test_from_xml(self) -> None:
        """Test creating profile from XML attributes."""
        attrs = {
            "name": "custom",
            "width": "1280",
            "height": "720",
            "frame_rate_num": "30",
            "frame_rate_den": "1",
        }
        p = Profile.from_xml(attrs)
        assert p.width == 1280
        assert p.height == 720
        assert p.fps == 30.0

    def test_fps_property(self) -> None:
        """Test fps property."""
        p = Profile.hd1080_2997()
        assert abs(p.fps - 29.97) < 0.01

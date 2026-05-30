import pytest
from mlt_python.marker import Marker, markers_to_json, markers_from_json

@pytest.fixture
def sample_marker():
    return Marker(pos=0.0, comment="Test Marker")

class TestMarker:
    def test_initialization(self, sample_marker):
        assert isinstance(sample_marker, Marker)
        assert sample_marker.pos == 0.0
        assert sample_marker.comment == "Test Marker"

    def test_from_timecode(self):
        # Test creation from timecode string (no fps needed)
        mc = Marker.from_timecode("00:00:00:00")
        assert mc.pos == 0.0
        assert mc.comment == "Marker"

        # Test with a different timecode (00:01:30:00 = 90 seconds)
        mc2 = Marker.from_timecode("00:01:30:00")
        assert abs(mc2.pos - 90.0) < 0.01

    def test_from_timecode_mmm(self):
        """Test creation from HH:MM:SS.mmm format."""
        mc = Marker.from_timecode("00:01:30.500")
        assert abs(mc.pos - 90.5) < 0.01

    def test_pos_timecode(self):
        # Test getting timecode from pos
        marker = Marker(pos=0.0, comment="Test")
        assert marker.pos_timecode() == "00:00:00.000"

        marker2 = Marker(pos=90.0, comment="Test")
        assert marker2.pos_timecode() == "00:01:30.000"

    def test_pos_timecode_with_ms(self):
        marker = Marker(pos=90.5, comment="Test")
        assert marker.pos_timecode() == "00:01:30.500"

    def test_update_comment(self, sample_marker):
        sample_marker.comment = "Updated Comment"
        assert sample_marker.comment == "Updated Comment"

class TestMarkerUtilities:
    def test_markers_to_json(self):
        # Create markers in seconds
        m1 = Marker(pos=1.0, comment="Start Point")  # 1 second
        m2 = Marker(pos=5.5, comment="Mid Point")   # 5.5 seconds
        markers = [m1, m2]

        # Convert to JSON string (default fps=30)
        json_str = markers_to_json(markers)

        # Check if the output is valid and contains expected data
        assert isinstance(json_str, str)
        import json
        data = json.loads(json_str)

        # At 30fps: 1s = 30 frames, 5.5s = 165 frames
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["pos"] == 30
        assert data[0]["comment"] == "Start Point"
        assert "type" in data[0]

    def test_markers_from_json(self):
        # Test converting from a sample JSON string (frame-based)
        sample_data = [
            {"pos": 300, "comment": "Loaded Start", "type": 0, "duration": 0},
            {"pos": 750, "comment": "Loaded End", "type": 0, "duration": 0}
        ]
        import json
        json_str = json.dumps(sample_data)

        # Convert JSON string back to list of Marker objects (default fps=30)
        markers = markers_from_json(json_str)

        assert isinstance(markers, list)
        assert len(markers) == 2
        assert abs(markers[0].pos - 10.0) < 0.01  # 300 frames / 30 fps = 10s
        assert markers[0].comment == "Loaded Start"
        assert abs(markers[1].pos - 25.0) < 0.01  # 750 frames / 30 fps = 25s

    def test_markers_to_json_with_fps(self):
        """Test markers_to_json with custom fps."""
        m = Marker(pos=10.0, comment="Test")
        json_str = markers_to_json([m], fps=25.0)
        import json
        data = json.loads(json_str)
        assert data[0]["pos"] == 250  # 10s * 25fps = 250 frames

class TestMarkerEdgeCases:
    def test_empty_lists(self):
        json_str = markers_to_json([])
        assert json_str == "[]"

        json_str_empty = "[]"
        markers = markers_from_json(json_str_empty)
        assert len(markers) == 0

    def test_marker_with_duration(self):
        # Test marker with duration in seconds
        m = Marker(pos=10.0, comment="Region", duration=2.5)
        assert m.duration == 2.5

        json_str = markers_to_json([m])
        import json
        data = json.loads(json_str)
        assert data[0]["duration"] == 75  # 2.5s * 30fps

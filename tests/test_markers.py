import pytest
from mlt_python.marker import Marker, markers_to_json, markers_from_json

@pytest.fixture
def sample_marker():
    return Marker(pos=0, comment="Test Marker")

class TestMarker:
    def test_initialization(self, sample_marker):
        assert isinstance(sample_marker, Marker)
        assert sample_marker.pos == 0
        assert sample_marker.comment == "Test Marker"

    def test_from_timecode(self):
        # Test creation from timecode string with fps (format: HH:MM:SS:FF)
        mc = Marker.from_timecode("00:00:00:00", fps=30.0)
        assert mc.pos == 0
        assert mc.comment == "Marker"

        # Test with a different timecode (00:01:30:00 = 90 seconds * 30 fps = 2700 frames)
        mc2 = Marker.from_timecode("00:01:30:00", fps=30.0)
        assert mc2.pos == 2700

    def test_pos_timecode(self):
        # Test getting timecode from pos
        marker = Marker(pos=0, comment="Test")
        assert marker.pos_timecode(30.0) == "00:00:00:00"

        marker2 = Marker(pos=2700, comment="Test")
        assert marker2.pos_timecode(30.0) == "00:01:30:00"

    def test_update_comment(self, sample_marker):
        # Test updating the comment (direct attribute assignment)
        sample_marker.comment = "Updated Comment"
        assert sample_marker.comment == "Updated Comment"

class TestMarkerUtilities:
    def test_markers_to_json(self):
        # Create markers
        m1 = Marker(pos=30, comment="Start Point")  # 1 second at 30fps
        m2 = Marker(pos=165, comment="Mid Point")   # 5.5 seconds at 30fps
        markers = [m1, m2]

        # Convert to JSON string
        json_str = markers_to_json(markers)
        
        # Check if the output is valid and contains expected data
        assert isinstance(json_str, str)
        import json
        data = json.loads(json_str)
        
        # Check structure: should be a list of dicts with 'pos' key
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["pos"] == 30
        assert data[0]["comment"] == "Start Point"
        assert "type" in data[0]

    def test_markers_from_json(self):
        # Test converting from a sample JSON string (using 'pos' key)
        sample_data = [
            {"pos": 300, "comment": "Loaded Start", "type": 0, "duration": 0},
            {"pos": 750, "comment": "Loaded End", "type": 0, "duration": 0}
        ]
        import json
        json_str = json.dumps(sample_data)

        # Convert JSON string back to list of Marker objects
        markers = markers_from_json(json_str)

        assert isinstance(markers, list)
        assert len(markers) == 2
        assert markers[0].pos == 300
        assert markers[0].comment == "Loaded Start"
        assert markers[1].pos == 750

class TestMarkerEdgeCases:
    def test_empty_lists(self):
        # Empty list to JSON
        json_str = markers_to_json([])
        assert json_str == "[]"

        # Empty JSON to list
        json_str_empty = "[]"
        markers = markers_from_json(json_str_empty)
        assert len(markers) == 0

    def test_marker_with_duration(self):
        # Test marker with duration
        m = Marker(pos=100, comment="Region", duration=50)
        assert m.duration == 50
        
        json_str = markers_to_json([m])
        import json
        data = json.loads(json_str)
        assert data[0]["duration"] == 50

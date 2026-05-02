# MLT XML Library for Kdenlive

A pure Python library for creating, modifying, and parsing MLT XML files compatible with Kdenlive.

## Features

- **Pure Python** - No MLT framework dependency, direct XML manipulation
- **Timecode API** - All public methods accept `HH:MM:SS:FF` format
- **Frame Alignment** - Library automatically converts timecodes to frame numbers
- **Media Management** - Add/modify/delete audio/video files in the bin
- **Timeline Editing** - Add clips, tracks, filters, and transitions
- **Subtitle Support** - External SRT file references
- **Kdenlive Compatible** - Generates XML that Kdenlive can open

## Installation

### Using uv (recommended)

```bash
uv pip install mlt-python
```

### Using pip

```bash
pip install mlt-python
```

### For development

```bash
git clone https://github.com/gpapp/mlt-python.git
cd mlt-python
uv sync
```

## Quick Start

```python
from mlt_python import MLTProject

# Create a new project
project = MLTProject(profile="hd1080_30")

# Add media to bin
video = project.add_producer("video.mp4", id="vid1")

# Add a video track
track = project.add_track("video", id="playlist0")

# Add a clip using timecodes
project.add_clip(
    track_id="playlist0",
    producer_id="vid1",
    start="00:00:00:00",
    duration="00:00:10:00"
)

# Add subtitles from SRT file
project.add_subtitle("subtitles.srt", track=0, start="00:00:00:00")

# Save to file
project.save("project.kdenlive.xml")
```

## Supported Operations

### Producers (Media Bin)
- `add_producer()` - Add video/audio/image to bin
- `remove_producer()` - Remove from bin
- `get_producer()` - Get producer by ID

### Tracks (Playlists)
- `add_track()` - Add video/audio track
- `remove_track()` - Remove track
- `add_clip()` - Add clip to track using timecodes

### Filters & Effects
- `add_filter()` - Add filter to project/track
- Built-in filters: `Filters.greyscale()`, `Filters.volume()`, `Filters.watermark()`

### Transitions
- `add_transition()` - Add transition between tracks
- Built-in transitions: `Transitions.luma()`, `Transitions.mix()`, `Transitions.composite()`

### Subtitles
- `add_subtitle()` - Add subtitles from SRT file
- `SRTFile` - Utility class for reading/writing SRT files

## Profile Presets

- `hd1080_30` - Full HD 1080p @ 30fps
- `hd1080_2997` - Full HD 1080p @ 29.97fps
- `hd1080_25` - Full HD 1080p @ 25fps (PAL)
- `hd1080_24` - Full HD 1080p @ 24fps
- `hd720_30` - HD 720p @ 30fps
- `uhd_30` - 4K UHD @ 30fps
- `uhd_24` - 4K UHD @ 24fps
- `sdtv_ntsc` - SD NTSC 480i
- `sdtv_pal` - SD PAL 576i

## Example

See `examples/example.py` for a complete example showing:
- Multiple video/audio tracks
- B-roll with transitions
- Audio mixing
- Subtitle integration
- Filter effects

## Running Tests

```bash
uv run pytest tests/ -v
```

## License

MIT License - see LICENSE file for details

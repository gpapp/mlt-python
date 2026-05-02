# MLT XML & Kdenlive Compatibility Reference

This document outlines the specific MLT XML structures and requirements for compatibility with Kdenlive 23.08+, as implemented in this library.

## Core MLT Elements

### 1. Root Element (`<mlt>`)
- **Version**: Usually `7.x.x`.
- **Kdenlive Specifics**:
    - `LC_NUMERIC="en_US.UTF-8"` is required for consistent float parsing.
    - `producer="main_bin"` attribute points to the project's asset bin.

### 2. Profile (`<profile>`)
- Defines frame rate, dimensions, and aspect ratio.
- Kdenlive expects `colorspace="709"` for HD/UHD projects.

### 3. Producers and Chains
- **Producers**: Generic MLT sources.
- **Chains**: Specialized producers (usually `avformat-novalidate`) that handle media files.
- **Filters on Producers**: Kdenlive supports filters directly inside `<chain>` or `<producer>` elements for "bin-level" effects.

### 4. Playlists
- Ordered collections of `<entry>` (media) and `<blank>` (silence/empty space) elements.
- **Main Bin**: A specialized `<playlist id="main_bin">` that contains all project assets.
    - **CRITICAL**: In Kdenlive 23.08+, all `<property>` tags in the bin playlist MUST be defined before any `<entry>` tags.

### 5. Tractors
- Used for layering tracks or applying effects to groups.
- **Sequence Tractor**: Represents the main timeline.
- **Project Tractor**: A wrapper tractor containing the sequence tractor, usually with `kdenlive:projectTractor="1"`.

## Kdenlive 23.08+ Timeline Structure

Kdenlive uses a nested tractor structure to manage audio/video separation on a single UI track.

### Track Hierarchy
Each UI track is represented as a `<tractor>` containing exactly two tracks:
1. `<track producer="playlist_v" hide="audio"/>`: Shows only the video components.
2. `<track producer="playlist_a" hide="video"/>`: Shows only the audio components.

### Track Blending
Every track tractor must be blended against the "background" track (track 0, usually a black color producer) in the main sequence tractor.

- **Audio Tracks**: Use the `mix` service.
    - Required properties: `always_active=1`, `sum=1`, `accepts_blanks=1`.
- **Video Tracks**: Use the `qtblend` service.
    - Required properties: `compositing=0`, `distort=0`, `rotate_center=0`, `always_active=1`.

## UUIDs and Identifiers
- **Sequence UUID**: Kdenlive identifies timelines via a UUID in `{curly-brackets}`.
- **Document UUID**: A global project UUID used in `main_bin` properties.
- **Kdenlive IDs**: Many elements (filters, transitions, bin entries) require a `kdenlive_id` property matching their MLT service name to show up correctly in the UI.

## Timecodes
- Kdenlive/MLT uses `HH:MM:SS.mmm` (milliseconds) for bin entries and some metadata.
- Frame-based offsets (`HH:MM:SS:FF`) are used for timeline positions.
- The library handles the conversion between these formats automatically.

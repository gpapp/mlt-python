"""Example usage of MLT XML library.

Demonstrates how to create a Kdenlive-compatible MLT XML file
with video, audio, filters, transitions, and subtitles using timecodes.
"""

from mlt_python import MLTProject, Profile, Timecode, Filters, Transitions, SRTFile


def main() -> None:
    """Create a sample Kdenlive project with the library."""

    # Create a new project with Full HD 1080p at 30fps
    print("Creating MLT project...")
    project = MLTProject(profile="hd1080_30")
    print(f"Project created: {project}\n")

    # Add media files to the bin (media library)
    print("Adding media to bin...")
    video1 = project.add_producer("interview.mp4", id="vid_interview")
    video2 = project.add_producer("b_roll.mp4", id="vid_broll")
    audio1 = project.add_producer("background_music.mp3", id="aud_music")
    audio2 = project.add_producer("interview_audio.wav", id="aud_interview")
    print(f"Added 4 media items to bin\n")

    # Create tracks (playlists)
    print("Creating tracks...")
    main_video = project.add_track("video", id="playlist_video_main")
    overlay_video = project.add_track("video", id="playlist_video_overlay")
    main_audio = project.add_track("audio", id="playlist_audio_main")
    music_track = project.add_track("audio", id="playlist_audio_music")
    print("Created 4 tracks (2 video, 2 audio)\n")

    # Add clips to video track 1 (main interview)
    print("Adding clips to timeline...")
    project.add_clip(
        track_id="playlist_video_main",
        producer_id="vid_interview",
        start="00:00:00:00",
        duration="00:02:00:00",  # 2 minutes
    )

    # Add b-roll overlay with transition
    project.add_clip(
        track_id="playlist_video_overlay",
        producer_id="vid_broll",
        start="00:00:30:00",
        duration="00:00:10:00",  # 10 seconds
    )

    # Add audio clips
    project.add_clip(
        track_id="playlist_audio_main",
        producer_id="aud_interview",
        start="00:00:00:00",
        duration="00:02:00:00",
    )

    project.add_clip(
        track_id="playlist_audio_music",
        producer_id="aud_music",
        start="00:00:00:00",
        duration="00:02:00:00",
    )
    print("Added clips to all tracks\n")

    # Add filters
    print("Adding filters...")
    # Greyscale effect on b-roll
    greyscale = project.add_filter(
        mlt_service="greyscale",
        track=1,  # overlay video track
        start="00:00:30:00",
        duration="00:00:10:00",
    )
    print(f"Added greyscale filter: {greyscale}")

    # Volume adjustment on music track
    volume = project.add_filter(
        mlt_service="volume",
        track=3,  # music track
        start="00:00:00:00",
        duration="00:02:00:00",
    )
    volume.set_property("level", "0.3")  # Lower music volume
    print("Added volume filter for background music")

    # Add transition (luma wipe between main video and b-roll)
    luma = project.add_transition(
        mlt_service="luma",
        a_track=0,  # main video
        b_track=1,  # overlay video
        start="00:00:30:00",
        duration="00:00:02:00",  # 2-second transition
    )
    print("Added luma transition between video tracks\n")

    # Create and add subtitle file
    print("Creating subtitles...")
    subtitles = [
        {"start": "00:00:00,000", "end": "00:00:05,000", "text": "Welcome to the interview"},
        {"start": "00:00:05,500", "end": "00:00:10,000", "text": "Today we discuss MLT XML"},
        {"start": "00:01:00,000", "end": "00:01:05,000", "text": "Thank you for watching"},
    ]
    SRTFile.create_from_dict(subtitles, "subtitles.srt")

    # Add subtitle filter referencing the SRT file
    project.add_subtitle(
        srt_file="subtitles.srt",
        track=0,
        start="00:00:00:00",
        end="00:02:00:00",
    )
    print("Added subtitles from SRT file\n")

    # Generate and save the MLT XML file
    print("Saving project...")
    project.save("example_project.kdenlive.xml")
    print("Project saved to: example_project.kdenlive.xml\n")

    # Display some info about the project
    print("=" * 60)
    print("Project Summary:")
    print("=" * 60)
    print(f"Profile: {project.profile.name}")
    print(f"Resolution: {project.profile.width}x{project.profile.height}")
    print(f"FPS: {project.profile.fps}")
    print(f"Total producers (bin items): {len(project.producers)}")
    print(f"Total tracks: {len(project.playlists)}")
    print(f"Total filters: {len(project.filters)}")
    print(f"Total transitions: {len(project.transitions)}")
    print("=" * 60)

    # Test loading the project back
    print("\nTesting project load...")
    loaded = MLTProject.load("example_project.kdenlive.xml")
    print(f"Loaded project: {loaded}")
    print("Project successfully saved and loaded!\n")


if __name__ == "__main__":
    main()

"""Utilities for creating Kdenlive-specific MLT structures."""

import json
from typing import List, Dict, Any
from xml.etree import ElementTree as ET

class KdenliveTrackBuilder:
    """Helper for constructing nested Kdenlive UI tracks (tractors)."""
    
    @staticmethod
    def create_ui_track(
        name: str, 
        track_type: str, 
        playlist_id_1: str, 
        playlist_id_2: str = None,
        is_audio: bool = False
    ) -> ET.Element:
        """Create a tractor representing a single Kdenlive UI track."""
        attrs = {"id": f"tractor_{name.lower().replace(' ', '_')}"}
        tractor = ET.Element("tractor", attrs)
        
        ET.SubElement(tractor, "property", {"name": "kdenlive:track_name"}).text = name
        if is_audio:
            ET.SubElement(tractor, "property", {"name": "kdenlive:audio_track"}).text = "1"
        
        # Add tracks to the tractor. Kdenlive typically uses 2 per UI track.
        t1_attrs = {"producer": playlist_id_1}
        t1_attrs["hide"] = "video" if is_audio else "audio"
        ET.SubElement(tractor, "track", t1_attrs)
        
        if playlist_id_2:
            t2_attrs = {"producer": playlist_id_2}
            t2_attrs["hide"] = "video" if is_audio else "audio"
            ET.SubElement(tractor, "track", t2_attrs)
            
        return tractor

    @staticmethod
    def generate_av_split_groups(splits: List[Dict[str, int]]) -> str:
        """Generate the JSON string for kdenlive:sequenceproperties.groups.
        
        Args:
            splits: List of dicts with keys 'video_track', 'audio_track', 'clip_index'.
        """
        groups = []
        for split in splits:
            group = {
                "type": "AVSplit",
                "children": [
                    {
                        "type": "Leaf", "leaf": "clip", 
                        "data": f"{split['video_track']}:{split['clip_index']}:-1"
                    },
                    {
                        "type": "Leaf", "leaf": "clip", 
                        "data": f"{split['audio_track']}:{split['clip_index']}:-1"
                    }
                ]
            }
            groups.append(group)
        return json.dumps(groups, indent=4)

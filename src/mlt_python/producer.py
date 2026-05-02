"""Producer class for MLT XML library.

Represents media items in the bin (video files, audio files, images, etc.).
Producers are the basic building blocks that generate frames in MLT.
"""

from typing import Any
from xml.etree import ElementTree as ET

from .filter import Filter


class Producer:
    """Represents an MLT producer (media source).

    Producers are the media items in the bin/timeline. They can be:
    - Video files (mp4, mov, etc.)
    - Audio files (wav, mp3, etc.)
    - Images (png, jpg, etc.)
    - Generators (colour, noise, etc.)

    Attributes:
        id: Unique identifier for the producer
        resource: File path or special resource identifier
        mlt_service: MLT service type (avformat, colour, etc.)
        properties: Additional MLT properties
        in_point: Start frame (optional)
        out_point: End frame (optional)
        filters: List of filters attached to this producer
    """

    def __init__(
        self,
        id: str,
        resource: str,
        mlt_service: str = "avformat",
        properties: dict[str, str] | None = None,
        in_point: int | None = None,
        out_point: int | None = None,
    ) -> None:
        """Initialize a Producer.

        Args:
            id: Unique identifier (e.g., "producer0", "vid1")
            resource: File path or resource string
            mlt_service: MLT service type (default: "avformat" for media files)
            properties: Additional MLT properties
            in_point: Optional start frame
            out_point: Optional end frame
        """
        self.id = id
        self.resource = resource
        self.mlt_service = mlt_service
        self.properties: dict[str, str] = properties or {}
        self.in_point = in_point
        self.out_point = out_point
        self.filters: list[Filter] = []

        # Set resource in properties if not already set
        if "resource" not in self.properties:
            self.properties["resource"] = resource

    @classmethod
    def create_colour(
        cls,
        id: str,
        colour: str = "0x00000000",
        length: int = 0,
    ) -> "Producer":
        """Create a colour producer (solid color generator).

        Args:
            id: Unique identifier
            colour: Hex colour with alpha (e.g., "0xffffffff" for white)
            length: Length in frames (0 = unlimited)

        Returns:
            Producer object for a colour generator
        """
        props = {"mlt_service": "colour", "resource": colour}
        if length > 0:
            props["length"] = str(length)
        return cls(id=id, resource=colour, mlt_service="colour", properties=props)

    @classmethod
    def create_from_file(
        cls,
        id: str,
        file_path: str,
        audio_track: int | None = None,
        video_track: int | None = None,
    ) -> "Producer":
        """Create a producer from a media file.

        Args:
            id: Unique identifier
            file_path: Path to media file
            audio_track: Specific audio track to use (optional)
            video_track: Specific video track to use (optional)

        Returns:
            Producer object for the media file
        """
        props: dict[str, str] = {"resource": file_path}
        if audio_track is not None:
            props["audio_track"] = str(audio_track)
        if video_track is not None:
            props["video_track"] = str(video_track)
        return cls(id=id, resource=file_path, mlt_service="avformat", properties=props)

    def set_property(self, name: str, value: str) -> None:
        """Set an MLT property on the producer.

        Args:
            name: Property name
            value: Property value
        """
        self.properties[name] = value

    def get_property(self, name: str, default: str | None = None) -> str | None:
        """Get an MLT property value.

        Args:
            name: Property name
            default: Default value if property doesn't exist

        Returns:
            Property value or default
        """
        return self.properties.get(name, default)

    def add_filter(self, filter_obj: Filter) -> None:
        """Add a filter to this producer.

        Args:
            filter_obj: Filter to attach to this producer
        """
        self.filters.append(filter_obj)

    def to_xml(self) -> ET.Element:
        """Generate XML element for this producer.

        Returns:
            XML Element representing the producer
        """
        attrs: dict[str, str] = {"id": self.id}
        if self.mlt_service and self.mlt_service != "avformat":
            attrs["mlt_service"] = self.mlt_service
        if self.in_point is not None:
            attrs["in"] = str(self.in_point)
        if self.out_point is not None:
            attrs["out"] = str(self.out_point)

        elem = ET.Element("producer", attrs)

        # Add properties
        for name, value in self.properties.items():
            prop = ET.SubElement(elem, "property", {"name": name})
            # Convert backslashes to forward slashes for paths
            prop.text = value.replace("\\", "/") if name == "resource" else value

        # Add filters attached to this producer
        for filter_obj in self.filters:
            elem.append(filter_obj.to_xml())

        return elem

    def to_xml_chain(self, fps: float = 30.0, chain_id: str | None = None) -> ET.Element:
        """Generate XML element as a chain (for Kdenlive bin).

        Args:
            fps: Frames per second for timestamp conversion
            chain_id: Optional chain ID (auto-generated if None)

        Returns:
            XML Element representing the producer as a chain element
        """
        import uuid

        # Determine clip type based on resource extension
        resource = self.properties.get("resource", "")
        is_audio = resource.endswith((".mp3", ".wav", ".aac", ".flac", ".ogg"))
        is_video = resource.endswith((".mkv", ".mp4", ".avi", ".mov", ".webm"))

        if chain_id is None:
            chain_id = f"chain{self.id}" if not self.id.startswith("chain") else self.id
        # Only set out if producer has an explicit length property
        length = self.properties.get("length")
        out_point = None
        if length is not None:
            try:
                frames = int(length)
                if frames < 2147483647:  # Skip absurd default
                    total_seconds = frames / fps
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = total_seconds % 60
                    out_point = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
            except ValueError:
                pass

        attrs: dict[str, str] = {"id": chain_id}
        if out_point is not None:
            attrs["out"] = out_point
        chain = ET.Element("chain", attrs)

        # Add mlt_service - use avformat-novalidate for Kdenlive
        if self.mlt_service:
            prop = ET.SubElement(chain, "property", {"name": "mlt_service"})
            prop.text = "avformat-novalidate" if self.mlt_service == "avformat" else self.mlt_service

        # Add standard properties
        for name, value in self.properties.items():
            prop = ET.SubElement(chain, "property", {"name": name})
            prop.text = value.replace("\\", "/") if name == "resource" else value

        # Add kdenlive:original_path for file resources
        resource = self.properties.get("resource", "")
        if resource and resource != "black" and not resource.startswith("+"):
            prop = ET.SubElement(chain, "property", {"name": "kdenlive:original_path"})
            prop.text = resource.replace("\\", "/")

        # Add additional properties for Kdenlive compatibility
        if resource and resource != "black" and not resource.startswith("+"):
            prop = ET.SubElement(chain, "property", {"name": "seekable"})
            prop.text = "1"
            # Determine audio/video indices based on resource type
            is_audio = resource.endswith((".mp3", ".wav", ".aac", ".flac", ".ogg"))
            is_video = resource.endswith((".mkv", ".mp4", ".avi", ".mov", ".webm"))
            if is_audio:
                prop = ET.SubElement(chain, "property", {"name": "audio_index"})
                prop.text = "0"
                prop = ET.SubElement(chain, "property", {"name": "video_index"})
                prop.text = "-1"
                prop = ET.SubElement(chain, "property", {"name": "astream"})
                prop.text = "0"
                prop = ET.SubElement(chain, "property", {"name": "set.test_audio"})
                prop.text = "0"
                prop = ET.SubElement(chain, "property", {"name": "set.test_image"})
                prop.text = "1"
            elif is_video:
                prop = ET.SubElement(chain, "property", {"name": "audio_index"})
                prop.text = "1"
                prop = ET.SubElement(chain, "property", {"name": "video_index"})
                prop.text = "0"
                prop = ET.SubElement(chain, "property", {"name": "vstream"})
                prop.text = "0"
                prop = ET.SubElement(chain, "property", {"name": "astream"})
                prop.text = "0"
                prop = ET.SubElement(chain, "property", {"name": "set.test_audio"})
                prop.text = "1"
                prop = ET.SubElement(chain, "property", {"name": "set.test_image"})
                prop.text = "0"
            # Add xml property
            prop = ET.SubElement(chain, "property", {"name": "xml"})
            prop.text = "was here"
            prop = ET.SubElement(chain, "property", {"name": "mute_on_pause"})
            prop.text = "0"

        # Add Kdenlive-specific properties
        prop = ET.SubElement(chain, "property", {"name": "kdenlive:control_uuid"})
        prop.text = str(uuid.uuid4())
        prop = ET.SubElement(chain, "property", {"name": "kdenlive:id"})
        # Use a hash of the id for numeric ID
        prop.text = str(abs(hash(self.id)) % 100)
        prop = ET.SubElement(chain, "property", {"name": "kdenlive:clip_type"})
        prop.text = "1" if is_audio else "2" if is_video else "0"
        prop = ET.SubElement(chain, "property", {"name": "kdenlive:file_size"})
        prop.text = "0"  # Placeholder
        prop = ET.SubElement(chain, "property", {"name": "kdenlive:folderid"})
        prop.text = "-1"

        # Add filters
        for i, filter_obj in enumerate(self.filters):
            filter_elem = filter_obj.to_xml()
            if "id" not in filter_elem.attrib:
                filter_elem.set("id", f"filter{i}")
            if not any(p.get("name") == "kdenlive_id" for p in filter_elem.findall("property")):
                prop = ET.SubElement(filter_elem, "property", {"name": "kdenlive_id"})
                prop.text = filter_obj.mlt_service
            chain.append(filter_elem)

        return chain

    @classmethod
    def from_xml(cls, elem: ET.Element) -> "Producer":
        """Parse a producer from XML element.

        Args:
            elem: XML Element representing a producer

        Returns:
            Producer object
        """
        id = elem.get("id", "")
        mlt_service = elem.get("mlt_service", "avformat")
        in_point = int(elem.get("in", "0")) if elem.get("in") else None
        out_point = int(elem.get("out", "0")) if elem.get("out") else None

        # Parse properties
        properties: dict[str, str] = {}
        for prop in elem.findall("property"):
            name = prop.get("name", "")
            if name:
                properties[name] = prop.text or ""

        # Get resource from properties or use empty string
        resource = properties.get("resource", "")

        return cls(
            id=id,
            resource=resource,
            mlt_service=mlt_service,
            properties=properties,
            in_point=in_point,
            out_point=out_point,
        )

    def __repr__(self) -> str:
        return f"Producer(id='{self.id}', resource='{self.resource}')"

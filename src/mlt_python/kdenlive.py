"""Kdenlive-specific extensions for MLT XML library.

Adds support for Kdenlive-specific properties and project structure,
including document properties, bin structure, and timeline metadata.
"""

from typing import Optional
from xml.etree import ElementTree as ET


class KdenliveProperties:
    """Manages Kdenlive-specific properties in MLT XML.

    Kdenlive adds various properties to the MLT XML for project management,
    including document properties, bin folder structure, and timeline metadata.
    """

    # Document property keys (stored as properties on the tractor)
    DOC_PROP_PREFIX = "kdenlive:docproperties."
    BIN_PREFIX = "kdenlive:bin."
    CLIP_PREFIX = "kdenlive:clip."

    def __init__(self) -> None:
        """Initialize Kdenlive properties storage."""
        self.doc_properties: dict[str, str] = {}
        self.bin_folders: dict[str, dict[str, str]] = {}  # folder_id -> {name, parent}
        self.clip_properties: dict[str, dict[str, str]] = {}  # clip_id -> {properties}

    def set_doc_property(self, key: str, value: str) -> None:
        """Set a Kdenlive document property.

        Args:
            key: Property key (without prefix)
            value: Property value
        """
        self.doc_properties[key] = value

    def get_doc_property(self, key: str, default: str | None = None) -> str | None:
        """Get a Kdenlive document property.

        Args:
            key: Property key (without prefix)
            default: Default value if not found

        Returns:
            Property value or default
        """
        return self.doc_properties.get(key, default)

    def set_bin_folder(
        self,
        folder_id: str,
        name: str,
        parent_id: str = "root",
    ) -> None:
        """Add a bin folder for organizing media.

        Args:
            folder_id: Unique folder identifier
            name: Folder display name
            parent_id: Parent folder ID (default: "root")
        """
        self.bin_folders[folder_id] = {
            "name": name,
            "parent": parent_id,
        }

    def remove_bin_folder(self, folder_id: str) -> None:
        """Remove a bin folder.

        Args:
            folder_id: Folder identifier to remove
        """
        self.bin_folders.pop(folder_id, None)

    def set_clip_property(
        self,
        clip_id: str,
        key: str,
        value: str,
    ) -> None:
        """Set a Kdenlive-specific property on a clip.

        Args:
            clip_id: Producer/clip ID
            key: Property key (without prefix)
            value: Property value
        """
        if clip_id not in self.clip_properties:
            self.clip_properties[clip_id] = {}
        self.clip_properties[clip_id][key] = value

    def get_clip_property(
        self,
        clip_id: str,
        key: str,
        default: str | None = None,
    ) -> str | None:
        """Get a Kdenlive-specific property from a clip.

        Args:
            clip_id: Producer/clip ID
            key: Property key (without prefix)
            default: Default value if not found

        Returns:
            Property value or default
        """
        return self.clip_properties.get(clip_id, {}).get(key, default)

    def to_xml_properties(self) -> list[tuple[str, str]]:
        """Generate XML properties for Kdenlive attributes.

        Returns:
            List of (property_name, value) tuples
        """
        props: list[tuple[str, str]] = []

        # Document properties
        for key, value in self.doc_properties.items():
            props.append((f"{self.DOC_PROP_PREFIX}{key}", value))

        # Bin folder structure (stored as a special property)
        if self.bin_folders:
            bin_xml = self._build_bin_xml()
            props.append(("kdenlive:bin_folders", bin_xml))

        # Clip properties
        for clip_id, clip_props in self.clip_properties.items():
            for key, value in clip_props.items():
                props.append((f"{self.CLIP_PREFIX}{clip_id}.{key}", value))

        return props

    def _build_bin_xml(self) -> str:
        """Build XML string for bin folder structure.

        Returns:
            XML string representing bin folders
        """
        root = ET.Element("bin_folders")
        for folder_id, folder_data in self.bin_folders.items():
            folder = ET.SubElement(root, "folder", {
                "id": folder_id,
                "name": folder_data["name"],
                "parent": folder_data["parent"],
            })
        return ET.tostring(root, encoding="unicode")

    @classmethod
    def from_xml_properties(
        cls,
        properties: dict[str, str],
    ) -> "KdenliveProperties":
        """Parse Kdenlive properties from XML properties.

        Args:
            properties: Dictionary of all properties from XML

        Returns:
            KdenliveProperties object
        """
        kdenlive = cls()

        for key, value in properties.items():
            if key.startswith(cls.DOC_PROP_PREFIX):
                doc_key = key[len(cls.DOC_PROP_PREFIX):]
                kdenlive.doc_properties[doc_key] = value
            elif key == "kdenlive:bin_folders":
                kdenlive._parse_bin_xml(value)
            elif key.startswith(cls.CLIP_PREFIX):
                # Parse clip.clipId.property
                remainder = key[len(cls.CLIP_PREFIX):]
                parts = remainder.split(".", 1)
                if len(parts) == 2:
                    clip_id, prop_key = parts
                    kdenlive.set_clip_property(clip_id, prop_key, value)

        return kdenlive

    def _parse_bin_xml(self, xml_string: str) -> None:
        """Parse bin folder XML.

        Args:
            xml_string: XML string from kdenlive:bin_folders property
        """
        try:
            root = ET.fromstring(xml_string)
            for folder in root.findall("folder"):
                folder_id = folder.get("id", "")
                name = folder.get("name", "")
                parent = folder.get("parent", "root")
                if folder_id:
                    self.bin_folders[folder_id] = {
                        "name": name,
                        "parent": parent,
                    }
        except ET.ParseError:
            pass  # Invalid XML, skip


class KdenliveMetadata:
    """Common Kdenlive metadata constants and helpers."""

    # Document property keys
    DOC_VERSION = "version"
    DOC_PROFILE = "profile"
    DOC_WIDTH = "width"
    DOC_HEIGHT = "height"
    DOC_FPS = "fps"
    DOC_SAMPLE_ASPECT = "sample_aspect"
    DOC_DISPLAY_ASPECT = "display_aspect"

    # Clip property keys
    CLIP_TYPE = "type"  # video, audio, image
    CLIP_NAME = "name"
    CLIP_DESCRIPTION = "description"
    CLIP_DURATION = "duration"
    CLIP_THUMBNAIL = "thumbnail"

    # Known clip types
    TYPE_VIDEO = "video"
    TYPE_AUDIO = "audio"
    TYPE_IMAGE = "image"
    TYPE_TEXT = "text"
    TYPE_SLIDE = "slide"

    @staticmethod
    def create_doc_properties(
        version: str = "1.0",
        profile_name: str = "",
        width: int = 1920,
        height: int = 1080,
        fps: float = 30.0,
    ) -> dict[str, str]:
        """Create standard Kdenlive document properties.

        Args:
            version: Kdenlive document version
            profile_name: Profile name
            width: Frame width
            height: Frame height
            fps: Frames per second

        Returns:
            Dictionary of document properties
        """
        return {
            "version": version,
            "profile": profile_name,
            "width": str(width),
            "height": str(height),
            "fps": str(fps),
        }

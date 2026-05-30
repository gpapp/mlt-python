"""Video profile handling for MLT XML library.

Defines video profiles with frame rate, resolution, aspect ratio, and other
properties used by MLT and Kdenlive.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Profile:
    """Represents a video profile with all necessary properties for MLT.

    Attributes:
        name: Human-readable profile name
        width: Frame width in pixels
        height: Frame height in pixels
        frame_rate_num: Numerator of frame rate fraction
        frame_rate_den: Denominator of frame rate fraction
        sample_aspect_num: Numerator of sample (pixel) aspect ratio
        sample_aspect_den: Denominator of sample (pixel) aspect ratio
        display_aspect_num: Numerator of display aspect ratio
        display_aspect_den: Denominator of display aspect ratio
        colorspace: Colorspace (601, 709, etc.)
        progressive: Whether the video is progressive (not interlaced)
    """

    name: str
    width: int
    height: int
    frame_rate_num: int
    frame_rate_den: int
    sample_aspect_num: int = 1
    sample_aspect_den: int = 1
    display_aspect_num: int = 0  # 0 means auto-calculate
    display_aspect_den: int = 1
    colorspace: int = 709
    progressive: bool = True

    def __post_init__(self) -> None:
        """Calculate display aspect ratio if not provided."""
        if self.display_aspect_num == 0:
            # Calculate display aspect ratio (typically 16:9 for HD, 4:3 for SD)
            # Use simplified ratio: width/height with common denominators
            if self.width / self.height == 16/9:
                self.display_aspect_num = 16
                self.display_aspect_den = 9
            elif self.width / self.height == 4/3:
                self.display_aspect_num = 4
                self.display_aspect_den = 3
            else:
                # Fallback to calculated values
                self.display_aspect_num = self.width * self.sample_aspect_num
                self.display_aspect_den = self.height * self.sample_aspect_den

    @property
    def fps(self) -> float:
        """Get frames per second as a float.

        Returns:
            FPS value
        """
        return self.frame_rate_num / self.frame_rate_den

    @property
    def frame_rate(self) -> float:
        """Alias for fps property.

        Returns:
            FPS value
        """
        return self.fps

    @property
    def is_progressive(self) -> int:
        """Get progressive as integer for MLT XML.

        Returns:
            1 if progressive, 0 if interlaced
        """
        return 1 if self.progressive else 0

    def to_xml_attributes(self) -> dict[str, str]:
        """Generate XML attributes for the profile element.

        Returns:
            Dictionary of attribute name-value pairs
        """
        # Build human-readable description from profile properties
        scan = "p" if self.progressive else "i"
        fps = self.frame_rate_num // self.frame_rate_den if self.frame_rate_den == 1 else f"{self.frame_rate_num / self.frame_rate_den:.2f}"
        description = f"HD {self.height}{scan} {fps} fps"

        return {
            "description": description,
            "width": str(self.width),
            "height": str(self.height),
            "frame_rate_num": str(self.frame_rate_num),
            "frame_rate_den": str(self.frame_rate_den),
            "sample_aspect_num": str(self.sample_aspect_num),
            "sample_aspect_den": str(self.sample_aspect_den),
            "display_aspect_num": str(self.display_aspect_num),
            "display_aspect_den": str(self.display_aspect_den),
            "colorspace": str(self.colorspace),
            "progressive": str(self.is_progressive),
        }

    @classmethod
    def from_xml(cls, attrs: dict[str, str]) -> "Profile":
        """Create a Profile from XML attributes.

        Args:
            attrs: Dictionary of XML attribute values

        Returns:
            Profile object
        """
        return cls(
            name=attrs.get("name", "custom"),
            width=int(attrs.get("width", 1920)),
            height=int(attrs.get("height", 1080)),
            frame_rate_num=int(attrs.get("frame_rate_num", 30)),
            frame_rate_den=int(attrs.get("frame_rate_den", 1)),
            sample_aspect_num=int(attrs.get("sample_aspect_num", 1)),
            sample_aspect_den=int(attrs.get("sample_aspect_den", 1)),
            display_aspect_num=int(attrs.get("display_aspect_num", 0)),
            display_aspect_den=int(attrs.get("display_aspect_den", 1)),
            colorspace=int(attrs.get("colorspace", 709)),
            progressive=attrs.get("progressive", "1") == "1",
        )

    # Common profile presets
    @classmethod
    def hd1080_60(cls) -> "Profile":
        """Full HD 1080p at 60fps."""
        return cls(
            name="hd1080_60",
            width=1920,
            height=1080,
            frame_rate_num=60,
            frame_rate_den=1,
        )

    @classmethod
    def hd1080_30(cls) -> "Profile":
        """Full HD 1080p at 30fps."""
        return cls(
            name="hd1080_30",
            width=1920,
            height=1080,
            frame_rate_num=30,
            frame_rate_den=1,
        )

    @classmethod
    def hd1080_2997(cls) -> "Profile":
        """Full HD 1080p at 29.97fps."""
        return cls(
            name="hd1080_2997",
            width=1920,
            height=1080,
            frame_rate_num=30000,
            frame_rate_den=1001,
        )

    @classmethod
    def hd1080_25(cls) -> "Profile":
        """Full HD 1080p at 25fps (PAL)."""
        return cls(
            name="hd1080_25",
            width=1920,
            height=1080,
            frame_rate_num=25,
            frame_rate_den=1,
        )

    @classmethod
    def hd1080_24(cls) -> "Profile":
        """Full HD 1080p at 24fps."""
        return cls(
            name="hd1080_24",
            width=1920,
            height=1080,
            frame_rate_num=24,
            frame_rate_den=1,
        )

    @classmethod
    def hd720_30(cls) -> "Profile":
        """HD 720p at 30fps."""
        return cls(
            name="hd720_30",
            width=1280,
            height=720,
            frame_rate_num=30,
            frame_rate_den=1,
        )

    @classmethod
    def uhd_30(cls) -> "Profile":
        """4K UHD at 30fps."""
        return cls(
            name="uhd_30",
            width=3840,
            height=2160,
            frame_rate_num=30,
            frame_rate_den=1,
        )

    @classmethod
    def uhd_24(cls) -> "Profile":
        """4K UHD at 24fps."""
        return cls(
            name="uhd_24",
            width=3840,
            height=2160,
            frame_rate_num=24,
            frame_rate_den=1,
        )

    @classmethod
    def sdtv_ntsc(cls) -> "Profile":
        """SD NTSC 480i."""
        return cls(
            name="sdtv_ntsc",
            width=720,
            height=480,
            frame_rate_num=30000,
            frame_rate_den=1001,
            progressive=False,
        )

    @classmethod
    def sdtv_pal(cls) -> "Profile":
        """SD PAL 576i."""
        return cls(
            name="sdtv_pal",
            width=720,
            height=576,
            frame_rate_num=25,
            frame_rate_den=1,
            progressive=False,
        )

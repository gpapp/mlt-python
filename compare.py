"""Compare MLT XML files to find differences."""
import xml.etree.ElementTree as ET
from pathlib import Path

def compare_files(ref_path, fixed_path, ours_path):
    ref = ET.parse(ref_path)
    fixed = ET.parse(fixed_path)
    ours = ET.parse(ours_path)
    
    print("=== ROOT ATTRIBUTES ===")
    print(f"Reference: {dict(ref.getroot().attrib)}")
    print(f"Fixed: {dict(fixed.getroot().attrib)}")
    print(f"Ours: {dict(ours.getroot().attrib)}")
    
    # Compare main tractor filters
    print("\n=== MAIN TRACTOR FILTERS ===")
    for name, tree in [("Reference", ref), ("Fixed", fixed), ("Ours", ours)]:
        for tractor in tree.findall(".//tractor"):
            tid = tractor.get("id", "")
            if "{" in tid:  # UUID tractor
                filters = tractor.findall("filter")
                print(f"{name}: {len(filters)} filters")
                for f in filters:
                    mlt_svc = f.find("property[@name='mlt_service']")
                    print(f"  {f.get('id')}: {mlt_svc.text if mlt_svc is not None else 'unknown'}")
    
    # Compare playlist elements
    print("\n=== PLAYLIST ELEMENTS ===")
    for name, tree in [("Reference", ref), ("Fixed", fixed), ("Ours", ours)]:
        playlists = tree.findall("playlist")
        print(f"{name}: {len(playlists)} playlists")
        for p in playlists[:8]:  # First 8
            props = {prop.get("name"): prop.text for prop in p.findall("property")}
            print(f"  {p.get('id')}: props={list(props.keys())}")
    
    # Compare main_bin properties
    print("\n=== MAIN_BIN PROPERTIES ===")
    for name, tree in [("Reference", ref), ("Fixed", fixed), ("Ours", ours)]:
        main_bin = tree.find("playlist[@id='main_bin']")
        if main_bin is not None:
            props = [(p.get("name"), p.text[:50] if p.text else "") for p in main_bin.findall("property")]
            print(f"{name}: {len(props)} properties")
            for pname, pval in props:
                print(f"  {pname}: {pval}")
        
        # Check for entries
        entries = main_bin.findall("entry") if main_bin is not None else []
        print(f"  entries: {len(entries)}")
    
    # Check for chain elements
    print("\n=== CHAIN ELEMENTS ===")
    for name, tree in [("Reference", ref), ("Fixed", fixed), ("Ours", ours)]:
        chains = tree.findall("chain")
        print(f"{name}: {len(chains)} chains")
        for c in chains:
            print(f"  {c.get('id')}")

compare_files(
    "C:/Users/gerge/source/repos/video-processing-tool/kdenlive/empty.kdenlive",
    "tests/output/01_empty-fixed.kdenlive",
    "tests/output/01_empty.kdenlive"
)

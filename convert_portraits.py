"""
Convert TGA portrait files to PNG for the wiki.

Usage:
    python convert_portraits.py <path_to_Backgrounds_folder>

Example:
    python convert_portraits.py "C:\path\to\HardcoreClassesEnhanced\Backgrounds"

Requires: pip install Pillow
"""
import sys, os
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: python convert_portraits.py <path_to_Backgrounds_folder>")
    sys.exit(1)

src = Path(sys.argv[1])
dst = Path(__file__).parent / "portraits"
dst.mkdir(exist_ok=True)

count = 0
for tga in src.glob("*.tga"):
    out = dst / (tga.stem + ".png")
    img = Image.open(tga)
    img = img.resize((200, 200), Image.LANCZOS)
    img.save(out, "PNG")
    count += 1
    print(f"  {tga.name} -> {out.name}")

print(f"\nConverted {count} portraits to {dst}")

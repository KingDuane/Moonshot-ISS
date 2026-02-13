#!/usr/bin/env python3
"""
Convert a raw RGB565 screenshot from the ISS tracker to PNG.

The ESP32 saves the 240x240 framebuffer as raw RGB565 bytes (little-endian,
115200 bytes). This script decodes the binary and writes a standard PNG.

Usage:
    python convert_screenshot.py screenshot_001.bin
    python convert_screenshot.py screenshot_*.bin
    python convert_screenshot.py screenshot_001.bin -o mandala.png
    python convert_screenshot.py screenshot_001.bin --saturation 0.3  (hint of color)
    python convert_screenshot.py screenshot_001.bin --saturation 1.0  (full color)
"""

import argparse
import struct
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

WIDTH = 240
HEIGHT = 240
EXPECTED_SIZE = WIDTH * HEIGHT * 2  # 115200 bytes


def rgb565_to_rgb888(pixel):
    """Convert a 16-bit RGB565 value to (R, G, B) tuple."""
    r = (pixel >> 11) & 0x1F
    g = (pixel >> 5) & 0x3F
    b = pixel & 0x1F
    return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)


def desaturate(r, g, b, saturation):
    """Blend RGB toward luminance-weighted greyscale."""
    lum = int(0.299 * r + 0.587 * g + 0.114 * b)
    return (
        int(lum + saturation * (r - lum)),
        int(lum + saturation * (g - lum)),
        int(lum + saturation * (b - lum)),
    )


def convert(input_path, output_path, saturation=0.0):
    data = Path(input_path).read_bytes()
    if len(data) != EXPECTED_SIZE:
        sys.exit(f"Expected {EXPECTED_SIZE} bytes, got {len(data)}")

    img = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = img.load()

    for y in range(HEIGHT):
        for x in range(WIDTH):
            offset = (y * WIDTH + x) * 2
            pixel = struct.unpack_from("<H", data, offset)[0]
            r, g, b = rgb565_to_rgb888(pixel)
            pixels[x, y] = desaturate(r, g, b, saturation)

    img.save(output_path)
    print(f"Saved {output_path} ({WIDTH}x{HEIGHT})")


def main():
    parser = argparse.ArgumentParser(description="Convert ISS tracker screenshot to PNG")
    parser.add_argument("input", nargs="+", help="Path(s) to screenshot .bin file(s)")
    parser.add_argument("-o", "--output", help="Output PNG path (only valid with a single input file)")
    parser.add_argument("--saturation", type=float, default=0.0,
                        help="Color saturation (default: 0.0=greyscale, 1.0=full color)")
    args = parser.parse_args()

    if args.output and len(args.input) > 1:
        sys.exit("-o/--output can only be used with a single input file")

    for path in args.input:
        output = args.output or str(Path(path).with_suffix(".png"))
        convert(path, output, args.saturation)


if __name__ == "__main__":
    main()

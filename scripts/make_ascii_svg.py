#!/usr/bin/env python3
"""
make_ascii_svg.py
Converts prepped photo (source-prepped.png) into a clean, monochrome, animated SVG
that types itself row-by-row like a terminal output.
"""

import sys
import os
import argparse
from PIL import Image, ImageDraw

RAMP = " .`:-=+*cs#%@" # Bright (sparse / space) -> Dark (dense)

def create_sample_portrait(path: str = "source-prepped.png"):
    """Generates a default fallback silhouette if no user photo exists."""
    img = Image.new("L", (300, 300), color=255)
    draw = ImageDraw.Draw(img)
    
    # Draw simple avatar silhouette
    # Head
    draw.ellipse((90, 50, 210, 170), fill=60)
    # Shoulders / Torso
    draw.ellipse((40, 160, 260, 340), fill=80)
    # Eyes & details
    draw.ellipse((120, 95, 140, 115), fill=20)
    draw.ellipse((160, 95, 180, 115), fill=20)
    draw.arc((125, 120, 175, 145), start=0, end=180, fill=20, width=4)
    img.save(path)
    return path

def image_to_ascii(image_path: str, target_width: int = 80):
    if not os.path.exists(image_path):
        print(f"Warning: '{image_path}' not found. Generating default avatar silhouette.")
        create_sample_portrait(image_path)

    img = Image.open(image_path).convert("L")
    
    # Terminal characters are approximately 2x taller than wide (aspect ratio ~ 0.55)
    orig_w, orig_h = img.size
    aspect = orig_h / orig_w
    target_height = int(target_width * aspect * 0.52)
    
    img_resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    pixels = img_resized.load()
    
    ramp_len = len(RAMP)
    lines = []
    
    for y in range(target_height):
        line_chars = []
        for x in range(target_width):
            val = pixels[x, y] # 0 (black) .. 255 (white)
            # Invert: white (255) -> 0 (space in RAMP), black (0) -> ramp_len-1 (@ in RAMP)
            ramp_idx = int((255 - val) / 255.0 * (ramp_len - 1))
            ramp_idx = max(0, min(ramp_len - 1, ramp_idx))
            line_chars.append(RAMP[ramp_idx])
        lines.append("".join(line_chars))
        
    return lines, target_width, target_height

def generate_svg(lines: list, target_width: int, target_height: int, output_path: str, static: bool = False):
    char_width = 7.2
    line_height = 13.5
    padding_x = 24
    padding_top = 46
    padding_bottom = 24
    
    content_width = target_width * char_width
    content_height = target_height * line_height
    
    svg_width = int(content_width + padding_x * 2)
    svg_height = int(content_height + padding_top + padding_bottom)

    row_delay_step = 0.05 # Delay per row in seconds
    row_duration = 0.25   # Typing wipe duration per row
    
    text_elements = []
    clip_elements = []
    
    for idx, raw_line in enumerate(lines):
        y_pos = padding_top + (idx + 1) * line_height - 3
        # Escape XML chars
        escaped_line = (raw_line.replace("&", "&amp;")
                                .replace("<", "&lt;")
                                .replace(">", "&gt;")
                                .replace("\"", "&quot;")
                                .replace(" ", "&#160;"))
        
        clip_id = f"row-clip-{idx}"
        delay = idx * row_delay_step
        
        if not static:
            # SMIL animated clip-path for typewriter wipe effect
            clip_elements.append(f"""
    <clipPath id="{clip_id}">
      <rect x="{padding_x}" y="{y_pos - line_height + 2}" width="0" height="{line_height + 2}">
        <animate attributeName="width" from="0" to="{content_width}" dur="{row_duration}s" begin="{delay:.2f}s" fill="freeze" />
      </rect>
    </clipPath>""")
            clip_attr = f'clip-path="url(#{clip_id})"'
        else:
            clip_attr = ""

        text_elements.append(
            f'    <text x="{padding_x}" y="{y_pos:.1f}" class="ascii-row" {clip_attr}>{escaped_line}</text>'
        )

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%">
  <defs>
    <style>
      .bg {{ fill: #0d1117; }}
      .border {{ stroke: #30363d; stroke-width: 1; fill: none; }}
      .title-text {{ fill: #7ee787; font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 12px; font-weight: 600; }}
      .ascii-row {{
        fill: #c9d1d9;
        font-family: "Courier New", Courier, monospace;
        font-size: 11.5px;
        font-weight: 500;
        letter-spacing: 0.5px;
        white-space: pre;
      }}
    </style>
    {''.join(clip_elements)}
  </defs>

  <!-- Background Box -->
  <rect width="{svg_width}" height="{svg_height}" rx="8" class="bg" />
  <rect width="{svg_width - 1}" height="{svg_height - 1}" x="0.5" y="0.5" rx="8" class="border" />

  <!-- Terminal Header -->
  <circle cx="18" cy="18" r="4.5" fill="#ff5f56" />
  <circle cx="32" cy="18" r="4.5" fill="#ffbd2e" />
  <circle cx="46" cy="18" r="4.5" fill="#27c93f" />
  <text x="65" y="22" class="title-text">portrait.ascii</text>

  <!-- ASCII Art Body -->
  <g id="ascii-body">
{chr(10).join(text_elements)}
  </g>
</svg>
"""

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Generated ASCII SVG ({target_width}x{target_height}): {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Convert preprocessed photo into animated ASCII SVG.")
    parser.add_argument("--input", "-i", default="source-prepped.png", help="Path to prepped photo")
    parser.add_argument("--output", "-o", default="avi-ascii.svg", help="Output SVG path")
    parser.add_argument("--width", "-w", type=int, default=52, help="Grid character width (~45 to 80)")
    parser.add_argument("--static", action="store_true", help="Disable typing animation")
    args = parser.parse_args()

    static_mode = args.static or os.environ.get("STATIC", "0") == "1"
    lines, w, h = image_to_ascii(args.input, args.width)
    generate_svg(lines, w, h, args.output, static=static_mode)

if __name__ == "__main__":
    main()

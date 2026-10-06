#!/usr/bin/env python3
"""
prep_photo.py
Preprocesses an input photo for ASCII art conversion:
1. Removes background (via rembg) so subject is isolated
2. Applies OpenCV CLAHE (Contrast-Limited Adaptive Histogram Equalization) for crisp facial features
3. Composites onto a pure white background (so white becomes blank space in ASCII)
4. Saves prepped grayscale image to source-prepped.png
"""

import sys
import os
import argparse
import numpy as np
from PIL import Image

def process_photo(input_path: str, output_path: str = "source-prepped.png"):
    if not os.path.exists(input_path):
        print(f"Error: Input photo '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading image from {input_path}...")
    img = Image.open(input_path).convert("RGBA")

    # Step 1: Background removal
    try:
        from rembg import remove
        print("Removing background with rembg...")
        img_no_bg = remove(img)
    except Exception as e:
        print(f"Warning: rembg background removal failed or not installed ({e}). Using original image alpha.")
        img_no_bg = img

    # Step 2: Separate alpha mask and RGB
    np_img = np.array(img_no_bg)
    alpha = np_img[:, :, 3] if np_img.shape[2] == 4 else np.ones(np_img.shape[:2], dtype=np.uint8) * 255
    rgb = np_img[:, :, :3]

    # Grayscale conversion
    import cv2
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # Step 3: Boost local contrast with CLAHE
    print("Applying CLAHE contrast enhancement...")
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)

    # Step 4: Composite subject onto pure white background
    # Where alpha is low (background), replace with 255 (white)
    norm_alpha = alpha.astype(float) / 255.0
    final_gray = (enhanced_gray * norm_alpha + 255.0 * (1.0 - norm_alpha)).astype(np.uint8)

    prepped_img = Image.fromarray(final_gray)
    prepped_img.save(output_path)
    print(f"Successfully saved prepped image to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Preprocess portrait photo for ASCII conversion.")
    parser.add_argument("input", nargs="?", default="source-photo.jpg", help="Path to input photo (jpg/png)")
    parser.add_argument("--output", "-o", default="source-prepped.png", help="Path for prepped output image")
    args = parser.parse_args()

    process_photo(args.input, args.output)

if __name__ == "__main__":
    main()

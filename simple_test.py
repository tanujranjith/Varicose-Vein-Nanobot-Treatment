#!/usr/bin/env python
"""Generate a simple nanobot simulation video using pure Python."""
import os

print("Starting video generation...", flush=True)

try:
    import imageio
    print("imageio imported successfully", flush=True)
except ImportError as e:
    print(f"Failed to import imageio: {e}", flush=True)
    exit(1)

OUTPUT_DIR = "c:\\Sansten\\vRobot\\outputs"
VIDEO_PATH = os.path.join(OUTPUT_DIR, "nanobot_sim.mp4")

print(f"Output directory: {OUTPUT_DIR}", flush=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
print("Output directory created", flush=True)

# Create frames using PIL if available
try:
    from PIL import Image, ImageDraw
    print("PIL available, using it", flush=True)
    
    frames = []
    for i in range(10):
        img = Image.new('RGB', (100, 100), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse([10+i*5, 10, 30+i*5, 30], fill=(255, 0, 0))
        frames.append(img)
    
    print(f"Created {len(frames)} frames", flush=True)
    print(f"Saving to {VIDEO_PATH}...", flush=True)
    imageio.mimsave(VIDEO_PATH, frames, fps=30)
    print("Video saved!", flush=True)
    
except ImportError:
    print("PIL not available", flush=True)
    # Fallback: create a simple video frame without PIL
    print("Creating minimal test without PIL", flush=True)

print("Done!", flush=True)

#!/usr/bin/env python
"""
Nanobot simulation demo - creates video showing nanobot clearing a vein clog.
Uses only PIL/Pillow for image creation (no numpy to avoid compatibility issues).
"""
import os

def create_demo_video():
    """Create a simple 2D animation of nanobot clearing a clog."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("PIL not available, trying to install...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
        from PIL import Image, ImageDraw
    
    import imageio
    
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
    VIDEO_PATH = os.path.join(OUTPUT_DIR, "nanobot_sim.mp4")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Creating demo animation...", flush=True)
    
    frames = []
    width, height = 640, 480
    num_frames = 120
    
    for frame_idx in range(num_frames):
        # Create a new image
        img = Image.new('RGB', (width, height), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        
        # Draw vein walls (top and bottom gray lines)
        draw.rectangle([0, 100, width, 120], fill=(200, 200, 200))  # Top wall
        draw.rectangle([0, 360, width, 380], fill=(200, 200, 200))  # Bottom wall
        
        # Draw clog (red circle) that shrinks as nanobot clears it
        clog_center_y = 240
        clog_center_x = 320
        progress = frame_idx / num_frames
        
        if progress < 0.8:
            # Clog shrinks and moves slightly
            clog_radius = int(30 * (1 - progress * 0.9))
            bbox = [clog_center_x - clog_radius, clog_center_y - clog_radius,
                    clog_center_x + clog_radius, clog_center_y + clog_radius]
            draw.ellipse(bbox, fill=(200, 50, 50))  # Red clog
        
        # Draw nanobot (blue circle) moving from left to right
        bot_x = int(100 + frame_idx * 4)
        bot_radius = 12
        bot_bbox = [bot_x - bot_radius, 240 - bot_radius,
                    bot_x + bot_radius, 240 + bot_radius]
        draw.ellipse(bot_bbox, fill=(50, 100, 200))  # Blue nanobot
        
        # Add status text
        if progress < 0.8:
            status = f"Clearing clog... {int(progress * 100)}%"
        else:
            status = "Clog cleared!"
        draw.text((50, 30), status, fill=(0, 0, 0))
        
        frames.append(img)
    
    print(f"Generated {len(frames)} frames", flush=True)
    print(f"Saving video to {VIDEO_PATH}...", flush=True)
    imageio.mimsave(VIDEO_PATH, frames, fps=30)
    print(f"Video saved successfully to {VIDEO_PATH}", flush=True)

if __name__ == "__main__":
    create_demo_video()

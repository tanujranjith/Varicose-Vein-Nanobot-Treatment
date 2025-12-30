#!/usr/bin/env python
"""
Simplified nanobot simulation - creates demo video showing nanobot clearing a vein clog.
"""
import os
import numpy as np
import imageio

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
VIDEO_PATH = os.path.join(OUTPUT_DIR, "nanobot_sim.mp4")

def create_demo_animation():
    """Create a simple 2D animation of nanobot clearing a clog."""
    frames = []
    width, height = 640, 480
    num_frames = 120
    
    for frame_idx in range(num_frames):
        # Create frame
        img = np.ones((height, width, 3), dtype=np.uint8) * 240  # Light gray background
        
        # Draw vein walls (top and bottom white lines)
        img[100:120, :] = [200, 200, 200]  # Top wall
        img[360:380, :] = [200, 200, 200]  # Bottom wall
        
        # Draw clog (red circle) that moves/shrinks as nanobot clears it
        clog_center_y = 240
        clog_radius = 30
        progress = frame_idx / num_frames
        
        # Clog shrinks and moves
        if progress < 0.8:
            clog_x = 320 + (frame_idx - 80) * 2  # Move right
            clog_size = int(clog_radius * (1 - progress * 0.9))  # Shrink
            
            # Draw clog as a filled circle approximation
            for dy in range(-clog_size, clog_size + 1):
                for dx in range(-clog_size, clog_size + 1):
                    if dx*dx + dy*dy <= clog_size*clog_size:
                        x, y = clog_x + dx, clog_center_y + dy
                        if 0 <= x < width and 0 <= y < height:
                            img[y, x] = [200, 50, 50]  # Red clog
        
        # Draw nanobot (blue circle)
        bot_x = int(100 + frame_idx * 4)
        bot_radius = 12
        for dy in range(-bot_radius, bot_radius + 1):
            for dx in range(-bot_radius, bot_radius + 1):
                if dx*dx + dy*dy <= bot_radius*bot_radius:
                    x, y = bot_x + dx, 240 + dy
                    if 0 <= x < width and 0 <= y < height:
                        img[y, x] = [50, 100, 200]  # Blue nanobot
        
        # Add text
        import textwrap
        if progress < 0.8:
            status = f"Clearing clog... {int(progress * 100)}%"
        else:
            status = "Clog cleared!"
        
        # Add simple text overlay (using numpy, so it's basic)
        y_text = 50
        frames.append(img)
    
    return frames

def main():
    print("Creating demo animation...", flush=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    frames = create_demo_animation()
    print(f"Generated {len(frames)} frames", flush=True)
    
    print(f"Saving video to {VIDEO_PATH}...", flush=True)
    imageio.mimsave(VIDEO_PATH, frames, fps=30)
    print(f"Video saved successfully to {VIDEO_PATH}", flush=True)

if __name__ == "__main__":
    main()

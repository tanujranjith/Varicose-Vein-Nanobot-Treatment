#!/usr/bin/env python
"""
Nanobot Simulation: Visualizing a nanobot clearing a varicose vein clog.
Creates an MP4 video showing the simulation.
"""
import os
from PIL import Image, ImageDraw, ImageFont

def create_nanobot_simulation():
    """
    Create a simulation showing a blue nanobot moving through a vein
    and clearing a red clog blockage.
    """
    import imageio
    
    OUTPUT_DIR = "c:\\Sansten\\vRobot\\outputs"
    VIDEO_PATH = os.path.join(OUTPUT_DIR, "nanobot_sim.mp4")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Creating nanobot vein-clearing simulation...", flush=True)
    
    frames = []
    width, height = 800, 600
    num_frames = 200
    
    for frame_idx in range(num_frames):
        # Create background
        img = Image.new('RGB', (width, height), color=(245, 245, 250))  # Light blue background
        draw = ImageDraw.Draw(img)
        
        # Draw vein walls (top and bottom)
        wall_color = (180, 180, 200)
        draw.rectangle([0, 150, width, 170], fill=wall_color)  # Top wall
        draw.rectangle([0, 430, width, 450], fill=wall_color)  # Bottom wall
        
        # Add grid to show vein interior
        for x in range(0, width, 80):
            draw.line([x, 170, x, 430], fill=(220, 220, 230), width=1)
        
        # Calculate progress (0 to 1)
        progress = frame_idx / num_frames
        
        # Draw clog (red obstacle) that shrinks and disappears
        clog_center_x = 400
        clog_center_y = 300
        clog_start_radius = 60
        
        if progress < 0.85:
            # Clog shrinks as nanobot works on it
            shrink_factor = 1.0 - (progress * 1.2)  # Exaggerate shrinking for visual effect
            clog_radius = int(clog_start_radius * max(0, shrink_factor))
            
            if clog_radius > 2:
                # Draw clog with shading
                bbox = [clog_center_x - clog_radius, clog_center_y - clog_radius,
                        clog_center_x + clog_radius, clog_center_y + clog_radius]
                draw.ellipse(bbox, fill=(220, 50, 50))  # Bright red clog
                draw.ellipse(bbox, outline=(150, 0, 0), width=2)  # Dark red outline
        
        # Draw nanobot (blue sphere) moving left to right
        bot_speed = 3.5
        bot_x = int(50 + frame_idx * bot_speed)
        bot_radius = 18
        
        # Nanobot glow effect (light blue circle around it)
        glow_radius = bot_radius + 8
        glow_bbox = [bot_x - glow_radius, 300 - glow_radius,
                     bot_x + glow_radius, 300 + glow_radius]
        draw.ellipse(glow_bbox, fill=(180, 200, 255), outline=(100, 150, 255))
        
        # Main nanobot body
        bot_bbox = [bot_x - bot_radius, 300 - bot_radius,
                    bot_x + bot_radius, 300 + bot_radius]
        draw.ellipse(bot_bbox, fill=(50, 100, 200))  # Deep blue
        draw.ellipse(bot_bbox, outline=(0, 50, 150), width=2)  # Dark blue outline
        
        # Add directional indicator on nanobot
        draw.ellipse([bot_x + 5, 295, bot_x + 12, 305], fill=(100, 200, 255))
        
        # Add labels and status information
        title_text = "Nanobot Vein Clog Clearance Simulation"
        draw.text((width//2 - 150, 20), title_text, fill=(0, 0, 0))
        
        # Status text
        if progress < 0.7:
            status = f"Nanobot approaching clog... {int(progress * 100)}%"
            status_color = (0, 100, 0)
        elif progress < 0.85:
            status = f"Clearing clog... {int((progress - 0.7) / 0.15 * 100)}%"
            status_color = (200, 100, 0)
        else:
            status = "Clog cleared! Blood flow restored."
            status_color = (0, 150, 0)
        
        draw.text((50, 500), status, fill=status_color)
        
        # Draw distance indicator
        distance_text = f"Position: {int(bot_x)}px"
        draw.text((width - 250, 500), distance_text, fill=(100, 100, 100))
        
        # Velocity indicator (arrow showing speed)
        arrow_y = 550
        arrow_speed = int(progress * 150)
        draw.line([(100, arrow_y), (100 + arrow_speed, arrow_y)], fill=(100, 100, 200), width=3)
        draw.polygon([(100 + arrow_speed, arrow_y - 5), (100 + arrow_speed, arrow_y + 5),
                      (100 + arrow_speed + 8, arrow_y)], fill=(100, 100, 200))
        draw.text((50, arrow_y + 10), "Speed →", fill=(100, 100, 100))
        
        frames.append(img)
    
    print(f"Generated {len(frames)} frames", flush=True)
    print(f"Saving video to {VIDEO_PATH}...", flush=True)
    imageio.mimsave(VIDEO_PATH, frames, fps=30)
    print(f"✓ Video saved successfully: {VIDEO_PATH}", flush=True)
    return VIDEO_PATH

if __name__ == "__main__":
    video_path = create_nanobot_simulation()
    print(f"\nSimulation complete! Video created at:")
    print(f"  {video_path}")

#!/usr/bin/env python
"""
Advanced Nanobot Simulation with Biological Clog Detection
Simulates a nanobot detecting and clearing a varicose vein clog using:
- Viscosity sensing
- Optical/reflectance detection
- Pressure/flow resistance detection
"""
import os
import math
from PIL import Image, ImageDraw

class VeinSimulation:
    """Simulate blood vessel environment with realistic clog properties."""
    
    def __init__(self, width=900, height=650):
        self.width = width
        self.height = height
        self.vein_top = 200
        self.vein_bottom = 450
        self.vein_center = (self.vein_top + self.vein_bottom) / 2
        
    def get_viscosity_at_position(self, x, y):
        """
        Calculate blood viscosity at position.
        Normal blood viscosity: ~4-5 cP
        Clotted blood viscosity: ~20-50+ cP
        """
        clog_center_x = 450
        clog_center_y = int(self.vein_center)
        clog_radius = 50
        
        # Distance from clog center
        dist = math.sqrt((x - clog_center_x)**2 + (y - clog_center_y)**2)
        
        # Base viscosity of normal blood
        normal_viscosity = 4.5
        
        # Increased viscosity near clog (fibrin, platelets accumulation)
        if dist < clog_radius * 1.5:
            # Gradient: higher viscosity closer to clog
            viscosity_increase = 45 * math.exp(-dist / (clog_radius * 0.7))
            return normal_viscosity + viscosity_increase
        
        return normal_viscosity
    
    def get_optical_reflectance(self, x, y):
        """
        Optical property detection.
        Normal blood: low reflectance (darker)
        Clot: high reflectance (fibrin matrix is denser, more reflective)
        """
        clog_center_x = 450
        clog_center_y = int(self.vein_center)
        clog_radius = 50
        
        dist = math.sqrt((x - clog_center_x)**2 + (y - clog_center_y)**2)
        
        # Normal blood reflectance: 5-10%
        base_reflectance = 0.08
        
        # Clot reflectance increases with proximity
        if dist < clog_radius * 1.5:
            reflectance_increase = 0.85 * math.exp(-dist / (clog_radius * 0.6))
            return base_reflectance + reflectance_increase
        
        return base_reflectance
    
    def get_flow_resistance(self, x, y):
        """
        Calculate flow resistance (inverse of conductivity).
        Normal flow resistance: ~1.0
        Blocked flow resistance: 10-100+
        """
        clog_center_x = 450
        clog_center_y = int(self.vein_center)
        clog_radius = 50
        
        dist = math.sqrt((x - clog_center_x)**2 + (y - clog_center_y)**2)
        
        base_resistance = 1.0
        
        if dist < clog_radius * 1.5:
            resistance_increase = 95 * math.exp(-dist / (clog_radius * 0.8))
            return base_resistance + resistance_increase
        
        return base_resistance


class Nanobot:
    """Represents a nanobot with sensing capabilities."""
    
    def __init__(self, x=50, y=325):
        self.x = x
        self.y = y
        self.radius = 18
        
        # Sensing arrays
        self.viscosity_sensors = 8  # Distributed around the nanobot
        self.optical_sensors = 4
        self.pressure_sensors = 6
        
        # Detection state
        self.clog_detected = False
        self.clog_signal_strength = 0.0
        self.detection_data = {
            'viscosity': 4.5,
            'reflectance': 0.08,
            'resistance': 1.0,
            'position': 'normal_blood'
        }
    
    def sense_environment(self, vein_sim, frame_idx):
        """Use multiple sensor arrays to detect clog."""
        # Sample viscosity from multiple angles
        viscosity_samples = []
        for angle in range(0, 360, 45):  # 8 sensors
            rad = math.radians(angle)
            sensor_x = self.x + self.radius * math.cos(rad)
            sensor_y = self.y + self.radius * math.sin(rad)
            visc = vein_sim.get_viscosity_at_position(sensor_x, sensor_y)
            viscosity_samples.append(visc)
        
        avg_viscosity = sum(viscosity_samples) / len(viscosity_samples)
        viscosity_signal = min(1.0, (avg_viscosity - 4.5) / 45.0)  # Normalize 0-1
        
        # Sample optical reflectance
        reflectance_samples = []
        for angle in range(0, 360, 90):  # 4 sensors
            rad = math.radians(angle)
            sensor_x = self.x + self.radius * 1.5 * math.cos(rad)
            sensor_y = self.y + self.radius * 1.5 * math.sin(rad)
            refl = vein_sim.get_optical_reflectance(sensor_x, sensor_y)
            reflectance_samples.append(refl)
        
        avg_reflectance = sum(reflectance_samples) / len(reflectance_samples)
        reflectance_signal = min(1.0, avg_reflectance / 0.85)  # Normalize
        
        # Sample flow resistance
        resistance_samples = []
        for angle in range(0, 360, 60):  # 6 sensors
            rad = math.radians(angle)
            sensor_x = self.x + self.radius * 2.0 * math.cos(rad)
            sensor_y = self.y + self.radius * 2.0 * math.sin(rad)
            res = vein_sim.get_flow_resistance(sensor_x, sensor_y)
            resistance_samples.append(res)
        
        avg_resistance = sum(resistance_samples) / len(resistance_samples)
        resistance_signal = min(1.0, (avg_resistance - 1.0) / 95.0)  # Normalize
        
        # Combine sensor signals (multi-modal detection)
        self.detection_data = {
            'viscosity': avg_viscosity,
            'reflectance': avg_reflectance,
            'resistance': avg_resistance,
            'viscosity_signal': viscosity_signal,
            'reflectance_signal': reflectance_signal,
            'resistance_signal': resistance_signal,
        }
        
        # Clog detection threshold: if multiple sensors exceed threshold
        threshold = 0.3
        signal_count = sum([
            viscosity_signal > threshold,
            reflectance_signal > threshold,
            resistance_signal > threshold
        ])
        
        # Require at least 2 sensors to trigger clog detection
        if signal_count >= 2:
            self.clog_detected = True
            # Combined signal strength
            self.clog_signal_strength = (viscosity_signal + reflectance_signal + resistance_signal) / 3.0
        else:
            self.clog_signal_strength = max(viscosity_signal, reflectance_signal, resistance_signal)
        
        # Determine position type
        if avg_resistance > 20:
            self.detection_data['position'] = 'CLOG_DETECTED'
        elif avg_resistance > 5:
            self.detection_data['position'] = 'near_clog'
        else:
            self.detection_data['position'] = 'normal_blood'


def draw_blood_cells(draw, x, y, size, color_variation=0):
    """Draw a realistic blood cell (RBC - biconcave disc representation)."""
    # Simplified RBC as overlapping circles
    cell_color = (200 - color_variation, 50 - color_variation, 50 - color_variation)
    bbox = [x - size, y - size, x + size, y + size]
    draw.ellipse(bbox, fill=cell_color, outline=(150, 30, 30))


def create_advanced_simulation():
    """Create biologically realistic nanobot simulation."""
    import imageio
    
    OUTPUT_DIR = "c:\\Sansten\\vRobot\\outputs"
    VIDEO_PATH = os.path.join(OUTPUT_DIR, "nanobot_sim_biological.mp4")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Creating biologically-realistic nanobot simulation...", flush=True)
    
    vein_sim = VeinSimulation(width=900, height=650)
    nanobot = Nanobot()
    
    frames = []
    num_frames = 300
    
    for frame_idx in range(num_frames):
        # Create background
        img = Image.new('RGB', (vein_sim.width, vein_sim.height), color=(255, 240, 240))
        draw = ImageDraw.Draw(img)
        
        # === Draw vein structure ===
        # Vein walls (more realistic)
        draw.rectangle([0, vein_sim.vein_top - 10, vein_sim.width, vein_sim.vein_top], 
                      fill=(100, 100, 150))  # Endothelium
        draw.rectangle([0, vein_sim.vein_bottom, vein_sim.width, vein_sim.vein_bottom + 10], 
                      fill=(100, 100, 150))
        
        # === Draw blood cells (background) ===
        import random
        random.seed(frame_idx // 5)  # Stable but changing
        for i in range(20):
            cell_x = (frame_idx + i * 50) % vein_sim.width
            cell_y = vein_sim.vein_center + (i % 3 - 1) * 30
            if vein_sim.vein_top < cell_y < vein_sim.vein_bottom:
                draw_blood_cells(draw, cell_x, cell_y, 4)
        
        # === Draw clog (thrombus) with realistic structure ===
        clog_center_x = 450
        clog_center_y = int(vein_sim.vein_center)
        clog_radius = 50
        
        # Draw fibrin matrix (network structure)
        draw.rectangle([clog_center_x - clog_radius, clog_center_y - clog_radius,
                       clog_center_x + clog_radius, clog_center_y + clog_radius],
                      fill=(220, 80, 80), outline=(150, 0, 0), width=3)  # Darker, opaque clot
        
        # Draw platelets in clot
        for offset_angle in range(0, 360, 40):
            rad = math.radians(offset_angle)
            platelet_x = clog_center_x + (clog_radius * 0.6) * math.cos(rad)
            platelet_y = clog_center_y + (clog_radius * 0.6) * math.sin(rad)
            draw.ellipse([platelet_x - 4, platelet_y - 4, platelet_x + 4, platelet_y + 4],
                        fill=(180, 40, 40))
        
        # === Draw nanobot ===
        nanobot.x = 50 + frame_idx * 2.5
        nanobot.sense_environment(vein_sim, frame_idx)
        
        # Nanobot glow intensity based on detection
        glow_intensity = int(nanobot.clog_signal_strength * 200)
        glow_radius = nanobot.radius + 12
        glow_color = (100 + glow_intensity, 180, 255)
        
        glow_bbox = [nanobot.x - glow_radius, nanobot.y - glow_radius,
                    nanobot.x + glow_radius, nanobot.y + glow_radius]
        draw.ellipse(glow_bbox, fill=glow_color, outline=(100, 150, 255), width=1)
        
        # Main nanobot body (changes color based on detection)
        if nanobot.clog_detected:
            bot_color = (255, 150, 50)  # Orange when detecting clog
            bot_outline = (200, 100, 0)
        else:
            bot_color = (50, 100, 200)  # Blue in normal mode
            bot_outline = (0, 50, 150)
        
        bot_bbox = [nanobot.x - nanobot.radius, nanobot.y - nanobot.radius,
                   nanobot.x + nanobot.radius, nanobot.y + nanobot.radius]
        draw.ellipse(bot_bbox, fill=bot_color, outline=bot_outline, width=2)
        
        # Draw sensor points
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            sensor_x = nanobot.x + (nanobot.radius + 6) * math.cos(rad)
            sensor_y = nanobot.y + (nanobot.radius + 6) * math.sin(rad)
            draw.ellipse([sensor_x - 2, sensor_y - 2, sensor_x + 2, sensor_y + 2],
                        fill=(255, 200, 0))  # Yellow sensor points
        
        # === Display sensor data ===
        progress = frame_idx / num_frames
        
        # Title and description
        draw.text((20, 15), "Biological Clog Detection - Multi-Modal Sensing", fill=(0, 0, 0))
        draw.text((20, 35), "Viscosity | Optical | Flow Resistance", fill=(60, 60, 60))
        
        # Sensor readings as bars
        bar_y = 60
        bar_height = 15
        bar_width = 200
        
        # Viscosity bar
        draw.rectangle([20, bar_y, 20 + bar_width, bar_y + bar_height], outline=(100, 100, 100))
        visc_fill = int(nanobot.detection_data['viscosity_signal'] * bar_width)
        if visc_fill > 0:
            draw.rectangle([20, bar_y, 20 + visc_fill, bar_y + bar_height], 
                          fill=(255, 100, 100))  # Red for viscosity
        draw.text((230, bar_y), f"Viscosity: {nanobot.detection_data['viscosity']:.1f} cP", fill=(0, 0, 0))
        
        # Optical bar
        bar_y += 20
        draw.rectangle([20, bar_y, 20 + bar_width, bar_y + bar_height], outline=(100, 100, 100))
        opt_fill = int(nanobot.detection_data['reflectance_signal'] * bar_width)
        if opt_fill > 0:
            draw.rectangle([20, bar_y, 20 + opt_fill, bar_y + bar_height], 
                          fill=(100, 150, 255))  # Blue for optical
        draw.text((230, bar_y), f"Reflectance: {nanobot.detection_data['reflectance']:.3f}", fill=(0, 0, 0))
        
        # Flow Resistance bar
        bar_y += 20
        draw.rectangle([20, bar_y, 20 + bar_width, bar_y + bar_height], outline=(100, 100, 100))
        res_fill = int(nanobot.detection_data['resistance_signal'] * bar_width)
        if res_fill > 0:
            draw.rectangle([20, bar_y, 20 + res_fill, bar_y + bar_height], 
                          fill=(100, 200, 100))  # Green for resistance
        draw.text((230, bar_y), f"Flow Resistance: {nanobot.detection_data['resistance']:.1f}", fill=(0, 0, 0))
        
        # Position status
        status_text = f"Position: {nanobot.detection_data['position']}"
        status_color = (255, 100, 0) if nanobot.clog_detected else (0, 100, 0)
        draw.text((20, bar_y + 30), status_text, fill=status_color)
        
        # Combined signal strength
        draw.text((20, bar_y + 50), 
                 f"Combined Signal: {nanobot.clog_signal_strength:.2f} / 1.0", 
                 fill=(0, 0, 0))
        
        # Overall status
        if nanobot.clog_detected:
            status = "🔴 CLOG DETECTED - Activating clearance protocol"
            msg_color = (255, 0, 0)
        elif nanobot.clog_signal_strength > 0.2:
            status = "🟡 CLOG APPROACHING - Sensors increasing sensitivity"
            msg_color = (255, 150, 0)
        else:
            status = "🟢 Normal blood - No blockage detected"
            msg_color = (0, 150, 0)
        
        draw.text((20, vein_sim.height - 50), status, fill=msg_color)
        
        # Progress indicator
        progress_bar_width = 400
        draw.rectangle([20, vein_sim.height - 20, 20 + progress_bar_width, vein_sim.height - 10],
                      outline=(100, 100, 100))
        draw.rectangle([20, vein_sim.height - 20, 20 + int(progress * progress_bar_width), vein_sim.height - 10],
                      fill=(100, 200, 100))
        
        frames.append(img)
    
    print(f"Generated {len(frames)} frames with biological detection", flush=True)
    print(f"Saving video to {VIDEO_PATH}...", flush=True)
    imageio.mimsave(VIDEO_PATH, frames, fps=30)
    print(f"✓ Advanced simulation saved: {VIDEO_PATH}", flush=True)
    return VIDEO_PATH


if __name__ == "__main__":
    video_path = create_advanced_simulation()
    print(f"\nBiological simulation complete!")
    print(f"Video: {video_path}")
    print("\nDetection methods simulated:")
    print("  • Viscosity sensing (4.5 cP normal → 45+ cP in clot)")
    print("  • Optical reflectance detection (8% normal → 85% in clot)")
    print("  • Flow resistance measurement (1.0 normal → 95+ in clot)")
    print("  • Multi-modal signal fusion (requires 2+ sensors)")

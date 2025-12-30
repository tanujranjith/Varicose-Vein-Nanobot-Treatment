#!/usr/bin/env python
"""
Advanced Nanobot Simulation with Realistic Movement and Clearing
Based on Cornell University 100-250 micron light-powered microbots
Includes:
- Realistic acceleration/deceleration movement physics
- Proper clog detection and clearing behavior
- Stationary clearing phase until blockage is resolved
"""
import os
import math
from PIL import Image, ImageDraw

class RealisticNanobot:
    """
    Realistic nanobot with physics-based movement and clearing capability.
    Based on Cornell light-powered microbots (100-250 microns).
    """
    
    def __init__(self, x=50, y=325):
        self.x = x
        self.y = y
        self.radius = 18
        
        # Physics parameters (realistic for 100-250 micron robot)
        self.velocity = 0.0  # pixels/frame
        self.acceleration = 0.0
        self.max_velocity = 3.5  # pixels/frame (~500 μm/s)
        self.max_acceleration = 0.15  # pixels/frame² (realistic for microbot)
        
        # State machine
        self.state = "SEARCHING"  # SEARCHING, APPROACHING, CLEARING, CONTINUING
        self.target_reached = False
        
        # Sensing
        self.clog_detected = False
        self.clog_distance = float('inf')
        self.detection_signal = 0.0
        
        # Clearing parameters
        self.clearing_progress = 0.0  # 0.0 to 1.0
        self.clearing_rate = 0.01  # How fast clog is cleared per frame
        self.is_clearing = False
        self.clearing_time = 0
        self.clearing_time_needed = 200  # frames to clear FULL-WIDTH clog (was 100)
        
        # Sensor data
        self.sensor_data = {
            'viscosity': 4.5,
            'reflectance': 0.08,
            'resistance': 1.0,
        }
    
    def update_sensors(self, vein_sim, frame_idx):
        """Update sensor readings from environment."""
        # Viscosity sensing
        visc_samples = []
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            sensor_x = self.x + self.radius * math.cos(rad)
            sensor_y = self.y + self.radius * math.sin(rad)
            visc = vein_sim.get_viscosity_at_position(sensor_x, sensor_y)
            visc_samples.append(visc)
        
        avg_viscosity = sum(visc_samples) / len(visc_samples)
        
        # Optical sensing
        refl_samples = []
        for angle in range(0, 360, 90):
            rad = math.radians(angle)
            sensor_x = self.x + self.radius * 1.5 * math.cos(rad)
            sensor_y = self.y + self.radius * 1.5 * math.sin(rad)
            refl = vein_sim.get_optical_reflectance(sensor_x, sensor_y)
            refl_samples.append(refl)
        
        avg_reflectance = sum(refl_samples) / len(refl_samples)
        
        # Resistance sensing
        res_samples = []
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            sensor_x = self.x + self.radius * 2.0 * math.cos(rad)
            sensor_y = self.y + self.radius * 2.0 * math.sin(rad)
            res = vein_sim.get_flow_resistance(sensor_x, sensor_y)
            res_samples.append(res)
        
        avg_resistance = sum(res_samples) / len(res_samples)
        
        # Store sensor data
        self.sensor_data = {
            'viscosity': avg_viscosity,
            'reflectance': avg_reflectance,
            'resistance': avg_resistance,
        }
        
        # Calculate normalized signals (0-1)
        visc_signal = min(1.0, (avg_viscosity - 4.5) / 45.0)
        refl_signal = min(1.0, avg_reflectance / 0.85)
        res_signal = min(1.0, (avg_resistance - 1.0) / 95.0)
        
        # Multi-modal detection
        signal_count = sum([
            visc_signal > 0.3,
            refl_signal > 0.3,
            res_signal > 0.3
        ])
        
        if signal_count >= 2:
            self.clog_detected = True
            self.detection_signal = (visc_signal + refl_signal + res_signal) / 3.0
            self.clog_distance = max(0, avg_resistance - 5)  # Distance proxy
        else:
            self.clog_detected = False
            self.detection_signal = max(visc_signal, refl_signal, res_signal)
            self.clog_distance = float('inf')
    
    def update_movement(self, target_x):
        """
        Update nanobot movement with realistic physics.
        Uses acceleration/deceleration for natural motion.
        """
        # Calculate desired direction
        dx = target_x - self.x
        
        if self.state == "SEARCHING":
            # Normal searching: accelerate toward target
            if dx > 0:
                # Accelerate if below max velocity
                if self.velocity < self.max_velocity:
                    self.acceleration = self.max_acceleration
                else:
                    self.acceleration = 0
            else:
                self.acceleration = 0
        
        elif self.state == "APPROACHING":
            # Approaching clog: decelerate for precision
            desired_vel = 1.0  # Slower approach
            if self.velocity > desired_vel:
                self.acceleration = -self.max_acceleration * 0.8  # Gentle deceleration
            elif self.velocity < desired_vel:
                self.acceleration = self.max_acceleration * 0.5
            else:
                self.acceleration = 0
        
        elif self.state == "CLEARING":
            # Stop completely while clearing
            self.acceleration = -self.velocity * 0.3  # Friction to stop
            if abs(self.velocity) < 0.05:
                self.velocity = 0
                self.acceleration = 0
        
        elif self.state == "CONTINUING":
            # Resume after clearing: accelerate smoothly
            if self.velocity < self.max_velocity:
                self.acceleration = self.max_acceleration
            else:
                self.acceleration = 0
        
        # Apply physics: v = v + a
        self.velocity += self.acceleration
        
        # Clamp velocity
        self.velocity = max(-self.max_velocity, min(self.max_velocity, self.velocity))
        
        # Update position: x = x + v
        self.x += self.velocity
    
    def update_state(self, frame_idx):
        """
        Update state machine based on detection and clearing progress.
        Early clearing: Start clearing as soon as clog is detected (not just when close).
        """
        if self.clog_detected and self.detection_signal > 0.4:
            if self.state == "SEARCHING":
                # Start approaching immediately when clog detected
                self.state = "APPROACHING"
            
            # Start clearing as soon as signal is strong enough (earlier detection)
            if self.detection_signal > 0.6 and self.state == "APPROACHING":
                self.state = "CLEARING"
                self.is_clearing = True
                self.clearing_time = 0
        
        # Update clearing progress
        if self.state == "CLEARING" and self.is_clearing:
            self.clearing_time += 1
            self.clearing_progress = min(1.0, self.clearing_time / self.clearing_time_needed)
            
            # Clearing complete
            if self.clearing_progress >= 1.0:
                self.is_clearing = False
                self.clog_detected = False
                self.state = "CONTINUING"
        
        # Resume movement after clearing
        if self.state == "CONTINUING" and self.velocity >= self.max_velocity * 0.8:
            self.state = "SEARCHING"


class VeinEnvironment:
    """Vein environment with clog properties."""
    
    def __init__(self, width=900, height=650):
        self.width = width
        self.height = height
        self.vein_top = 200
        self.vein_bottom = 450
        self.vein_center = (self.vein_top + self.vein_bottom) / 2
        self.vein_width = self.vein_bottom - self.vein_top
        
        # Multiple clogs - each spans full vein width
        self.clogs = [
            {'center_x': 300, 'density': 1.0, 'cleared': False},
            {'center_x': 550, 'density': 1.0, 'cleared': False},
            {'center_x': 750, 'density': 1.0, 'cleared': False},
        ]
        self.current_clog_idx = 0
        self.vein_width_coverage = self.vein_width  # FULL WIDTH blockage
    
    def is_in_clog_zone(self, x, y):
        """Check if position is in a clog zone."""
        for clog in self.clogs:
            if clog['cleared']:
                continue  # Skip cleared clogs
            clog_center_x = clog['center_x']
            in_x = abs(x - clog_center_x) < 80  # Clog zone width
            in_y = self.vein_top <= y <= self.vein_bottom
            if in_x and in_y:
                return True, clog
        return False, None
    
    def get_current_clog(self, x):
        """Get the next un-cleared clog that bot will encounter."""
        for idx, clog in enumerate(self.clogs):
            if not clog['cleared'] and x < clog['center_x']:
                return idx, clog
        return None, None
    
    def get_viscosity_at_position(self, x, y):
        """Viscosity gradient around clogs (full width)."""
        normal_viscosity = 4.5
        max_viscosity_increase = 0
        
        # Check all clogs
        for clog in self.clogs:
            if clog['cleared']:
                continue
            clog_center_x = clog['center_x']
            if abs(x - clog_center_x) < 100:  # In range of any clog
                distance_from_center_x = abs(x - clog_center_x)
                proximity_factor = max(0, 1.0 - distance_from_center_x / 80.0)
                viscosity_increase = 45 * clog['density'] * proximity_factor
                max_viscosity_increase = max(max_viscosity_increase, viscosity_increase)
        
        return normal_viscosity + max_viscosity_increase
    
    def get_optical_reflectance(self, x, y):
        """Optical reflectance around clogs (full width)."""
        base_reflectance = 0.08
        max_reflectance_increase = 0
        
        # Check all clogs
        for clog in self.clogs:
            if clog['cleared']:
                continue
            clog_center_x = clog['center_x']
            if abs(x - clog_center_x) < 100:
                distance_from_center_x = abs(x - clog_center_x)
                proximity_factor = max(0, 1.0 - distance_from_center_x / 80.0)
                reflectance_increase = 0.85 * clog['density'] * proximity_factor
                max_reflectance_increase = max(max_reflectance_increase, reflectance_increase)
        
        return base_reflectance + max_reflectance_increase
    
    def get_flow_resistance(self, x, y):
        """Flow resistance around clogs (full width)."""
        base_resistance = 1.0
        max_resistance_increase = 0
        
        # Check all clogs
        for clog in self.clogs:
            if clog['cleared']:
                continue
            clog_center_x = clog['center_x']
            if abs(x - clog_center_x) < 100:
                distance_from_center_x = abs(x - clog_center_x)
                proximity_factor = max(0, 1.0 - distance_from_center_x / 80.0)
                resistance_increase = 95 * clog['density'] * proximity_factor
                max_resistance_increase = max(max_resistance_increase, resistance_increase)
        
        return base_resistance + max_resistance_increase


def create_realistic_simulation():
    """Create simulation with realistic movement and clearing."""
    import imageio
    
    OUTPUT_DIR = "c:\\Sansten\\vRobot\\outputs"
    VIDEO_PATH = os.path.join(OUTPUT_DIR, "nanobot_sim_realistic.mp4")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Creating realistic nanobot simulation with MULTIPLE clogs...", flush=True)
    
    vein_sim = VeinEnvironment(width=900, height=650)
    nanobot = RealisticNanobot()
    
    frames = []
    num_frames = 900  # Extended to handle 3 clogs (was 600)
    
    for frame_idx in range(num_frames):
        # Update nanobot sensors
        nanobot.update_sensors(vein_sim, frame_idx)
        
        # Find next unclearedclog as target
        clog_idx, next_clog = vein_sim.get_current_clog(nanobot.x)
        if next_clog:
            target_x = next_clog['center_x'] + 100
        else:
            # All clogs cleared, continue forward
            target_x = 850
        
        # Update movement with physics
        nanobot.update_movement(target_x)
        
        # Update state machine
        nanobot.update_state(frame_idx)
        
        # Update clog density if clearing (full removal required)
        if nanobot.is_clearing:
            # Find the current clog being cleared
            clog_idx, current_clog = vein_sim.get_current_clog(nanobot.x)
            if current_clog is None:
                # Try to find any clog in range
                for clog in vein_sim.clogs:
                    if not clog['cleared'] and abs(nanobot.x - clog['center_x']) < 150:
                        current_clog = clog
                        break
            
            if current_clog:
                # Decrease density (0.0 = fully cleared)
                current_clog['density'] = max(0.0, 1.0 - nanobot.clearing_progress)
                # Mark as cleared when done
                if nanobot.clearing_progress >= 1.0:
                    current_clog['density'] = 0.0
                    current_clog['cleared'] = True
        
        # === Draw frame ===
        img = Image.new('RGB', (vein_sim.width, vein_sim.height), color=(255, 240, 240))
        draw = ImageDraw.Draw(img)
        
        # Vein structure
        draw.rectangle([0, vein_sim.vein_top - 10, vein_sim.width, vein_sim.vein_top], 
                      fill=(100, 100, 150))
        draw.rectangle([0, vein_sim.vein_bottom, vein_sim.width, vein_sim.vein_bottom + 10], 
                      fill=(100, 100, 150))
        
        # Blood cells background
        import random
        random.seed(frame_idx // 5)
        for i in range(20):
            cell_x = (frame_idx + i * 50) % vein_sim.width
            cell_y = vein_sim.vein_center + (i % 3 - 1) * 30
            if vein_sim.vein_top < cell_y < vein_sim.vein_bottom:
                draw.ellipse([cell_x - 4, cell_y - 4, cell_x + 4, cell_y + 4],
                            fill=(200, 50, 50), outline=(150, 30, 30))
        
        # === Draw all clogs (full-width blockages) ===
        for clog in vein_sim.clogs:
            if clog['density'] > 0.01:  # Only draw if clog still exists
                clog_center_x = clog['center_x']
                # Clog spans full vein width
                clog_left = clog_center_x - 80
                clog_right = clog_center_x + 80
                clog_top = int(vein_sim.vein_top)
                clog_bottom = int(vein_sim.vein_bottom)
                
                # Draw clog with density-based opacity (darker = denser)
                clog_color = (int(220 * clog['density']), 
                             int(80 * clog['density']), 
                             int(80 * clog['density']))
                outline_color = (int(150 * clog['density']), 0, 0)
                
                draw.rectangle([clog_left, clog_top, clog_right, clog_bottom], 
                              fill=clog_color, outline=outline_color, width=3)
                
                # Platelets distributed across full blockage
                for y_offset in range(int(vein_sim.vein_top), int(vein_sim.vein_bottom), 30):
                    for x_offset in range(clog_left, clog_right, 30):
                        if clog['density'] > 0.1:  # Only show platelets if clog exists
                            platelet_color = (int(180 * clog['density']), 
                                            int(40 * clog['density']), 
                                            int(40 * clog['density']))
                            draw.ellipse([x_offset - 5, y_offset - 5, x_offset + 5, y_offset + 5],
                                        fill=platelet_color)
        
        # === Draw nanobot with state indication ===
        # Glow based on state and detection
        if nanobot.state == "CLEARING":
            glow_color = (255, 100, 50)  # Orange-red during clearing
            glow_intensity = 200
        elif nanobot.clog_detected:
            glow_color = (255, 150, 100)  # Orange when detecting
            glow_intensity = int(nanobot.detection_signal * 200)
        else:
            glow_color = (100, 180, 255)  # Blue when searching
            glow_intensity = 100
        
        glow_radius = nanobot.radius + 12
        glow_bbox = [nanobot.x - glow_radius, nanobot.y - glow_radius,
                    nanobot.x + glow_radius, nanobot.y + glow_radius]
        draw.ellipse(glow_bbox, fill=glow_color, outline=(100, 150, 255), width=1)
        
        # Main body color based on state
        if nanobot.state == "CLEARING":
            bot_color = (255, 100, 0)  # Bright orange
            bot_outline = (200, 50, 0)
        elif nanobot.clog_detected:
            bot_color = (200, 120, 50)  # Orange
            bot_outline = (150, 70, 0)
        else:
            bot_color = (50, 100, 200)  # Blue
            bot_outline = (0, 50, 150)
        
        bot_bbox = [nanobot.x - nanobot.radius, nanobot.y - nanobot.radius,
                   nanobot.x + nanobot.radius, nanobot.y + nanobot.radius]
        draw.ellipse(bot_bbox, fill=bot_color, outline=bot_outline, width=2)
        
        # Sensor points
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            sensor_x = nanobot.x + (nanobot.radius + 6) * math.cos(rad)
            sensor_y = nanobot.y + (nanobot.radius + 6) * math.sin(rad)
            draw.ellipse([sensor_x - 2, sensor_y - 2, sensor_x + 2, sensor_y + 2],
                        fill=(255, 200, 0))
        
        # Movement vectors (showing velocity)
        if nanobot.velocity > 0.1:
            velocity_arrow_length = min(30, int(nanobot.velocity * 10))
            arrow_end_x = nanobot.x + velocity_arrow_length
            draw.line([nanobot.x, nanobot.y - 5, arrow_end_x, nanobot.y - 5],
                     fill=(100, 200, 100), width=2)
            # Arrow head
            draw.polygon([(arrow_end_x, nanobot.y - 5),
                         (arrow_end_x - 5, nanobot.y - 8),
                         (arrow_end_x - 5, nanobot.y - 2)],
                        fill=(100, 200, 100))
        
        # === Display information ===
        draw.text((20, 15), "Realistic Nanobot Movement & Clearing", fill=(0, 0, 0))
        draw.text((20, 35), "Based on Cornell Light-Powered Microbots (100-250 μm)", fill=(60, 60, 60))
        
        # Clog status display
        cleared_count = sum(1 for clog in vein_sim.clogs if clog['cleared'])
        draw.text((20, 50), f"Clogs: {cleared_count}/{len(vein_sim.clogs)} cleared", fill=(100, 100, 100))
        
        # State display
        state_colors = {
            "SEARCHING": (0, 150, 0),
            "APPROACHING": (200, 150, 0),
            "CLEARING": (255, 0, 0),
            "CONTINUING": (0, 100, 200)
        }
        state_color = state_colors.get(nanobot.state, (0, 0, 0))
        draw.text((20, 70), f"State: {nanobot.state}", fill=state_color)
        
        # Velocity display
        draw.text((20, 90), f"Velocity: {nanobot.velocity:.2f} px/frame", fill=(0, 0, 0))
        draw.text((20, 110), f"Acceleration: {nanobot.acceleration:.3f} px/frame²", fill=(0, 0, 0))
        
        # Sensor readings
        visc_signal = min(1.0, (nanobot.sensor_data['viscosity'] - 4.5) / 45.0)
        refl_signal = min(1.0, nanobot.sensor_data['reflectance'] / 0.85)
        res_signal = min(1.0, (nanobot.sensor_data['resistance'] - 1.0) / 95.0)
        
        bar_y = 135
        bar_width = 200
        
        # Viscosity
        draw.rectangle([20, bar_y, 20 + bar_width, bar_y + 15], outline=(100, 100, 100))
        draw.rectangle([20, bar_y, 20 + int(visc_signal * bar_width), bar_y + 15], 
                      fill=(255, 100, 100))
        draw.text((230, bar_y), f"Viscosity: {nanobot.sensor_data['viscosity']:.1f} cP", fill=(0, 0, 0))
        
        # Reflectance
        bar_y += 20
        draw.rectangle([20, bar_y, 20 + bar_width, bar_y + 15], outline=(100, 100, 100))
        draw.rectangle([20, bar_y, 20 + int(refl_signal * bar_width), bar_y + 15], 
                      fill=(100, 150, 255))
        draw.text((230, bar_y), f"Reflectance: {nanobot.sensor_data['reflectance']:.3f}", fill=(0, 0, 0))
        
        # Resistance
        bar_y += 20
        draw.rectangle([20, bar_y, 20 + bar_width, bar_y + 15], outline=(100, 100, 100))
        draw.rectangle([20, bar_y, 20 + int(res_signal * bar_width), bar_y + 15], 
                      fill=(100, 200, 100))
        draw.text((230, bar_y), f"Resistance: {nanobot.sensor_data['resistance']:.1f}", fill=(0, 0, 0))
        
        # Clog detection
        if nanobot.clog_detected:
            status = f"🔴 CLOG DETECTED (Signal: {nanobot.detection_signal:.2f})"
            status_color = (255, 0, 0)
        else:
            status = "🟢 Searching for blockage"
            status_color = (0, 150, 0)
        
        draw.text((20, bar_y + 30), status, fill=status_color)
        
        # === Clearing phase display ===
        if nanobot.is_clearing:
            clearing_y = vein_sim.height - 100
            draw.text((20, clearing_y), "CLEARING IN PROGRESS", fill=(255, 0, 0))
            draw.text((20, clearing_y + 20), f"Clearing Progress: {nanobot.clearing_progress*100:.0f}%", 
                     fill=(255, 100, 0))
            
            # Progress bar
            progress_bar_width = 400
            draw.rectangle([20, clearing_y + 45, 20 + progress_bar_width, clearing_y + 60],
                          outline=(100, 100, 100))
            draw.rectangle([20, clearing_y + 45, 20 + int(nanobot.clearing_progress * progress_bar_width), 
                           clearing_y + 60], fill=(255, 100, 0))
            
            draw.text((20, clearing_y + 65), "Nanobot is STATIONARY - clearing blockage...", 
                     fill=(255, 0, 0))
        
        frames.append(img)
    
    print(f"Generated {len(frames)} frames with realistic movement", flush=True)
    print(f"Saving video to {VIDEO_PATH}...", flush=True)
    imageio.mimsave(VIDEO_PATH, frames, fps=30)
    print(f"✓ Realistic simulation saved: {VIDEO_PATH}", flush=True)
    return VIDEO_PATH


if __name__ == "__main__":
    video_path = create_realistic_simulation()
    print(f"\nRealistic nanobot simulation complete!")
    print(f"Video: {video_path}")
    print("\nRealistic features:")
    print("  • Physics-based acceleration/deceleration")
    print("  • Natural motion with velocity changes")
    print("  • Proper approach behavior (slower near clog)")
    print("  • STATIONARY clearing phase (stops until clog cleared)")
    print("  • Clog progressively shrinks during clearing")
    print("  • Resume movement after clearing complete")
    print("  • Based on Cornell light-powered microbots (100-250 μm)")

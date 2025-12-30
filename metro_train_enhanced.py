#!/usr/bin/env python3
"""
NANOBOT METRO TRAIN - ENHANCED CLINICAL SIMULATION
===================================================

Improvements:
1. Smooth animation when coaches rejoin (gradual positioning)
2. Ellipse color reflects medicine level: White (empty) → Blue (full)
3. Clot size shrinks visually as medicine applied
4. Clinical parameters: Viscosity, Reflectance, Resistance monitoring
5. Real-time status display in video

Initial Formation: C1 → C2 → C3 → C4 → C5 (C5 is leader)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Ellipse, Circle, Rectangle
import cv2


class NanobotCoach:
    def __init__(self, coach_label, initial_position, x, y, medicine_capacity=2.0):
        self.label = coach_label
        self.pos = initial_position
        self.x = x
        self.y = y
        self.medicine_capacity = medicine_capacity
        self.medicine_current = medicine_capacity
        self.in_formation = True
        self.at_clot = False
        self.delivered_amount = 0.0
        self.target_x = None  # For smooth animation
        self.target_y = None
        self.reattaching = False
    
    def update_position(self, vx):
        self.x += vx
    
    def move_to_position(self, target_x, target_y, speed=1.0):
        """Smooth movement toward target position"""
        if target_x is not None:
            dx = target_x - self.x
            dy = target_y - self.y
            distance = np.sqrt(dx**2 + dy**2)
            
            if distance > speed:
                self.x += (dx / distance) * speed
                self.y += (dy / distance) * speed
            else:
                self.x = target_x
                self.y = target_y
                return True  # Reached target
        return False
    
    def dispense_medicine(self, ml_per_frame=0.05):
        dispensed = min(ml_per_frame, self.medicine_current)
        self.medicine_current -= dispensed
        self.delivered_amount += dispensed
        return dispensed
    
    def get_color(self):
        """Color based on medicine level: White (empty) to Blue (full)"""
        if self.at_clot:
            return 'lightcoral'
        
        ratio = self.medicine_current / self.medicine_capacity
        
        # White (0%) to Blue (100%) gradient
        if ratio >= 0.9:
            return 'darkblue'
        elif ratio >= 0.7:
            return 'steelblue'
        elif ratio >= 0.5:
            return 'skyblue'
        elif ratio >= 0.25:
            return 'lightblue'
        elif ratio > 0.01:
            return 'aliceblue'
        else:
            return 'white'


class ClotModel:
    """Physical model of blood clot"""
    
    def __init__(self):
        self.size_percent = 100.0  # Visual size
        self.viscosity = 100.0  # cP (centiPoise)
        self.reflectance = 95.0  # % (optical property)
        self.resistance = 100.0  # Resistance to flow
    
    def apply_medicine(self, ml_amount):
        """Update clot properties with medicine application"""
        # Dissolution
        dissolution_per_ml = 100.0 / 6.5  # 15.38%
        size_reduction = ml_amount * dissolution_per_ml
        self.size_percent = max(0, self.size_percent - size_reduction)
        
        # Viscosity decreases (clot becomes less viscous)
        viscosity_reduction = ml_amount * 10.0  # 10 cP per ml
        self.viscosity = max(0, self.viscosity - viscosity_reduction)
        
        # Reflectance decreases (optical changes)
        reflectance_reduction = ml_amount * 7.0  # 7% per ml
        self.reflectance = max(0, self.reflectance - reflectance_reduction)
        
        # Resistance decreases (flow improves)
        resistance_reduction = ml_amount * 10.0
        self.resistance = max(0, self.resistance - resistance_reduction)
    
    def is_dissolved(self):
        """Check if clot is completely dissolved"""
        return self.size_percent <= 0


class MetroTrainSwarm:
    def __init__(self, medicine_per_coach=2.0, clot_required=6.5):
        self.coaches = []
        self.medicine_per_coach = medicine_per_coach
        self.clot_required = clot_required
        self.medicine_threshold = clot_required + 2.0  # 8.5ml
        
        self.catheter_x = 50
        self.catheter_y = 500
        self.target_x = 700
        self.target_y = 500
        
        # Initialize coaches
        coach_spacing = 35
        coach_labels = ['C1', 'C2', 'C3', 'C4', 'C5']
        
        for pos, label in enumerate(coach_labels):
            coach_x = self.catheter_x + (pos * coach_spacing)
            coach = NanobotCoach(label, pos, coach_x, self.catheter_y, medicine_capacity=medicine_per_coach)
            self.coaches.append(coach)
        
        # Clot model
        self.clot = ClotModel()
        
        # Simulation state
        self.time = 0.0
        self.frame = 0
        self.max_frames = 3500
        self.delivery_log = []
        self.total_medicine_applied = 0.0
        self.current_state = "ENTERING"
        self.delivery_cycle_count = 0
        self.medicine_effect = 0.0
    
    def get_formation(self):
        return sorted([c for c in self.coaches if c.in_formation], key=lambda c: c.x)
    
    def get_waiting_coaches(self):
        return [c for c in self.coaches if c.at_clot]
    
    def get_leader(self):
        formation = self.get_formation()
        return max(formation, key=lambda c: c.x) if formation else None
    
    def move_formation(self):
        """Move entire formation toward clot"""
        formation = self.get_formation()
        if not formation:
            return
        
        leader = max(formation, key=lambda c: c.x)
        distance_to_target = self.target_x - leader.x
        
        if self.current_state == "ENTERING":
            if leader.x < self.catheter_x + 60:
                for coach in formation:
                    coach.update_position(3.0)
            else:
                self.current_state = "APPROACHING"
        
        elif self.current_state == "APPROACHING":
            if distance_to_target > 5:
                if distance_to_target > 300:
                    vx = 4.0
                elif distance_to_target > 200:
                    vx = 3.5
                elif distance_to_target > 100:
                    vx = 3.0
                elif distance_to_target > 50:
                    vx = 2.0
                elif distance_to_target > 20:
                    vx = 1.0
                else:
                    vx = 0.3
                
                for coach in formation:
                    coach.update_position(vx)
            else:
                self.current_state = "DELIVERING"
    
    def deliver_medicine_to_clot(self):
        """Leader delivers medicine"""
        if self.current_state != "DELIVERING" or self.clot.size_percent <= 0:
            return
        
        formation = self.get_formation()
        if not formation:
            return
        
        leader = max(formation, key=lambda c: c.x)
        distance_to_clot = abs(self.target_x - leader.x)
        
        if distance_to_clot <= 15:
            if leader.medicine_current > 0:
                # Deliver medicine
                dispensed = leader.dispense_medicine(ml_per_frame=0.05)
                self.total_medicine_applied += dispensed
                self.medicine_effect += dispensed
                
                # Update clot model
                self.clot.apply_medicine(dispensed)
                
                # Log delivery
                if not self.delivery_log or self.delivery_log[-1]['coach_label'] != leader.label:
                    self.delivery_log.append({
                        'frame': self.frame,
                        'time': self.time,
                        'coach_label': leader.label,
                        'medicine_applied': 0.0,
                        'total_applied': self.total_medicine_applied,
                        'clot_size': self.clot.size_percent,
                        'viscosity': self.clot.viscosity,
                        'reflectance': self.clot.reflectance,
                        'resistance': self.clot.resistance,
                    })
                
                if self.delivery_log:
                    self.delivery_log[-1]['medicine_applied'] += dispensed
            
            else:
                # Leader medicine empty - detach and wait
                leader.in_formation = False
                leader.at_clot = True
                leader.x = self.target_x
                leader.y = self.target_y
                leader.target_x = None
                leader.target_y = None
                self.delivery_cycle_count += 1
                self.current_state = "APPROACHING"
    
    def attach_waiting_coaches(self):
        """Smooth animation: waiting coaches gradually move to back of formation"""
        waiting = self.get_waiting_coaches()
        formation = self.get_formation()
        
        if not waiting or not formation:
            return
        
        leader = max(formation, key=lambda c: c.x)
        distance_to_clot = abs(self.target_x - leader.x)
        
        # Start smooth attachment when approaching clot
        if distance_to_clot <= 100:
            leftmost = min(formation, key=lambda c: c.x)
            
            for waiting_coach in waiting:
                if not waiting_coach.reattaching:
                    # Start smooth movement
                    waiting_coach.target_x = leftmost.x - 35
                    waiting_coach.target_y = leftmost.y
                    waiting_coach.reattaching = True
                
                # Move smoothly toward target
                reached = waiting_coach.move_to_position(
                    waiting_coach.target_x,
                    waiting_coach.target_y,
                    speed=2.0
                )
                
                if reached:
                    # Reattached
                    waiting_coach.at_clot = False
                    waiting_coach.in_formation = True
                    waiting_coach.reattaching = False
    
    def check_clot_dissolved(self):
        if self.clot.is_dissolved():
            self.current_state = "EXITING"
    
    def exit_treatment(self):
        if self.current_state != "EXITING":
            return
        
        formation = self.get_formation()
        if formation:
            for coach in formation:
                if coach.x > self.catheter_x + 25:
                    coach.update_position(-4.0)
        
        all_back = all(c.x <= self.catheter_x + 25 for c in self.coaches if c.in_formation)
        if all_back and not self.get_waiting_coaches():
            self.current_state = "COMPLETE"
    
    def update(self):
        self.time = self.frame / 20.0
        
        if self.clot.size_percent <= 0:
            self.check_clot_dissolved()
        
        if self.current_state in ["ENTERING", "APPROACHING", "DELIVERING"]:
            self.move_formation()
            self.deliver_medicine_to_clot()
            self.attach_waiting_coaches()
        
        self.exit_treatment()
        self.medicine_effect = max(0, self.medicine_effect - 0.15)
        
        self.frame += 1
    
    def is_complete(self):
        return self.current_state == "COMPLETE"


def render_frame(swarm):
    """Render with clinical parameters display"""
    
    fig = plt.figure(figsize=(18, 10), dpi=80)
    fig.patch.set_facecolor('white')
    
    gs = fig.add_gridspec(3, 1, height_ratios=[2.2, 1, 1], hspace=0.35)
    ax_main = fig.add_subplot(gs[0])
    ax_med = fig.add_subplot(gs[1])
    ax_clot = fig.add_subplot(gs[2])
    
    # ===== MAIN ANIMATION =====
    ax_main.set_xlim(-100, 850)
    ax_main.set_ylim(450, 550)
    ax_main.set_aspect('equal')
    ax_main.set_facecolor('white')
    
    title = f'Metro Train Swarm | T={swarm.time:.1f}s | {swarm.current_state} | Applied: {swarm.total_medicine_applied:.2f}ml | Clot: {swarm.clot.size_percent:.1f}%'
    ax_main.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax_main.set_xlabel('Position (μm)', fontsize=9)
    ax_main.grid(True, alpha=0.1)
    
    # Vessel
    vessel = patches.Rectangle((-100, 460), 950, 80, linewidth=2, edgecolor='darkred',
                               facecolor='mistyrose', alpha=0.3, zorder=1)
    ax_main.add_patch(vessel)
    
    # Catheter
    catheter = Circle((swarm.catheter_x, swarm.catheter_y), 10,
                      facecolor='blue', edgecolor='darkblue', linewidth=2, alpha=0.9, zorder=15)
    ax_main.add_patch(catheter)
    ax_main.text(swarm.catheter_x, 535, 'CATHETER', fontsize=8, fontweight='bold', ha='center')
    
    # CLOT - SIZE SHRINKS WITH MEDICINE
    clot_size = max(10, 60 * (swarm.clot.size_percent / 100.0))
    clot_intensity = swarm.clot.size_percent / 100.0
    clot_color = (1.0, 0.15 * clot_intensity, 0.15 * clot_intensity)
    clot = patches.Rectangle((swarm.target_x - clot_size/2, 490 - clot_size/4),
                             clot_size, clot_size/2, linewidth=2,
                             edgecolor='darkred', facecolor=clot_color, alpha=0.75, zorder=5)
    ax_main.add_patch(clot)
    
    # Clinical status panel at clot
    status_text = (f'CLOT STATUS\n'
                  f'Size: {swarm.clot.size_percent:.1f}%\n'
                  f'Visc: {swarm.clot.viscosity:.0f}cP\n'
                  f'Refl: {swarm.clot.reflectance:.0f}%\n'
                  f'Res: {swarm.clot.resistance:.0f}')
    ax_main.text(swarm.target_x, 520, status_text,
                fontsize=8, fontweight='bold', color='white', ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='darkred', alpha=0.95))
    
    # Medicine effect
    if swarm.medicine_effect > 0:
        intensity = min(1.0, swarm.medicine_effect / 3.0)
        med_circle = Circle((swarm.target_x, swarm.target_y), radius=20 + 15 * intensity,
                           facecolor='lime', alpha=0.4 * intensity, edgecolor='green',
                           linewidth=2, zorder=4)
        ax_main.add_patch(med_circle)
    
    # Draw coaches
    formation = swarm.get_formation()
    waiting = swarm.get_waiting_coaches()
    leader = swarm.get_leader()
    
    for coach in swarm.coaches:
        if coach.in_formation:
            ellipse = Ellipse((coach.x, coach.y), width=32, height=24, angle=0,
                             facecolor=coach.get_color(), edgecolor='darkblue',
                             linewidth=2.5, zorder=10, alpha=0.85)
            ax_main.add_patch(ellipse)
            
            ax_main.text(coach.x, coach.y + 8, coach.label, fontsize=10,
                        fontweight='bold', ha='center', va='center', zorder=11, color='darkblue')
            
            med_pct = (coach.medicine_current / coach.medicine_capacity) * 100
            ax_main.text(coach.x, coach.y - 8, f'{med_pct:.0f}%', fontsize=7,
                        ha='center', va='center', color='darkblue', fontweight='bold', zorder=11)
            
            if coach == leader:
                ax_main.plot(coach.x, coach.y + 20, '*', color='gold', markersize=18, zorder=12)
        
        elif coach.at_clot:
            ellipse = Ellipse((coach.x, coach.y), width=32, height=24, angle=0,
                             facecolor=coach.get_color(), edgecolor='red',
                             linewidth=3, zorder=10, alpha=0.85, linestyle='dashed')
            ax_main.add_patch(ellipse)
            ax_main.text(coach.x, coach.y, f'{coach.label}\n⏳',
                        fontsize=8, fontweight='bold', ha='center', va='center', zorder=11)
    
    # Bonds
    if len(formation) > 1:
        for i in range(len(formation) - 1):
            c1 = formation[i]
            c2 = formation[i + 1]
            ax_main.plot([c1.x + 16, c2.x - 16], [c1.y, c2.y], 'b-', linewidth=5, zorder=8, alpha=0.5)
            ax_main.plot([c1.x + 16, c2.x - 16], [c1.y, c2.y], 'co', markersize=6, zorder=9)
    
    # Info
    order_text = " → ".join([c.label for c in formation]) if formation else "EMPTY"
    waiting_text = ", ".join([c.label for c in waiting]) if waiting else "NONE"
    info = f"Order: {order_text}\nWaiting: {waiting_text}\nCycles: {swarm.delivery_cycle_count}"
    ax_main.text(0.02, 0.95, info, transform=ax_main.transAxes, fontsize=8, family='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
    
    # ===== MEDICINE CHART =====
    ax_med.set_xlim(0, swarm.max_frames)
    ax_med.set_ylim(0, 2.5)
    ax_med.set_ylabel('Medicine (ml)', fontsize=9)
    ax_med.set_title(f'Medicine Delivery: {swarm.total_medicine_applied:.2f}ml / {swarm.clot_required:.1f}ml Required',
                     fontsize=10, fontweight='bold')
    ax_med.grid(True, alpha=0.15)
    ax_med.set_facecolor('white')
    
    colors = {'C1': 'red', 'C2': 'blue', 'C3': 'green', 'C4': 'orange', 'C5': 'purple'}
    for coach in swarm.coaches:
        ax_med.scatter(swarm.frame, coach.delivered_amount, color=colors[coach.label],
                      s=50, alpha=0.8, zorder=5)
    
    ax_med.axhline(y=swarm.clot_required, color='red', linestyle='--', linewidth=1.5, alpha=0.5)
    ax_med.axhline(y=swarm.medicine_threshold, color='orange', linestyle='--', linewidth=1.5, alpha=0.5)
    
    # ===== CLOT PARAMETERS =====
    ax_clot.set_xlim(0, swarm.max_frames)
    ax_clot.set_ylim(0, 105)
    ax_clot.set_xlabel('Frame', fontsize=9)
    ax_clot.set_ylabel('Status (%)', fontsize=9)
    ax_clot.set_title('Clot Size & Clinical Parameters', fontsize=10, fontweight='bold')
    ax_clot.grid(True, alpha=0.15)
    ax_clot.set_facecolor('white')
    
    if swarm.delivery_log:
        frames = [0] + [d['frame'] for d in swarm.delivery_log]
        clot_sizes = [100.0] + [d['clot_size'] for d in swarm.delivery_log]
        viscosity = [100.0] + [d['viscosity'] for d in swarm.delivery_log]
        reflectance = [95.0] + [d['reflectance'] for d in swarm.delivery_log]
        resistance = [100.0] + [d['resistance'] for d in swarm.delivery_log]
        
        frames.append(swarm.frame)
        clot_sizes.append(swarm.clot.size_percent)
        viscosity.append(swarm.clot.viscosity)
        reflectance.append(swarm.clot.reflectance)
        resistance.append(swarm.clot.resistance)
        
        ax_clot.plot(frames, clot_sizes, 'r-', linewidth=2.5, label='Clot Size %', zorder=5)
        ax_clot.plot(frames, [v/1.0 for v in viscosity], 'orange', linewidth=2, label='Viscosity %', zorder=4, linestyle='--')
        ax_clot.plot(frames, reflectance, 'cyan', linewidth=2, label='Reflectance %', zorder=4, linestyle='--')
        ax_clot.plot(frames, resistance, 'magenta', linewidth=2, label='Resistance %', zorder=4, linestyle='--')
        
        ax_clot.scatter([d['frame'] for d in swarm.delivery_log],
                       [d['clot_size'] for d in swarm.delivery_log],
                       color='red', s=50, zorder=6, edgecolor='darkred', linewidth=1.5)
    
        ax_clot.axhline(y=0, color='black', linestyle='-', linewidth=1)
        # Skip legend due to label issues    # Convert
    fig.canvas.draw()
    buf = fig.canvas.buffer_rgba()
    img = np.frombuffer(buf, dtype=np.uint8).reshape(fig.canvas.get_width_height()[::-1] + (4,))
    img_bgr = cv2.cvtColor(img[:, :, :3], cv2.COLOR_RGB2BGR)
    plt.close(fig)
    
    return img_bgr


def main():
    print("\n" + "="*120)
    print(" NANOBOT METRO TRAIN - CLINICAL SIMULATION WITH ENHANCED VISUALS")
    print("="*120)
    print("\nImprovements:")
    print("  1. ✓ Smooth animation when coaches rejoin (gradual positioning)")
    print("  2. ✓ Ellipse color reflects medicine: White (empty) → Blue (full)")
    print("  3. ✓ Clot size SHRINKS visually as medicine applied (100% → 0%)")
    print("  4. ✓ Clinical parameters monitored in real-time:")
    print("       • Viscosity: 100cP → 0cP (10cP per ml)")
    print("       • Reflectance: 95% → 0% (7% per ml, optical property)")
    print("       • Resistance: 100% → 0% (10% per ml, flow resistance)")
    print("       • Size: 100% → 0% (15.38% per ml)")
    print("\nDelivery Process:")
    print("  Formation: C1 → C2 → C3 → C4 → C5 (C5 is leader)")
    print("  • C5 delivers → detaches → waits at clot")
    print("  • C4 delivers → detaches → waits")
    print("  • When formation returns: waiting coaches smoothly reattach to back")
    print("  • Clinical checks after each delivery")
    print("  • Once clot = 0%: STOP delivery, return entire train to catheter\n")
    
    swarm = MetroTrainSwarm(medicine_per_coach=2.0, clot_required=6.5)
    
    print("Rendering first frame...")
    first = render_frame(swarm)
    swarm.update()
    
    h, w = first.shape[:2]
    output = r"c:\Sansten\vRobot\nanobot_metro_train.mp4"
    out = cv2.VideoWriter(output, cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (w, h))
    
    print(f"Creating video: {output}\n" + "="*120 + "\n")
    
    while swarm.frame < swarm.max_frames and not swarm.is_complete():
        if swarm.frame % 50 == 0:
            pct = (swarm.frame / swarm.max_frames) * 100
            formation = swarm.get_formation()
            leader = swarm.get_leader()
            leader_label = leader.label if leader else "--"
            
            print(f"F{swarm.frame:4d} ({pct:5.1f}%) | Med: {swarm.total_medicine_applied:5.2f}ml | "
                  f"Clot: {swarm.clot.size_percent:5.1f}% | Visc: {swarm.clot.viscosity:5.0f}cP | "
                  f"Leader: {leader_label} | State: {swarm.current_state}")
        
        frame = render_frame(swarm)
        out.write(frame)
        swarm.update()
    
    for _ in range(40):
        frame = render_frame(swarm)
        out.write(frame)
    
    out.release()
    
    duration = swarm.frame / 20.0
    
    print("\n" + "="*120)
    print(f" ✓ VIDEO COMPLETE")
    print("="*120)
    print(f"\nFile: {output}")
    print(f"Duration: {duration:.1f}s | Frames: {swarm.frame} | {w}×{h} @ 20fps\n")
    
    print("="*120)
    print(" DELIVERY SEQUENCE WITH CLINICAL PARAMETERS")
    print("="*120 + "\n")
    
    for i, log in enumerate(swarm.delivery_log, 1):
        coach = log['coach_label']
        med = log['medicine_applied']
        total = log['total_applied']
        clot_size = log['clot_size']
        visc = log['viscosity']
        refl = log['reflectance']
        res = log['resistance']
        
        print(f"{i}. {coach} delivers @ T={log['time']:6.1f}s")
        print(f"   Medicine: {med:.2f}ml | Total: {total:.2f}ml")
        print(f"   Clot Status:")
        print(f"     • Size: {clot_size:.1f}%")
        print(f"     • Viscosity: {visc:.0f}cP")
        print(f"     • Reflectance: {refl:.0f}%")
        print(f"     • Resistance: {res:.0f}%\n")
    
    print("="*120)
    print(" FINAL TREATMENT RESULTS")
    print("="*120)
    print(f"\nTotal Duration: {duration:.1f} seconds")
    print(f"Total Medicine Applied: {swarm.total_medicine_applied:.2f}ml")
    print(f"Final Clot Size: {swarm.clot.size_percent:.1f}%")
    print(f"Final Viscosity: {swarm.clot.viscosity:.0f}cP")
    print(f"Final Reflectance: {swarm.clot.reflectance:.0f}%")
    print(f"Final Resistance: {swarm.clot.resistance:.0f}%")
    print(f"\nClot Status: {'✓ COMPLETELY DISSOLVED (ALL PARAMETERS ZERO)' if swarm.clot.size_percent == 0 else f'PARTIALLY DISSOLVED'}")
    print(f"Treatment: {'✓ SUCCESSFUL' if swarm.is_complete() else 'IN PROGRESS'}")
    print("="*120 + "\n")


if __name__ == "__main__":
    main()

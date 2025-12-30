#!/usr/bin/env python3
"""
NANOBOT METRO TRAIN - CORRECT BEHAVIOR
=======================================

Initial Order: C1 → C2 → C3 → C4 → C5 (C5 at FRONT - leader)

DELIVERY PHASE:
- C5 delivers 2ml → clot: 100% → 69.24%
- C5 DETACHES but STAYS AT CLOT LOCATION
- Train continues moving (now C1→C2→C3→C4)
- C4 becomes new leader, approaches clot again
- C4 delivers 2ml → clot: 69.24% → 38.48%
- C4 DETACHES but STAYS AT CLOT
- C5 (waiting at clot) ATTACHES to back of train (C1)
- Train order: C1 → C2 → C3 → C5 (C3 is leader)
- C3 continues cycle...

KEY: Detached coaches WAIT at clot, attach to back when train returns

CLOT DISSOLUTION PHASE:
- Continue until clot reaches 0%
- Once clot = 0%: STOP delivery, no more medicine applied
- Entire train (all coaches together) returns to catheter
- Exit when all coaches back at catheter

RATES:
- 1ml medicine = 15.38% clot dissolution
- 6.5ml needed = 100% dissolution
- 8.5ml sent (safety margin)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Ellipse, Circle
import cv2


class NanobotCoach:
    def __init__(self, coach_label, initial_position, x, y, medicine_capacity=2.0):
        self.label = coach_label
        self.pos = initial_position
        self.x = x
        self.y = y
        self.medicine_capacity = medicine_capacity
        self.medicine_current = medicine_capacity
        self.in_formation = True  # In active train
        self.at_clot = False  # Waiting at clot after delivery
        self.delivered_amount = 0.0
    
    def update_position(self, vx):
        self.x += vx
    
    def dispense_medicine(self, ml_per_frame=0.05):
        dispensed = min(ml_per_frame, self.medicine_current)
        self.medicine_current -= dispensed
        self.delivered_amount += dispensed
        return dispensed
    
    def get_color(self):
        if self.at_clot:
            return 'lightcoral'
        ratio = self.medicine_current / self.medicine_capacity
        if ratio > 0.75:
            return 'lightblue'
        elif ratio > 0.5:
            return 'skyblue'
        elif ratio > 0.25:
            return 'steelblue'
        else:
            return 'darkblue'


class MetroTrainSwarm:
    def __init__(self, medicine_per_coach=2.0, clot_required=6.5):
        """
        Initial order: C1, C2, C3, C4, C5 (C5 at front/right)
        C5 is the leader and delivers first
        """
        self.coaches = []
        self.medicine_per_coach = medicine_per_coach
        self.clot_required = clot_required
        self.medicine_threshold = clot_required + 2.0  # 8.5ml
        self.dissolution_per_ml = 100.0 / clot_required  # 15.38%/ml
        
        self.catheter_x = 50
        self.catheter_y = 500
        self.target_x = 700
        self.target_y = 500
        
        # Initial order: C1, C2, C3, C4, C5
        coach_spacing = 35
        coach_labels = ['C1', 'C2', 'C3', 'C4', 'C5']
        
        for pos, label in enumerate(coach_labels):
            coach_x = self.catheter_x + (pos * coach_spacing)
            coach = NanobotCoach(label, pos, coach_x, self.catheter_y, medicine_capacity=medicine_per_coach)
            self.coaches.append(coach)
        
        self.time = 0.0
        self.frame = 0
        self.max_frames = 3000
        self.delivery_log = []
        self.clot_remaining = 100.0
        self.total_medicine_applied = 0.0
        self.current_state = "ENTERING"
        self.delivery_cycle_count = 0
        self.medicine_effect = 0.0
        self.treatment_complete = False
    
    def get_formation(self):
        """Get coaches in active formation, sorted by x (left to right)"""
        return sorted([c for c in self.coaches if c.in_formation], key=lambda c: c.x)
    
    def get_waiting_coaches(self):
        """Get coaches waiting at clot"""
        return [c for c in self.coaches if c.at_clot]
    
    def get_leader(self):
        """Leader is rightmost (highest x) in formation"""
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
        """Leader delivers medicine to clot"""
        if self.current_state != "DELIVERING" or self.clot_remaining <= 0:
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
                
                # Clot dissolves
                dissolution = dispensed * self.dissolution_per_ml
                self.clot_remaining = max(0, self.clot_remaining - dissolution)
                
                # Log delivery
                if not self.delivery_log or self.delivery_log[-1]['coach_label'] != leader.label:
                    self.delivery_log.append({
                        'frame': self.frame,
                        'time': self.time,
                        'coach_label': leader.label,
                        'medicine_applied': 0.0,
                        'total_applied': self.total_medicine_applied,
                        'clot_remaining': self.clot_remaining,
                    })
                
                if self.delivery_log:
                    self.delivery_log[-1]['medicine_applied'] += dispensed
            
            else:
                # Leader medicine is empty - DETACH and wait at clot
                leader.in_formation = False
                leader.at_clot = True
                self.delivery_cycle_count += 1
                
                # Train continues approaching for next delivery
                self.current_state = "APPROACHING"
    
    def attach_waiting_coaches(self):
        """When formation approaches again, attach waiting coaches to back"""
        waiting = self.get_waiting_coaches()
        formation = self.get_formation()
        
        if not waiting or not formation:
            return
        
        leader = max(formation, key=lambda c: c.x)
        distance_to_clot = abs(self.target_x - leader.x)
        
        # When formation is at clot, waiting coaches attach to back
        if distance_to_clot <= 30:
            for waiting_coach in waiting:
                # Check if this coach should attach
                if waiting_coach.at_clot:
                    # Find leftmost coach in formation (back position)
                    leftmost = min(formation, key=lambda c: c.x)
                    
                    # Attach to the back
                    waiting_coach.at_clot = False
                    waiting_coach.in_formation = True
                    waiting_coach.x = leftmost.x - 35
                    waiting_coach.y = leftmost.y
                    
                    # Newly attached coach is not leader yet
                    # It will become leader after current leader detaches
    
    def check_clot_dissolved(self):
        """Check if clot is fully dissolved"""
        if self.clot_remaining <= 0:
            self.treatment_complete = True
            self.current_state = "EXITING"
    
    def exit_treatment(self):
        """Return entire formation to catheter"""
        if self.current_state != "EXITING":
            return
        
        formation = self.get_formation()
        if formation:
            for coach in formation:
                if coach.x > self.catheter_x + 25:
                    coach.update_position(-4.0)
        
        # Check if all formation coaches back at catheter
        all_back = all(c.x <= self.catheter_x + 25 for c in self.coaches if c.in_formation)
        
        if all_back and not self.get_waiting_coaches():
            self.current_state = "COMPLETE"
    
    def update(self):
        """Update simulation by one frame"""
        self.time = self.frame / 20.0
        
        # Clot dissolved check
        if self.clot_remaining <= 0:
            self.check_clot_dissolved()
        
        # Movement and delivery
        if self.current_state in ["ENTERING", "APPROACHING", "DELIVERING"]:
            self.move_formation()
            self.deliver_medicine_to_clot()
            self.attach_waiting_coaches()
        
        # Exit
        self.exit_treatment()
        
        # Visual effect
        self.medicine_effect = max(0, self.medicine_effect - 0.15)
        
        self.frame += 1
    
    def is_complete(self):
        return self.current_state == "COMPLETE"


def render_frame(swarm):
    """Render single frame"""
    
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
    
    title = f'Metro Train Swarm | T={swarm.time:.1f}s | {swarm.current_state} | Applied: {swarm.total_medicine_applied:.2f}ml | Clot: {max(0, swarm.clot_remaining):.1f}%'
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
    
    # Clot
    clot_intensity = max(0, swarm.clot_remaining) / 100.0
    clot_color = (1.0, 0.15 * clot_intensity, 0.15 * clot_intensity)
    clot = patches.Rectangle((swarm.target_x - 60, 480), 120, 40, linewidth=2, 
                             edgecolor='darkred', facecolor=clot_color, alpha=0.75, zorder=5)
    ax_main.add_patch(clot)
    ax_main.text(swarm.target_x, 520, f'CLOT\n{max(0, swarm.clot_remaining):.1f}%',
                fontsize=11, fontweight='bold', color='white', ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='darkred', alpha=0.95))
    
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
            # In formation
            ellipse = Ellipse((coach.x, coach.y), width=32, height=24, angle=0,
                             facecolor=coach.get_color(), edgecolor='darkblue',
                             linewidth=2.5, zorder=10, alpha=0.85)
            ax_main.add_patch(ellipse)
            
            ax_main.text(coach.x, coach.y + 8, coach.label, fontsize=10,
                        fontweight='bold', ha='center', va='center', zorder=11, color='darkblue')
            
            med_pct = (coach.medicine_current / coach.medicine_capacity) * 100
            ax_main.text(coach.x, coach.y - 8, f'{med_pct:.0f}%', fontsize=7,
                        ha='center', va='center', color='darkblue', fontweight='bold', zorder=11)
            
            # Leader indicator
            if coach == leader:
                ax_main.plot(coach.x, coach.y + 20, '*', color='gold', markersize=18, zorder=12)
                ax_main.text(coach.x, coach.y + 32, '★ LEADER', fontsize=7, color='gold',
                           fontweight='bold', ha='center', zorder=12)
        
        elif coach.at_clot:
            # Waiting at clot
            ellipse = Ellipse((coach.x, coach.y), width=32, height=24, angle=0,
                             facecolor=coach.get_color(), edgecolor='red',
                             linewidth=3, zorder=10, alpha=0.85, linestyle='dashed')
            ax_main.add_patch(ellipse)
            ax_main.text(coach.x, coach.y, f'{coach.label}\n⏳',
                        fontsize=8, fontweight='bold', ha='center', va='center', zorder=11)
    
    # Bonds in formation
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
    ax_med.set_title(f'Medicine: {swarm.total_medicine_applied:.2f}ml / {swarm.clot_required:.1f}ml Required', 
                     fontsize=10, fontweight='bold')
    ax_med.grid(True, alpha=0.15)
    ax_med.set_facecolor('white')
    
    colors = {'C1': 'red', 'C2': 'blue', 'C3': 'green', 'C4': 'orange', 'C5': 'purple'}
    for coach in swarm.coaches:
        ax_med.scatter(swarm.frame, coach.delivered_amount, color=colors[coach.label], 
                      s=50, alpha=0.8, zorder=5)
    
    ax_med.axhline(y=swarm.clot_required, color='red', linestyle='--', linewidth=1.5, alpha=0.5)
    ax_med.axhline(y=swarm.medicine_threshold, color='orange', linestyle='--', linewidth=1.5, alpha=0.5)
    
    # ===== CLOT DISSOLUTION =====
    ax_clot.set_xlim(0, swarm.max_frames)
    ax_clot.set_ylim(0, 105)
    ax_clot.set_xlabel('Frame (Time = Frame / 20s)', fontsize=9)
    ax_clot.set_ylabel('Status (%)', fontsize=9)
    ax_clot.set_title('Clot Dissolution (15.38% per 1ml)', fontsize=10, fontweight='bold')
    ax_clot.grid(True, alpha=0.15)
    ax_clot.set_facecolor('white')
    
    if swarm.delivery_log:
        frames = [0] + [d['frame'] for d in swarm.delivery_log]
        clot_vals = [100.0] + [d['clot_remaining'] for d in swarm.delivery_log]
        med_vals = [0] + [(d['total_applied'] / swarm.medicine_threshold) * 100 for d in swarm.delivery_log]
        
        frames.append(swarm.frame)
        clot_vals.append(max(0, swarm.clot_remaining))
        med_vals.append((swarm.total_medicine_applied / swarm.medicine_threshold) * 100)
        
        ax_clot.plot(frames, clot_vals, 'r-', linewidth=2.5, zorder=5)
        ax_clot.plot(frames, med_vals, 'g-', linewidth=2.5, zorder=4)
        ax_clot.scatter([d['frame'] for d in swarm.delivery_log], [d['clot_remaining'] for d in swarm.delivery_log],
                       color='red', s=50, zorder=6, edgecolor='darkred', linewidth=1.5)
    
    ax_clot.axhline(y=0, color='black', linestyle='-', linewidth=1)
    
    # Convert
    fig.canvas.draw()
    buf = fig.canvas.buffer_rgba()
    img = np.frombuffer(buf, dtype=np.uint8).reshape(fig.canvas.get_width_height()[::-1] + (4,))
    img_bgr = cv2.cvtColor(img[:, :, :3], cv2.COLOR_RGB2BGR)
    plt.close(fig)
    
    return img_bgr


def main():
    print("\n" + "="*110)
    print(" NANOBOT METRO TRAIN - MEDICAL TREATMENT (REVISED BEHAVIOR)")
    print("="*110)
    print("\nInitial Formation (Left to Right): C1 → C2 → C3 → C4 → C5")
    print("                                    (back)                    (front - LEADER)")
    print("\nKey Behavior Change:")
    print("  ✓ When a coach DEPLETES: It DETACHES but WAITS AT CLOT (shown in red)")
    print("  ✓ Train continues moving with remaining coaches")
    print("  ✓ When train RETURNS to clot: Waiting coaches ATTACH to BACK")
    print("  ✓ New leader delivers next dose")
    print("  ✓ This repeats until clot = 0%")
    print("  ✓ Once clot DISSOLVED: NO MORE DELIVERY, entire train RETURNS to catheter")
    print("\nDelivery Cycles:")
    print("  1. C5 delivers 2ml (clot 100% → 69.24%), WAITS at clot")
    print("     Formation: C1 → C2 → C3 → C4  |  Waiting: C5")
    print("  2. C4 delivers 2ml (clot 69.24% → 38.48%), WAITS at clot")
    print("     C5 reattaches to back → Formation: C5 → C1 → C2 → C3 → C4  |  Waiting: C4")
    print("  3. C3 delivers 2ml (clot 38.48% → 7.72%), WAITS at clot")
    print("     C4 reattaches → Formation continues rotating...")
    print("  ... until clot reaches 0%")
    print("  Final: Clot = 0% → ALL coaches return together to catheter")
    print("\nParameters:")
    print(f"  • Dissolution rate: 15.38% per 1ml")
    print(f"  • Each coach: 2ml, ellipse shape, electromagnetically bonded")
    print(f"  • Total: 10ml | Required: 6.5ml | Sending: 8.5ml (safety)\n")
    
    swarm = MetroTrainSwarm(medicine_per_coach=2.0, clot_required=6.5)
    
    print("Rendering first frame...")
    first = render_frame(swarm)
    swarm.update()
    
    h, w = first.shape[:2]
    output = r"c:\Sansten\vRobot\nanobot_metro_train.mp4"
    out = cv2.VideoWriter(output, cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (w, h))
    
    print(f"Creating video: {output}\n" + "="*110 + "\n")
    
    while swarm.frame < swarm.max_frames and not swarm.is_complete():
        if swarm.frame % 50 == 0:
            pct = (swarm.frame / swarm.max_frames) * 100
            formation = swarm.get_formation()
            waiting = swarm.get_waiting_coaches()
            leader = swarm.get_leader()
            leader_label = leader.label if leader else "--"
            formation_order = " → ".join([c.label for c in formation]) if formation else "EMPTY"
            waiting_str = ", ".join([c.label for c in waiting]) if waiting else "none"
            
            print(f"F{swarm.frame:4d} ({pct:5.1f}%) | Med: {swarm.total_medicine_applied:5.2f}ml | "
                  f"Clot: {max(0, swarm.clot_remaining):5.1f}% | Leader: {leader_label} | "
                  f"Formation: {formation_order} | Waiting: {waiting_str}")
        
        frame = render_frame(swarm)
        out.write(frame)
        swarm.update()
    
    # Final frames
    for _ in range(40):
        frame = render_frame(swarm)
        out.write(frame)
    
    out.release()
    
    duration = swarm.frame / 20.0
    
    print("\n" + "="*110)
    print(f" ✓ VIDEO COMPLETE")
    print("="*110)
    print(f"\nFile: {output}")
    print(f"Duration: {duration:.1f}s | Frames: {swarm.frame} | {w}×{h} @ 20fps\n")
    
    print("="*110)
    print(" DELIVERY SEQUENCE LOG")
    print("="*110 + "\n")
    
    formation_state = ['C1 → C2 → C3 → C4 → C5']
    
    for i, log in enumerate(swarm.delivery_log, 1):
        coach = log['coach_label']
        med = log['medicine_applied']
        total = log['total_applied']
        clot = max(0, log['clot_remaining'])
        
        # Update formation state
        coaches_in_order = ['C5', 'C4', 'C3', 'C2', 'C1']
        delivered_coaches = [d['coach_label'] for d in swarm.delivery_log[:i]]
        
        remaining = [c for c in coaches_in_order if c not in delivered_coaches]
        if remaining:
            next_leader = remaining[0]
            waiting_coaches = [c for c in coaches_in_order if c in delivered_coaches[:i-1]]
            formation_state.append(" → ".join(remaining) + f" | Waiting: {', '.join(waiting_coaches) if waiting_coaches else 'none'}")
        
        print(f"{i}. {coach} delivers @ T={log['time']:6.1f}s")
        print(f"   Medicine: {med:.2f}ml | Total: {total:.2f}ml | Clot: {clot:.1f}%")
        print(f"   Formation: {formation_state[-1]}\n")
    
    print("="*110)
    print(" TREATMENT RESULTS")
    print("="*110)
    print(f"\nTotal Duration: {duration:.1f} seconds")
    print(f"Total Medicine Applied: {swarm.total_medicine_applied:.2f}ml")
    print(f"Final Clot Status: {max(0, swarm.clot_remaining):.1f}%")
    print(f"Delivery Cycles: {swarm.delivery_cycle_count}")
    print(f"\nClot Status: {'✓ COMPLETELY DISSOLVED (0%)' if max(0, swarm.clot_remaining) == 0 else f'{max(0, swarm.clot_remaining):.1f}% REMAINING'}")
    print(f"Train Exit: {'✓ ALL COACHES RETURNED TO CATHETER' if swarm.is_complete() else 'STILL EXITING'}")
    print("="*110 + "\n")


if __name__ == "__main__":
    main()

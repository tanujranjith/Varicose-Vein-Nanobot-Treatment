#!/usr/bin/env python3
"""
NANOBOT METRO TRAIN - CORRECT INITIAL ORDER
=============================================

Initial Train Order (Left to Right): C1 → C2 → C3 → C4 → C5
C5 is at FRONT (rightmost) - HITS CLOT FIRST

Delivery Sequence:
1. C5 delivers 2ml → clot -15.38%*2 = -30.76%
2. C5 detaches from FRONT, U-turns, returns to back
3. Order becomes: C5, C1, C2, C3, C4 (C4 is now leader at front)
4. C4 delivers 2ml → clot -30.76%
5. C4 detaches, returns, joins back
6. Order becomes: C4, C5, C1, C2, C3 (C3 is now leader)
7. Continue until 6.5ml delivered (clot = 0%)
8. System checks clot dissolution completely
9. Entire train returns to catheter

Medicine: 1ml = 15.38% clot dissolution (100% / 6.5ml)
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
        """
        coach_label: 'C1', 'C2', 'C3', 'C4', 'C5'
        initial_position: 0=C1 (leftmost), 4=C5 (rightmost/front)
        """
        self.label = coach_label
        self.pos = initial_position
        self.x = x
        self.y = y
        self.medicine_capacity = medicine_capacity
        self.medicine_current = medicine_capacity
        self.active = True
        self.returning = False
        self.delivered_amount = 0.0
    
    def update_position(self, vx):
        self.x += vx
    
    def dispense_medicine(self, ml_per_frame=0.05):
        dispensed = min(ml_per_frame, self.medicine_current)
        self.medicine_current -= dispensed
        self.delivered_amount += dispensed
        return dispensed
    
    def get_color(self):
        if self.returning:
            return 'orange'
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
        Initial order (left to right): C1 → C2 → C3 → C4 → C5
        C5 at right/front touches clot first
        """
        self.coaches = []
        self.medicine_per_coach = medicine_per_coach
        self.clot_required = clot_required
        self.medicine_threshold = clot_required + 2.0  # 8.5ml
        self.dissolution_per_ml = 100.0 / clot_required  # 15.38% per 1ml
        
        self.catheter_x = 50
        self.catheter_y = 500
        self.target_x = 700
        self.target_y = 500
        
        # Initial order: C1, C2, C3, C4, C5 (C5 at front/right)
        coach_spacing = 35
        coach_labels = ['C1', 'C2', 'C3', 'C4', 'C5']
        
        for pos, label in enumerate(coach_labels):
            coach_x = self.catheter_x + (pos * coach_spacing)
            coach = NanobotCoach(label, pos, coach_x, self.catheter_y, medicine_capacity=medicine_per_coach)
            self.coaches.append(coach)
        
        self.time = 0.0
        self.frame = 0
        self.max_frames = 2500
        self.delivery_log = []
        self.clot_remaining = 100.0
        self.total_medicine_applied = 0.0
        self.current_state = "ENTERING"
        self.delivery_cycle_count = 0
        self.medicine_effect = 0.0
    
    def get_active_train(self):
        """Get coaches in formation, sorted by x position (left to right)"""
        return sorted([c for c in self.coaches if c.active and not c.returning], key=lambda c: c.x)
    
    def get_returning_coaches(self):
        return [c for c in self.coaches if c.returning]
    
    def get_leader(self):
        """Leader is the rightmost (highest x) coach in active train"""
        active = self.get_active_train()
        return max(active, key=lambda c: c.x) if active else None
    
    def move_train(self):
        """Move entire connected train toward clot"""
        active = self.get_active_train()
        if not active:
            return
        
        leader = max(active, key=lambda c: c.x)  # Rightmost coach
        distance_to_target = self.target_x - leader.x
        
        if self.current_state == "ENTERING":
            if leader.x < self.catheter_x + 60:
                for coach in active:
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
                
                for coach in active:
                    coach.update_position(vx)
            else:
                self.current_state = "DELIVERING"
    
    def deliver_medicine_to_clot(self):
        """Leader coach (rightmost) delivers medicine"""
        active = self.get_active_train()
        if not active:
            return
        
        leader = max(active, key=lambda c: c.x)  # Rightmost = leader
        distance_to_clot = abs(self.target_x - leader.x)
        
        if distance_to_clot <= 15 and self.current_state == "DELIVERING":
            if leader.medicine_current > 0:
                dispensed = leader.dispense_medicine(ml_per_frame=0.05)
                self.total_medicine_applied += dispensed
                self.medicine_effect += dispensed
                
                # 1ml = 15.38% dissolution
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
                
                if self.total_medicine_applied >= self.medicine_threshold:
                    self.current_state = "EVALUATING"
            else:
                # Leader medicine depleted - detach from FRONT and return
                leader.active = False
                leader.returning = True
                self.delivery_cycle_count += 1
                self.current_state = "APPROACHING"
    
    def move_returning_coaches(self):
        """Detached coaches return to catheter and rejoin at back"""
        returning = self.get_returning_coaches()
        
        for coach in returning:
            if coach.x > self.catheter_x + 15:
                coach.update_position(-3.0)
            else:
                # Reached catheter - rejoin at back (leftmost position)
                coach.returning = False
                coach.active = True
                coach.x = self.catheter_x
                coach.y = self.catheter_y
                
                # Place at left of active train (new back)
                active = self.get_active_train()
                if active:
                    leftmost = min(active, key=lambda c: c.x)
                    coach.x = leftmost.x - 35
                    coach.y = leftmost.y
    
    def evaluate_dissolution(self):
        """Check if clot is fully dissolved"""
        if self.current_state == "EVALUATING":
            if self.clot_remaining <= 0:
                # Clot fully dissolved
                self.current_state = "EXITING"
            elif self.total_medicine_applied >= self.medicine_threshold:
                # Threshold reached - exit
                self.current_state = "EXITING"
            else:
                # Continue if coaches available
                active = self.get_active_train()
                if active:
                    self.current_state = "APPROACHING"
                else:
                    self.current_state = "EXITING"
    
    def exit_treatment(self):
        """Return entire train to catheter"""
        if self.current_state == "EXITING":
            active = self.get_active_train()
            if active:
                for coach in active:
                    if coach.x > self.catheter_x + 25:
                        coach.update_position(-4.0)
            
            all_back = all(c.x <= self.catheter_x + 25 for c in self.coaches)
            if all_back:
                self.current_state = "COMPLETE"
    
    def update(self):
        """Update simulation by one frame"""
        self.time = self.frame / 20.0
        
        if self.current_state in ["ENTERING", "APPROACHING", "DELIVERING"]:
            self.move_train()
            self.deliver_medicine_to_clot()
        
        self.move_returning_coaches()
        self.evaluate_dissolution()
        self.exit_treatment()
        self.medicine_effect = max(0, self.medicine_effect - 0.15)
        
        self.frame += 1
    
    def is_complete(self):
        return self.current_state == "COMPLETE"


def render_frame(swarm):
    """Render single frame with 3 panels"""
    
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
    active_train = swarm.get_active_train()
    returning = swarm.get_returning_coaches()
    leader = swarm.get_leader()
    
    for coach in swarm.coaches:
        if coach.active and not coach.returning:
            ellipse = Ellipse((coach.x, coach.y), width=32, height=24, angle=0,
                             facecolor=coach.get_color(), edgecolor='darkblue',
                             linewidth=2.5, zorder=10, alpha=0.85)
            ax_main.add_patch(ellipse)
            
            ax_main.text(coach.x, coach.y + 8, coach.label, fontsize=10,
                        fontweight='bold', ha='center', va='center', zorder=11, color='darkblue')
            
            med_pct = (coach.medicine_current / coach.medicine_capacity) * 100
            ax_main.text(coach.x, coach.y - 8, f'{med_pct:.0f}%', fontsize=7,
                        ha='center', va='center', color='darkblue', fontweight='bold', zorder=11)
            
            # Leader indicator (rightmost)
            if coach == leader:
                ax_main.plot(coach.x, coach.y + 20, '*', color='gold', markersize=18, zorder=12)
                ax_main.text(coach.x, coach.y + 32, '★ LEADER', fontsize=7, color='gold',
                           fontweight='bold', ha='center', zorder=12)
        
        elif coach in returning:
            ellipse = Ellipse((coach.x, coach.y), width=32, height=24, angle=0,
                             facecolor='orange', edgecolor='darkorange', linewidth=2.5,
                             zorder=10, alpha=0.85)
            ax_main.add_patch(ellipse)
            ax_main.text(coach.x, coach.y, f'{coach.label}\n↶',
                        fontsize=8, fontweight='bold', ha='center', va='center', zorder=11)
    
    # Bonds
    if len(active_train) > 1:
        for i in range(len(active_train) - 1):
            c1 = active_train[i]
            c2 = active_train[i + 1]
            ax_main.plot([c1.x + 16, c2.x - 16], [c1.y, c2.y], 'b-', linewidth=5, zorder=8, alpha=0.5)
            ax_main.plot([c1.x + 16, c2.x - 16], [c1.y, c2.y], 'co', markersize=6, zorder=9)
    
    # Order display
    order_text = " → ".join([c.label for c in active_train])
    ax_main.text(0.02, 0.95, f"Order: {order_text}\nActive: {len(active_train)} | Returning: {len(returning)}", 
                transform=ax_main.transAxes, fontsize=8, family='monospace',
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
    
    # ===== CLOT DISSOLUTION =====
    ax_clot.set_xlim(0, swarm.max_frames)
    ax_clot.set_ylim(0, 105)
    ax_clot.set_xlabel('Frame (Time = Frame / 20s)', fontsize=9)
    ax_clot.set_ylabel('Status (%)', fontsize=9)
    ax_clot.set_title('Clot Dissolution Progress (1ml = 15.38% reduction)', fontsize=10, fontweight='bold')
    ax_clot.grid(True, alpha=0.15)
    ax_clot.set_facecolor('white')
    
    if swarm.delivery_log:
        frames = [0] + [d['frame'] for d in swarm.delivery_log]
        clot_vals = [100.0] + [d['clot_remaining'] for d in swarm.delivery_log]
        med_vals = [0] + [(d['total_applied'] / swarm.medicine_threshold) * 100 for d in swarm.delivery_log]
        
        frames.append(swarm.frame)
        clot_vals.append(max(0, swarm.clot_remaining))
        med_vals.append((swarm.total_medicine_applied / swarm.medicine_threshold) * 100)
        
        ax_clot.plot(frames, clot_vals, 'r-', linewidth=2.5, zorder=5, label='Clot Remaining')
        ax_clot.plot(frames, med_vals, 'g-', linewidth=2.5, zorder=4, label='Medicine Applied')
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
    print("\n" + "="*100)
    print(" NANOBOT METRO TRAIN - CORRECT INITIAL ORDER")
    print("="*100)
    print("\nInitial Train Formation (Left to Right):")
    print("  C1 → C2 → C3 → C4 → C5 (C5 at FRONT/RIGHT - touches clot first)")
    print("\nDelivery & Cycling Sequence:")
    print("  1. C5 delivers 2ml (clot: 100% → 69.24%)")
    print("  2. C5 detaches from FRONT, U-turns, returns to back")
    print("     Order becomes: C5, C1, C2, C3, C4")
    print("  3. C4 is now leader at front → delivers 2ml (clot: 69.24% → 38.48%)")
    print("  4. C4 detaches, returns, joins back")
    print("     Order becomes: C4, C5, C1, C2, C3")
    print("  5. C3 is now leader → delivers 2ml (clot: 38.48% → 7.72%)")
    print("  6. Cycle continues until 6.5ml delivered (clot = 0%)")
    print("\nParameters:")
    print(f"  • Dissolution rate: 15.38% per 1ml (100% ÷ 6.5ml)")
    print("  • Each coach: 2ml capacity, ellipse shape, electromagnetically bonded")
    print("  • Total capacity: 10ml | Required: 6.5ml | Sending: 8.5ml (safety margin)")
    print("  • Final check: Verify clot completely dissolved before exit\n")
    
    swarm = MetroTrainSwarm(medicine_per_coach=2.0, clot_required=6.5)
    
    print("Rendering first frame...")
    first = render_frame(swarm)
    swarm.update()
    
    h, w = first.shape[:2]
    output = r"c:\Sansten\vRobot\nanobot_metro_train.mp4"
    out = cv2.VideoWriter(output, cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (w, h))
    
    print(f"Creating video: {output}\n" + "="*100 + "\n")
    
    while swarm.frame < swarm.max_frames and not swarm.is_complete():
        if swarm.frame % 50 == 0:
            pct = (swarm.frame / swarm.max_frames) * 100
            active = swarm.get_active_train()
            leader = swarm.get_leader()
            leader_label = leader.label if leader else "--"
            order = " → ".join([c.label for c in active]) if active else "EMPTY"
            
            print(f"Frame {swarm.frame:4d} ({pct:5.1f}%) | Med: {swarm.total_medicine_applied:5.2f}ml | "
                  f"Clot: {max(0, swarm.clot_remaining):5.1f}% | Leader: {leader_label} | Order: {order}")
        
        frame = render_frame(swarm)
        out.write(frame)
        swarm.update()
    
    for _ in range(40):
        frame = render_frame(swarm)
        out.write(frame)
    
    out.release()
    
    duration = swarm.frame / 20.0
    
    print("\n" + "="*100)
    print(f" ✓ VIDEO COMPLETE: {output}")
    print("="*100)
    print(f"\nVideo Duration: {duration:.1f}s | Frames: {swarm.frame} | {w}×{h} @ 20fps\n")
    
    print("="*100)
    print(" DELIVERY SEQUENCE WITH ORDER CHANGES")
    print("="*100 + "\n")
    
    order_sequence = ['C1 → C2 → C3 → C4 → C5']
    
    for i, log in enumerate(swarm.delivery_log, 1):
        coach = log['coach_label']
        med = log['medicine_applied']
        total = log['total_applied']
        clot = max(0, log['clot_remaining'])
        
        # Update order after each delivery
        if coach == 'C5':
            order_sequence.append('C5, C1 → C2 → C3 → C4')
        elif coach == 'C4':
            order_sequence.append('C4, C5, C1 → C2 → C3')
        elif coach == 'C3':
            order_sequence.append('C3, C4, C5, C1 → C2')
        elif coach == 'C2':
            order_sequence.append('C2, C3, C4, C5, C1')
        elif coach == 'C1':
            order_sequence.append('C1, C2, C3, C4, C5')
        
        print(f"{i}. {coach} delivers @ T={log['time']:6.1f}s")
        print(f"   Medicine: {med:.2f}ml | Total: {total:.2f}ml | Clot: {clot:.1f}%")
        print(f"   Train order: {order_sequence[-1]}\n")
    
    print("="*100)
    print(" TREATMENT RESULTS")
    print("="*100)
    print(f"\nTotal Duration: {duration:.1f} seconds")
    print(f"Total Medicine Applied: {swarm.total_medicine_applied:.2f}ml")
    print(f"Final Clot Status: {max(0, swarm.clot_remaining):.1f}%")
    print(f"Delivery Cycles: {swarm.delivery_cycle_count}")
    print(f"\nTreatment Status: {'✓ SUCCESSFUL - CLOT DISSOLVED' if max(0, swarm.clot_remaining) == 0 else 'IN PROGRESS'}")
    print(f"Exit Status: {'✓ TRAIN RETURNED TO CATHETER' if swarm.is_complete() else 'STILL EXITING'}")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()

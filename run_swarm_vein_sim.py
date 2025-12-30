#!/usr/bin/env python
"""
Swarm Vein Simulation: Role-based nanobot swarm in a branching vein network.
Creates an MP4 video showing swarm sensing, mapping, and blockage clearing.
"""
import os
import math
import random
import argparse
from PIL import Image, ImageDraw

SENSOR_FIELDS = ("viscosity", "impedance", "reflectance", "strain")
SENSOR_NORM_KEYS = {
    "viscosity": "visc_norm",
    "impedance": "imp_norm",
    "reflectance": "refl_norm",
    "strain": "strain_norm",
}
SENSOR_SHORT = {
    "viscosity": "visc",
    "impedance": "imp",
    "reflectance": "refl",
    "strain": "strain",
}
ROLE_ORDER = ("Scout", "Worker", "Support", "Monitor")
ROLE_SHORT = {"Scout": "S", "Worker": "W", "Support": "Su", "Monitor": "M"}
ROLE_COLORS = {
    "Scout": (70, 190, 235),
    "Worker": (245, 140, 60),
    "Support": (120, 200, 120),
    "Monitor": (90, 160, 180),
}
ROLE_OUTLINES = {
    "Scout": (40, 120, 170),
    "Worker": (170, 90, 40),
    "Support": (70, 140, 70),
    "Monitor": (30, 90, 110),
}
ROLE_SIZES = {
    "Scout": 3,
    "Worker": 5,
    "Support": 4,
    "Monitor": 3,
}
SENSOR_COLORS = {
    "viscosity": (220, 80, 80),
    "impedance": (80, 140, 220),
    "reflectance": (220, 210, 90),
    "strain": (255, 120, 40),
}


def clamp(value, low, high):
    return max(low, min(high, value))


def lerp_color(color_a, color_b, t):
    return (
        int(color_a[0] + (color_b[0] - color_a[0]) * t),
        int(color_a[1] + (color_b[1] - color_a[1]) * t),
        int(color_a[2] + (color_b[2] - color_a[2]) * t),
    )


class VeinSegment:
    def __init__(self, seg_id, start, end, children, name, parent_id=None):
        self.seg_id = seg_id
        self.start = start
        self.end = end
        self.children = children
        self.parent_id = parent_id
        self.name = name
        self.length = math.hypot(end[0] - start[0], end[1] - start[1])

        self.blockage = 0.0
        self.inflammation = 0.0
        self.pooling = 0.0
        self.beacon = 0.0
        self.mapping = 0.0
        self.pressure_spike = 0.0
        self.scaffold = 0.0
        self.affected = False
        self.fields = {}
        self.initial_state = {}

    def midpoint(self):
        return ((self.start[0] + self.end[0]) / 2.0, (self.start[1] + self.end[1]) / 2.0)

    def compute_fields(self):
        viscosity = 4.5 + 32.0 * self.blockage + 6.5 * self.inflammation + 10.0 * self.pooling
        impedance = 1.0 + 70.0 * self.blockage + 12.0 * self.inflammation + 14.0 * self.pooling
        reflectance = 0.10 + 0.60 * self.blockage + 0.22 * self.inflammation + 0.10 * self.pooling
        strain = 0.15 + 0.55 * self.pooling + 1.05 * self.pressure_spike
        if self.scaffold > 0.01:
            strain *= max(0.35, 1.0 - 0.6 * self.scaffold)

        visc_norm = clamp((viscosity - 4.5) / 40.0, 0.0, 1.0)
        imp_norm = clamp((impedance - 1.0) / 95.0, 0.0, 1.0)
        refl_norm = clamp((reflectance - 0.10) / 0.75, 0.0, 1.0)
        strain_norm = clamp(strain / 1.2, 0.0, 1.0)

        self.fields = {
            "viscosity": viscosity,
            "impedance": impedance,
            "reflectance": reflectance,
            "strain": strain,
            "visc_norm": visc_norm,
            "imp_norm": imp_norm,
            "refl_norm": refl_norm,
            "strain_norm": strain_norm,
            "abnormal": (visc_norm + imp_norm + refl_norm + strain_norm) / 4.0,
        }
        return self.fields


class SwarmAgent:
    def __init__(self, role, segment_id, t, direction=1):
        self.role = role
        self.segment_id = segment_id
        self.t = t
        self.direction = direction


def build_vein_network():
    segments = [
        VeinSegment(0, (80, 300), (260, 300), [1, 2], "Trunk"),
        VeinSegment(1, (260, 300), (430, 210), [3, 4], "Upper"),
        VeinSegment(2, (260, 300), (430, 390), [5], "Lower"),
        VeinSegment(3, (430, 210), (730, 150), [], "Upper-R"),
        VeinSegment(4, (430, 210), (720, 250), [], "Mid-R"),
        VeinSegment(5, (430, 390), (730, 450), [], "Lower-R"),
    ]

    for seg in segments:
        for child_id in seg.children:
            segments[child_id].parent_id = seg.seg_id

    return segments


def initialize_pathology(segments):
    baseline = {
        0: (0.05, 0.10, 0.18),
        1: (0.18, 0.20, 0.25),
        2: (0.12, 0.18, 0.22),
        3: (0.85, 0.60, 0.50),
        4: (0.40, 0.30, 0.42),
        5: (0.75, 0.55, 0.60),
    }

    for seg in segments:
        blockage, inflammation, pooling = baseline.get(seg.seg_id, (0.1, 0.1, 0.1))
        seg.blockage = blockage
        seg.inflammation = inflammation
        seg.pooling = pooling
        seg.affected = seg.blockage > 0.5 or seg.inflammation > 0.45
        seg.initial_state = {
            "blockage": seg.blockage,
            "inflammation": seg.inflammation,
            "pooling": seg.pooling,
        }


def reset_segments(segments):
    for seg in segments:
        seg.blockage = seg.initial_state["blockage"]
        seg.inflammation = seg.initial_state["inflammation"]
        seg.pooling = seg.initial_state["pooling"]
        seg.beacon = 0.0
        seg.mapping = 0.0
        seg.pressure_spike = 0.0
        seg.scaffold = 0.0


def create_agents(swarm_size, rng):
    counts = {
        "Scout": int(swarm_size * 0.25),
        "Worker": int(swarm_size * 0.45),
        "Support": int(swarm_size * 0.15),
    }
    counts["Monitor"] = swarm_size - sum(counts.values())

    roles = []
    for role, count in counts.items():
        roles.extend([role] * count)
    rng.shuffle(roles)

    agents = []
    for role in roles:
        direction = -1 if role == "Monitor" and rng.random() < 0.5 else 1
        agents.append(SwarmAgent(role, 0, rng.random(), direction))
    return agents


def role_counts(agents):
    counts = {role: 0 for role in ROLE_ORDER}
    for agent in agents:
        counts[agent.role] += 1
    return counts


def weighted_choice(items, weights, rng):
    total = sum(weights)
    if total <= 0:
        return rng.choice(items)
    pick = rng.random() * total
    for item, weight in zip(items, weights):
        pick -= weight
        if pick <= 0:
            return item
    return items[-1]


def score_segment_for_role(segment, role):
    if role == "Scout":
        return (1.0 - segment.mapping) * 0.7 + segment.blockage * 0.2 + segment.inflammation * 0.2
    if role == "Worker":
        return segment.beacon * 1.3 + segment.blockage * 0.8 + segment.inflammation * 0.3
    if role == "Support":
        return segment.fields.get("strain_norm", 0.0) * 1.6 + segment.pressure_spike * 1.3
    if role == "Monitor":
        return (1.0 - segment.mapping) * 1.2 + segment.pooling * 0.2
    return 0.1


def choose_next_segment(current_segment, segments, role, rng):
    if not current_segment.children:
        return segments[0]
    weights = []
    for child_id in current_segment.children:
        child = segments[child_id]
        weights.append(score_segment_for_role(child, role) + 0.05)
    chosen_id = weighted_choice(current_segment.children, weights, rng)
    return segments[chosen_id]


def update_role_switching(agents, segments, rng, role_switch, fps, frame_idx):
    if not role_switch or frame_idx % fps != 0:
        return

    avg_beacon = sum(seg.beacon for seg in segments) / len(segments)
    avg_strain = sum(seg.fields.get("strain_norm", 0.0) for seg in segments) / len(segments)
    avg_mapping = sum(seg.mapping for seg in segments) / len(segments)

    if avg_beacon > 0.25:
        scouts = [agent for agent in agents if agent.role == "Scout"]
        rng.shuffle(scouts)
        for agent in scouts[:2]:
            agent.role = "Worker"

    if avg_strain > 0.35:
        workers = [agent for agent in agents if agent.role == "Worker"]
        rng.shuffle(workers)
        for agent in workers[:1]:
            agent.role = "Support"

    if avg_mapping > 0.7:
        monitors = [agent for agent in agents if agent.role == "Monitor"]
        rng.shuffle(monitors)
        for agent in monitors[:1]:
            agent.role = "Scout"


def draw_ui(draw, width, height, status, control, reset_flash):
    panel_bg = (240, 240, 245)
    panel_border = (80, 80, 90)
    title_color = (20, 20, 20)

    status_panel = [10, 10, 300, 170]
    draw.rectangle(status_panel, fill=panel_bg, outline=panel_border)
    draw.text((20, 18), "Swarm Vein Simulation", fill=title_color)

    y = 40
    for line, color in status:
        draw.text((20, y), line, fill=color)
        y += 16

    control_panel = [width - 300, 10, width - 10, 185]
    draw.rectangle(control_panel, fill=panel_bg, outline=panel_border)
    draw.text((width - 290, 18), "Control Panel", fill=title_color)

    y = 40
    for line, color in control:
        draw.text((width - 290, y), line, fill=color)
        y += 16

    reset_box = [width - 290, 150, width - 30, 175]
    reset_color = (255, 220, 150) if reset_flash else (220, 220, 230)
    draw.rectangle(reset_box, fill=reset_color, outline=panel_border)
    draw.text((width - 280, 154), "Reset scenario", fill=(30, 30, 30))


def render_frame(frame_idx, fps, width, height, segments, agents, sensor_field, sensor_overlay, ui_data, render_rng):
    img = Image.new("RGB", (width, height), color=(245, 245, 250))
    draw = ImageDraw.Draw(img)

    base_color = (170, 110, 120)
    vessel_shadow = (200, 160, 165)
    line_base_width = 14

    for seg in segments:
        seg.compute_fields()

    label_segments = []
    sensor_norm_key = SENSOR_NORM_KEYS[sensor_field]
    if sensor_overlay:
        label_segments = sorted(
            segments,
            key=lambda seg: seg.fields.get(sensor_norm_key, seg.fields.get("strain_norm", 0.0)),
            reverse=True,
        )[:2]

    for seg in segments:
        sensor_norm = seg.fields.get(sensor_norm_key, seg.fields.get("strain_norm", 0.0))

        color = base_color
        width_mod = 0

        if sensor_overlay:
            overlay_color = SENSOR_COLORS[sensor_field]
            color = lerp_color(base_color, overlay_color, sensor_norm)
            width_mod = int(6 * sensor_norm)

        if seg.scaffold > 0.2:
            color = lerp_color(color, (170, 240, 170), min(1.0, seg.scaffold))
            width_mod += 4

        if seg.blockage > 0.6 and not sensor_overlay:
            color = lerp_color(color, (200, 90, 90), min(1.0, seg.blockage))

        draw.line([seg.start, seg.end], fill=vessel_shadow, width=line_base_width + width_mod + 4)
        draw.line([seg.start, seg.end], fill=color, width=line_base_width + width_mod)

        if seg.pressure_spike > 0.4:
            mid_x, mid_y = seg.midpoint()
            spike_radius = 6 + int(8 * seg.pressure_spike)
            draw.ellipse(
                [mid_x - spike_radius, mid_y - spike_radius, mid_x + spike_radius, mid_y + spike_radius],
                outline=(255, 120, 60),
                width=2,
            )

    if label_segments and sensor_overlay:
        offsets = [(10, -18), (10, 12)]
        for seg, offset in zip(label_segments, offsets):
            sensor_value = seg.fields.get(sensor_field, 0.0)
            if seg.fields.get(sensor_norm_key, 0.0) < 0.55:
                continue
            mid_x, mid_y = seg.midpoint()
            text = f"{seg.name} {SENSOR_SHORT[sensor_field]} {sensor_value:.2f}"
            draw.text((mid_x + offset[0], mid_y + offset[1]), text, fill=(50, 50, 50))

    for agent in agents:
        seg = segments[agent.segment_id]
        dx = seg.end[0] - seg.start[0]
        dy = seg.end[1] - seg.start[1]
        length = math.hypot(dx, dy) or 1.0
        ux, uy = dx / length, dy / length
        px, py = -uy, ux

        jitter = 0.8
        offset = (render_rng.uniform(-jitter, jitter), render_rng.uniform(-jitter, jitter))
        x = seg.start[0] + ux * seg.length * agent.t + px * offset[0]
        y = seg.start[1] + uy * seg.length * agent.t + py * offset[1]

        radius = ROLE_SIZES[agent.role]
        color = ROLE_COLORS[agent.role]
        outline = ROLE_OUTLINES[agent.role]

        if agent.role == "Monitor":
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], outline=outline, width=1)
        else:
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color, outline=outline)

        if agent.role == "Scout":
            draw.ellipse([x - radius - 2, y - radius - 2, x + radius + 2, y + radius + 2],
                         outline=(200, 230, 250), width=1)

    draw_ui(draw, width, height, ui_data["status"], ui_data["control"], ui_data["reset_flash"])

    return img


def create_swarm_simulation(
    swarm_size=160,
    flow=1.0,
    noise=0.08,
    beacon_strength=0.6,
    mode="rest",
    sensor_field="viscosity",
    sensor_overlay=1,
    role_switch=1,
    duration_sec=20,
    fps=30,
    seed=7,
    reset_at=None,
):
    import imageio

    rng = random.Random(seed)
    render_rng = random.Random(seed + 101)

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    video_path = os.path.join(output_dir, "swarm_vein_sim.mp4")

    width, height = 800, 600
    num_frames = int(duration_sec * fps)

    segments = build_vein_network()
    initialize_pathology(segments)

    agents = create_agents(swarm_size, rng)
    initial_total_blockage = sum(seg.blockage for seg in segments)

    reset_frames = [0]
    if reset_at is None and duration_sec >= 12:
        reset_frames.append(int(10 * fps))
    elif reset_at is not None and reset_at > 0:
        reset_frames.append(int(reset_at * fps))
    reset_frames = sorted(set(frame for frame in reset_frames if 0 <= frame < num_frames))

    frames = []
    support_peak_history = []
    support_peak = 0.0
    last_reset_time = 0.0

    spike_segment_ids = [4]

    for frame_idx in range(num_frames):
        if frame_idx in reset_frames and frame_idx != 0:
            support_peak_history.append(round(support_peak, 3))
            support_peak = 0.0
            last_reset_time = frame_idx / fps
            reset_segments(segments)
            agents = create_agents(swarm_size, rng)

        cycle_time = frame_idx / fps - last_reset_time
        is_activity = mode.lower() == "activity"

        for seg in segments:
            seg.beacon *= 0.92
            seg.scaffold *= 0.95
            seg.pressure_spike *= 0.93

            if mode.lower() == "rest" and seg.affected:
                seg.inflammation = clamp(seg.inflammation + 0.0004, 0.0, 1.0)
                seg.pooling = clamp(seg.pooling + 0.00025, 0.0, 1.0)

        if is_activity:
            if 4.0 <= cycle_time <= 7.0:
                for spike_id in spike_segment_ids:
                    segments[spike_id].pressure_spike = clamp(
                        segments[spike_id].pressure_spike + 0.06, 0.0, 1.0
                    )

        for seg in segments:
            seg.compute_fields()

        update_role_switching(agents, segments, rng, role_switch, fps, frame_idx)

        worker_activity = {seg.seg_id: 0 for seg in segments}

        for agent in agents:
            seg = segments[agent.segment_id]
            signal = seg.fields.get("abnormal", 0.0)

            if agent.role == "Scout":
                if signal > 0.55:
                    seg.beacon = clamp(seg.beacon + beacon_strength * (0.03 + 0.05 * signal), 0.0, 1.0)

            if agent.role == "Worker":
                if seg.beacon > 0.3 or seg.blockage > 0.4:
                    worker_activity[seg.seg_id] += 1

            if agent.role == "Monitor":
                seg.mapping = clamp(seg.mapping + 0.003, 0.0, 1.0)

            if agent.role == "Support" and is_activity:
                if seg.fields.get("strain_norm", 0.0) > 0.6 or seg.pressure_spike > 0.4:
                    seg.scaffold = clamp(seg.scaffold + 0.04, 0.0, 1.0)

            base_speed = flow
            if agent.role == "Worker" and (seg.beacon > 0.4 or seg.blockage > 0.5):
                base_speed *= 0.45
            if agent.role == "Support" and seg.fields.get("strain_norm", 0.0) > 0.5:
                base_speed *= 0.35
            if agent.role == "Monitor":
                base_speed *= 0.8

            speed = max(0.05, base_speed + rng.uniform(-noise, noise))
            step = speed / seg.length

            if agent.role == "Monitor":
                agent.t += step * agent.direction
                if agent.t > 1.0:
                    if seg.children and rng.random() > 0.4:
                        next_seg = choose_next_segment(seg, segments, agent.role, rng)
                        agent.segment_id = next_seg.seg_id
                        agent.t = 0.0
                    else:
                        agent.t = 1.0
                        agent.direction = -1
                elif agent.t < 0.0:
                    if seg.parent_id is not None and rng.random() > 0.3:
                        agent.segment_id = seg.parent_id
                        agent.t = 1.0
                    else:
                        agent.t = 0.0
                        agent.direction = 1
            else:
                agent.t += step
                if agent.t >= 1.0:
                    next_seg = choose_next_segment(seg, segments, agent.role, rng)
                    agent.segment_id = next_seg.seg_id
                    agent.t = 0.0

        for seg in segments:
            reduction = 0.00005 * worker_activity[seg.seg_id] * (1.0 + seg.beacon)
            seg.blockage = clamp(seg.blockage - reduction, 0.0, 1.0)

            if seg.scaffold > 0.01:
                seg.pressure_spike = clamp(seg.pressure_spike - 0.04 * seg.scaffold, 0.0, 1.0)

        mapped_percent = sum(seg.mapping for seg in segments) / len(segments) * 100.0
        total_blockage = sum(seg.blockage for seg in segments)
        blockage_reduced = (initial_total_blockage - total_blockage) / initial_total_blockage * 100.0
        support_deployed = sum(seg.scaffold for seg in segments) / len(segments) * 100.0
        support_peak = max(support_peak, support_deployed)

        counts = role_counts(agents)
        status_lines = [
            (f"Mapped: {mapped_percent:5.1f}%", (20, 20, 20)),
            (f"Blockage reduced: {blockage_reduced:5.1f}%", (20, 20, 20)),
            (f"Support deployed: {support_deployed:5.1f}%", (20, 20, 20)),
            (f"Swarm size: {swarm_size}", (20, 20, 20)),
            (f"Mode: {'Activity' if is_activity else 'Rest'}", (20, 80, 20) if is_activity else (80, 60, 20)),
            (
                f"Roles S/W/Su/M: {counts['Scout']}/{counts['Worker']}/{counts['Support']}/{counts['Monitor']}",
                (20, 20, 20),
            ),
        ]

        control_lines = [
            (f"Swarm: {swarm_size}", (20, 20, 20)),
            (f"Flow: {flow:.2f}", (20, 20, 20)),
            (f"Noise: {noise:.2f}", (20, 20, 20)),
            (f"Beacon: {beacon_strength:.2f}", (20, 20, 20)),
            (f"Mode: {'Activity' if is_activity else 'Rest'}", (20, 80, 20) if is_activity else (80, 60, 20)),
            (f"Sensor overlay: {'ON' if sensor_overlay else 'OFF'}", (20, 20, 20)),
            (f"Role switch: {'ON' if role_switch else 'OFF'}", (20, 20, 20)),
            (f"Sensor: {sensor_field.title()}", (20, 20, 20)),
        ]

        reset_flash = any(abs(frame_idx - frame) <= 4 for frame in reset_frames if frame != 0)

        ui_data = {
            "status": status_lines,
            "control": control_lines,
            "reset_flash": reset_flash,
        }

        frame = render_frame(
            frame_idx,
            fps,
            width,
            height,
            segments,
            agents,
            sensor_field,
            sensor_overlay,
            ui_data,
            render_rng,
        )
        frames.append(frame)

    support_peak_history.append(round(support_peak, 3))

    print(f"Generated {len(frames)} frames for swarm simulation", flush=True)
    print(f"Saving video to {video_path}...", flush=True)
    imageio.mimsave(video_path, frames, fps=fps)

    final_counts = role_counts(agents)
    final_mapped = sum(seg.mapping for seg in segments) / len(segments) * 100.0
    final_total_blockage = sum(seg.blockage for seg in segments)
    final_blockage_reduced = (initial_total_blockage - final_total_blockage) / initial_total_blockage * 100.0

    print("Swarm simulation summary:", flush=True)
    print(f"  Final mapped: {final_mapped:.1f}%", flush=True)
    print(f"  Final blockage reduced: {final_blockage_reduced:.1f}%", flush=True)
    print(f"  Support deployed peaks: {support_peak_history}", flush=True)
    print(
        f"  Role counts S/W/Su/M: {final_counts['Scout']}/{final_counts['Worker']}/"
        f"{final_counts['Support']}/{final_counts['Monitor']}",
        flush=True,
    )
    print(f"Video saved: {video_path}", flush=True)

    return video_path


def parse_args():
    parser = argparse.ArgumentParser(description="Swarm vein simulation runner")
    parser.add_argument("--swarm_size", type=int, default=160)
    parser.add_argument("--flow", type=float, default=1.0)
    parser.add_argument("--noise", type=float, default=0.08)
    parser.add_argument("--beacon", type=float, default=0.6)
    parser.add_argument("--mode", type=str, default="rest", choices=["rest", "activity"])
    parser.add_argument(
        "--sensor_field",
        type=str,
        default="viscosity",
        choices=list(SENSOR_FIELDS),
    )
    parser.add_argument("--sensor_overlay", type=int, default=1, choices=[0, 1])
    parser.add_argument("--role_switch", type=int, default=1, choices=[0, 1])
    parser.add_argument("--duration_sec", type=int, default=20)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--reset_at", type=float, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    create_swarm_simulation(
        swarm_size=args.swarm_size,
        flow=args.flow,
        noise=args.noise,
        beacon_strength=args.beacon,
        mode=args.mode,
        sensor_field=args.sensor_field,
        sensor_overlay=args.sensor_overlay,
        role_switch=args.role_switch,
        duration_sec=args.duration_sec,
        fps=args.fps,
        seed=args.seed,
        reset_at=args.reset_at,
    )

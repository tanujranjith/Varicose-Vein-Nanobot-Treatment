#!/usr/bin/env python
"""
Flow Redirection Swarm Simulation: Demonstrates rerouting by localized interventions.
Creates an MP4 video showing temporary microplug closure and longer-term valve remodeling.
"""
import os
import math
import random
import argparse
from PIL import Image, ImageDraw

ROLE_ORDER = ("Scout", "Worker", "Repair", "Monitor")
ROLE_COLORS = {
    "Scout": (70, 190, 235),
    "Worker": (245, 140, 60),
    "Repair": (140, 200, 120),
    "Monitor": (90, 160, 180),
}
ROLE_OUTLINES = {
    "Scout": (40, 120, 170),
    "Worker": (170, 90, 40),
    "Repair": (70, 140, 70),
    "Monitor": (30, 90, 110),
}
ROLE_SIZES = {
    "Scout": 3,
    "Worker": 5,
    "Repair": 4,
    "Monitor": 3,
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
    def __init__(self, seg_id, start, end, name, parent_id=None, is_faulty=False):
        self.seg_id = seg_id
        self.start = start
        self.end = end
        self.name = name
        self.parent_id = parent_id
        self.length = math.hypot(end[0] - start[0], end[1] - start[1])
        self.children = []
        self.is_faulty = is_faulty

        self.beacon = 0.0
        self.mapping = 0.0
        self.pooling = 0.0
        self.reflux = 0.0
        self.valve_competence = 1.0
        self.permeability = 1.0
        self.sensors = {}

    def midpoint(self):
        return ((self.start[0] + self.end[0]) / 2.0, (self.start[1] + self.end[1]) / 2.0)


class SwarmAgent:
    def __init__(self, role, segment_id, t):
        self.role = role
        self.segment_id = segment_id
        self.t = t


def build_network():
    segments = [
        VeinSegment(0, (80, 320), (280, 320), "Trunk"),
        VeinSegment(1, (280, 320), (560, 240), "Deep Path"),
        VeinSegment(2, (280, 320), (540, 400), "Superficial", is_faulty=True),
        VeinSegment(3, (280, 320), (520, 470), "Side Branch"),
    ]

    segments[0].children = [1, 2, 3]
    segments[1].parent_id = 0
    segments[2].parent_id = 0
    segments[3].parent_id = 0

    return segments


def initialize_pathology(segments):
    for seg in segments:
        if seg.is_faulty:
            seg.pooling = 0.65
            seg.valve_competence = 0.2
        else:
            seg.pooling = 0.05
            seg.valve_competence = 0.95


def compute_sensors(seg):
    viscosity = 4.5 + 28.0 * seg.pooling + 18.0 * seg.reflux
    impedance = 1.0 + 60.0 * seg.pooling + 35.0 * seg.reflux
    reflectance = 0.10 + 0.45 * seg.pooling + 0.25 * seg.reflux
    strain = 0.15 + 0.6 * seg.pooling + 0.9 * seg.reflux

    visc_norm = clamp((viscosity - 4.5) / 40.0, 0.0, 1.0)
    imp_norm = clamp((impedance - 1.0) / 95.0, 0.0, 1.0)
    refl_norm = clamp((reflectance - 0.10) / 0.75, 0.0, 1.0)
    strain_norm = clamp(strain / 1.2, 0.0, 1.0)

    seg.sensors = {
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


def create_agents(swarm_size, rng):
    counts = {
        "Scout": int(swarm_size * 0.25),
        "Worker": int(swarm_size * 0.4),
        "Repair": int(swarm_size * 0.2),
    }
    counts["Monitor"] = swarm_size - sum(counts.values())

    roles = []
    for role, count in counts.items():
        roles.extend([role] * count)
    rng.shuffle(roles)

    agents = []
    for role in roles:
        agents.append(SwarmAgent(role, 0, rng.random()))
    return agents


def role_counts(agents):
    counts = {role: 0 for role in ROLE_ORDER}
    for agent in agents:
        counts[agent.role] += 1
    return counts


def compute_flow_shares(segments, plug_progress):
    faulty_segment = next(seg for seg in segments if seg.is_faulty)
    faulty_segment.permeability = clamp(1.0 - plug_progress, 0.05, 1.0)

    weights = {
        1: 1.0,
        2: 0.9 * faulty_segment.permeability * (0.35 + 0.65 * faulty_segment.valve_competence),
        3: 0.7,
    }
    total = sum(weights.values())
    shares = {seg_id: weight / total for seg_id, weight in weights.items()}
    return shares


def choose_branch(flow_shares, segments, role, rng, beacon_bias):
    branch_ids = [1, 2, 3]
    weights = []
    for seg_id in branch_ids:
        seg = segments[seg_id]
        weight = flow_shares.get(seg_id, 0.0) + 0.05
        if role in ("Worker", "Repair", "Scout") and seg.is_faulty:
            weight += beacon_bias
        if role == "Monitor":
            weight += (1.0 - seg.mapping) * 0.4
        weights.append(weight)
    total = sum(weights)
    pick = rng.random() * total
    for seg_id, weight in zip(branch_ids, weights):
        pick -= weight
        if pick <= 0:
            return seg_id
    return branch_ids[-1]


def draw_arrow(draw, start, end, color, direction=1):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    if direction < 0:
        ux, uy = -ux, -uy
    mid_x = start[0] + (end[0] - start[0]) * 0.6
    mid_y = start[1] + (end[1] - start[1]) * 0.6
    tip_x = mid_x + ux * 18
    tip_y = mid_y + uy * 18
    left = (tip_x - ux * 8 - uy * 5, tip_y - uy * 8 + ux * 5)
    right = (tip_x - ux * 8 + uy * 5, tip_y - uy * 8 - ux * 5)
    draw.line([mid_x, mid_y, tip_x, tip_y], fill=color, width=2)
    draw.polygon([left, right, (tip_x, tip_y)], fill=color)


def draw_ui(draw, width, height, status_lines, side_lines):
    panel_bg = (240, 240, 245)
    panel_border = (80, 80, 90)

    status_panel = [10, 10, width - 10, 55]
    draw.rectangle(status_panel, fill=panel_bg, outline=panel_border)
    x = 20
    for text, color in status_lines:
        draw.text((x, 20), text, fill=color)
        x += 200

    side_panel = [width - 270, 70, width - 10, height - 20]
    draw.rectangle(side_panel, fill=panel_bg, outline=panel_border)
    y = 80
    for text, color in side_lines:
        draw.text((width - 260, y), text, fill=color)
        y += 16


def render_frame(
    width,
    height,
    segments,
    agents,
    tracers,
    flow_shares,
    reflux_direction,
    plug_progress,
    pooling_level,
    phase_label,
    status_lines,
    side_lines,
    render_rng,
):
    img = Image.new("RGB", (width, height), color=(245, 245, 250))
    draw = ImageDraw.Draw(img)

    base_color = (170, 110, 120)
    vessel_shadow = (200, 160, 165)
    line_base_width = 12

    for seg in segments:
        seg_color = base_color
        width_mod = 0

        if seg.is_faulty:
            seg_color = lerp_color(base_color, (200, 80, 80), 0.35 + pooling_level * 0.5)
            width_mod += int(8 * pooling_level)

        draw.line([seg.start, seg.end], fill=vessel_shadow, width=line_base_width + width_mod + 4)
        draw.line([seg.start, seg.end], fill=seg_color, width=line_base_width + width_mod)

        if seg.is_faulty and plug_progress > 0.05:
            mid_x, mid_y = seg.midpoint()
            dx = seg.end[0] - seg.start[0]
            dy = seg.end[1] - seg.start[1]
            length = math.hypot(dx, dy) or 1.0
            ux, uy = dx / length, dy / length
            px, py = -uy, ux
            band = 18 + int(12 * plug_progress)
            half = band / 2.0
            p1 = (mid_x + px * half, mid_y + py * half)
            p2 = (mid_x - px * half, mid_y - py * half)
            draw.line([p1, p2], fill=(250, 210, 90), width=5)
            draw.ellipse([mid_x - 6, mid_y - 6, mid_x + 6, mid_y + 6], fill=(250, 190, 80))

    for seg_id, tracer_list in tracers.items():
        seg = segments[seg_id]
        dx = seg.end[0] - seg.start[0]
        dy = seg.end[1] - seg.start[1]
        length = math.hypot(dx, dy) or 1.0
        ux, uy = dx / length, dy / length
        px, py = -uy, ux

        for t in tracer_list:
            offset = render_rng.uniform(-2.5, 2.5)
            x = seg.start[0] + ux * seg.length * t + px * offset
            y = seg.start[1] + uy * seg.length * t + py * offset
            draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(90, 140, 200))

    for seg in segments:
        if seg.seg_id == 0:
            direction = 1
        elif seg.is_faulty:
            direction = reflux_direction
        else:
            direction = 1
        arrow_color = (80, 140, 200)
        if seg.is_faulty and reflux_direction < 0:
            arrow_color = (220, 90, 90)
        draw_arrow(draw, seg.start, seg.end, arrow_color, direction=direction)

    for agent in agents:
        seg = segments[agent.segment_id]
        dx = seg.end[0] - seg.start[0]
        dy = seg.end[1] - seg.start[1]
        length = math.hypot(dx, dy) or 1.0
        ux, uy = dx / length, dy / length
        px, py = -uy, ux

        jitter = 0.9
        offset = render_rng.uniform(-jitter, jitter)
        x = seg.start[0] + ux * seg.length * agent.t + px * offset
        y = seg.start[1] + uy * seg.length * agent.t + py * offset

        radius = ROLE_SIZES[agent.role]
        color = ROLE_COLORS[agent.role]
        outline = ROLE_OUTLINES[agent.role]
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color, outline=outline)

        if agent.role == "Scout":
            draw.ellipse([x - radius - 2, y - radius - 2, x + radius + 2, y + radius + 2],
                         outline=(200, 230, 250), width=1)
        if agent.role == "Monitor":
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], outline=outline, width=1)

    draw_ui(draw, width, height, status_lines, side_lines)
    return img


def create_flow_redirection_simulation(
    swarm_size=200,
    flow=1.0,
    noise=0.08,
    beacon_strength=0.6,
    duration_sec=20,
    fps=30,
    seed=7,
    save_frames=0,
):
    import imageio

    rng = random.Random(seed)
    render_rng = random.Random(seed + 101)

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    video_path = os.path.join(output_dir, "flow_redirection_swarm_sim.mp4")

    width, height = 800, 600
    num_frames = int(duration_sec * fps)

    segments = build_network()
    initialize_pathology(segments)

    agents = create_agents(swarm_size, rng)
    tracers = {seg.seg_id: [] for seg in segments}

    plug_progress = 0.0
    plug_state = "inactive"
    plug_timer = 0.0
    plug_hold_time = 4.0
    plug_dissolve_time = 4.0

    worker_threshold = max(12, int(swarm_size * 0.08))

    if save_frames:
        frame_dir = os.path.join(output_dir, "flow_redirection_frames")
        os.makedirs(frame_dir, exist_ok=True)

    frames = []

    for frame_idx in range(num_frames):
        time_sec = frame_idx / fps
        if time_sec < 5.0:
            phase_label = "Baseline"
        elif time_sec < 12.0:
            phase_label = "Temporary Plug"
        else:
            phase_label = "Remodeling"

        flow_shares = compute_flow_shares(segments, plug_progress)
        faulty_seg = next(seg for seg in segments if seg.is_faulty)

        reflux_base = clamp((1.0 - faulty_seg.valve_competence) * 0.9 * faulty_seg.permeability, 0.0, 1.0)
        reflux_pulse = reflux_base * (0.6 + 0.4 * math.sin(time_sec * 2.4))
        faulty_seg.reflux = reflux_pulse
        reflux_direction = -1 if reflux_pulse > 0.55 and plug_progress < 0.2 else 1

        pooling_delta = (reflux_pulse * 0.018 - flow_shares[2] * 0.013 - plug_progress * 0.02) / fps
        pooling_delta -= faulty_seg.valve_competence * 0.003
        faulty_seg.pooling = clamp(faulty_seg.pooling + pooling_delta, 0.0, 1.0)

        for seg in segments:
            if seg.is_faulty:
                seg.pooling = faulty_seg.pooling
                seg.valve_competence = faulty_seg.valve_competence
                seg.reflux = faulty_seg.reflux
            else:
                seg.reflux = 0.0
            seg.beacon *= 0.9
            compute_sensors(seg)

        worker_on_faulty = 0
        repair_on_faulty = 0

        for agent in agents:
            seg = segments[agent.segment_id]
            abnormal = seg.sensors.get("abnormal", 0.0)

            if agent.role == "Scout" and seg.is_faulty and abnormal > 0.45:
                seg.beacon = clamp(seg.beacon + beacon_strength * 0.04, 0.0, 1.0)

            if agent.role == "Worker" and seg.is_faulty:
                worker_on_faulty += 1

            if agent.role == "Repair" and seg.is_faulty:
                repair_on_faulty += 1

            if agent.role == "Monitor":
                seg.mapping = clamp(seg.mapping + 0.003, 0.0, 1.0)

            base_speed = flow * (0.7 + 0.8 * flow_shares.get(seg.seg_id, 1.0))
            if agent.role == "Worker" and seg.is_faulty:
                base_speed *= 0.6
            if agent.role == "Repair" and seg.is_faulty:
                base_speed *= 0.5
            if agent.role == "Monitor":
                base_speed *= 0.85

            direction = 1
            if seg.is_faulty and reflux_direction < 0:
                direction = -1

            speed = max(0.05, base_speed + rng.uniform(-noise, noise))
            step = speed / seg.length
            agent.t += step * direction

            if agent.t > 1.0 or agent.t < 0.0:
                if seg.seg_id == 0:
                    beacon_bias = segments[2].beacon * 0.8
                    next_id = choose_branch(flow_shares, segments, agent.role, rng, beacon_bias)
                    agent.segment_id = next_id
                    agent.t = 0.0 if direction > 0 else 1.0
                else:
                    agent.segment_id = 0
                    agent.t = 0.0 if direction > 0 else 1.0

        if phase_label == "Temporary Plug":
            if plug_state in ("inactive", "forming") and worker_on_faulty >= worker_threshold:
                plug_state = "forming"
                plug_progress = clamp(plug_progress + 0.02, 0.0, 1.0)
                if plug_progress >= 1.0:
                    plug_state = "active"
                    plug_timer = plug_hold_time
            elif plug_state in ("inactive", "forming"):
                plug_progress = clamp(plug_progress - 0.006, 0.0, 1.0)

        if plug_state == "active":
            plug_timer -= 1.0 / fps
            if plug_timer <= 0 or phase_label == "Remodeling":
                plug_state = "dissolving"
                plug_timer = plug_dissolve_time

        if plug_state == "dissolving":
            plug_progress = clamp(plug_progress - 1.0 / (plug_dissolve_time * fps), 0.0, 1.0)
            plug_timer -= 1.0 / fps
            if plug_progress <= 0.0:
                plug_state = "inactive"
                plug_timer = 0.0

        if phase_label == "Remodeling" and repair_on_faulty > 0:
            faulty_seg.valve_competence = clamp(
                faulty_seg.valve_competence + 0.0008 * repair_on_faulty, 0.0, 1.0
            )

        for seg_id, tracer_list in tracers.items():
            target_flow = flow_shares.get(seg_id, 0.3) if seg_id != 0 else 1.0
            desired_count = int(8 + target_flow * 22)
            if seg_id == 2 and plug_progress > 0.6:
                desired_count = max(4, int(desired_count * (1.0 - plug_progress)))
            current_count = len(tracer_list)
            if current_count < desired_count:
                tracer_list.extend([rng.random() for _ in range(desired_count - current_count)])
            elif current_count > desired_count:
                del tracer_list[desired_count:]

            speed = 0.004 + target_flow * 0.006
            direction = reflux_direction if seg_id == 2 else 1
            for idx, t in enumerate(tracer_list):
                t += speed * direction
                if t > 1.0:
                    t = 0.0
                elif t < 0.0:
                    t = 1.0
                tracer_list[idx] = t

        mapped_percent = sum(seg.mapping for seg in segments) / len(segments) * 100.0
        reflux_percent = faulty_seg.reflux * 100.0
        pooling_percent = faulty_seg.pooling * 100.0
        valve_percent = faulty_seg.valve_competence * 100.0
        flow_main = flow_shares[1] * 100.0
        flow_faulty = flow_shares[2] * 100.0

        plug_text = "inactive"
        if plug_state == "forming":
            plug_text = "forming"
        elif plug_state == "active":
            plug_text = f"active {plug_timer:0.1f}s"
        elif plug_state == "dissolving":
            plug_text = f"dissolving {plug_progress:0.2f}"

        counts = role_counts(agents)
        status_lines = [
            (f"Time {time_sec:4.1f}s", (20, 20, 20)),
            (f"Phase: {phase_label}", (20, 80, 20) if phase_label != "Baseline" else (80, 60, 20)),
            (f"Reflux {reflux_percent:4.0f}%", (200, 70, 70)),
            (f"Pooling {pooling_percent:4.0f}%", (160, 90, 160)),
        ]

        side_lines = [
            (f"Mapped: {mapped_percent:4.1f}%", (20, 20, 20)),
            (f"Flow split main/faulty:", (20, 20, 20)),
            (f"  {flow_main:4.0f}% / {flow_faulty:4.0f}%", (20, 20, 20)),
            (f"Plug state: {plug_text}", (20, 20, 20)),
            (f"Valve competence: {valve_percent:4.0f}%", (20, 20, 20)),
            (f"Swarm size: {swarm_size}", (20, 20, 20)),
            (
                f"Roles S/W/R/M: {counts['Scout']}/{counts['Worker']}/{counts['Repair']}/{counts['Monitor']}",
                (20, 20, 20),
            ),
        ]

        frame = render_frame(
            width,
            height,
            segments,
            agents,
            tracers,
            flow_shares,
            reflux_direction,
            plug_progress,
            faulty_seg.pooling,
            phase_label,
            status_lines,
            side_lines,
            render_rng,
        )

        if save_frames:
            frame_path = os.path.join(frame_dir, f"frame_{frame_idx:04d}.png")
            frame.save(frame_path)

        frames.append(frame)

    print(f"Generated {len(frames)} frames for flow redirection simulation", flush=True)
    print(f"Saving video to {video_path}...", flush=True)
    imageio.mimsave(video_path, frames, fps=fps)

    final_flow_shares = compute_flow_shares(segments, plug_progress)
    print("Flow redirection summary:", flush=True)
    print(f"  Final reflux severity: {segments[2].reflux * 100.0:.1f}%", flush=True)
    print(f"  Final pooling: {segments[2].pooling * 100.0:.1f}%", flush=True)
    print(f"  Valve competence: {segments[2].valve_competence * 100.0:.1f}%", flush=True)
    print(
        f"  Flow split main/faulty: {final_flow_shares[1] * 100.0:.1f}%/"
        f"{final_flow_shares[2] * 100.0:.1f}%",
        flush=True,
    )
    print(f"Video saved: {video_path}", flush=True)
    return video_path


def parse_args():
    parser = argparse.ArgumentParser(description="Flow redirection swarm simulation runner")
    parser.add_argument("--swarm_size", type=int, default=200)
    parser.add_argument("--flow", type=float, default=1.0)
    parser.add_argument("--noise", type=float, default=0.08)
    parser.add_argument("--beacon", type=float, default=0.6)
    parser.add_argument("--duration_sec", type=int, default=20)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--save_frames", type=int, default=0, choices=[0, 1])
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    create_flow_redirection_simulation(
        swarm_size=args.swarm_size,
        flow=args.flow,
        noise=args.noise,
        beacon_strength=args.beacon,
        duration_sec=args.duration_sec,
        fps=args.fps,
        seed=args.seed,
        save_frames=args.save_frames,
    )

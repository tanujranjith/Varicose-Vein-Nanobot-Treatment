# Nanobot Simulation (Varicose Vein)

A Python project that simulates a magnetically driven nanobot navigating a vein and clearing a clog blockage. The simulation is visualized as an MP4 video.

## Features
- Simulation of a nanobot clearing a varicose vein clog
- Visual animation showing nanobot movement and clog clearance
- MP4 video export with progress indicators
- Simple PIL-based rendering (no complex graphics libraries required)

## Prerequisites
- Python 3.10+
- Windows or cross-platform compatible

## Quick Start

### 1. Install Dependencies (Windows)
```bat
pip install pillow imageio imageio-ffmpeg
```

### 2. Run the Simulation
```bat
python run_nanobot_sim.py
```

The simulation will generate an MP4 video at `outputs/nanobot_sim.mp4` showing:
- A blue nanobot (sphere) moving through a vein
- A red clog (blockage) that shrinks as the nanobot clears it
- Progress indicators and status messages
- The nanobot's velocity and position

### 3. View the Video
Open `outputs/nanobot_sim.mp4` in any video player (VLC, Windows Media Player, etc.)

## Swarm Vein Simulation (New)

This mode renders a branching vein network with a role-based nanobot swarm.

### Run the Swarm Simulation
```bat
python run_swarm_vein_sim.py
```

Output video: `outputs/swarm_vein_sim.mp4`

Optional flags:
```bat
python run_swarm_vein_sim.py --swarm_size 160 --flow 1.0 --noise 0.08 --beacon 0.6 --mode rest --sensor_field viscosity --sensor_overlay 1 --role_switch 1 --duration_sec 20 --fps 30 --seed 7 --reset_at 10
```

By default, a timed reset cue triggers around 10s when duration is 12s or longer. Use `--reset_at` to set a different time.

## Project Structure
```
c:\Sansten\vRobot
├── run_nanobot_sim.py      # Main simulation runner
├── requirements.txt         # Package dependencies
├── README.md               # This file
└── outputs/
    └── nanobot_sim.mp4    # Generated simulation video
```

## How It Works

The simulation shows:
1. **Nanobot**: A small blue sphere with a glow effect representing the magnetic nanobot
2. **Vein**: A corridor bounded by walls representing the blood vessel
3. **Clog**: A red sphere representing the blockage/clot
4. **Clearance**: As the nanobot moves toward the clog, it progressively shrinks and disappears

The animation demonstrates how a nanobot could be guided magnetically through a vein to reach and clear an obstruction, minimizing invasiveness compared to traditional surgery.

## Optional: Advanced PyBullet Physics Simulation

For a full physics-based simulation using PyBullet (requires C++ build tools):
```bat
pip install pybullet
python -m src.run_simulation
```

## Notes
- The visualization is qualitative; it simplifies blood flow and micro-scale physics
- Real nanobot research is still experimental but progressing rapidly
- For educational purposes: suitable for science fairs and presentations
- Video format: MP4, 30 FPS, 800×600 resolution

## References
See `requirements.md` for scientific background and references on varicose veins and nanomedical research.


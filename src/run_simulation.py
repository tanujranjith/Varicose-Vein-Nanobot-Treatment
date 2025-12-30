import os
import time
from simulation.vein_env import VeinEnvironment
from simulation.nanobot import Nanobot

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
VIDEO_PATH = os.path.join(OUTPUT_DIR, "nanobot_sim.mp4")


def ensure_dirs():
    os.makedirs(FRAMES_DIR, exist_ok=True)


def main(gui: bool = True, record_video: bool = True):
    print(f"Entering main(gui={gui}, record_video={record_video})", flush=True)
    import pybullet as p
    print("PyBullet imported", flush=True)
    import pybullet_data
    print("PyBullet data imported", flush=True)
    import imageio
    print("imageio imported", flush=True)
    
    print(f"Output directory: {OUTPUT_DIR}", flush=True)
    print(f"Frames directory: {FRAMES_DIR}", flush=True)
    ensure_dirs()

    conn_mode = p.GUI if gui else p.DIRECT
    p.connect(conn_mode)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())

    env = VeinEnvironment(length=5.0, radius=0.2, wall_thickness=0.1)
    env.setup()

    clog_id = env.add_clog(position=(0.0, 0.0, 0.0), radius=0.07)
    bot = Nanobot(start_pos=(-env.length/2 + 0.1, 0.0, 0.0), radius=0.05, mass=1.0)

    target = (0.0, 0.0, 0.0)
    done = False
    frames = []

    # Optional: slow down for viewing when GUI is on
    step_sleep = 1.0/240.0 if gui else 0.0

    for step in range(3000):
        if not done:
            bot.apply_force_towards(target, magnitude=5.0)
            contacts = p.getContactPoints(bodyA=bot.body_id, bodyB=clog_id)
            if contacts:
                env.remove_clog(clog_id)
                done = True
        p.stepSimulation()
        if record_video:
            # Capture camera image
            try:
                if gui:
                    width, height, view_matrix, proj_matrix, _, _, _, _, _, _, _, _ = p.getDebugVisualizerCamera()
                    img = p.getCameraImage(width, height, renderer=p.ER_BULLET_HARDWARE_OPENGL,
                                           viewMatrix=view_matrix, projectionMatrix=proj_matrix)
                else:
                    # Headless mode: use default camera
                    img = p.getCameraImage(640, 480)
                frame = img[2]  # RGB array
                frames.append(frame)
            except Exception as e:
                pass  # Skip frame on error
        if step_sleep:
            time.sleep(step_sleep)

    if record_video and frames:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        imageio.mimsave(VIDEO_PATH, frames, fps=30)
        print(f"Saved video to: {VIDEO_PATH}")
    elif record_video:
        print(f"No frames captured. Frames list: {len(frames)} items")

    p.disconnect()
    print("Simulation complete.", "Clog cleared." if done else "Clog not reached in time.")


if __name__ == "__main__":
    main(gui=False, record_video=True)

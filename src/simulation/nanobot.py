from typing import Tuple

class Nanobot:
    def __init__(self, start_pos: Tuple[float, float, float], radius: float = 0.05, mass: float = 1.0):
        self.radius = radius
        self.mass = mass
        self.body_id = self._create_body(start_pos)

    def _create_body(self, start_pos):
        import pybullet as p
        bot_collision = p.createCollisionShape(p.GEOM_SPHERE, radius=self.radius)
        bot_visual = p.createVisualShape(p.GEOM_SPHERE, radius=self.radius, rgbaColor=[0.2, 0.2, 1.0, 1])
        return p.createMultiBody(baseMass=self.mass, baseCollisionShapeIndex=bot_collision,
                                 baseVisualShapeIndex=bot_visual, basePosition=list(start_pos))

    def apply_force_towards(self, target: Tuple[float, float, float], magnitude: float = 5.0) -> None:
        import pybullet as p
        pos, _ = p.getBasePositionAndOrientation(self.body_id)
        dir_vec = [target[i] - pos[i] for i in range(3)]
        p.applyExternalForce(self.body_id, -1,
                             [magnitude * dir_vec[0], magnitude * dir_vec[1], magnitude * dir_vec[2]],
                             pos, flags=p.WORLD_FRAME)

    def position(self) -> Tuple[float, float, float]:
        import pybullet as p
        pos, _ = p.getBasePositionAndOrientation(self.body_id)
        return tuple(pos)

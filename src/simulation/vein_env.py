from typing import List, Tuple

class VeinEnvironment:
    def __init__(self, length: float = 5.0, radius: float = 0.2, wall_thickness: float = 0.1):
        self.length = length
        self.radius = radius
        self.wall_thickness = wall_thickness
        self.wall_ids: List[int] = []
        self.clog_ids: List[int] = []

    def setup(self) -> None:
        import pybullet as p
        p.setGravity(0, 0, 0)
        half_length = self.length / 2
        half_rad = self.radius
        half_thickness = self.wall_thickness / 2

        wall_collision = p.createCollisionShape(p.GEOM_BOX, halfExtents=[half_length, half_thickness, half_rad])
        wall_visual = p.createVisualShape(p.GEOM_BOX, halfExtents=[half_length, half_thickness, half_rad], rgbaColor=[0.9, 0.9, 0.9, 1])
        # Left wall
        self.wall_ids.append(p.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_collision, baseVisualShapeIndex=wall_visual,
                                               basePosition=[0, -half_rad - half_thickness, 0]))
        # Right wall
        self.wall_ids.append(p.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_collision, baseVisualShapeIndex=wall_visual,
                                               basePosition=[0,  half_rad + half_thickness, 0]))

        floor_collision = p.createCollisionShape(p.GEOM_BOX, halfExtents=[half_length, half_rad, half_thickness])
        floor_visual = p.createVisualShape(p.GEOM_BOX, halfExtents=[half_length, half_rad, half_thickness], rgbaColor=[0.9, 0.9, 0.9, 1])
        # Bottom wall
        self.wall_ids.append(p.createMultiBody(baseMass=0, baseCollisionShapeIndex=floor_collision, baseVisualShapeIndex=floor_visual,
                                               basePosition=[0, 0, -half_rad - half_thickness]))
        # Top wall
        self.wall_ids.append(p.createMultiBody(baseMass=0, baseCollisionShapeIndex=floor_collision, baseVisualShapeIndex=floor_visual,
                                               basePosition=[0, 0,  half_rad + half_thickness]))

    def add_clog(self, position: Tuple[float, float, float] = (0.0, 0.0, 0.0), radius: float = 0.07) -> int:
        import pybullet as p
        clog_collision = p.createCollisionShape(p.GEOM_SPHERE, radius=radius)
        clog_visual = p.createVisualShape(p.GEOM_SPHERE, radius=radius, rgbaColor=[1.0, 0.2, 0.2, 1])
        clog_id = p.createMultiBody(baseMass=0, baseCollisionShapeIndex=clog_collision, baseVisualShapeIndex=clog_visual,
                                    basePosition=list(position))
        self.clog_ids.append(clog_id)
        return clog_id

    def remove_clog(self, clog_id: int) -> None:
        import pybullet as p
        p.removeBody(clog_id)
        self.clog_ids = [cid for cid in self.clog_ids if cid != clog_id]

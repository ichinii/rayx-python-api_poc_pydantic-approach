"""Thin pydantic/numpy layer on top of the C++ model."""

import numpy as np
from pydantic import BaseModel, Field

from ._core import Model


class Particle(BaseModel):
    name: str = "p"
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def to_model(self) -> Model:
        m = Model()
        m.name = self.name
        m.position = self.position
        m.velocity = self.velocity
        return m


def simulate(particle: Particle, dt: float = 0.1, steps: int = 10) -> np.ndarray:
    """Run the C++ model and return the trajectory as an (steps, 3) array."""
    m = particle.to_model()
    return np.array([(m.step(dt), m.position)[1] for _ in range(steps)], dtype=np.float32)

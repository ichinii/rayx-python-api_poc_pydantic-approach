from model0 import Particle, simulate

p = Particle(name="ball", position=(0.0, 0.0, 0.0), velocity=(1.0, 2.0, 0.0))
trajectory = simulate(p, dt=0.5, steps=4)

print(p)
print("speed:", p.to_model().speed())
print("trajectory:\n", trajectory)

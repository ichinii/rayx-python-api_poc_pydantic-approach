import math
import json
import rayx

source = rayx.PointSource(
    global_transform=rayx.Transform(position=[0.0, 0.0, 0.0]),
    num_rays=1,
    ray_origin=[0.0, 0.0, 0.0],
    ray_angle=[
        rayx.GaussianDistribution(mean=0.0, standard_deviation=0.001),
        0.0
    ],
    photon_energy=rayx.GaussianDistribution(mean=300.0, standard_deviation=1.0),
    polarization=rayx.LocalElectricField(value=[1.0 + 0.0j, 0.0 + 0.0j]),
)

mirror = rayx.Mirror(
    global_transform=rayx.Transform(
        position=[0.0, 0.0, 1.0],
        orientation=rayx.AxisAngle(axis=[1.0, 0.0, 0.0], angle=math.radians(-45.0))
    ),
    area=rayx.RectArea(width=0.2, height=0.2),
    substrate="Si",
)

detector = rayx.Detector(
    global_transform=rayx.Transform(
        position=[0.0, 1.0, 1.0],
        orientation=rayx.AxisAngle(axis=[1.0, 0.0, 0.0], angle=math.radians(90.0))
    ),
    area=rayx.RectArea(width=0.2, height=0.2),
)

objects = [source, mirror, detector]
beamline = rayx.Beamline(objects=objects)

trace_params = rayx.TraceParams(
    ray_attr_record_mask=(
        rayx.RayAttrMask.POSITION | rayx.RayAttrMask.EVENT_TYPE | rayx.RayAttrMask.OBJECT_ID
    )
)

rays = rayx.trace(beamline, trace_params)
detector_id = next(i for i, o in enumerate(objects) if o is detector)
on_detector = (rays.event_type == rayx.EventType.HIT_ELEMENT) & (rays.object_id == detector_id)

print(f"{len(rays.position_x)} events recorded, {on_detector.sum()} of them on the detector")
print("position_x:", rays.position_x[on_detector])
print("position_y:", rays.position_y[on_detector])
print("position_z:", rays.position_z[on_detector])


# write json
with open("beamline.json", "w") as f:
    f.write(beamline.model_dump_json(indent=2))

# read json and check equality
with open("beamline.json", "r") as f:
    beamline_import = rayx.Beamline.model_validate_json(f.read())
    print(f"json export+import equality: {beamline_import == beamline}")

# write json schema
with open("beamline_schema.json", "w") as f:
    f.write(json.dumps(rayx.Beamline.model_json_schema(), indent=2))

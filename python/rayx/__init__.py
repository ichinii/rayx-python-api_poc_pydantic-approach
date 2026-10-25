"""rayx - ray tracing for x-ray optics beamlines.

The public API is the pydantic model in `rayx._model1`, re-exported here. `rayx._model0`
is the plain wire model shared with the C++ core. `rayx._validate` checks a model1
tree, `rayx._lower` translates it to model0, and `rayx._trace` drives a trace.

What is exported here is deliberately narrower than `rayx._model1.__all__`: the `Model`
base class and the validation tolerances are implementation details, reachable as
`rayx._model1.Model` and so on, but not part of the API.
"""

# enums and ray storage, shared with the C++ core
from ._model1 import (
    ElectronEnergyOrientation,
    EventType,
    RayAttrMask,
    ToroidType,
    UndulatorSigmaType,
)

# types
from ._model1 import (
    AxisAngle,
    Basis,
    LocalElectricField,
    Material,
    Orientation,
    Polarization,
    Stokes,
    Transform,
    Vec3,
    to_axis_angle,
    to_basis,
    to_local_electric_field,
    to_stokes,
)

# element building blocks
from ._model1 import (
    Area,
    Coating,
    CoatingLayer,
    CubicCurvature,
    Curvature,
    DiffractiveArea,
    EllipseArea,
    FlatCurvature,
    QuadricCurvature,
    RectArea,
    SlopeError,
    ToroidialCurvature,
    TrapezoidArea,
)

# elements
from ._model1 import (
    Aperture,
    Crystal,
    Detector,
    Foil,
    Grating,
    Mirror,
    Rzp,
    Slit,
)

# source building blocks
from ._model1 import (
    BakedDistribution,
    DiscreteUniformDistribution,
    Distribution,
    Distribution2,
    Distribution3,
    GaussianDistribution,
    WhiteNoiseDistribution,
)

# sources
from ._model1 import (
    CircleSource,
    DipoleSource,
    MatrixSource,
    PixelSource,
    PointSource,
    SimpleUndulatorSource,
)

# beamline and tracing
from ._model1 import Beamline, Object, TraceParams
from ._rays import Rays
from ._trace import trace
from ._validate import validate

__all__ = [
    # enums and ray storage, shared with the C++ core
    "ElectronEnergyOrientation",
    "EventType",
    "RayAttrMask",
    "Rays",
    "ToroidType",
    "UndulatorSigmaType",
    # types
    "AxisAngle",
    "Basis",
    "LocalElectricField",
    "Material",
    "Orientation",
    "Polarization",
    "Stokes",
    "Transform",
    "Vec3",
    "to_axis_angle",
    "to_basis",
    "to_local_electric_field",
    "to_stokes",
    # element building blocks
    "Area",
    "Coating",
    "CoatingLayer",
    "CubicCurvature",
    "Curvature",
    "DiffractiveArea",
    "EllipseArea",
    "FlatCurvature",
    "QuadricCurvature",
    "RectArea",
    "SlopeError",
    "ToroidialCurvature",
    "TrapezoidArea",
    # elements
    "Aperture",
    "Crystal",
    "Detector",
    "Foil",
    "Grating",
    "Mirror",
    "Rzp",
    "Slit",
    # source building blocks
    "BakedDistribution",
    "DiscreteUniformDistribution",
    "Distribution",
    "Distribution2",
    "Distribution3",
    "GaussianDistribution",
    "WhiteNoiseDistribution",
    # sources
    "CircleSource",
    "DipoleSource",
    "MatrixSource",
    "PixelSource",
    "PointSource",
    "SimpleUndulatorSource",
    # beamline and tracing
    "Beamline",
    "Object",
    "TraceParams",
    "trace",
    "validate",
]

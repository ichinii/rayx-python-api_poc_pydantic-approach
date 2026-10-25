import cmath
import math
import numbers
from typing import Annotated, Any, Literal, Optional, Union

from annotated_types import Len
from typing_extensions import TypeAliasType
from pydantic import BaseModel, ConfigDict, Discriminator, Field, Tag, model_validator

from ._model0 import (
    ElectronEnergyOrientation,
    EventType,
    RayAttrMask,
    ToroidType,
    UndulatorSigmaType,
)

##############################################################################
# types
##############################################################################


class Model(BaseModel):
    # validation runs wherever an object is complete: at construction, when loading
    # json, and over the whole beamline in `rayx.validate` before a trace. it
    # deliberately does not run on assignment, because building a value up field by
    # field passes through states that are not yet valid -- there is no order in which
    # the components of a quaternion can be written that keeps it unit at every step.
    model_config = ConfigDict(extra="forbid")


# alias, so that a registry or Literal of known materials can replace it later
Material = TypeAliasType("Material", str)


Vec3 = TypeAliasType("Vec3", Annotated[list[float], Len(3, 3)])

# orientations are rejected rather than normalized, so that a mistyped vector is an
# error instead of plausible looking but wrong geometry
ORIENTATION_TOLERANCE = 1e-9


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


class AxisAngle(Model):
    """A rotation of `angle` rad about `axis`, right handed.

    Defaults to the identity rotation. The axis must be a unit vector; its length
    carries no information, so a non unit one is rejected rather than silently scaled.
    Use `normalized()` to opt in.
    """

    kind: Literal["axis_angle"] = "axis_angle"

    axis: Vec3 = [0.0, 0.0, 1.0]
    angle: float = 0.0  # rad

    @model_validator(mode="after")
    def _check_unit_axis(self) -> "AxisAngle":
        norm = math.sqrt(_dot(self.axis, self.axis))
        if abs(norm - 1.0) > ORIENTATION_TOLERANCE:
            raise ValueError(
                f"axis must be a unit vector, got norm {norm}. "
                f"use AxisAngle.normalized() to scale it explicitly"
            )
        return self

    def normalized(self) -> "AxisAngle":
        """This rotation with its axis scaled to unit length."""
        norm = math.sqrt(_dot(self.axis, self.axis))
        if norm == 0.0:
            raise ValueError("a zero axis does not define a rotation")
        return AxisAngle(axis=[c / norm for c in self.axis], angle=self.angle)


class Basis(Model):
    # orthonormal and right handed, defaults to the standard basis
    kind: Literal["basis"] = "basis"

    x: Vec3 = [1.0, 0.0, 0.0]
    y: Vec3 = [0.0, 1.0, 0.0]
    z: Vec3 = [0.0, 0.0, 1.0]

    # note: there is deliberately no `orthonormalized()` counterpart to
    # `AxisAngle.normalized()`. orthonormalizing a skewed frame has to pick an
    # arbitrary vector to hold fixed, so it would silently invent an orientation.
    @model_validator(mode="after")
    def _check_orthonormal(self) -> "Basis":
        for name, v in (("x", self.x), ("y", self.y), ("z", self.z)):
            norm = math.sqrt(_dot(v, v))
            if abs(norm - 1.0) > ORIENTATION_TOLERANCE:
                raise ValueError(
                    f"basis vector {name} must be a unit vector, got norm {norm}"
                )

        for a_name, a, b_name, b in (
            ("x", self.x, "y", self.y),
            ("y", self.y, "z", self.z),
            ("x", self.x, "z", self.z),
        ):
            dot = _dot(a, b)
            if abs(dot) > ORIENTATION_TOLERANCE:
                raise ValueError(
                    f"basis vectors {a_name} and {b_name} must be orthogonal, "
                    f"got dot product {dot}"
                )

        # for an orthonormal basis the determinant is +-1, so its sign is the handedness
        determinant = _dot(self.x, _cross(self.y, self.z))
        if determinant <= 0.0:
            raise ValueError(
                f"basis must be right handed, i.e. cross(x, y) == z, "
                f"got determinant {determinant}"
            )
        return self


Orientation = TypeAliasType("Orientation", Annotated[Union[AxisAngle, Basis], Field(discriminator="kind")])


def to_basis(value: Orientation) -> Basis:
    """The orientation as the images of the local x, y and z axes."""
    if isinstance(value, Basis):
        return value

    kx, ky, kz = value.axis
    cos, sin = math.cos(value.angle), math.sin(value.angle)
    t = 1.0 - cos
    # rodrigues, taken column wise: each column is where one local axis ends up
    return Basis(
        x=[t * kx * kx + cos, t * kx * ky + sin * kz, t * kx * kz - sin * ky],
        y=[t * kx * ky - sin * kz, t * ky * ky + cos, t * ky * kz + sin * kx],
        z=[t * kx * kz + sin * ky, t * ky * kz - sin * kx, t * kz * kz + cos],
    )


def to_axis_angle(value: Orientation) -> AxisAngle:
    """The orientation as a rotation about a single axis.

    The identity has no axis to speak of, so it reports the z axis and a zero angle.
    """
    if isinstance(value, AxisAngle):
        return value

    # R[row][col] == value.<col>[row], since a basis vector is a column
    trace = value.x[0] + value.y[1] + value.z[2]
    angle = math.acos(max(-1.0, min(1.0, (trace - 1.0) / 2.0)))

    if angle < ORIENTATION_TOLERANCE:
        return AxisAngle()

    if math.pi - angle > ORIENTATION_TOLERANCE:
        # the antisymmetric part is 2 sin(angle) * axis
        axis = [value.y[2] - value.z[1], value.z[0] - value.x[2], value.x[1] - value.y[0]]
        scale = 2.0 * math.sin(angle)
        return AxisAngle(axis=[c / scale for c in axis], angle=angle)

    # at half a turn the antisymmetric part vanishes, so take the axis from the
    # diagonal instead, using the largest entry to keep the division well conditioned
    diagonal = [value.x[0], value.y[1], value.z[2]]
    largest = diagonal.index(max(diagonal))
    columns = [value.x, value.y, value.z]
    axis = [0.0, 0.0, 0.0]
    axis[largest] = math.sqrt(max(diagonal[largest] + 1.0, 0.0) / 2.0)
    for other in range(3):
        if other != largest:
            axis[other] = columns[other][largest] / (2.0 * axis[largest])
    return AxisAngle(axis=axis, angle=angle)


class Transform(Model):
    position: Vec3 = [0.0, 0.0, 0.0]  # mm
    orientation: Orientation = AxisAngle()


# only fully polarized light is supported, so a degree of polarization is required to
# be 1 within this tolerance rather than being silently projected onto the Poincare
# sphere
POLARIZATION_TOLERANCE = 1e-9


class LocalElectricField(Model):
    """Jones vector, in the basis of the object it belongs to.

    Two components, because in that basis the field is transverse to the direction of
    propagation. A Jones vector can only describe fully polarized light, so
    `degree_of_polarization` is 1 by construction.
    """

    kind: Literal["local_electric_field"] = "local_electric_field"

    value: Annotated[list[complex], Len(2, 2)]

    def degree_of_polarization(self) -> float:
        return 1.0

    @model_validator(mode="after")
    def _check_nonzero(self) -> "LocalElectricField":
        if self.intensity() <= 0.0:
            raise ValueError("the electric field must be non zero, it carries no polarization otherwise")
        return self

    def intensity(self) -> float:
        ex, ey = self.value
        return abs(ex) ** 2 + abs(ey) ** 2


class Stokes(Model):
    """Stokes parameters `[I, Q, U, V]`, in the basis of the object they belong to.

    I is the total intensity, Q the horizontal versus vertical linear polarization, U
    the same at 45 degrees, and V the circular polarization. Unlike a Jones vector these
    can describe partially polarized light, which is why the invariant below exists.
    """

    kind: Literal["stokes"] = "stokes"

    value: Annotated[list[float], Len(4, 4)]

    def degree_of_polarization(self) -> float:
        i, q, u, v = self.value
        return math.sqrt(q * q + u * u + v * v) / i

    @model_validator(mode="after")
    def _check_fully_polarized(self) -> "Stokes":
        if self.intensity() <= 0.0:
            raise ValueError(f"the stokes intensity I must be positive, got {self.intensity()}")
        degree = self.degree_of_polarization()
        if abs(degree - 1.0) > POLARIZATION_TOLERANCE:
            raise ValueError(
                f"only fully polarized light is supported, got degree of polarization {degree}. "
                f"it must satisfy Q^2 + U^2 + V^2 == I^2"
            )
        return self

    def intensity(self) -> float:
        i, q, u, v = self.value
        return i


Polarization = TypeAliasType("Polarization", Annotated[Union[LocalElectricField, Stokes], Field(discriminator="kind")])


def to_stokes(value: Polarization) -> Stokes:
    """The polarization as stokes parameters.

    Sign convention: `U = 2 Re(Ex conj(Ey))` and `V = 2 Im(conj(Ex) Ey)`, so that
    `Ex = 1, Ey = 1j` gives `V = +2`.
    """
    if isinstance(value, Stokes):
        return value

    ex, ey = value.value
    return Stokes(
        value=[
            abs(ex) ** 2 + abs(ey) ** 2,
            abs(ex) ** 2 - abs(ey) ** 2,
            2.0 * (ex * ey.conjugate()).real,
            2.0 * (ex.conjugate() * ey).imag,
        ]
    )


def to_local_electric_field(value: Polarization) -> LocalElectricField:
    """The polarization as a jones vector.

    This is only defined for fully polarized light, which `Stokes` already guarantees.

    Stokes parameters carry no overall phase, so the result puts the whole relative
    phase on the y component and leaves x real. Round tripping a `LocalElectricField`
    through `to_stokes` therefore returns a vector that is equal up to a global phase
    factor, which is the same physical state but not the same numbers.
    """
    if isinstance(value, LocalElectricField):
        return value

    i, q, u, v = value.value
    # clamped because Q may exceed I by a rounding error even when the invariant holds
    magnitude_x = math.sqrt(max(i + q, 0.0) / 2.0)
    magnitude_y = math.sqrt(max(i - q, 0.0) / 2.0)
    relative_phase = math.atan2(v, u)
    return LocalElectricField(value=[complex(magnitude_x, 0.0), magnitude_y * cmath.exp(1j * relative_phase)])


##############################################################################
# element building blocks
##############################################################################


class RectArea(Model):
    kind: Literal["rectangular"] = "rectangular"

    width: float
    height: float


class EllipseArea(Model):
    kind: Literal["elliptical"] = "elliptical"

    horizontal_diameter: float
    vertical_diameter: float


class TrapezoidArea(Model):
    kind: Literal["trapezoidal"] = "trapezoidal"

    top_width: float
    bottom_width: float
    height: float


Area = TypeAliasType(
    "Area",
    Annotated[
        Union[RectArea, EllipseArea, TrapezoidArea],
        Field(discriminator="kind"),
    ],
)
DiffractiveArea = TypeAliasType(
    "DiffractiveArea",
    Annotated[
        Union[RectArea, EllipseArea],
        Field(discriminator="kind"),
    ],
)


class FlatCurvature(Model):
    kind: Literal["flat"] = "flat"


class QuadricCurvature(Model):
    kind: Literal["quadric"] = "quadric"

    icurv: int
    a11: float
    a12: float
    a13: float
    a14: float
    a22: float
    a23: float
    a24: float
    a33: float
    a34: float
    a44: float


class ToroidialCurvature(Model):
    kind: Literal["toroidial"] = "toroidial"

    long_radius: float
    short_radius: float
    toroid_type: ToroidType


class CubicCurvature(Model):
    kind: Literal["cubic"] = "cubic"

    a11: float
    a12: float
    a13: float
    a14: float
    a22: float
    a23: float
    a24: float
    a33: float
    a34: float
    a44: float

    b12: float
    b13: float
    b21: float
    b23: float
    b31: float
    b32: float

    psi: float


Curvature = TypeAliasType(
    "Curvature",
    Annotated[
        Union[FlatCurvature, QuadricCurvature, ToroidialCurvature, CubicCurvature],
        Field(discriminator="kind"),
    ],
)


class SlopeError(Model):
    # defaults to a perfect surface, so that `SlopeError()` is a meaningful default
    saggital_rms: float = 0.0
    meridional_rms: float = 0.0


class CoatingLayer(Model):
    material: Material
    thickness: float
    roughness: float


class Coating(Model):
    layers: list[CoatingLayer] = []


##############################################################################
# elements
##############################################################################


class Detector(Model):
    kind: Literal["detector"] = "detector"

    # general object properties
    global_transform: Transform = Transform()

    # general element properties
    area: RectArea
    curvature: Curvature = FlatCurvature()


class Aperture(Model):
    kind: Literal["aperture"] = "aperture"

    # general object properties
    global_transform: Transform = Transform()

    # general element properties
    area: RectArea
    curvature: Curvature = FlatCurvature()

    # specific element properties
    aperture_area: Area


class Slit(Model):
    kind: Literal["slit"] = "slit"

    # general object properties
    global_transform: Transform = Transform()

    # general element properties
    area: RectArea

    # specific element properties
    slit_area: DiffractiveArea


class Foil(Model):
    kind: Literal["foil"] = "foil"

    # general object properties
    global_transform: Transform = Transform()

    # general element properties
    area: RectArea
    curvature: Curvature = FlatCurvature()
    slope_error: SlopeError = SlopeError()

    # specific element properties
    substrate: Material
    substrate_thickness: float
    substrate_roughness: float
    coating: Coating = Coating()


class Mirror(Model):
    kind: Literal["mirror"] = "mirror"

    # general object properties
    global_transform: Transform = Transform()

    # general element properties
    area: RectArea
    curvature: Curvature = FlatCurvature()
    slope_error: SlopeError = SlopeError()

    # specific element properties
    substrate: Material
    coating: Coating = Coating()


class Grating(Model):
    kind: Literal["grating"] = "grating"

    # general object properties
    global_transform: Transform = Transform()

    # general element properties
    area: RectArea
    curvature: Curvature = FlatCurvature()
    slope_error: SlopeError = SlopeError()

    # specific element properties
    order_of_diffraction: int
    line_density: float
    vls: Annotated[list[float], Len(6, 6)]


class Rzp(Model):
    kind: Literal["rzp"] = "rzp"

    # general object properties
    global_transform: Transform = Transform()

    # general element properties
    area: RectArea
    curvature: Curvature = FlatCurvature()
    slope_error: SlopeError = SlopeError()

    # specific element properties
    image_type: int
    rzp_type: int
    derivation_method: int
    design_order_of_diffraction: int
    order_of_diffraction: int
    additional_order: int
    design_wavelength: float
    fresnel_z_offset: float
    design_sagittal_entrance_arm_length: float
    design_sagittal_exit_arm_length: float
    design_meridional_entrance_arm_length: float
    design_meridional_exit_arm_length: float
    design_alpha_angle: float
    design_beta_angle: float


class Crystal(Model):
    kind: Literal["crystal"] = "crystal"

    # general object properties
    global_transform: Transform = Transform()

    # general element properties
    area: RectArea
    curvature: Curvature = FlatCurvature()
    slope_error: SlopeError = SlopeError()

    # specific element properties
    d_spacing2: float
    unit_cell_volume: float
    offset_angle: float
    structure_factor_re_f0: float
    structure_factor_im_f0: float
    structure_factor_re_fh: float
    structure_factor_im_fh: float
    structure_factor_re_fhc: float
    structure_factor_im_fhc: float


##############################################################################
# source building blocks
##############################################################################


class DiscreteUniformDistribution(Model):
    kind: Literal["discrete_uniform"] = "discrete_uniform"

    center: float
    width: float
    count: int


class WhiteNoiseDistribution(Model):
    kind: Literal["white_noise"] = "white_noise"

    center: float
    width: float


class GaussianDistribution(Model):
    kind: Literal["gaussian"] = "gaussian"

    mean: float
    standard_deviation: float


class BakedDistribution(Model):
    kind: Literal["baked"] = "baked"

    values: list[float]
    weights: Optional[list[float]] = None

    @model_validator(mode="after")
    def _check_weights(self) -> "BakedDistribution":
        if self.weights is not None and len(self.weights) != len(self.values):
            raise ValueError(
                f"weights must have the same size as values, "
                f"got {len(self.weights)} weights for {len(self.values)} values"
            )
        return self


def _distribution_tag(value: Any) -> Optional[str]:
    """Pick the union member for a distribution, including a bare number.

    A plain float cannot carry a `kind` field, so the tag is computed rather than read.
    Doing this with a callable discriminator instead of a plain union is what keeps a
    failure reported against a single member, rather than listing every branch tried.
    """
    if isinstance(value, numbers.Real) and not isinstance(value, bool):
        return "constant"
    if isinstance(value, dict):
        return value.get("kind")
    return getattr(value, "kind", None)


# a constant is a plain number, so that it stays one in python and in json rather than
# being wrapped in an object that has to be unwrapped again after loading
Distribution = TypeAliasType(
    "Distribution",
    Annotated[
        Union[
            Annotated[float, Tag("constant")],
            Annotated[DiscreteUniformDistribution, Tag("discrete_uniform")],
            Annotated[WhiteNoiseDistribution, Tag("white_noise")],
            Annotated[GaussianDistribution, Tag("gaussian")],
            Annotated[BakedDistribution, Tag("baked")],
        ],
        Discriminator(_distribution_tag),
    ],
)

# one distribution per axis. plain lists rather than wrapper classes, so that what you
# write is what you read back and `source.ray_origin[0] = 5.0` works
# (horizontal, vertical)
Distribution2 = TypeAliasType("Distribution2", Annotated[list[Distribution], Len(2, 2)])
# (horizontal, vertical, depth)
Distribution3 = TypeAliasType("Distribution3", Annotated[list[Distribution], Len(3, 3)])


##############################################################################
# sources
##############################################################################


class PointSource(Model):
    kind: Literal["point_source"] = "point_source"

    # general object properties
    global_transform: Transform = Transform()

    # general source properties
    num_rays: int

    # specific source properties
    ray_origin: Distribution3
    ray_angle: Distribution2
    photon_energy: Distribution
    polarization: Polarization


class MatrixSource(Model):
    kind: Literal["matrix_source"] = "matrix_source"

    # general object properties
    global_transform: Transform = Transform()

    # general source properties
    num_rays: int

    # specific source properties
    width: float
    height: float
    horizontal_divergence: float
    vertical_divergence: float
    photon_energy: Distribution
    polarization: Polarization


class CircleSource(Model):
    kind: Literal["circle_source"] = "circle_source"

    # general object properties
    global_transform: Transform = Transform()

    # general source properties
    num_rays: int

    # specific source properties
    circle_radius: float
    divergence: float
    photon_energy: Distribution
    polarization: Polarization


class SimpleUndulatorSource(Model):
    kind: Literal["simple_undulator_source"] = "simple_undulator_source"

    # general object properties
    global_transform: Transform = Transform()

    # general source properties
    num_rays: int

    # specific source properties
    undulator_sigma_type: UndulatorSigmaType
    undulator_length: float
    electron_sigma_x: float
    electron_sigma_xs: float
    electron_sigma_y: float
    electron_sigma_ys: float
    depth: float
    photon_energy: Distribution
    polarization: Polarization


class PixelSource(Model):
    kind: Literal["pixel_source"] = "pixel_source"

    # general object properties
    global_transform: Transform = Transform()

    # general source properties
    num_rays: int

    # specific source properties
    width: float
    height: float
    depth: float
    horizontal_divergence: float
    vertical_divergence: float
    photon_energy: Distribution
    polarization: Polarization


class DipoleSource(Model):
    kind: Literal["dipole_source"] = "dipole_source"

    # general object properties
    global_transform: Transform = Transform()

    # general source properties
    num_rays: int

    # specific source properties
    bending_radius: float
    electron_energy_orientation: ElectronEnergyOrientation
    width: float
    height: float
    electron_energy: float
    critical_energy: float
    photon_energy: Distribution
    vertical_electron_beam_divergence: float
    energy_spread: float
    horizontal_divergence: float


##############################################################################
# beamline
##############################################################################

Object = TypeAliasType(
    "Object",
    Annotated[
        Union[
            # elements
            Detector,
            Aperture,
            Slit,
            Foil,
            Mirror,
            Grating,
            Rzp,
            Crystal,
            # sources
            PointSource,
            MatrixSource,
            CircleSource,
            SimpleUndulatorSource,
            PixelSource,
            DipoleSource,
        ],
        Field(discriminator="kind"),
    ],
)


class Beamline(Model):
    objects: list[Object] = []


##############################################################################
# tracing
##############################################################################


class TraceParams(Model):
    seed: int = 0
    sequential: bool = False
    object_record_mask: Optional[set[int]] = None
    ray_attr_record_mask: RayAttrMask = RayAttrMask.ALL
    max_events: Optional[int] = None
    max_batch_size: Optional[int] = None


__all__ = [
    # reused from model0
    "ElectronEnergyOrientation",
    "EventType",
    "RayAttrMask",
    "ToroidType",
    "UndulatorSigmaType",
    # types
    "Model",
    "Material",
    "Vec3",
    "ORIENTATION_TOLERANCE",
    "AxisAngle",
    "Basis",
    "Orientation",
    "to_axis_angle",
    "to_basis",
    "Transform",
    "POLARIZATION_TOLERANCE",
    "LocalElectricField",
    "Stokes",
    "Polarization",
    "to_stokes",
    "to_local_electric_field",
    # element building blocks
    "RectArea",
    "EllipseArea",
    "TrapezoidArea",
    "Area",
    "DiffractiveArea",
    "FlatCurvature",
    "QuadricCurvature",
    "ToroidialCurvature",
    "CubicCurvature",
    "Curvature",
    "SlopeError",
    "CoatingLayer",
    "Coating",
    # elements
    "Detector",
    "Aperture",
    "Slit",
    "Foil",
    "Mirror",
    "Grating",
    "Rzp",
    "Crystal",
    # source building blocks
    "DiscreteUniformDistribution",
    "WhiteNoiseDistribution",
    "GaussianDistribution",
    "BakedDistribution",
    "Distribution",
    "Distribution2",
    "Distribution3",
    # sources
    "PointSource",
    "MatrixSource",
    "CircleSource",
    "SimpleUndulatorSource",
    "PixelSource",
    "DipoleSource",
    # beamline
    "Object",
    "Beamline",
    # tracing
    "TraceParams",
]

#include <nanobind/nanobind.h>
#include <nanobind/stl/array.h>
#include <nanobind/stl/complex.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/variant.h>
#include <nanobind/stl/vector.h>

#include <array>

#include "model0.h"

namespace nb = nanobind;
using namespace nb::literals;

//////////////////////////////////////////////////////////////
// glm interop
//////////////////////////////////////////////////////////////

// A 4x4 transform is exposed to python as a nested sequence using glm's own
// column-major indexing, i.e. `m[col][row]`. A translation therefore sits in
// the last row, `m[3][0..2]`.
using Mat4 = std::array<std::array<double, 4>, 4>;

namespace nanobind::detail {

template <>
struct type_caster<glm::dmat4> {
    using Caster = make_caster<Mat4>;
    NB_TYPE_CASTER(glm::dmat4, Caster::Name)

    bool from_python(handle src, uint8_t flags, cleanup_list* cleanup) noexcept {
        Caster caster;
        if (!caster.from_python(src, flags, cleanup)) return false;
        for (int i = 0; i < 4; ++i)
            for (int j = 0; j < 4; ++j) value[i][j] = caster.value[i][j];
        return true;
    }

    static handle from_cpp(const glm::dmat4& m, rv_policy policy, cleanup_list* cleanup) noexcept {
        Mat4 result;
        for (int i = 0; i < 4; ++i)
            for (int j = 0; j < 4; ++j) result[i][j] = m[i][j];
        return Caster::from_cpp(result, policy, cleanup);
    }
};

}  // namespace nanobind::detail

//////////////////////////////////////////////////////////////
// module
//////////////////////////////////////////////////////////////

NB_MODULE(_model0, m) {
    m.doc() = "C++ core of the rayx package";

    //////////////////////////////////////////////////////////
    // rays
    //////////////////////////////////////////////////////////

    nb::enum_<EventType>(m, "EventType")
        .value("UNINITIALIZED", EventType::Uninitialized)
        .value("EMITTED", EventType::Emitted)
        .value("HIT_ELEMENT", EventType::HitElement)
        .value("FATAL_ERROR", EventType::FatalError)
        .value("ABSORBED", EventType::Absorbed)
        .value("BEYOND_HORIZON", EventType::BeyondHorizon)
        .value("TOO_MANY_EVENTS", EventType::TooManyEvents);

    nb::enum_<RayAttrMask>(m, "RayAttrMask", nb::is_flag(), "Bitmask over the ray attributes")
#define X(snake, upper_snake, camel, pascal, type) .value(#upper_snake, RayAttrMask::pascal)
        RAYX_RAY_ATTRS(X)
#undef X
        .value("POSITION", RayAttrMask::Position)
        .value("DIRECTION", RayAttrMask::Direction)
        .value("ELECTRIC_FIELD", RayAttrMask::ElectricField)
        .value("EMPTY", RayAttrMask::Empty)
        .value("ALL", RayAttrMask::All);

    nb::class_<Rays>(m, "Rays")
        .def(nb::init<>())
#define X(snake, upper_snake, camel, pascal, type) .def_rw(#snake, &Rays::camel)
        RAYX_RAY_ATTRS(X)
#undef X
        ;

    //////////////////////////////////////////////////////////
    // element building blocks
    //////////////////////////////////////////////////////////

    nb::class_<RectangularArea>(m, "RectangularArea")
        .def(nb::init<>())
        .def_rw("width", &RectangularArea::width)
        .def_rw("height", &RectangularArea::height);

    nb::class_<EllipticalArea>(m, "EllipticalArea")
        .def(nb::init<>())
        .def_rw("horizontal_diameter", &EllipticalArea::horizontalDiameter)
        .def_rw("vertical_diameter", &EllipticalArea::verticalDiameter);

    nb::class_<TrapezoidalArea>(m, "TrapezoidalArea")
        .def(nb::init<>())
        .def_rw("top_width", &TrapezoidalArea::topWidth)
        .def_rw("bottom_width", &TrapezoidalArea::bottomWidth)
        .def_rw("height", &TrapezoidalArea::height);

    nb::class_<FlatCurvature>(m, "FlatCurvature")
        .def(nb::init<>());

    nb::class_<QuadricCurvature>(m, "QuadricCurvature")
        .def(nb::init<>())
        .def_rw("icurv", &QuadricCurvature::icurv)
        .def_rw("a11", &QuadricCurvature::a11)
        .def_rw("a12", &QuadricCurvature::a12)
        .def_rw("a13", &QuadricCurvature::a13)
        .def_rw("a14", &QuadricCurvature::a14)
        .def_rw("a22", &QuadricCurvature::a22)
        .def_rw("a23", &QuadricCurvature::a23)
        .def_rw("a24", &QuadricCurvature::a24)
        .def_rw("a33", &QuadricCurvature::a33)
        .def_rw("a34", &QuadricCurvature::a34)
        .def_rw("a44", &QuadricCurvature::a44);

    nb::enum_<ToroidType>(m, "ToroidType")
        .value("CONVEX", ToroidType::Convex)
        .value("CONCAVE", ToroidType::Concave);

    nb::class_<ToroidialCurvature>(m, "ToroidialCurvature")
        .def(nb::init<>())
        .def_rw("long_radius", &ToroidialCurvature::longRadius)
        .def_rw("short_radius", &ToroidialCurvature::shortRadius)
        .def_rw("toroid_type", &ToroidialCurvature::toroidType);

    nb::class_<CubicCurvature>(m, "CubicCurvature")
        .def(nb::init<>())
        .def_rw("a11", &CubicCurvature::a11)
        .def_rw("a12", &CubicCurvature::a12)
        .def_rw("a13", &CubicCurvature::a13)
        .def_rw("a14", &CubicCurvature::a14)
        .def_rw("a22", &CubicCurvature::a22)
        .def_rw("a23", &CubicCurvature::a23)
        .def_rw("a24", &CubicCurvature::a24)
        .def_rw("a33", &CubicCurvature::a33)
        .def_rw("a34", &CubicCurvature::a34)
        .def_rw("a44", &CubicCurvature::a44)
        .def_rw("b12", &CubicCurvature::b12)
        .def_rw("b13", &CubicCurvature::b13)
        .def_rw("b21", &CubicCurvature::b21)
        .def_rw("b23", &CubicCurvature::b23)
        .def_rw("b31", &CubicCurvature::b31)
        .def_rw("b32", &CubicCurvature::b32)
        .def_rw("psi", &CubicCurvature::psi);

    nb::class_<SlopeError>(m, "SlopeError")
        .def(nb::init<>())
        .def_rw("saggital_rms", &SlopeError::saggitalRms)
        .def_rw("meridional_rms", &SlopeError::meridionalRms);

    nb::class_<CoatingLayer>(m, "CoatingLayer")
        .def(nb::init<>())
        .def_rw("material", &CoatingLayer::material)
        .def_rw("thickness", &CoatingLayer::thickness)
        .def_rw("roughness", &CoatingLayer::roughness);

    nb::class_<Coating>(m, "Coating")
        .def(nb::init<>())
        .def_rw("layers", &Coating::layers);

    //////////////////////////////////////////////////////////
    // elements
    //////////////////////////////////////////////////////////

    nb::class_<Detector>(m, "Detector")
        .def(nb::init<>())
        .def_rw("global_transform", &Detector::globalTransform)
        .def_rw("area", &Detector::area)
        .def_rw("curvature", &Detector::curvature);

    nb::class_<Aperture>(m, "Aperture")
        .def(nb::init<>())
        .def_rw("global_transform", &Aperture::globalTransform)
        .def_rw("area", &Aperture::area)
        .def_rw("curvature", &Aperture::curvature)
        .def_rw("aperture_area", &Aperture::apertureArea);

    nb::class_<Slit>(m, "Slit")
        .def(nb::init<>())
        .def_rw("global_transform", &Slit::globalTransform)
        .def_rw("area", &Slit::area)
        .def_rw("slit_area", &Slit::slitArea);

    nb::class_<Foil>(m, "Foil")
        .def(nb::init<>())
        .def_rw("global_transform", &Foil::globalTransform)
        .def_rw("area", &Foil::area)
        .def_rw("curvature", &Foil::curvature)
        .def_rw("slope_error", &Foil::slopeError)
        .def_rw("substrate", &Foil::substrate)
        .def_rw("substrate_thickness", &Foil::substrateThickness)
        .def_rw("substrate_roughness", &Foil::substrateRoughness)
        .def_rw("coating", &Foil::coating);

    nb::class_<Mirror>(m, "Mirror")
        .def(nb::init<>())
        .def_rw("global_transform", &Mirror::globalTransform)
        .def_rw("area", &Mirror::area)
        .def_rw("curvature", &Mirror::curvature)
        .def_rw("slope_error", &Mirror::slopeError)
        .def_rw("substrate", &Mirror::substrate)
        .def_rw("coating", &Mirror::coating);

    nb::class_<Grating>(m, "Grating")
        .def(nb::init<>())
        .def_rw("global_transform", &Grating::globalTransform)
        .def_rw("area", &Grating::area)
        .def_rw("curvature", &Grating::curvature)
        .def_rw("slope_error", &Grating::slopeError)
        .def_rw("order_of_diffraction", &Grating::orderOfDiffraction)
        .def_rw("line_density", &Grating::lineDensity)
        .def_rw("vls", &Grating::vls);

    nb::class_<Rzp>(m, "Rzp")
        .def(nb::init<>())
        .def_rw("global_transform", &Rzp::globalTransform)
        .def_rw("area", &Rzp::area)
        .def_rw("curvature", &Rzp::curvature)
        .def_rw("slope_error", &Rzp::slopeError)
        .def_rw("image_type", &Rzp::imageType)
        .def_rw("rzp_type", &Rzp::rzpType)
        .def_rw("derivation_method", &Rzp::derivationMethod)
        .def_rw("design_order_of_diffraction", &Rzp::designOrderOfDiffraction)
        .def_rw("order_of_diffraction", &Rzp::orderOfDiffraction)
        .def_rw("additional_order", &Rzp::additionalOrder)
        .def_rw("design_wavelength", &Rzp::designWavelength)
        .def_rw("fresnel_z_offset", &Rzp::fresnelZOffset)
        .def_rw("design_sagittal_entrance_arm_length", &Rzp::designSagittalEntranceArmLength)
        .def_rw("design_sagittal_exit_arm_length", &Rzp::designSagittalExitArmLength)
        .def_rw("design_meridional_entrance_arm_length", &Rzp::designMeridionalEntranceArmLength)
        .def_rw("design_meridional_exit_arm_length", &Rzp::designMeridionalExitArmLength)
        .def_rw("design_alpha_angle", &Rzp::designAlphaAngle)
        .def_rw("design_beta_angle", &Rzp::designBetaAngle);

    nb::class_<Cystal>(m, "Cystal")
        .def(nb::init<>())
        .def_rw("global_transform", &Cystal::globalTransform)
        .def_rw("area", &Cystal::area)
        .def_rw("curvature", &Cystal::curvature)
        .def_rw("slope_error", &Cystal::slopeError)
        .def_rw("d_spacing2", &Cystal::dSpacing2)
        .def_rw("unit_cell_volume", &Cystal::unitCellVolume)
        .def_rw("offset_angle", &Cystal::offsetAngle)
        .def_rw("structure_factor_re_f0", &Cystal::structureFactorReF0)
        .def_rw("structure_factor_im_f0", &Cystal::structureFactorImF0)
        .def_rw("structure_factor_re_fh", &Cystal::structureFactorReFH)
        .def_rw("structure_factor_im_fh", &Cystal::structureFactorImFH)
        .def_rw("structure_factor_re_fhc", &Cystal::structureFactorReFHC)
        .def_rw("structure_factor_im_fhc", &Cystal::structureFactorImFHC);

    //////////////////////////////////////////////////////////
    // distributions
    //////////////////////////////////////////////////////////

    nb::class_<DiscreteUniformDistribution>(m, "DiscreteUniformDistribution")
        .def(nb::init<>())
        .def_rw("center", &DiscreteUniformDistribution::center)
        .def_rw("width", &DiscreteUniformDistribution::width)
        .def_rw("count", &DiscreteUniformDistribution::count);

    nb::class_<WhiteNoiseDistribution>(m, "WhiteNoiseDistribution")
        .def(nb::init<>())
        .def_rw("center", &WhiteNoiseDistribution::center)
        .def_rw("width", &WhiteNoiseDistribution::width);

    nb::class_<GaussianDistribution>(m, "GaussianDistribution")
        .def(nb::init<>())
        .def_rw("mean", &GaussianDistribution::mean)
        .def_rw("standard_deviation", &GaussianDistribution::standardDeviation);

    nb::class_<BakedDistribution>(m, "BakedDistribution")
        .def(nb::init<>())
        .def_rw("values", &BakedDistribution::values)
        .def_rw("weights", &BakedDistribution::weights);

    nb::class_<Distribution2>(m, "Distribution2")
        .def(nb::init<>())
        .def_rw("horizontal", &Distribution2::horizontal)
        .def_rw("vertical", &Distribution2::vertical);

    nb::class_<Distribution3>(m, "Distribution3")
        .def(nb::init<>())
        .def_rw("horizontal", &Distribution3::horizontal)
        .def_rw("vertical", &Distribution3::vertical)
        .def_rw("depth", &Distribution3::depth);

    //////////////////////////////////////////////////////////
    // sources
    //////////////////////////////////////////////////////////

    nb::class_<PointSource>(m, "PointSource")
        .def(nb::init<>())
        .def_rw("global_transform", &PointSource::globalTransform)
        .def_rw("num_rays", &PointSource::numRays)
        .def_rw("ray_origin", &PointSource::rayOrigin)
        .def_rw("ray_angle", &PointSource::rayAngle)
        .def_rw("photon_energy", &PointSource::photonEnergy)
        .def_rw("polarization", &PointSource::polarization);

    nb::class_<MatrixSource>(m, "MatrixSource")
        .def(nb::init<>())
        .def_rw("global_transform", &MatrixSource::globalTransform)
        .def_rw("num_rays", &MatrixSource::numRays)
        .def_rw("width", &MatrixSource::width)
        .def_rw("height", &MatrixSource::height)
        .def_rw("horizontal_divergence", &MatrixSource::horizontalDivergence)
        .def_rw("vertical_divergence", &MatrixSource::verticalDivergence)
        .def_rw("photon_energy", &MatrixSource::photonEnergy)
        .def_rw("polarization", &MatrixSource::polarization);

    nb::class_<CircleSource>(m, "CircleSource")
        .def(nb::init<>())
        .def_rw("global_transform", &CircleSource::globalTransform)
        .def_rw("num_rays", &CircleSource::numRays)
        .def_rw("circle_radius", &CircleSource::circleRadius)
        .def_rw("divergence", &CircleSource::divergence)
        .def_rw("photon_energy", &CircleSource::photonEnergy)
        .def_rw("polarization", &CircleSource::polarization);

    nb::enum_<UndulatorSigmaType>(m, "UndulatorSigmaType")
        .value("STANDARD", UndulatorSigmaType::Standard)
        .value("ACCURATE", UndulatorSigmaType::Accurate);

    nb::class_<SimpleUndulatorSource>(m, "SimpleUndulatorSource")
        .def(nb::init<>())
        .def_rw("global_transform", &SimpleUndulatorSource::globalTransform)
        .def_rw("num_rays", &SimpleUndulatorSource::numRays)
        .def_rw("undulator_sigma_type", &SimpleUndulatorSource::undulatorSigmaType)
        .def_rw("undulator_length", &SimpleUndulatorSource::undulatorLength)
        .def_rw("electron_sigma_x", &SimpleUndulatorSource::electronSigmaX)
        .def_rw("electron_sigma_xs", &SimpleUndulatorSource::electronSigmaXs)
        .def_rw("electron_sigma_y", &SimpleUndulatorSource::electronSigmaY)
        .def_rw("electron_sigma_ys", &SimpleUndulatorSource::electronSigmaYs)
        .def_rw("depth", &SimpleUndulatorSource::depth)
        .def_rw("photon_energy", &SimpleUndulatorSource::photonEnergy)
        .def_rw("polarization", &SimpleUndulatorSource::polarization);

    nb::class_<PixelSource>(m, "PixelSource")
        .def(nb::init<>())
        .def_rw("global_transform", &PixelSource::globalTransform)
        .def_rw("num_rays", &PixelSource::numRays)
        .def_rw("width", &PixelSource::width)
        .def_rw("height", &PixelSource::height)
        .def_rw("depth", &PixelSource::depth)
        .def_rw("horizontal_divergence", &PixelSource::horizontalDivergence)
        .def_rw("vertical_divergence", &PixelSource::verticalDivergence)
        .def_rw("photon_energy", &PixelSource::photonEnergy)
        .def_rw("polarization", &PixelSource::polarization);

    nb::enum_<ElectronEnergyOrientation>(m, "ElectronEnergyOrientation")
        .value("CLOCKWISE", ElectronEnergyOrientation::Clockwise)
        .value("COUNTERCLOCKWISE", ElectronEnergyOrientation::Counterclockwise);

    nb::class_<DipoleSource>(m, "DipoleSource")
        .def(nb::init<>())
        .def_rw("global_transform", &DipoleSource::globalTransform)
        .def_rw("num_rays", &DipoleSource::numRays)
        .def_rw("bending_radius", &DipoleSource::bendingRadius)
        .def_rw("electron_energy_orientation", &DipoleSource::electronEnergyOrientation)
        .def_rw("width", &DipoleSource::width)
        .def_rw("height", &DipoleSource::height)
        .def_rw("electron_energy", &DipoleSource::electronEnergy)
        .def_rw("critical_energy", &DipoleSource::criticalEnergy)
        .def_rw("photon_energy", &DipoleSource::photonEnergy)
        .def_rw("vertical_electron_beam_divergence", &DipoleSource::verticalElectronBeamDivergence)
        .def_rw("energy_spread", &DipoleSource::energySpread)
        .def_rw("horizontal_divergence", &DipoleSource::horizontalDivergence);

    //////////////////////////////////////////////////////////
    // beamline and tracing
    //////////////////////////////////////////////////////////

    nb::class_<Beamline>(m, "Beamline")
        .def(nb::init<>())
        .def_rw("objects", &Beamline::objects);

    nb::class_<TraceParams>(m, "TraceParams")
        .def(nb::init<>())
        .def_rw("seed", &TraceParams::seed)
        .def_rw("sequential", &TraceParams::sequential)
        .def_rw("object_record_mask", &TraceParams::objectRecordMask)
        .def_rw("ray_attr_record_mask", &TraceParams::rayAttrRecordMask)
        .def_rw("max_events", &TraceParams::maxEvents)
        .def_rw("max_batch_size", &TraceParams::maxBatchSize);

    m.def("trace", &trace, "beamline"_a, "params"_a, "Trace a beamline and return the recorded rays");
}

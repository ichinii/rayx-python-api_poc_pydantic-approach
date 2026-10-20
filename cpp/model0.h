#pragma once

#include <glm/glm.hpp>
#include <string>
#include <array>
#include <vector>
#include <variant>
#include <optional>
#include <complex>
#include <cstdint>
#include <string_view>

// units and assumptions:
// - angle: rad
// - energy: eV
// - distance: mm
// - element backface hit: // TODO: should we ignore or absorb the ray?

//////////////////////////////////////////////////////////////
// types
//////////////////////////////////////////////////////////////

using RandCounter = uint64_t;
// TODO: we could use the tracer types instead. e.g. glm::tvec3<std::complex<double>>
using LocalElectricField = std::array<std::complex<double>, 2>;
using ElectricField = std::array<std::complex<double>, 3>;

//////////////////////////////////////////////////////////////
// rays
//////////////////////////////////////////////////////////////

enum class EventType {
    Uninitialized = 0,
    Emitted       = 1,
    HitElement    = 2,
    FatalError    = 3,
    Absorbed      = 4,
    BeyondHorizon = 5,
    TooManyEvents = 6,
};

//    snake                upper_snake          camel              pascal             type
#define RAYX_RAY_ATTRS(X) \
    X(path_id,             PATH_ID,             pathId,            PathId,            uint64_t) \
    X(path_event_id,       PATH_EVENT_ID,       pathEventId,       PathEventId,       uint32_t) \
    X(position_x,          POSITION_X,          positionX,         PositionX,         double) \
    X(position_y,          POSITION_Y,          positionY,         PositionY,         double) \
    X(position_z,          POSITION_Z,          positionZ,         PositionZ,         double) \
    X(direction_x,         DIRECTION_X,         directionX,        DirectionX,        double) \
    X(direction_y,         DIRECTION_Y,         directionY,        DirectionY,        double) \
    X(direction_z,         DIRECTION_Z,         directionZ,        DirectionZ,        double) \
    X(electric_field_x,    ELECTRIC_FIELD_X,    electricFieldX,    ElectricFieldX,    std::complex<double>) \
    X(electric_field_y,    ELECTRIC_FIELD_Y,    electricFieldY,    ElectricFieldY,    std::complex<double>) \
    X(electric_field_z,    ELECTRIC_FIELD_Z,    electricFieldZ,    ElectricFieldZ,    std::complex<double>) \
    X(optical_path_length, OPTICAL_PATH_LENGTH, opticalPathLength, OpticalPathLength, double) \
    X(energy,              ENERGY,              energy,            Energy,            double) \
    X(order,               ORDER,               order,             Order,             int32_t) \
    X(object_id,           OBJECT_ID,           objectId,          ObjectId,          int32_t) \
    X(source_id,           SOURCE_ID,           sourceId,          SourceId,          int32_t) \
    X(event_type,          EVENT_TYPE,          eventType,         EventType,         EventType) \
    X(rand_counter,        RAND_COUNTER,        randCounter,       RandCounter,       RandCounter)

enum class RayAttr {
#define X(snake, upper_snake, camel, pascal, type) pascal,
    RAYX_RAY_ATTRS(X)
#undef X
    Count,
};

// we use upper_snake case here, because it is coherent with python. in case there are string to mask conversions, the user will encoutner coherent names. the camel case and pascal case are only used in the C++ code, where they are more idiomatic.
inline constexpr std::array<std::string_view, static_cast<size_t>(RayAttr::Count)> rayAttrNames = {
#define X(snake, upper_snake, camel, pascal, type) #upper_snake,
    RAYX_RAY_ATTRS(X)
#undef X
};

enum class RayAttrMask : uint32_t {
#define X(snake, upper_snake, camel, pascal, type) pascal = 1 << static_cast<uint32_t>(RayAttr::pascal),
    RAYX_RAY_ATTRS(X)
#undef X
    Position      = PositionX | PositionY | PositionZ,
    Direction     = DirectionX | DirectionY | DirectionZ,
    ElectricField = ElectricFieldX | ElectricFieldY | ElectricFieldZ,
    Empty = 0,
    All   = (1u << static_cast<uint32_t>(RayAttr::Count)) - 1,
};

inline constexpr RayAttrMask operator|(const RayAttrMask lhs, const RayAttrMask rhs) {
    return static_cast<RayAttrMask>(static_cast<std::underlying_type_t<RayAttrMask>>(lhs) | static_cast<std::underlying_type_t<RayAttrMask>>(rhs));
}
inline constexpr RayAttrMask operator&(const RayAttrMask lhs, const RayAttrMask rhs) {
    return static_cast<RayAttrMask>(static_cast<std::underlying_type_t<RayAttrMask>>(lhs) & static_cast<std::underlying_type_t<RayAttrMask>>(rhs));
}
inline constexpr RayAttrMask operator^(const RayAttrMask lhs, const RayAttrMask rhs) {
    return static_cast<RayAttrMask>(static_cast<std::underlying_type_t<RayAttrMask>>(lhs) ^ static_cast<std::underlying_type_t<RayAttrMask>>(rhs));
}
inline constexpr RayAttrMask operator~(const RayAttrMask lhs) {
    return static_cast<RayAttrMask>(~static_cast<std::underlying_type_t<RayAttrMask>>(lhs)) & RayAttrMask::All;
}
inline constexpr bool operator!(const RayAttrMask lhs) { return lhs == RayAttrMask::Empty; }
inline constexpr RayAttrMask& operator|=(RayAttrMask& lhs, const RayAttrMask rhs) { return lhs = lhs | rhs; }
inline constexpr RayAttrMask& operator&=(RayAttrMask& lhs, const RayAttrMask rhs) { return lhs = lhs & rhs; }
inline constexpr RayAttrMask& operator^=(RayAttrMask& lhs, const RayAttrMask rhs) { return lhs = lhs ^ rhs; }

inline constexpr RayAttrMask toMask(const RayAttr attr) {
    return static_cast<RayAttrMask>(1u << static_cast<std::underlying_type_t<RayAttrMask>>(attr));
}

struct Rays {
#define X(snake, upper_snake, camel, pascal, type) std::vector<type> camel;
    RAYX_RAY_ATTRS(X)
#undef X
};

//////////////////////////////////////////////////////////////
// elements
//////////////////////////////////////////////////////////////

struct RectangularArea {
    double width;
    double height;
};

struct EllipticalArea {
    double horizontalDiameter;
    double verticalDiameter;
};

struct TrapezoidalArea {
    double topWidth;
    double bottomWidth;
    double height;
};

using Area            = std::variant<RectangularArea, EllipticalArea, TrapezoidalArea>;
using DiffractiveArea = std::variant<RectangularArea, EllipticalArea>;

struct FlatCurvature {};

struct QuadricCurvature {
    int icurv;
    double a11;
    double a12;
    double a13;
    double a14;
    double a22;
    double a23;
    double a24;
    double a33;
    double a34;
    double a44;
};

enum class ToroidType {
    Convex,
    Concave,
};

struct ToroidialCurvature {
    double longRadius;
    double shortRadius;
    ToroidType toroidType;
};

struct CubicCurvature {
    double a11;
    double a12;
    double a13;
    double a14;
    double a22;
    double a23;
    double a24;
    double a33;
    double a34;
    double a44;

    double b12;
    double b13;
    double b21;
    double b23;
    double b31;
    double b32;

    double psi;
};

using Curvature = std::variant<FlatCurvature, QuadricCurvature, ToroidialCurvature, CubicCurvature>;

struct SlopeError {
    double saggitalRms;
    double meridionalRms;
};

using Material = std::string;

struct CoatingLayer {
    Material material;
    double thickness;
    double roughness;
};

struct Coating {
    std::vector<CoatingLayer> layers;
};

struct Detector {
    // general object properties
    glm::dmat4 globalTransform;

    // general element properties
    RectangularArea area;
    Curvature curvature;
};

struct Aperture {
    // general object properties
    glm::dmat4 globalTransform;

    // general element properties
    RectangularArea area;
    Curvature curvature;

    // specific element properties
    Area apertureArea;
};

struct Slit {
    // general object properties
    glm::dmat4 globalTransform;

    // general element properties
    RectangularArea area;

    // specific element properties
    DiffractiveArea slitArea;
};

struct Foil {
    // general object properties
    glm::dmat4 globalTransform;

    // general element properties
    RectangularArea area;
    Curvature curvature;
    SlopeError slopeError; // TODO: does it make sense? TODO: should we apply slopeerror on both entry and exit?

    // specific element properties
    Material substrate;
    double substrateThickness;
    double substrateRoughness;
    Coating coating;
};

struct Mirror {
    // general object properties
    glm::dmat4 globalTransform;

    // general element properties
    RectangularArea area;
    Curvature curvature;
    SlopeError slopeError;

    // specific element properties
    Material substrate;
    Coating coating;
};

struct Grating {
    // general object properties
    glm::dmat4 globalTransform;

    // general element properties
    RectangularArea area;
    Curvature curvature;
    SlopeError slopeError; // TODO: does it make sense?

    // specific element properties
    int orderOfDiffraction;
    double lineDensity;
    std::array<double, 6> vls;
};

struct Rzp {
    // general object properties
    glm::dmat4 globalTransform;

    // general element properties
    RectangularArea area;
    Curvature curvature;
    SlopeError slopeError; // TODO: does it make sense?

    // specific element properties
    int imageType;
    int rzpType;
    int derivationMethod;
    int designOrderOfDiffraction;
    int orderOfDiffraction;
    int additionalOrder;
    double designWavelength;
    double fresnelZOffset;
    double designSagittalEntranceArmLength;
    double designSagittalExitArmLength;
    double designMeridionalEntranceArmLength;
    double designMeridionalExitArmLength;
    double designAlphaAngle;
    double designBetaAngle;
};

struct Cystal {
    // general object properties
    glm::dmat4 globalTransform;

    // general element properties
    RectangularArea area;
    Curvature curvature;
    SlopeError slopeError; // TODO: does it make sense?

    // specific element properties
    double dSpacing2;
    double unitCellVolume;
    double offsetAngle;
    double structureFactorReF0;
    double structureFactorImF0;
    double structureFactorReFH;
    double structureFactorImFH;
    double structureFactorReFHC;
    double structureFactorImFHC;
};

//////////////////////////////////////////////////////////////
// sources
//////////////////////////////////////////////////////////////

struct DiscreteUniformDistribution {
    double center;
    double width;
    int count;
};

struct WhiteNoiseDistribution {
    double center;
    double width;
};

struct GaussianDistribution {
    double mean;
    double standardDeviation;
};

struct BakedDistribution {
    std::vector<double> values;

    // TODO: should we make a separate class WeightedBakedDistribution containing a single vector, thus eliminating invariant of same array size?
    std::optional<std::vector<double>> weights; // has to have the same size as values if provided

    // TODO: do we already have this implemented in the core? if not, remove it
    // bool smooth = false; // linear interpolation between values if true, otherwise nearest neighbor
};

using Distribution = std::variant<double, DiscreteUniformDistribution, WhiteNoiseDistribution, GaussianDistribution, BakedDistribution>;

struct Distribution2 {
    Distribution horizontal;
    Distribution vertical;
};

struct Distribution3 {
    Distribution horizontal;
    Distribution vertical;
    Distribution depth;
};

struct PointSource {
    // general object properties
    glm::dmat4 globalTransform;

    // general source properties
    int numRays;

    // specific source properties
    Distribution3 rayOrigin;
    Distribution2 rayAngle;
    Distribution photonEnergy;
    ElectricField polarization;
};

struct MatrixSource {
    // general object properties
    glm::dmat4 globalTransform;

    // general source properties
    int numRays;

    // specific source properties
    double width;
    double height;
    double horizontalDivergence;
    double verticalDivergence;
    Distribution photonEnergy;
    ElectricField polarization;
};

struct CircleSource {
    // general object properties
    glm::dmat4 globalTransform;

    // general source properties
    int numRays;

    // specific source properties
    double circleRadius;
    double divergence;
    Distribution photonEnergy;
    ElectricField polarization;
};

enum class UndulatorSigmaType { Standard, Accurate };

struct SimpleUndulatorSource {
    // general object properties
    glm::dmat4 globalTransform;

    // general source properties
    int numRays;

    // specific source properties
    UndulatorSigmaType undulatorSigmaType;
    double undulatorLength;
    double electronSigmaX;
    double electronSigmaXs;
    double electronSigmaY;
    double electronSigmaYs;
    double depth;
    Distribution photonEnergy;
    ElectricField polarization;
};

struct PixelSource {
    // general object properties
    glm::dmat4 globalTransform;

    // general source properties
    int numRays;

    // specific source properties
    double width;
    double height;
    double depth;
    double horizontalDivergence;
    double verticalDivergence;
    Distribution photonEnergy;
    ElectricField polarization;
};

enum class ElectronEnergyOrientation { Clockwise, Counterclockwise };

struct DipoleSource {
    // general object properties
    glm::dmat4 globalTransform;

    // general source properties
    int numRays;

    // specific source properties
    double bendingRadius;
    ElectronEnergyOrientation electronEnergyOrientation;
    double width;
    double height;
    double electronEnergy;
    double criticalEnergy;
    Distribution photonEnergy;
    double verticalElectronBeamDivergence;
    double energySpread;
    double horizontalDivergence;
};

// TODO: maybe we dont want to support this, yet
// struct InputSource {
//     // general object properties
//     glm::dmat4 globalTransform;
//
//     // specific source properties
//     Rays rays;
//     std::optional<Distribution3> rayOrigin;
//     std::optional<Distribution3> rayAangle;
//     std::optional<Distribution> photonEnergy;
//     std::optional<ElectricField> polarization;
// };

//////////////////////////////////////////////////////////////
// beamline
//////////////////////////////////////////////////////////////


using Object = std::variant<
    // elements
    Detector, Aperture, Slit, Foil, Mirror, Grating, Rzp, Cystal,
    // sources
    PointSource, MatrixSource, CircleSource, SimpleUndulatorSource, PixelSource, DipoleSource
>;

struct Beamline {
    std::vector<Object> objects;
};

//////////////////////////////////////////////////////////////
// tacing
//////////////////////////////////////////////////////////////

struct TraceParams {
    RandCounter seed;
    bool sequential;
    std::vector<bool> objectRecordMask;
    RayAttrMask rayAttrRecordMask;
    std::optional<int> maxEvents;
    std::optional<int> maxBatchSize;
};

inline Rays trace(const Beamline& beamline, const TraceParams& params) {
    return Rays{}; // TODO: here is where we connect the internals
}

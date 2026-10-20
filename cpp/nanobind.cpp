#include <nanobind/nanobind.h>
#include <nanobind/stl/array.h>
#include <nanobind/stl/string.h>

#include <array>

#include "model0.h"

namespace nb = nanobind;

using Vec3 = std::array<double, 3>;
using Mat4 = std::array<std::array<double, 4>, 4>;

static Vec3 to_tuple(const glm::dvec3& v) { return {v.x, v.y, v.z}; }
static glm::dvec3 from_tuple(const Vec3& v) { return {v[0], v[1], v[2]}; }

static Mat4 to_tuple(const glm::dmat4& m) {
    Mat4 result;
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j)
            result[i][j] = m[i][j];
    return result;
}

static glm::dmat4 from_tuple(const Mat4& m) {
    glm::dmat4 result;
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j)
            result[i][j] = m[i][j];
    return result;
}

NB_MODULE(model0, m) {
    m.doc() = "C++ core of the model0 package";

    nb::class_<RectangularArea>(m, "RectangularArea")
        .def(nb::init<>())
        .def_rw("width", &RectangularArea::width)
        .def_rw("height", &RectangularArea::height);
}

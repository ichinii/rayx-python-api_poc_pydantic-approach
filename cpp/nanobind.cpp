#include <nanobind/nanobind.h>
#include <nanobind/stl/array.h>
#include <nanobind/stl/string.h>

#include <array>

#include "model.h"

namespace nb = nanobind;

using Vec3 = std::array<float, 3>;

static Vec3 to_tuple(const glm::vec3& v) { return {v.x, v.y, v.z}; }
static glm::vec3 from_tuple(const Vec3& v) { return {v[0], v[1], v[2]}; }

NB_MODULE(_core, m) {
    m.doc() = "C++ core of the model0 package";

    nb::class_<Model>(m, "Model")
        .def(nb::init<>())
        .def_rw("name", &Model::name)
        .def_prop_rw("position",
                     [](const Model& s) { return to_tuple(s.position); },
                     [](Model& s, const Vec3& v) { s.position = from_tuple(v); })
        .def_prop_rw("velocity",
                     [](const Model& s) { return to_tuple(s.velocity); },
                     [](Model& s, const Vec3& v) { s.velocity = from_tuple(v); })
        .def("step", &Model::step, nb::arg("dt"))
        .def("speed", &Model::speed);
}

#pragma once

#include <glm/glm.hpp>
#include <string>

struct Model {
    std::string name;
    glm::vec3 position{0.0f, 0.0f, 0.0f};
    glm::vec3 velocity{0.0f, 0.0f, 0.0f};

    void step(float dt) { position += velocity * dt; }

    float speed() const { return glm::length(velocity); }
};

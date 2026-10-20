cmake_minimum_required(VERSION 3.26)
project(model0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Python 3.10 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(glm REQUIRED)

# Locate nanobind's CMake config through the Python package.
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_ROOT)
find_package(nanobind CONFIG REQUIRED)

nanobind_add_module(model0 cpp/nanobind.cpp)
target_link_libraries(model0 PRIVATE glm::glm)

# The shared object lands inside the python package.
install(TARGETS model0 LIBRARY DESTINATION model0)

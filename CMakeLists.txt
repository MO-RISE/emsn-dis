cmake_minimum_required(VERSION 3.0)

project(emsndis_cpp)

add_subdirectory(pybind11)

add_library(emsndis STATIC src/emsndis.cpp)
target_link_libraries(emsndis PUBLIC pybind11::embed)
target_compile_options(emsndis PRIVATE -fvisibility=hidden)

add_executable(main src/main.cpp)
target_compile_options(main PRIVATE -fvisibility=hidden)
target_link_libraries(main emsndis)


cmake_minimum_required(VERSION 3.16 FATAL_ERROR)
project(BNCT_Simulation)

# 寻找Geant4库 (必须包含UI和VIS界面模块)
find_package(Geant4 REQUIRED ui_all vis_all)

include(${Geant4_USE_FILE})
include_directories(${PROJECT_SOURCE_DIR}/include)

file(GLOB SOURCES src/*.cc)
file(GLOB HEADERS include/*.hh)

add_executable(BNCT_Simulation main.cc ${SOURCES} ${HEADERS})
target_link_libraries(BNCT_Simulation ${Geant4_LIBRARIES})

set(MACRO_SCRIPTS
  run.mac
  vis.mac
  run_gamma.mac
  run_proton.mac
)

foreach(_script ${MACRO_SCRIPTS})
  configure_file(
    ${PROJECT_SOURCE_DIR}/${_script}
    ${PROJECT_BINARY_DIR}/${_script}
    COPYONLY
  )
endforeach()

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
G4_DATA="/Users/liao./miniconda3/envs/g4/share/Geant4/data"

export G4ENSDFSTATEDATA="${G4_DATA}/ENSDFSTATE3.0"
export G4LEDATA="${G4_DATA}/EMLOW8.6.1"

cmake -S "${ROOT_DIR}" -B "${BUILD_DIR}" -DCMAKE_PREFIX_PATH=/Users/liao./miniconda3/envs/g4
cmake --build "${BUILD_DIR}"

(
  cd "${BUILD_DIR}"
  ./BNCT_Simulation run_gamma.mac
  ./BNCT_Simulation run_proton.mac
)

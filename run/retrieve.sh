#!/bin/bash
# Stop on errors
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [ -z "${HOME:-}" ]; then
  HOME="$(python3 - <<'PY'
from pathlib import Path
print(Path.home())
PY
)"
fi

CONDA_SH=""
if [ -n "${CONDA_EXE:-}" ]; then
  CONDA_BASE="$(cd "$(dirname "${CONDA_EXE}")/.." && pwd)"
  if [ -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]; then
    CONDA_SH="${CONDA_BASE}/etc/profile.d/conda.sh"
  fi
fi

if [ -z "${CONDA_SH}" ]; then
  for root in "$HOME/miniforge3" "$HOME/mambaforge" "$HOME/miniconda3" "$HOME/anaconda3"; do
    if [ -f "${root}/etc/profile.d/conda.sh" ]; then
      CONDA_SH="${root}/etc/profile.d/conda.sh"
      break
    fi
  done
fi

if [ -z "${CONDA_SH}" ] || [ ! -f "${CONDA_SH}" ]; then
  echo "Could not locate conda.sh" >&2
  exit 1
fi

source "${CONDA_SH}"

# Deactivate any existing environment
conda deactivate || true

# Activate target environment
conda activate idesign

save_dir=$1
echo $save_dir

if [ -z "${save_dir}" ]; then
  echo "Usage: bash run/retrieve.sh /abs/path/to/save_dir" >&2
  exit 1
fi

if [ ! -d "${save_dir}" ]; then
  echo "save_dir does not exist: ${save_dir}" >&2
  echo "This script expects a SceneWeaver output directory that already contains objav_cnts.json." >&2
  exit 1
fi

if [ ! -f "${save_dir}/objav_cnts.json" ]; then
  echo "Missing ${save_dir}/objav_cnts.json" >&2
  echo "Run the main SceneWeaver pipeline first, or create objav_cnts.json manually for a standalone retrieval test." >&2
  exit 1
fi

python infinigen/assets/objaverse_assets/retrieve_idesign.py ${save_dir}

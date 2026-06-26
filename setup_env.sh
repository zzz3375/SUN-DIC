#!/bin/bash
# ============================================================================
# SUN-DIC 环境自动安装脚本
#
# 用法:
#   git-bash:  bash setup_env.sh
#   Linux:     bash setup_env.sh
#
# 如果 conda 不在 PATH 中，请先设置 CONDA_PATH 变量:
#   CONDA_PATH=~/anaconda3 bash setup_env.sh
# ============================================================================
set -e

ENV_NAME="${ENV_NAME:-sundic}"
PYTHON_VER="${PYTHON_VER:-3.11}"

# --- detect conda -------------------------------------------------
if [ -n "$CONDA_PATH" ]; then
    CONDA_EXE="$CONDA_PATH/Scripts/conda.exe"
elif command -v conda &>/dev/null; then
    CONDA_EXE="conda"
else
    # common Windows install paths
    for p in "$HOME/anaconda3" "$HOME/miniconda3" "/c/Users/$USER/anaconda3" "/c/ProgramData/anaconda3"; do
        if [ -f "$p/Scripts/conda.exe" ]; then
            CONDA_EXE="$p/Scripts/conda.exe"
            break
        fi
    done
fi

if [ -z "$CONDA_EXE" ]; then
    echo "ERROR: conda not found. Set CONDA_PATH or install Anaconda/Miniconda first."
    exit 1
fi
echo "Using conda: $CONDA_EXE"

# --- create environment -------------------------------------------
echo ""
echo "=== Step 1/4: Creating conda environment '$ENV_NAME' (Python $PYTHON_VER) ==="
"$CONDA_EXE" create -n "$ENV_NAME" python="$PYTHON_VER" -y

# get python path inside new env
ENV_PYTHON=$("$CONDA_EXE" run -n "$ENV_NAME" python -c "import sys; print(sys.executable)")
echo "Python: $ENV_PYTHON"

# --- install dependencies -----------------------------------------
echo ""
echo "=== Step 2/4: Installing SUN-DIC dependencies ==="
"$ENV_PYTHON" -m pip install \
    numpy \
    opencv-python-headless \
    scikit-image \
    scipy \
    matplotlib \
    pandas \
    natsort \
    numba \
    msgpack-numpy \
    ray

# --- install PyQt6 (lock to 6.5.3 for MSVC 2019 compatibility) ----
echo ""
echo "=== Step 3/4: Installing PyQt6 6.5.3 ==="
"$ENV_PYTHON" -m pip install "PyQt6==6.5.3" "PyQt6-Qt6==6.5.3"

# test
"$ENV_PYTHON" -c "from PyQt6.QtCore import Qt; print('PyQt6 OK')"

# --- install SUN-DIC (editable mode) -------------------------------
echo ""
echo "=== Step 4/4: Installing SUN-DIC ==="
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"$ENV_PYTHON" -m pip install -e "$SCRIPT_DIR"

# re-lock Qt6 because pip install -e may upgrade it
"$ENV_PYTHON" -m pip install "PyQt6-Qt6==6.5.3" --quiet

# --- verify -------------------------------------------------------
echo ""
echo "=== Verification ==="
"$ENV_PYTHON" -c "
from PyQt6.QtWidgets import QApplication
from sundic.gui.mainWindow import main
from sundic import sundic
from sundic import post_process
print('SUN-DIC installation verified!')
"

echo ""
echo "=============================================="
echo "  Environment '$ENV_NAME' is ready."
echo ""
echo "  Activate:   conda activate $ENV_NAME"
echo "  GUI:        sundic"
echo "=============================================="

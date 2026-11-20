#!/usr/bin/env bash
# Build the isosurface example with the Cerebras SDK compiler.
#
# Usage: build.sh [PAD_X PAD_Y]     (default 0 0; extra PEs around the used rectangle)
# Environment: CSLC  path to the SDK's `cslc` wrapper (default: `cslc` from PATH)
#              ARCH  target architecture passed to `cslc --arch` (default: the compiler's default, wse2)
#              OUT   output directory (default: build/iso[_padXxY][_ARCH])
set -euo pipefail

CSLC="${CSLC:-cslc}"
PAD_X="${1:-0}"
PAD_Y="${2:-0}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NAME="iso"; if [[ "$PAD_X" != 0 || "$PAD_Y" != 0 ]]; then NAME="iso_pad${PAD_X}x${PAD_Y}"; fi
ARCH="${ARCH:-}"
ARCH_FLAG=(); if [[ -n "$ARCH" ]]; then ARCH_FLAG=(--arch="$ARCH"); NAME="${NAME}_${ARCH}"; fi
OUT="${OUT:-$ROOT/build/$NAME}"

SIZE=3          # patches per side
NUM_TASKS=15
PATCH_W=2
PATCH_H=2
KERNEL_W=$((SIZE * PATCH_W + 1 + PAD_X))
KERNEL_H=$((SIZE * PATCH_H + 1 + PAD_Y))
FABRIC_W=$((KERNEL_W + 7))
FABRIC_H=$((KERNEL_H + 2))
H2D_COLOR=15    # color used for streaming the shared local state host -> device

export CSL_IMPORT_PATH="$ROOT:$ROOT/examples"
mkdir -p "$(dirname "$OUT")"
cd "$ROOT"
"$CSLC" examples/isosurface/layout.csl -o "$OUT" \
  "${ARCH_FLAG[@]}" --memcpy --channels 1 \
  --fabric-dims="$FABRIC_W,$FABRIC_H" --fabric-offsets=4,1 \
  --import-path="$ROOT" --import-path="$ROOT/examples" \
  --params="kernel_width:$KERNEL_W,kernel_height:$KERNEL_H,size:$SIZE,num_tasks:$NUM_TASKS,patch_width:$PATCH_W,patch_height:$PATCH_H,MEMCPYH2D_DATA_1_ID:$H2D_COLOR"

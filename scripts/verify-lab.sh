#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
mkdir -p results

for tool in git cmake g++ make python3; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "Required tool not found: $tool" >&2
    exit 127
  }
done

PICT_SOURCE="$(mktemp -d)"
cleanup() { rm -rf "$PICT_SOURCE"; }
trap cleanup EXIT

echo "Cloning Microsoft PICT source outside the lab repository..."
git clone --depth 1 https://github.com/microsoft/pict.git "$PICT_SOURCE/pict"
PICT_COMMIT="$(git -C "$PICT_SOURCE/pict" log -1 --format='pict commit %h %ad' --date=short)"

echo "Building PICT from source..."
cmake -S "$PICT_SOURCE/pict" -B "$PICT_SOURCE/pict/build" -DCMAKE_BUILD_TYPE=Release \
  > results/pict-cmake-configure.txt 2>&1
cmake --build "$PICT_SOURCE/pict/build" --config Release -j2 \
  > results/pict-cmake-build.txt 2>&1

PICT_BIN="$PICT_SOURCE/pict/build/cli/pict"
if [[ ! -x "$PICT_BIN" ]]; then
  echo "PICT executable not found at expected path: $PICT_BIN" >&2
  find "$PICT_SOURCE/pict/build" -type f -name pict -print >&2
  exit 1
fi

"$PICT_BIN" > results/pict-usage-full.txt 2>&1 || true
{
  echo "$PICT_COMMIT"
  echo "Build: cmake -S pict -B pict/build -DCMAKE_BUILD_TYPE=Release"
  echo "Build: cmake --build pict/build --config Release -j2"
  echo "PICT usage (first lines):"
  sed -n '1,4p' results/pict-usage-full.txt
} > results/pict-build.txt

# Deterministic PICT calls: intentionally no /r random seed option.
"$PICT_BIN" browser.model > results/browser-2way.txt
"$PICT_BIN" browser.model /o:3 > results/browser-3way.txt
"$PICT_BIN" transfer-nc.model > results/transfer-nc.txt
"$PICT_BIN" transfer.model > results/transfer.txt
"$PICT_BIN" transfer-neg.model > results/transfer-neg.txt

python3 scripts/validate-results.py

echo "PICT build and all five deterministic model runs completed."

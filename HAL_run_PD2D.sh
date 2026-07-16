#!/bin/bash
# Run the 2D passenger-driver tumor evolution simulation
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "Compiling..."
javac -cp "Framework/lib/lwjgl.jar:Framework/lib/lwjgl_util.jar" $(find . -name "*.java")
echo "Done."

echo "Running simulation..."
mkdir -p data-output

java \
  -cp ".:Framework/lib/lwjgl.jar:Framework/lib/lwjgl_util.jar" \
  -Djava.library.path="Framework/lib" \
  Model.PD2D
echo "Simulation finished."
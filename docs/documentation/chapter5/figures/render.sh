#!/usr/bin/env bash
# Render Chapter Five / Section 3.3 PlantUML sources to PNG (200 dpi).
# Usage: figures/render.sh [file.puml ...]   (default: all sources)
set -euo pipefail
cd "$(dirname "$0")/src"
JAR="${PLANTUML_JAR:?set PLANTUML_JAR to plantuml.jar (PlantUML 1.2026.x)}"
files=("$@"); [ ${#files[@]} -eq 0 ] && files=(fig*.puml)
java -Djava.awt.headless=true -jar "$JAR" -tpng -o ../png "${files[@]}"
python3 - "${files[@]}" <<'PY'
import sys
from PIL import Image
for f in sys.argv[1:]:
    p = '../png/' + f.replace('.puml', '.png')
    w, h = Image.open(p).size
    scale = min(1216 / w, 1700 / h, 1.0)
    print(f"{p:40s} {w:5d}x{h:<5d} text at A4 = {12*scale:4.1f} pt")
PY

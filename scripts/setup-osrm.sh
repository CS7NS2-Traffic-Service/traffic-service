#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../osrm-data"
PBF_FILE="ireland-and-northern-ireland-latest.osm.pbf"
OSRM_IMAGE="osrm/osrm-backend"

mkdir -p "$DATA_DIR"

# Download Ireland OSM data from Geofabrik (skip if already exists)
if [ ! -f "$DATA_DIR/$PBF_FILE" ]; then
  echo "Downloading $PBF_FILE from Geofabrik..."
  curl -L -o "$DATA_DIR/$PBF_FILE" \
    "https://download.geofabrik.de/europe/ireland-and-northern-ireland-latest.osm.pbf"
else
  echo "$PBF_FILE already exists, skipping download."
fi

echo "Running osrm-extract..."
docker run --rm -v "$DATA_DIR:/data" "$OSRM_IMAGE" \
  osrm-extract -p /opt/car.lua "/data/$PBF_FILE"

echo "Running osrm-contract..."
docker run --rm -v "$DATA_DIR:/data" "$OSRM_IMAGE" \
  osrm-contract "/data/${PBF_FILE%.osm.pbf}.osrm"

echo "OSRM preprocessing complete. You can now run:"
echo "  docker compose up"

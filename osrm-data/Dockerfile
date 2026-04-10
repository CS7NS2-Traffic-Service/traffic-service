FROM osrm/osrm-backend AS builder
COPY ireland-and-northern-ireland-latest.osm.pbf /data/
RUN osrm-extract -p /opt/car.lua /data/ireland-and-northern-ireland-latest.osm.pbf \
 && osrm-contract /data/ireland-and-northern-ireland-latest.osrm

FROM osrm/osrm-backend
COPY --from=builder /data/ /data/
CMD ["osrm-routed", "--algorithm", "mld", "--port", "5555", "/data/ireland-and-northern-ireland-latest.osrm"]

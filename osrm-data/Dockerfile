FROM osrm/osrm-backend
COPY . /data/
CMD ["osrm-routed", "--algorithm", "mld", "/data/ireland-and-northern-ireland-latest.osrm"]

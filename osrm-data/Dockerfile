FROM osrm/osrm-backend
COPY . /data/
CMD ["osrm-routed", "--algorithm", "mld", "--port", "5555", "/data/ireland-and-northern-ireland-latest.osrm"]

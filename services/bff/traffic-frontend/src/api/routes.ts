import { authHeaders, handleResponse } from "@/api/client"

export type RouteResult = {
  route_id: string
  origin: string
  destination: string
  segment_ids: string[] | null
  geometry: unknown
  estimated_duration: number | null
  created_at: string
}

export type Segment = {
  segment_id: string
  osm_way_id: string | null
  name: string
  region: string
  capacity: number | null
  coordinates: unknown
}

export async function findRoute(
  originLat: number,
  originLng: number,
  destLat: number,
  destLng: number,
): Promise<RouteResult> {
  const params = new URLSearchParams({
    origin_lat: originLat.toString(),
    origin_lng: originLng.toString(),
    dest_lat: destLat.toString(),
    dest_lng: destLng.toString(),
  })
  const response = await fetch(`/api/routes/routes?${params}`, {
    headers: authHeaders(),
  })
  return handleResponse<RouteResult>(response, "Failed to find route")
}

export async function getRouteSegments(routeId: string): Promise<Segment[]> {
  const response = await fetch(`/api/routes/routes/${routeId}/segments`, {
    headers: authHeaders(),
  })
  return handleResponse<Segment[]>(response, "Failed to fetch route segments")
}

export type SegmentUtilization = {
  segment_id: string
  active_reservations: number
}

export async function getSegmentUtilization(
  segmentIds: string[],
  windowStart: string,
  windowEnd: string,
): Promise<SegmentUtilization[]> {
  const response = await fetch("/api/conflict-detection/utilization", {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      segment_ids: segmentIds,
      window_start: windowStart,
      window_end: windowEnd,
    }),
  })
  const data = await handleResponse<{ utilization: SegmentUtilization[] }>(response, "Failed to fetch utilization")
  return data.utilization
}

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

export async function findRoutes(
  originLat: number,
  originLng: number,
  destLat: number,
  destLng: number,
): Promise<RouteResult[]> {
  const params = new URLSearchParams({
    origin_lat: originLat.toString(),
    origin_lng: originLng.toString(),
    dest_lat: destLat.toString(),
    dest_lng: destLng.toString(),
  })
  const response = await fetch(`/api/routes/routes?${params}`, {
    headers: authHeaders(),
  })
  return handleResponse<RouteResult[]>(response, "Failed to find route")
}

export async function getRouteSegments(routeId: string): Promise<Segment[]> {
  const response = await fetch(`/api/routes/routes/${routeId}/segments`, {
    headers: authHeaders(),
  })
  return handleResponse<Segment[]>(response, "Failed to fetch route segments")
}

export async function fetchRoute(routeId: string): Promise<RouteResult> {
  const response = await fetch(`/api/routes/routes/${routeId}`, {
    headers: authHeaders(),
  })
  return handleResponse<RouteResult>(response, "Failed to fetch route")
}

export type SegmentUtilization = {
  segment_id: string
  active_reservations: number
}

export type SegmentWindow = {
  segment_id: string
  window_start: string
  window_end: string
}

export async function getSegmentUtilization(
  segments: SegmentWindow[],
): Promise<SegmentUtilization[]> {
  const response = await fetch("/api/conflict-detection/utilization", {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ segments }),
  })
  const data = await handleResponse<{ utilization: SegmentUtilization[] }>(response, "Failed to fetch utilization")
  return data.utilization
}

export type RouteAvailability = {
  route_id: string
  available: boolean
}

export async function checkRoutesAvailability(
  routes: RouteResult[],
  departureTime: string,
): Promise<RouteAvailability[]> {
  const response = await fetch("/api/conflict-detection/availability", {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      routes: routes.map((r) => ({
        route_id: r.route_id,
        segment_ids: r.segment_ids ?? [],
        estimated_duration: r.estimated_duration ?? 0,
      })),
      departure_time: departureTime,
    }),
  })
  const data = await handleResponse<{ routes: RouteAvailability[] }>(response, "Failed to check route availability")
  return data.routes
}

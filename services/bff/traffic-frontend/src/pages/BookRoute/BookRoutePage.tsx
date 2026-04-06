import { useCallback, useMemo, useRef } from "react"
import { useSearchParams } from "react-router-dom"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { findRoute, getRouteSegments, getSegmentUtilization } from "@/api/routes"
import RouteMap from "@/components/RouteMap"
import RouteResultCard from "./RouteResultCard"

type Coord = { lng: number; lat: number }

function BookRoutePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const originLat = searchParams.get("originLat") ?? ""
  const originLng = searchParams.get("originLng") ?? ""
  const destLat = searchParams.get("destLat") ?? ""
  const destLng = searchParams.get("destLng") ?? ""
  const departureTime = searchParams.get("departure") ?? new Date().toISOString().slice(0, 16)
  const clickCountRef = useRef(0)

  const setParam = (key: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set(key, e.target.value)
      return next
    }, { replace: true })

  const originCoord = useMemo<Coord | null>(() => {
    const lat = parseFloat(originLat)
    const lng = parseFloat(originLng)
    return !isNaN(lat) && !isNaN(lng) ? { lat, lng } : null
  }, [originLat, originLng])

  const destCoord = useMemo<Coord | null>(() => {
    const lat = parseFloat(destLat)
    const lng = parseFloat(destLng)
    return !isNaN(lat) && !isNaN(lng) ? { lat, lng } : null
  }, [destLat, destLng])

  const { mutate, data: route, isPending, error } = useMutation({
    mutationFn: () =>
      findRoute(
        parseFloat(originLat),
        parseFloat(originLng),
        parseFloat(destLat),
        parseFloat(destLng),
      ),
  })

  const hasSegments = (route?.segment_ids?.length ?? 0) > 0

  const { data: segments } = useQuery({
    queryKey: ["segments", route?.route_id],
    queryFn: () => getRouteSegments(route!.route_id),
    enabled: !!route?.route_id && hasSegments,
  })

  const { data: utilizationData } = useQuery({
    queryKey: ["utilization", route?.route_id, departureTime],
    queryFn: () => {
      const windowStart = new Date(departureTime).toISOString()
      const windowEnd = new Date(
        new Date(departureTime).getTime() + (route!.estimated_duration ?? 0) * 1000,
      ).toISOString()
      return getSegmentUtilization(
        segments!.map((s) => s.segment_id),
        windowStart,
        windowEnd,
      )
    },
    enabled: !!segments && segments.length > 0,
  })

  const utilization = useMemo(() => {
    const map: Record<string, number> = {}
    for (const u of utilizationData ?? []) {
      map[u.segment_id] = u.active_reservations
    }
    return map
  }, [utilizationData])

  const handleMapClick = useCallback((lngLat: Coord) => {
    if (clickCountRef.current === 0) {
      setSearchParams(new URLSearchParams({
        originLat: lngLat.lat.toFixed(6),
        originLng: lngLat.lng.toFixed(6),
      }), { replace: true })
      clickCountRef.current = 1
    } else {
      setSearchParams((prev) => {
        const newParams = new URLSearchParams(prev)
        newParams.set("destLat", lngLat.lat.toFixed(6))
        newParams.set("destLng", lngLat.lng.toFixed(6))
        return newParams
      }, { replace: true })
      clickCountRef.current = 0
    }
  }, [setSearchParams])

  function handleSubmit(e: React.SubmitEvent) {
    e.preventDefault()
    mutate()
  }

  const isValid = originLat && originLng && destLat && destLng
  const originLatValue = parseFloat(originLat)
  const originLngValue = parseFloat(originLng)
  const destLatValue = parseFloat(destLat)
  const destLngValue = parseFloat(destLng)
  const outOfRange =
    (!isNaN(originLatValue) && (originLatValue < -90 || originLatValue > 90)) ||
    (!isNaN(destLatValue) && (destLatValue < -90 || destLatValue > 90)) ||
    (!isNaN(originLngValue) && (originLngValue < -180 || originLngValue > 180)) ||
    (!isNaN(destLngValue) && (destLngValue < -180 || destLngValue > 180))

  const mapSegments = segments?.map((seg) => ({
    segment_id: seg.segment_id,
    coordinates: seg.coordinates,
    capacity: seg.capacity,
    utilization: (utilization[seg.segment_id] ?? 0) / (seg.capacity || 1),
  }))

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Find a Route</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && <p className="text-sm text-red-500">{error.message}</p>}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Origin Latitude</label>
                    <Input
                      type="number"
                      step="any"
                      placeholder="e.g. 48.2082"
                      value={originLat}
                      onChange={setParam("originLat")}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Origin Longitude</label>
                    <Input
                      type="number"
                      step="any"
                      placeholder="e.g. 16.3738"
                      value={originLng}
                      onChange={setParam("originLng")}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Destination Latitude</label>
                    <Input
                      type="number"
                      step="any"
                      placeholder="e.g. 47.0707"
                      value={destLat}
                      onChange={setParam("destLat")}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Destination Longitude</label>
                    <Input
                      type="number"
                      step="any"
                      placeholder="e.g. 15.4395"
                      value={destLng}
                      onChange={setParam("destLng")}
                    />
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Departure Time</label>
                  <Input type="datetime-local" value={departureTime} onChange={setParam("departure")} />
                </div>
                <Button type="submit" disabled={isPending || !isValid || outOfRange}>
                  {isPending ? "Searching..." : "Find Route"}
                </Button>
                {outOfRange && (
                  <p className="text-xs text-red-500">
                    Latitude must be between -90 and 90, longitude between -180 and 180.
                  </p>
                )}
                <p className="text-xs text-muted-foreground">
                  Tip: click the map to set origin (1st click) and destination (2nd click)
                </p>
              </form>
            </CardContent>
          </Card>

          {route && <RouteResultCard route={route} segments={segments} utilization={utilization} departureTime={departureTime} />}
        </div>

        <div className="lg:sticky lg:top-8 lg:self-start">
          <RouteMap
            geometry={route?.geometry as GeoJSON.Geometry | undefined}
            segments={mapSegments}
            origin={originCoord}
            destination={destCoord}
            onMapClick={handleMapClick}
          />
        </div>
      </div>
    </div>
  )
}

export default BookRoutePage

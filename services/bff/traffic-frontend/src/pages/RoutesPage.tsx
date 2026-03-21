import { useState, useCallback, useRef } from "react"
import { useMutation } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { findRoute, getRouteSegments, getSegmentUtilization, type RouteResult, type Segment } from "@/api/routes"
import RouteMap from "@/components/RouteMap"

type Coord = { lng: number; lat: number }

function RouteResultCard({ route, segments, utilization }: { route: RouteResult; segments: Segment[] | null; utilization: Record<string, number> | null }) {
  const durationMinutes = route.estimated_duration
    ? Math.round(route.estimated_duration / 60)
    : null

  return (
    <Card>
      <CardHeader>
        <CardTitle>Route Found</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <p><span className="font-medium">Route ID:</span> {route.route_id}</p>
          <p><span className="font-medium">Origin:</span> {route.origin}</p>
          <p><span className="font-medium">Destination:</span> {route.destination}</p>
          {durationMinutes !== null && (
            <p><span className="font-medium">Est. Duration:</span> {durationMinutes} min</p>
          )}
        </div>

        {segments && segments.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-semibold">Segments ({segments.length})</h3>
            <div className="space-y-1">
              {segments.map((seg) => (
                <div
                  key={seg.segment_id}
                  className="rounded-md border px-3 py-2 text-sm"
                >
                  <p className="font-medium">{seg.name}</p>
                  <p className="text-muted-foreground">
                    Region: {seg.region}
                    {seg.capacity !== null && ` | Capacity: ${seg.capacity}`}
                    {seg.capacity !== null && ` | Reserved: ${utilization?.[seg.segment_id] ?? 0} / ${seg.capacity}`}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function RoutesPage() {
  const [originLat, setOriginLat] = useState("")
  const [originLng, setOriginLng] = useState("")
  const [destLat, setDestLat] = useState("")
  const [destLng, setDestLng] = useState("")
  const [segments, setSegments] = useState<Segment[] | null>(null)
  const [utilization, setUtilization] = useState<Record<string, number>>({})
  const [departureTime, setDepartureTime] = useState(() => new Date().toISOString().slice(0, 16))
  const [originCoord, setOriginCoord] = useState<Coord | null>(null)
  const [destCoord, setDestCoord] = useState<Coord | null>(null)
  const clickCountRef = useRef(0)

  const { mutate, data: route, isPending, error } = useMutation({
    mutationFn: () =>
      findRoute(
        parseFloat(originLat),
        parseFloat(originLng),
        parseFloat(destLat),
        parseFloat(destLng),
      ),
    onSuccess: async (result) => {
      if (result.segment_ids && result.segment_ids.length > 0) {
        try {
          const segs = await getRouteSegments(result.route_id)
          setSegments(segs)

          try {
            const windowStart = new Date(departureTime).toISOString()
            const windowEnd = new Date(
              new Date(departureTime).getTime() + (result.estimated_duration ?? 0) * 1000,
            ).toISOString()
            const utilData = await getSegmentUtilization(
              segs.map((s) => s.segment_id),
              windowStart,
              windowEnd,
            )
            const utilMap: Record<string, number> = {}
            for (const u of utilData) {
              utilMap[u.segment_id] = u.active_reservations
            }
            setUtilization(utilMap)
          } catch {
            setUtilization({})
          }
        } catch {
          setSegments(null)
          setUtilization({})
        }
      } else {
        setSegments(null)
        setUtilization({})
      }
    },
  })

  const handleMapClick = useCallback((lngLat: Coord) => {
    if (clickCountRef.current === 0) {
      setOriginLat(lngLat.lat.toFixed(6))
      setOriginLng(lngLat.lng.toFixed(6))
      setDestLat("")
      setDestLng("")
      setOriginCoord(lngLat)
      setDestCoord(null)
      clickCountRef.current = 1
    } else {
      setDestLat(lngLat.lat.toFixed(6))
      setDestLng(lngLat.lng.toFixed(6))
      setDestCoord(lngLat)
      clickCountRef.current = 0
    }
  }, [])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSegments(null)
    setUtilization({})
    mutate()
  }

  const isValid = originLat && originLng && destLat && destLng

  const mapSegments = segments?.map((seg) => ({
    segment_id: seg.segment_id,
    coordinates: seg.coordinates,
    capacity: seg.capacity,
    utilization: (utilization[seg.segment_id] ?? 0) / (seg.capacity || 1),
  }))

  return (
    <div className="mx-auto max-w-3xl space-y-8 px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle>Find a Route</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && <p className="text-sm text-red-500">{(error as Error).message}</p>}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-medium">Origin Latitude</label>
                <Input
                  type="number"
                  step="any"
                  placeholder="e.g. 48.2082"
                  value={originLat}
                  onChange={(e) => setOriginLat(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">Origin Longitude</label>
                <Input
                  type="number"
                  step="any"
                  placeholder="e.g. 16.3738"
                  value={originLng}
                  onChange={(e) => setOriginLng(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">Destination Latitude</label>
                <Input
                  type="number"
                  step="any"
                  placeholder="e.g. 47.0707"
                  value={destLat}
                  onChange={(e) => setDestLat(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">Destination Longitude</label>
                <Input
                  type="number"
                  step="any"
                  placeholder="e.g. 15.4395"
                  value={destLng}
                  onChange={(e) => setDestLng(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">Departure Time</label>
              <Input type="datetime-local" value={departureTime} onChange={(e) => setDepartureTime(e.target.value)} />
            </div>
            <Button type="submit" disabled={isPending || !isValid}>
              {isPending ? "Searching..." : "Find Route"}
            </Button>
            <p className="text-xs text-muted-foreground">
              Tip: click the map to set origin (1st click) and destination (2nd click)
            </p>
          </form>
        </CardContent>
      </Card>

      <RouteMap
        geometry={route?.geometry as GeoJSON.Geometry | undefined}
        segments={mapSegments}
        origin={originCoord}
        destination={destCoord}
        onMapClick={handleMapClick}
      />

      {route && <RouteResultCard route={route} segments={segments} utilization={utilization} />}
    </div>
  )
}

export default RoutesPage

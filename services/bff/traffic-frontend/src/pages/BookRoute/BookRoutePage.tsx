import { useCallback, useMemo, useRef } from "react"
import { useSearchParams } from "react-router-dom"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { DateTimePicker } from "@/components/ui/date-time-picker"
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
  const fiveMinutesMs = 5 * 60 * 1000
  const roundTo5 = useCallback((d: Date) => {
    return new Date(Math.round(d.getTime() / fiveMinutesMs) * fiveMinutesMs)
  }, [fiveMinutesMs])
  const defaultDeparture = useMemo(() => roundTo5(new Date()), [roundTo5])
  const rawDeparture = searchParams.get("departure")
  const departureDate = useMemo(() => {
    const candidate = rawDeparture ? new Date(rawDeparture) : defaultDeparture
    if (isNaN(candidate.getTime())) return defaultDeparture
    return roundTo5(candidate)
  }, [rawDeparture, defaultDeparture, roundTo5])
  const departureTimeIso = useMemo(() => departureDate.toISOString(), [departureDate])
  const clickCountRef = useRef(0)

  const setParam = (key: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set(key, e.target.value)
      return next
    }, { replace: true })

  const handleDepartureChange = useCallback((date: Date) => {
    const rounded = roundTo5(date)
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set("departure", rounded.toISOString().slice(0, 16))
      return next
    }, { replace: true })
  }, [roundTo5, setSearchParams])

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
    queryKey: ["utilization", route?.route_id, departureTimeIso],
    queryFn: () => {
      const windowStart = departureTimeIso
      const windowEnd = new Date(
        departureDate.getTime() + (route!.estimated_duration ?? 0) * 1000,
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
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev)
        next.set("originLat", lngLat.lat.toFixed(6))
        next.set("originLng", lngLat.lng.toFixed(6))
        return next
      }, { replace: true })
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
                  <DateTimePicker
                    value={departureDate}
                    onChange={handleDepartureChange}
                    aria-label="Departure time"
                  />
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

          {route && <RouteResultCard route={route} segments={segments} utilization={utilization} departureTime={departureTimeIso} />}
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

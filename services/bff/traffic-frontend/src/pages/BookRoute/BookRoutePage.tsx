import { useCallback, useMemo, useRef } from "react"
import { useSearchParams } from "react-router-dom"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DateTimePicker } from "@/components/ui/date-time-picker"
import { LocationSearch } from "@/components/ui/LocationSearch"
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
  const originName = searchParams.get("originName") ?? (originLat && originLng ? `${parseFloat(originLat).toFixed(4)}, ${parseFloat(originLng).toFixed(4)}` : "")
  const destName = searchParams.get("destName") ?? (destLat && destLng ? `${parseFloat(destLat).toFixed(4)}, ${parseFloat(destLng).toFixed(4)}` : "")
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

  const handleOriginSelect = useCallback((name: string, lng: number, lat: number) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set("originLat", lat.toFixed(6))
      next.set("originLng", lng.toFixed(6))
      next.set("originName", name)
      return next
    }, { replace: true })
  }, [setSearchParams])

  const handleOriginClear = useCallback(() => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.delete("originLat")
      next.delete("originLng")
      next.delete("originName")
      return next
    }, { replace: true })
  }, [setSearchParams])

  const handleDestSelect = useCallback((name: string, lng: number, lat: number) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set("destLat", lat.toFixed(6))
      next.set("destLng", lng.toFixed(6))
      next.set("destName", name)
      return next
    }, { replace: true })
  }, [setSearchParams])

  const handleDestClear = useCallback(() => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.delete("destLat")
      next.delete("destLng")
      next.delete("destName")
      return next
    }, { replace: true })
  }, [setSearchParams])

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
    const coordLabel = `${lngLat.lat.toFixed(4)}, ${lngLat.lng.toFixed(4)}`
    if (clickCountRef.current === 0) {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev)
        next.set("originLat", lngLat.lat.toFixed(6))
        next.set("originLng", lngLat.lng.toFixed(6))
        next.set("originName", coordLabel)
        return next
      }, { replace: true })
      clickCountRef.current = 1
    } else {
      setSearchParams((prev) => {
        const newParams = new URLSearchParams(prev)
        newParams.set("destLat", lngLat.lat.toFixed(6))
        newParams.set("destLng", lngLat.lng.toFixed(6))
        newParams.set("destName", coordLabel)
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
                <LocationSearch
                  label="Origin"
                  placeholder="e.g. Dublin Airport"
                  displayValue={originName}
                  onSelect={handleOriginSelect}
                  onClear={handleOriginClear}
                />
                <LocationSearch
                  label="Destination"
                  placeholder="e.g. Cork City"
                  displayValue={destName}
                  onSelect={handleDestSelect}
                  onClear={handleDestClear}
                />
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

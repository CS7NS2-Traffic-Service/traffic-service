import { useCallback, useMemo, useRef, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DateTimePicker } from "@/components/ui/date-time-picker"
import { LocationSearch } from "@/components/ui/LocationSearch"
import { findRoutes, getRouteSegments, getSegmentUtilization, checkRoutesAvailability } from "@/api/routes"
import RouteMap from "@/components/RouteMap"
import RouteResultCard from "./RouteResultCard"
import { ensureUTCSuffix, parseLocalDateTime, formatDuration } from "@/lib/datetime"

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
    const candidate = rawDeparture
      ? /(?:Z|[+-]\d{2}:\d{2})$/.test(rawDeparture)
        ? new Date(ensureUTCSuffix(rawDeparture))
        : parseLocalDateTime(rawDeparture)
      : defaultDeparture
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
      next.set("departure", rounded.toISOString())
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

  const [userSelectedIndex, setUserSelectedIndex] = useState<number | null>(null)

  const { mutate, data: allRoutes, isPending, error } = useMutation({
    mutationFn: () =>
      findRoutes(
        parseFloat(originLat),
        parseFloat(originLng),
        parseFloat(destLat),
        parseFloat(destLng),
      ),
    onSuccess: () => setUserSelectedIndex(null),
    retry: (failureCount, err) => {
      if (!(err instanceof Error)) return failureCount < 2
      if (err.message.includes("No route found")) return false
      return failureCount < 2
    },
    retryDelay: (attempt) => attempt * 750,
  })

  const { data: availabilityData } = useQuery({
    queryKey: ["availability", allRoutes?.map((r) => r.route_id), departureTimeIso],
    queryFn: () => checkRoutesAvailability(allRoutes!, departureTimeIso),
    enabled: !!allRoutes && allRoutes.length > 0,
  })

  const availabilityMap = useMemo(() => {
    const m = new Map<string, boolean>()
    for (const a of availabilityData ?? []) m.set(a.route_id, a.available)
    return m
  }, [availabilityData])

  const selectedRouteIndex = useMemo(() => {
    if (userSelectedIndex !== null) return userSelectedIndex
    if (!allRoutes || !availabilityData) return 0
    const firstAvailable = allRoutes.findIndex((r) => availabilityMap.get(r.route_id) === true)
    return firstAvailable >= 0 ? firstAvailable : 0
  }, [userSelectedIndex, allRoutes, availabilityData, availabilityMap])

  const route = allRoutes?.[selectedRouteIndex]
  const routeAvailable = route ? availabilityMap.get(route.route_id) : undefined
  const noAvailableRoutes = !!availabilityData && availabilityData.length > 0 && !availabilityData.some((a) => a.available)

  const hasSegments = (route?.segment_ids?.length ?? 0) > 0

  const { data: segments } = useQuery({
    queryKey: ["segments", route?.route_id],
    queryFn: () => getRouteSegments(route!.route_id),
    enabled: !!route?.route_id && hasSegments,
  })

  const { data: utilizationData } = useQuery({
    queryKey: ["utilization", route?.route_id, departureTimeIso],
    queryFn: () => {
      const duration = (route!.estimated_duration ?? 0) * 1000
      const segmentWindows = segments!.map((s, index) => {
        const offset = index * 300 * 1000
        const start = new Date(departureDate.getTime() + offset)
        const end = new Date(start.getTime() + duration)
        return {
          segment_id: s.segment_id,
          window_start: start.toISOString(),
          window_end: end.toISOString(),
        }
      })
      return getSegmentUtilization(segmentWindows)
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

  const alternativeGeometries = useMemo(() => {
    if (!allRoutes || allRoutes.length <= 1) return undefined
    return allRoutes
      .filter((_, i) => i !== selectedRouteIndex)
      .map((r) => r.geometry as GeoJSON.Geometry)
      .filter(Boolean)
  }, [allRoutes, selectedRouteIndex])

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
    name: seg.name,
    region: seg.region,
    coordinates: seg.coordinates,
    capacity: seg.capacity,
    reserved: utilization[seg.segment_id] ?? 0,
    utilization: (utilization[seg.segment_id] ?? 0) / (seg.capacity || 1),
  }))

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[400px_minmax(0,1fr)]">
        <div className="space-y-6">
          <Card className="shadow-sm">
            <CardContent>
              <p className="mb-4 text-sm text-muted-foreground">
                Choose locations and departure time, or click the map to set points.
              </p>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                    {error.message.includes("No route found")
                      ? "No routes found between these two points. Try adjusting your origin or destination."
                      : error.message}
                  </p>
                )}
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
                <Button type="submit" disabled={isPending || !isValid} className="w-full">
                  {isPending ? "Searching..." : "Find Route"}
                </Button>
              </form>
            </CardContent>
          </Card>

          {allRoutes && allRoutes.length > 1 && (
            <Card className="shadow-sm">
              <CardContent className="space-y-2">
                <h3 className="text-sm font-semibold">Routes ({allRoutes.length})</h3>
                {allRoutes.map((r, i) => {
                  const available = availabilityMap.get(r.route_id)
                  const isSelected = i === selectedRouteIndex
                  return (
                    <button
                      key={r.route_id}
                      onClick={() => setUserSelectedIndex(i)}
                      className={`flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm transition-colors ${isSelected ? "border-blue-500 bg-blue-50" : "hover:bg-muted/50"}`}
                    >
                      <div>
                        <span className="font-medium">Route {i + 1}</span>
                        {r.estimated_duration != null && (
                          <span className="ml-2 text-muted-foreground">{formatDuration(r.estimated_duration)}</span>
                        )}
                      </div>
                      {available === false && (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">Fully booked</span>
                      )}
                      {available === true && (
                        <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">Available</span>
                      )}
                    </button>
                  )
                })}
              </CardContent>
            </Card>
          )}

          {noAvailableRoutes && (
            <Card className="shadow-sm">
              <CardContent>
                <p className="text-sm text-amber-700">
                  All routes between these points are fully booked for the selected departure time. Try a different time.
                </p>
              </CardContent>
            </Card>
          )}

          {route && <RouteResultCard route={route} segments={segments} utilization={utilization} departureTime={departureTimeIso} available={routeAvailable} />}
        </div>

        <div className="lg:sticky lg:top-6 lg:self-start">
          <RouteMap
            geometry={route?.geometry as GeoJSON.Geometry | undefined}
            alternativeGeometries={alternativeGeometries}
            segments={mapSegments}
            origin={originCoord}
            destination={destCoord}
            onMapClick={handleMapClick}
            className="h-[calc(100vh-9rem)] min-h-[360px] max-h-[520px] rounded-2xl shadow-sm"
          />
        </div>
      </div>
    </div>
  )
}

export default BookRoutePage

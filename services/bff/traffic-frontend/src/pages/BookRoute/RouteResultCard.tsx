import { createBooking, type Booking } from "@/api/bookings"
import type { RouteResult, Segment } from "@/api/routes"
import { StatusBadge } from "@/components/StatusBadge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

function RouteResultCard({
  route,
  segments,
  utilization,
  departureTime,
}: {
  route: RouteResult
  segments: Segment[] | undefined
  utilization: Record<string, number>
  departureTime: string
}) {
  const queryClient = useQueryClient()
  const [bookingResult, setBookingResult] = useState<Booking | null>(null)
  const [bookingError, setBookingError] = useState<string | null>(null)

  const { mutate: book, isPending: isBooking } = useMutation({
    mutationFn: createBooking,
    onSuccess: (booking) => {
      setBookingResult(booking)
      setBookingError(null)
      queryClient.invalidateQueries({ queryKey: ["bookings"] })
    },
    onError: (err: Error) => {
      setBookingError(err.message)
      setBookingResult(null)
    },
  })

  const durationMinutes = route.estimated_duration
    ? Math.round(route.estimated_duration / 60)
    : null

  function handleBook() {
    const departure = new Date(departureTime).toISOString()
    const estimatedArrival = route.estimated_duration
      ? new Date(new Date(departureTime).getTime() + route.estimated_duration * 1000).toISOString()
      : undefined

    book({
      route_id: route.route_id,
      departure_time: departure,
      estimated_arrival: estimatedArrival,
    })
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Route Found</CardTitle>
        {bookingResult ? (
          <div className="flex items-center gap-2 text-sm text-green-700">
            <p>Booking created: {bookingResult.booking_id}</p>
            <StatusBadge status={bookingResult.status} />
          </div>
        ) : (
          <div className="flex items-center gap-2">
            {bookingError && <p className="text-sm text-red-500">{bookingError}</p>}
            <Button onClick={handleBook} disabled={isBooking}>
              {isBooking ? "Booking..." : "Book this Route"}
            </Button>
          </div>
        )}
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
                    {seg.capacity !== null && ` | Reserved: ${utilization[seg.segment_id] ?? 0} / ${seg.capacity}`}
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

export default RouteResultCard

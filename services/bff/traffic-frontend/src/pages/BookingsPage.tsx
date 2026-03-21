import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { fetchBookings, createBooking, cancelBooking, type Booking } from "@/api/bookings"

const STATUS_COLORS: Record<string, string> = {
  PENDING: "bg-yellow-100 text-yellow-800",
  APPROVED: "bg-green-100 text-green-800",
  REJECTED: "bg-red-100 text-red-800",
  CANCELLED: "bg-gray-100 text-gray-800",
}

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? "bg-gray-100 text-gray-800"
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}>
      {status}
    </span>
  )
}

function BookingCard({ booking, onCancel, isCancelling }: {
  booking: Booking
  onCancel: (id: string) => void
  isCancelling: boolean
}) {
  const canCancel = booking.status === "PENDING" || booking.status === "APPROVED"

  return (
    <Card>
      <CardContent className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium">Route: {booking.route_id}</p>
          <p className="text-sm text-muted-foreground">
            Departure: {new Date(booking.departure_time).toLocaleString()}
          </p>
          <StatusBadge status={booking.status} />
        </div>
        {canCancel && (
          <Button
            variant="destructive"
            size="sm"
            disabled={isCancelling}
            onClick={() => onCancel(booking.booking_id)}
          >
            Cancel
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

function CreateBookingForm({ onCreated }: { onCreated: () => void }) {
  const [routeId, setRouteId] = useState("")
  const [departureTime, setDepartureTime] = useState("")
  const [error, setError] = useState<string | null>(null)

  const { mutate, isPending } = useMutation({
    mutationFn: createBooking,
    onSuccess: () => {
      setRouteId("")
      setDepartureTime("")
      setError(null)
      onCreated()
    },
    onError: (err: Error) => setError(err.message),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!routeId || !departureTime) return
    mutate({ route_id: routeId, departure_time: new Date(departureTime).toISOString() })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Booking</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="space-y-1">
            <label className="text-sm font-medium">Route ID</label>
            <Input
              placeholder="Enter route ID"
              value={routeId}
              onChange={(e) => setRouteId(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium">Departure Time</label>
            <Input
              type="datetime-local"
              value={departureTime}
              onChange={(e) => setDepartureTime(e.target.value)}
            />
          </div>
          <Button type="submit" disabled={isPending || !routeId || !departureTime}>
            {isPending ? "Creating..." : "Create Booking"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

function BookingsPage() {
  const queryClient = useQueryClient()

  const { data: bookings, isLoading, error } = useQuery({
    queryKey: ["bookings"],
    queryFn: fetchBookings,
    refetchInterval: 5000,
  })

  const { mutate: cancel, isPending: isCancelling } = useMutation({
    mutationFn: cancelBooking,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bookings"] }),
  })

  return (
    <div className="mx-auto max-w-3xl space-y-8 px-4 py-8">
      <CreateBookingForm onCreated={() => queryClient.invalidateQueries({ queryKey: ["bookings"] })} />

      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Your Bookings</h2>
        {isLoading && <p className="text-sm text-muted-foreground">Loading bookings...</p>}
        {error && <p className="text-sm text-red-500">{(error as Error).message}</p>}
        {bookings && bookings.length === 0 && (
          <p className="text-sm text-muted-foreground">No bookings yet.</p>
        )}
        {bookings?.map((booking) => (
          <BookingCard
            key={booking.booking_id}
            booking={booking}
            onCancel={cancel}
            isCancelling={isCancelling}
          />
        ))}
      </div>
    </div>
  )
}

export default BookingsPage

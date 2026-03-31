import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useSearchParams } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatusBadge } from "@/components/StatusBadge"
import { fetchBookings, cancelBooking, fetchBookingReservations, type Booking } from "@/api/bookings"

const STAT_LABELS = ["PENDING", "APPROVED", "REJECTED", "CANCELLED"] as const

const STAT_COLORS: Record<string, string> = {
  PENDING: "text-yellow-600",
  APPROVED: "text-green-600",
  REJECTED: "text-red-600",
  CANCELLED: "text-gray-500",
}

function StatCard({ label, count, active, onClick }: {
  label: string
  count: number
  active: boolean
  onClick: () => void
}) {
  return (
    <Card
      className={`cursor-pointer transition-colors ${active ? "ring-2 ring-primary" : ""}`}
      onClick={onClick}
    >
      <CardContent className="pt-2">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className={`text-2xl font-bold ${STAT_COLORS[label] ?? ""}`}>{count}</p>
      </CardContent>
    </Card>
  )
}

function BookingCard({ booking, onCancel, isCancelling, expanded, onToggle }: {
  booking: Booking
  onCancel: (id: string) => void
  isCancelling: boolean
  expanded: boolean
  onToggle: () => void
}) {
  const canCancel = booking.status === "PENDING" || booking.status === "APPROVED"

  const { data: reservations, isLoading: reservationsLoading } = useQuery({
    queryKey: ["reservations", booking.booking_id],
    queryFn: () => fetchBookingReservations(booking.booking_id),
    enabled: expanded,
  })

  return (
    <Card className="cursor-pointer" onClick={onToggle}>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
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
              onClick={(e) => { e.stopPropagation(); onCancel(booking.booking_id) }}
            >
              Cancel
            </Button>
          )}
        </div>
        {expanded && (
          <div className="border-t pt-3">
            <p className="text-sm font-medium mb-2">Segment Reservations</p>
            {reservationsLoading && (
              <p className="text-sm text-muted-foreground">Loading...</p>
            )}
            {reservations && reservations.length === 0 && (
              <p className="text-sm text-muted-foreground">No reservations found.</p>
            )}
            {reservations && reservations.length > 0 && (
              <div className="space-y-1">
                {reservations.map((r) => (
                  <div key={r.reservation_id} className="flex justify-between text-sm text-muted-foreground">
                    <span className="font-mono truncate max-w-48">{r.segment_id}</span>
                    <span>
                      {new Date(r.time_window_start).toLocaleTimeString()} – {new Date(r.time_window_end).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function BookingsPage() {
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeStatus = searchParams.get("status")
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const { data: bookings, isLoading, error } = useQuery({
    queryKey: ["bookings"],
    queryFn: fetchBookings,
    refetchInterval: 5000,
  })

  const { mutate: cancel, isPending: isCancelling } = useMutation({
    mutationFn: cancelBooking,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bookings"] }),
  })

  const statusCounts = (bookings ?? []).reduce<Record<string, number>>((acc, b) => {
    acc[b.status] = (acc[b.status] ?? 0) + 1
    return acc
  }, {})

  const filteredBookings = activeStatus
    ? (bookings ?? []).filter((b) => b.status === activeStatus)
    : bookings

  const toggleFilter = (status: string | null) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      if (status === null || status === activeStatus) {
        next.delete("status")
      } else {
        next.set("status", status)
      }
      return next
    }, { replace: true })
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
      {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
      {error && <p className="text-sm text-red-500">{(error as Error).message}</p>}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        <StatCard
          label="Total"
          count={bookings?.length ?? 0}
          active={activeStatus === null}
          onClick={() => toggleFilter(null)}
        />
        {STAT_LABELS.map((status) => (
          <StatCard
            key={status}
            label={status}
            count={statusCounts[status] ?? 0}
            active={activeStatus === status}
            onClick={() => toggleFilter(status)}
          />
        ))}
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Your Bookings</h2>
        {filteredBookings && filteredBookings.length === 0 && (
          <p className="text-sm text-muted-foreground">No bookings yet.</p>
        )}
        {filteredBookings?.map((booking) => (
          <BookingCard
            key={booking.booking_id}
            booking={booking}
            onCancel={cancel}
            isCancelling={isCancelling}
            expanded={expandedId === booking.booking_id}
            onToggle={() => setExpandedId(
              expandedId === booking.booking_id ? null : booking.booking_id
            )}
          />
        ))}
      </div>
    </div>
  )
}

export default BookingsPage

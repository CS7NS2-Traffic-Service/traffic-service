import { useState } from "react"
import { formatUTCToLocal, formatUTCToLocalTime, shortId } from "@/lib/datetime"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Link, useSearchParams } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatusBadge } from "@/components/StatusBadge"
import { fetchBookings, cancelBooking, fetchBookingReservations, type Booking } from "@/api/bookings"

const STAT_FILTERS: { label: string; statuses: string[] }[] = [
  { label: "Pending", statuses: ["PENDING"] },
  { label: "Approved", statuses: ["APPROVED"] },
  { label: "Rejected", statuses: ["REJECTED"] },
  { label: "Cancelled / Expired", statuses: ["CANCELLED", "EXPIRED"] },
]

const STAT_COLORS: Record<string, string> = {
  Pending: "text-yellow-600",
  Approved: "text-green-600",
  Rejected: "text-red-600",
  "Cancelled / Expired": "text-gray-500",
}

const STATUS_DESCRIPTIONS: Record<string, string> = {
  PENDING: "Awaiting route assessment — usually instant",
  APPROVED: "Road capacity reserved for your departure window",
  REJECTED: "No capacity available on this route",
  CANCELLED: "Booking was cancelled",
  EXPIRED: "Departure time has passed",
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
            <p className="text-sm font-medium">Route {shortId(booking.route_id)}</p>
            <p className="text-sm text-muted-foreground">
              Departure: {formatUTCToLocal(booking.departure_time)}
            </p>
            <StatusBadge status={booking.status} />
            {STATUS_DESCRIPTIONS[booking.status] && (
              <p className="text-xs text-muted-foreground">{STATUS_DESCRIPTIONS[booking.status]}</p>
            )}
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
                    <span className="text-muted-foreground">{shortId(r.segment_id)}</span>
                    <span>
                      {formatUTCToLocalTime(r.time_window_start)} – {formatUTCToLocalTime(r.time_window_end)}
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

  const activeFilter = STAT_FILTERS.find((f) => f.label === activeStatus)

  const filteredBookings = activeFilter
    ? (bookings ?? []).filter((b) => activeFilter.statuses.includes(b.status))
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
        {STAT_FILTERS.map(({ label, statuses }) => (
          <StatCard
            key={label}
            label={label}
            count={(bookings ?? []).filter((b) => statuses.includes(b.status)).length}
            active={activeStatus === label}
            onClick={() => toggleFilter(label)}
          />
        ))}
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Your Bookings</h2>
        <p className="text-sm text-muted-foreground">
          Pending bookings are reviewed asynchronously. Approved bookings reserve road capacity for
          your selected departure window.
        </p>
        {filteredBookings && filteredBookings.length === 0 && (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <p className="text-sm text-muted-foreground">No bookings yet.</p>
            <Link to="/routes" className="mt-1 inline-block text-sm font-medium text-primary hover:underline">
              Book a route →
            </Link>
          </div>
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

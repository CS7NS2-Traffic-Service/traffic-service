import { useState } from "react"
import { formatUTCToLocal, formatUTCToLocalTime, shortId } from "@/lib/datetime"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Link, useSearchParams } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatusBadge } from "@/components/StatusBadge"
import { fetchBookings, cancelBooking, fetchBookingReservations, type Booking, type BookingStatus } from "@/api/bookings"
import { cn } from "@/lib/utils"

type BookingFilter = {
  label: string
  value: string
  statuses: BookingStatus[]
}

const STAT_FILTERS: BookingFilter[] = [
  { label: "Pending", value: "pending", statuses: ["PENDING"] },
  { label: "Approved", value: "approved", statuses: ["APPROVED"] },
  { label: "Rejected", value: "rejected", statuses: ["REJECTED"] },
  { label: "Closed", value: "closed", statuses: ["CANCELLED", "EXPIRED"] },
]

const STAT_COLORS: Record<string, string> = {
  Total: "text-foreground",
  Pending: "text-yellow-600",
  Approved: "text-green-600",
  Rejected: "text-red-600",
  Closed: "text-gray-500",
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
    <button
      type="button"
      className={cn(
        "rounded-xl border bg-card px-3 py-2 text-left shadow-sm transition-colors hover:bg-muted/40",
        active && "border-primary bg-primary/5 ring-1 ring-primary"
      )}
      onClick={onClick}
    >
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn("text-xl font-semibold leading-tight", STAT_COLORS[label])}>{count}</p>
    </button>
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
    <Card className="cursor-pointer shadow-sm transition-colors hover:bg-muted/30" onClick={onToggle}>
      <CardContent className="space-y-3">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold">Route {shortId(booking.route_id)}</p>
              <StatusBadge status={booking.status} />
            </div>
            <p className="text-sm text-muted-foreground">{formatUTCToLocal(booking.departure_time)}</p>
            <p className="text-xs text-muted-foreground">
              {STATUS_DESCRIPTIONS[booking.status] ?? "Click to view reservation details"}
            </p>
            {!expanded && (
              <p className="text-xs font-medium text-primary">View segment reservations</p>
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
            <p className="mb-2 text-sm font-medium">Segment reservations</p>
            {reservationsLoading && (
              <p className="text-sm text-muted-foreground">Loading...</p>
            )}
            {reservations && reservations.length === 0 && (
              <p className="text-sm text-muted-foreground">No reservations found.</p>
            )}
            {reservations && reservations.length > 0 && (
              <div className="space-y-1.5">
                {reservations.map((r) => (
                  <div
                    key={r.reservation_id}
                    className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2 text-sm text-muted-foreground"
                  >
                    <span>Segment {shortId(r.segment_id)}</span>
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

  const activeFilter = STAT_FILTERS.find((f) => f.value === activeStatus)

  const filteredBookings = activeFilter
    ? (bookings ?? []).filter((b) => activeFilter.statuses.includes(b.status))
    : bookings
  const errorMessage = error instanceof Error ? error.message : "Failed to load bookings"
  const emptyMessage = activeFilter
    ? `No ${activeFilter.label.toLowerCase()} bookings.`
    : "No bookings yet."

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
    <div className="mx-auto max-w-4xl space-y-5 px-4 py-6">
      {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {errorMessage}
        </p>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <StatCard
          label="Total"
          count={bookings?.length ?? 0}
          active={activeStatus === null}
          onClick={() => toggleFilter(null)}
        />
        {STAT_FILTERS.map(({ label, value, statuses }) => (
          <StatCard
            key={label}
            label={label}
            count={(bookings ?? []).filter((b) => statuses.includes(b.status)).length}
            active={activeStatus === value}
            onClick={() => toggleFilter(value)}
          />
        ))}
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Your Bookings</h2>
        <p className="text-sm text-muted-foreground">
          Pending bookings are reviewed asynchronously. Approved bookings reserve road capacity for
          your selected departure window.
        </p>
        {filteredBookings && filteredBookings.length === 0 && (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <p className="text-sm text-muted-foreground">{emptyMessage}</p>
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

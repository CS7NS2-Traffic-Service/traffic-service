import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatusBadge } from "@/components/StatusBadge"
import { fetchBookings, cancelBooking, type Booking } from "@/api/bookings"

const STAT_LABELS = ["PENDING", "APPROVED", "REJECTED", "CANCELLED"] as const

const STAT_COLORS: Record<string, string> = {
  PENDING: "text-yellow-600",
  APPROVED: "text-green-600",
  REJECTED: "text-red-600",
  CANCELLED: "text-gray-500",
}

function StatCard({ label, count }: { label: string; count: number }) {
  return (
    <Card>
      <CardContent className="pt-2">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className={`text-2xl font-bold ${STAT_COLORS[label] ?? ""}`}>{count}</p>
      </CardContent>
    </Card>
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

  const statusCounts = (bookings ?? []).reduce<Record<string, number>>((acc, b) => {
    acc[b.status] = (acc[b.status] ?? 0) + 1
    return acc
  }, {})

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
      {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
      {error && <p className="text-sm text-red-500">{(error as Error).message}</p>}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        <StatCard label="Total" count={bookings?.length ?? 0} />
        {STAT_LABELS.map((status) => (
          <StatCard key={status} label={status} count={statusCounts[status] ?? 0} />
        ))}
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Your Bookings</h2>
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

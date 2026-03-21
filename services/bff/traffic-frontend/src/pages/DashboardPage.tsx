import { useQuery } from "@tanstack/react-query"
import { Card, CardContent } from "@/components/ui/card"
import { fetchBookings, type Booking } from "@/api/bookings"

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

function RecentBookingsTable({ bookings }: { bookings: Booking[] }) {
  const recent = bookings.slice(0, 10)

  if (recent.length === 0) {
    return <p className="text-sm text-muted-foreground">No bookings yet.</p>
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="px-4 py-2 text-left font-medium">Route</th>
            <th className="px-4 py-2 text-left font-medium">Departure</th>
            <th className="px-4 py-2 text-left font-medium">Status</th>
            <th className="px-4 py-2 text-left font-medium">Created</th>
          </tr>
        </thead>
        <tbody>
          {recent.map((b) => (
            <tr key={b.booking_id} className="border-b last:border-0">
              <td className="px-4 py-2 font-mono text-xs">{b.route_id}</td>
              <td className="px-4 py-2">{new Date(b.departure_time).toLocaleString()}</td>
              <td className="px-4 py-2">
                <StatusPill status={b.status} />
              </td>
              <td className="px-4 py-2 text-muted-foreground">
                {new Date(b.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function StatusPill({ status }: { status: string }) {
  const colors: Record<string, string> = {
    PENDING: "bg-yellow-100 text-yellow-800",
    APPROVED: "bg-green-100 text-green-800",
    REJECTED: "bg-red-100 text-red-800",
    CANCELLED: "bg-gray-100 text-gray-800",
  }
  const color = colors[status] ?? "bg-gray-100 text-gray-800"

  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}>
      {status}
    </span>
  )
}

function DashboardPage() {
  const { data: bookings, isLoading, error } = useQuery({
    queryKey: ["bookings"],
    queryFn: fetchBookings,
    refetchInterval: 5000,
  })

  const statusCounts = (bookings ?? []).reduce<Record<string, number>>((acc, b) => {
    acc[b.status] = (acc[b.status] ?? 0) + 1
    return acc
  }, {})

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
      {error && <p className="text-sm text-red-500">{(error as Error).message}</p>}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total" count={bookings?.length ?? 0} />
        {STAT_LABELS.map((status) => (
          <StatCard key={status} label={status} count={statusCounts[status] ?? 0} />
        ))}
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Recent Bookings</h2>
        <RecentBookingsTable bookings={bookings ?? []} />
      </div>
    </div>
  )
}

export default DashboardPage

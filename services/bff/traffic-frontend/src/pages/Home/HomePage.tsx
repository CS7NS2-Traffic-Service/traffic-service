import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { buttonVariants } from "@/components/ui/button"
import { StatusBadge } from "@/components/StatusBadge"
import { fetchBookings } from "@/api/bookings"
import { fetchMessages } from "@/api/messages"
import { useDriverStore } from "@/stores/driverStore"
import { shortId, formatUTCToLocal } from "@/lib/datetime"

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-semibold">{value}</p>
      </CardContent>
    </Card>
  )
}

function HomePage() {
  const token = useDriverStore((state) => state.token)
  const driver = useDriverStore((state) => state.driver)

  const { data: bookings } = useQuery({
    queryKey: ["bookings"],
    queryFn: fetchBookings,
    enabled: !!token,
    refetchInterval: 10000,
  })

  const { data: messages } = useQuery({
    queryKey: ["messages"],
    queryFn: fetchMessages,
    enabled: !!token,
    refetchInterval: 10000,
  })

  if (!token) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-10">
        <h1 className="text-2xl font-semibold">Traffic Service</h1>
        <p className="mt-2 text-muted-foreground">
          Plan your route, submit booking requests, and track approval updates in real time.
        </p>
      </div>
    )
  }

  const total = bookings?.length ?? 0
  const pending = bookings?.filter((b) => b.status === "PENDING").length ?? 0
  const approved = bookings?.filter((b) => b.status === "APPROVED").length ?? 0
  const rejected = bookings?.filter((b) => b.status === "REJECTED").length ?? 0
  const unread = messages?.filter((m) => !m.is_read).length ?? 0

  const recent = [...(bookings ?? [])]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 3)

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">
            Welcome back{driver?.name ? `, ${driver.name.split(" ")[0]}` : ""}
          </h1>
          <p className="text-sm text-muted-foreground">
            Here's an overview of your bookings and inbox.
          </p>
        </div>
        <Link to="/routes" className={buttonVariants()}>Book a route</Link>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <StatCard label="Total" value={total} />
        <StatCard label="Pending" value={pending} />
        <StatCard label="Approved" value={approved} />
        <StatCard label="Rejected" value={rejected} />
        <StatCard label="Unread Inbox" value={unread} />
      </div>

      {recent.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold">Recent bookings</h2>
            <Link to="/bookings" className="text-sm text-primary hover:underline">
              View all →
            </Link>
          </div>
          <div className="space-y-2">
            {recent.map((b) => (
              <Card key={b.booking_id}>
                <CardContent className="flex items-center justify-between py-3">
                  <div className="space-y-0.5">
                    <p className="text-sm font-medium">Route {shortId(b.route_id)}</p>
                    <p className="text-xs text-muted-foreground">
                      Departure: {formatUTCToLocal(b.departure_time)}
                    </p>
                  </div>
                  <StatusBadge status={b.status} />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default HomePage

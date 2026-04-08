import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { buttonVariants } from "@/components/ui/button"
import { StatusBadge } from "@/components/StatusBadge"
import { fetchBookings } from "@/api/bookings"
import { fetchMessages } from "@/api/messages"
import { useDriverStore } from "@/stores/driverStore"
import { shortId, formatUTCToLocal } from "@/lib/datetime"
import { cn } from "@/lib/utils"

const STAT_TONES: Record<string, string> = {
  Total: "text-foreground",
  Pending: "text-yellow-600",
  Approved: "text-green-600",
  Rejected: "text-red-600",
  "Unread Inbox": "text-primary",
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Card className="shadow-sm">
      <CardContent className="space-y-1">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className={cn("text-2xl font-semibold leading-none", STAT_TONES[label])}>{value}</p>
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
      <div className="mx-auto max-w-5xl px-4 py-10">
        <Card className="shadow-sm">
          <CardContent className="flex flex-col gap-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Distributed Traffic Service</p>
              <h1 className="text-2xl font-semibold">Plan routes with async capacity checks</h1>
              <p className="max-w-2xl text-sm text-muted-foreground">
                Submit booking requests, track approvals, and receive inbox updates when route
                capacity is assessed.
              </p>
            </div>
            <div className="flex gap-2">
              <Link to="/login" className={buttonVariants()}>Sign in</Link>
              <Link to="/register" className={buttonVariants({ variant: "outline" })}>Create account</Link>
            </div>
          </CardContent>
        </Card>
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

  const recentMessages = [...(messages ?? [])]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 3)

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-6">
      <div className="rounded-2xl border bg-card p-5 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Dashboard</p>
            <h1 className="text-2xl font-semibold">
              Welcome back{driver?.name ? `, ${driver.name.split(" ")[0]}` : ""}
            </h1>
            <p className="text-sm text-muted-foreground">
              Track bookings, inbox updates, and route capacity decisions.
            </p>
          </div>
          <div className="flex gap-2">
            <Link to="/routes" className={buttonVariants()}>Book a route</Link>
            <Link to="/inbox" className={buttonVariants({ variant: "outline" })}>Inbox</Link>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <StatCard label="Total" value={total} />
        <StatCard label="Pending" value={pending} />
        <StatCard label="Approved" value={approved} />
        <StatCard label="Rejected" value={rejected} />
        <StatCard label="Unread Inbox" value={unread} />
      </div>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
        <Card className="shadow-sm">
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold">Recent bookings</h2>
              <Link to="/bookings" className="text-sm text-primary hover:underline">
                View all →
              </Link>
            </div>
            {recent.length === 0 ? (
              <div className="rounded-lg border border-dashed p-6 text-center">
                <p className="text-sm text-muted-foreground">No bookings yet.</p>
                <Link to="/routes" className="mt-1 inline-block text-sm font-medium text-primary hover:underline">
                  Book a route →
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {recent.map((booking) => (
                  <div
                    key={booking.booking_id}
                    className="flex items-center justify-between rounded-lg bg-muted/40 px-3 py-2"
                  >
                    <div className="space-y-0.5">
                      <p className="text-sm font-medium">Route {shortId(booking.route_id)}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatUTCToLocal(booking.departure_time)}
                      </p>
                    </div>
                    <StatusBadge status={booking.status} />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold">Inbox updates</h2>
              <Link to="/inbox" className="text-sm text-primary hover:underline">
                Open inbox →
              </Link>
            </div>
            {recentMessages.length === 0 ? (
              <p className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                No inbox updates yet.
              </p>
            ) : (
              <div className="space-y-2">
                {recentMessages.map((message) => (
                  <div
                    key={message.message_id}
                    className="rounded-lg bg-muted/40 px-3 py-2"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-xs text-muted-foreground">Ref {shortId(message.booking_id)}</p>
                      {!message.is_read && (
                        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                          Unread
                        </span>
                      )}
                    </div>
                    <p className="mt-1 line-clamp-2 text-sm">{message.content}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default HomePage

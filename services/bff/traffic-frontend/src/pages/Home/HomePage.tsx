import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { fetchBookings } from "@/api/bookings"
import { fetchMessages } from "@/api/messages"
import { useDriverStore } from "@/stores/driverStore"

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

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Current booking pipeline and inbox overview.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <StatCard label="Total" value={total} />
        <StatCard label="Pending" value={pending} />
        <StatCard label="Approved" value={approved} />
        <StatCard label="Rejected" value={rejected} />
        <StatCard label="Unread Inbox" value={unread} />
      </div>
    </div>
  )
}

export default HomePage

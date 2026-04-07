import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { fetchMessages, markAsRead, type Message } from "@/api/messages"
import { shortId } from "@/lib/datetime"

function MessageItem({ message, onMarkRead }: {
  message: Message
  onMarkRead: (id: string) => void
}) {
  return (
    <button
      type="button"
      className={`w-full text-left rounded-lg border p-4 transition-colors hover:bg-muted/50 ${
        message.is_read ? "" : "border-l-4 border-l-primary"
      }`}
      onClick={() => {
        if (!message.is_read) onMarkRead(message.message_id)
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <p className={`text-sm ${message.is_read ? "text-muted-foreground" : "font-bold"}`}>
            {message.content}
          </p>
          <p className="text-xs text-muted-foreground">
            Ref: {shortId(message.booking_id)}
          </p>
        </div>
        <p className="shrink-0 text-xs text-muted-foreground">
          {new Date(message.created_at).toLocaleString()}
        </p>
      </div>
    </button>
  )
}

function InboxPage() {
  const queryClient = useQueryClient()

  const { data: messages, isLoading, error } = useQuery({
    queryKey: ["messages"],
    queryFn: fetchMessages,
    refetchInterval: 10000,
  })

  const { mutate: markRead } = useMutation({
    mutationFn: markAsRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["messages"] }),
  })

  const unreadCount = messages?.filter((m) => !m.is_read).length ?? 0

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle>
            Inbox
            {unreadCount > 0 && (
              <span className="ml-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-xs font-medium text-primary-foreground">
                {unreadCount}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {isLoading && <p className="text-sm text-muted-foreground">Loading messages...</p>}
          {error && <p className="text-sm text-red-500">{(error as Error).message}</p>}
          {messages && messages.length === 0 && (
            <p className="text-sm text-muted-foreground">Your inbox is empty.</p>
          )}
          {messages?.map((message) => (
            <MessageItem
              key={message.message_id}
              message={message}
              onMarkRead={markRead}
            />
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

export default InboxPage

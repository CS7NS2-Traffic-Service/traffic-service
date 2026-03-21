import { authHeaders, handleResponse } from "@/api/client"

export type Message = {
  message_id: string
  driver_id: string
  booking_id: string
  content: string
  is_read: boolean
  created_at: string
}

type FetchMessagesResponse = {
  messages: Message[]
}

export async function fetchMessages(): Promise<Message[]> {
  const response = await fetch("/api/messaging/messages", {
    headers: authHeaders(),
  })
  const data = await handleResponse<FetchMessagesResponse>(response, "Failed to fetch messages")
  return data.messages
}

export async function markAsRead(messageId: string): Promise<void> {
  const response = await fetch(`/api/messaging/messages/${messageId}/read`, {
    method: "PUT",
    headers: authHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to mark message as read" }))
    throw new Error(error.detail ?? "Failed to mark message as read")
  }
}

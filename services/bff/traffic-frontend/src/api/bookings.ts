import { authHeaders, handleResponse } from "@/api/client"

export type Booking = {
  booking_id: string
  driver_id: string
  route_id: string
  departure_time: string
  estimated_arrival: string | null
  status: string
  created_at: string
  expires_at: string | null
}

export type CreateBookingDto = {
  route_id: string
  departure_time: string
  estimated_arrival?: string
}

export async function fetchBookings(): Promise<Booking[]> {
  const response = await fetch("/api/booking/bookings", {
    headers: authHeaders(),
  })
  return handleResponse<Booking[]>(response, "Failed to fetch bookings")
}

export async function createBooking(data: CreateBookingDto): Promise<Booking> {
  const response = await fetch("/api/booking/bookings", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<Booking>(response, "Failed to create booking")
}

export async function cancelBooking(bookingId: string): Promise<void> {
  const response = await fetch(`/api/booking/bookings/${bookingId}`, {
    method: "DELETE",
    headers: authHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to cancel booking" }))
    throw new Error(error.detail ?? "Failed to cancel booking")
  }
}

package handler

import (
	"time"

	"github.com/google/uuid"
)

type BookingResponseDto struct {
	BookingID        uuid.UUID  `json:"booking_id"`
	DriverID         uuid.UUID  `json:"driver_id"`
	RouteID          uuid.UUID  `json:"route_id"`
	DepartureTime    time.Time  `json:"departure_time"`
	EstimatedArrival *time.Time `json:"estimated_arrival"`
	Status           string     `json:"status"`
	CreatedAt        time.Time  `json:"created_at"`
	ExpiresAt        *time.Time `json:"expires_at"`
}

type CreateBookingRequestDto struct {
	RouteID          uuid.UUID  `json:"route_id"`
	DepartureTime    time.Time  `json:"departure_time"`
	EstimatedArrival *time.Time `json:"estimated_arrival"`
}

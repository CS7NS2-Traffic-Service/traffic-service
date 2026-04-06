package domain

import "time"

type Event interface {
	Stream() string
}

type EventEnvelope struct {
	EventID       string    `json:"event_id"`
	CorrelationID string    `json:"correlation_id"`
	EventType     string    `json:"event_type"`
	CreatedAt     time.Time `json:"created_at"`
	Data          any       `json:"data"`
}

type BookingCreatedEvent struct {
	BookingID     string `json:"booking_id"`
	DriverID      string `json:"driver_id"`
	RouteID       string `json:"route_id"`
	DepartureTime string `json:"departure_time"`
}

func (e BookingCreatedEvent) Stream() string {
	return "booking.created"
}

type BookingUpdatedEvent struct {
	BookingID string `json:"booking_id"`
	DriverID  string `json:"driver_id"`
	Status    string `json:"status"`
}

func (e BookingUpdatedEvent) Stream() string {
	return "booking.updated"
}

type RouteAssessedEvent struct {
	BookingID         string `json:"booking_id"`
	RouteID           string `json:"route_id"`
	SegmentsAvailable bool   `json:"segments_available"`
}

func (e RouteAssessedEvent) Stream() string {
	return "route.assessed"
}

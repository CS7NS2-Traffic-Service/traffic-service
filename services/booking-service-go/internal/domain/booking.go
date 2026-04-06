package domain

import (
	"errors"
	"time"

	"github.com/google/uuid"
)

var ErrInvalidTransition = errors.New("invalid transition")

type Booking struct {
	BookingID        uuid.UUID
	DriverID         uuid.UUID
	RouteID          uuid.UUID
	DepartureTime    time.Time
	EstimatedArrival *time.Time
	Status           BookingStatus
	CreatedAt        time.Time
	ExpiresAt        *time.Time
}

func (b *Booking) CanTransition(to BookingStatus) bool {
	switch b.Status {
	case StatusPending:
		return to == StatusApproved || to == StatusCancelled || to == StatusExpired || to == StatusRejected
	case StatusApproved:
		return to == StatusCancelled || to == StatusExpired
	}
	return false
}

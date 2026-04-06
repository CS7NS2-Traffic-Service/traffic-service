package application

import (
	"context"

	"github.com/google/uuid"
	"github.com/lukaslinss98/booking-service/internal/domain"
)

type BookingRepository interface {
	Create(ctx context.Context, booking *domain.Booking) (*domain.Booking, error)
	GetAll(ctx context.Context, driverID uuid.UUID) ([]*domain.Booking, error)
	GetByID(ctx context.Context, bookingID uuid.UUID) (*domain.Booking, error)
	Cancel(ctx context.Context, bookingID uuid.UUID, driverID uuid.UUID) (*domain.Booking, error)
	UpdateStatus(ctx context.Context, bookingID uuid.UUID, status domain.BookingStatus) (*domain.Booking, error)
	FindExpired(ctx context.Context) ([]*domain.Booking, error)
}

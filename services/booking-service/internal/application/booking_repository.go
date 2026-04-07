package application

import (
	"context"

	"github.com/google/uuid"
	"github.com/lukaslinss98/booking-service/internal/domain"
)

type EnvelopeBuilder func(booking *domain.Booking) *domain.EventEnvelope

type BookingRepository interface {
	Create(ctx context.Context, booking *domain.Booking, envelope *domain.EventEnvelope) (*domain.Booking, error)
	GetAll(ctx context.Context, driverID uuid.UUID) ([]*domain.Booking, error)
	GetByID(ctx context.Context, bookingID uuid.UUID, driverID uuid.UUID) (*domain.Booking, error)
	Cancel(ctx context.Context, bookingID uuid.UUID, driverID uuid.UUID, envelope *domain.EventEnvelope) (*domain.Booking, error)
	UpdateStatus(ctx context.Context, bookingID uuid.UUID, status domain.BookingStatus, buildEnvelope EnvelopeBuilder) (*domain.Booking, error)
	FindExpired(ctx context.Context) ([]*domain.Booking, error)
	IsEventProcessed(ctx context.Context, eventID string, consumer string) (bool, error)
	MarkEventProcessed(ctx context.Context, eventID string, consumer string, stream string) (bool, error)
}

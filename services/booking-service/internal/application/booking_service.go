package application

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
	"github.com/lukaslinss98/booking-service/internal/domain"
)

type BookingService struct {
	repository BookingRepository
}

func NewBookingService(br BookingRepository) *BookingService {
	return &BookingService{
		repository: br,
	}
}

func (s *BookingService) HandleRouteAssessed(ctx context.Context, event domain.RouteAssessedEvent) error {
	bookingID, err := uuid.Parse(event.BookingID)
	if err != nil {
		return err
	}

	status := domain.StatusRejected
	if event.SegmentsAvailable {
		status = domain.StatusApproved
	}

	booking, err := s.repository.UpdateStatus(ctx, bookingID, status, func(b *domain.Booking) *domain.EventEnvelope {
		e := domain.NewEventEnvelope(ctx, domain.BookingUpdatedEvent{
			BookingID: b.BookingID.String(),
			DriverID:  b.DriverID.String(),
			Status:    string(status),
		})
		return &e
	})
	if err != nil {
		return err
	}
	if booking == nil {
		return fmt.Errorf("booking %v not found", bookingID)
	}

	log.Printf("updated status of booking %v to %v", bookingID, status)
	return nil
}

func (s *BookingService) StartExpiryLoop(ctx context.Context) {
	log.Println("booking expiry loop started (every 30s)")
	for {
		if ctx.Err() != nil {
			return
		}
		if err := s.ExpireBookings(ctx); err != nil {
			log.Printf("expiry loop error: %v", err)
		}
		select {
		case <-ctx.Done():
			return
		case <-time.After(30 * time.Second):
		}
	}
}

func (s *BookingService) ExpireBookings(ctx context.Context) error {
	expired, err := s.repository.FindExpired(ctx)
	if err != nil {
		return err
	}

	for _, booking := range expired {
		updated, err := s.repository.UpdateStatus(ctx, booking.BookingID, domain.StatusExpired, func(b *domain.Booking) *domain.EventEnvelope {
			e := domain.NewEventEnvelope(ctx, domain.BookingUpdatedEvent{
				BookingID: b.BookingID.String(),
				DriverID:  b.DriverID.String(),
				Status:    string(domain.StatusExpired),
			})
			return &e
		})
		if err != nil {
			log.Printf("failed to expire booking %v: %v", booking.BookingID, err)
			continue
		}
		if updated == nil {
			continue
		}
		log.Printf("expired booking %v", booking.BookingID)
	}

	return nil
}

func (s *BookingService) CreateBooking(ctx context.Context, booking *domain.Booking) (*domain.Booking, error) {
	booking.BookingID = uuid.New()

	event := domain.BookingCreatedEvent{
		BookingID:     booking.BookingID.String(),
		DriverID:      booking.DriverID.String(),
		RouteID:       booking.RouteID.String(),
		DepartureTime: booking.DepartureTime.UTC().Format(time.RFC3339),
	}
	envelope := domain.NewEventEnvelope(ctx, event)

	createdBooking, err := s.repository.Create(ctx, booking, &envelope)
	if err != nil {
		return nil, err
	}

	return createdBooking, nil
}

func (s *BookingService) GetAll(ctx context.Context, driverID uuid.UUID) ([]*domain.Booking, error) {
	return s.repository.GetAll(ctx, driverID)
}

func (s *BookingService) GetByID(ctx context.Context, bookingID uuid.UUID, driverID uuid.UUID) (*domain.Booking, error) {
	return s.repository.GetByID(ctx, bookingID, driverID)
}

func (s *BookingService) CancelBooking(ctx context.Context, bookingID uuid.UUID, driverID uuid.UUID) (*domain.Booking, error) {
	booking, err := s.repository.GetByID(ctx, bookingID, driverID)
	if err != nil {
		return nil, err
	}
	if booking == nil {
		return nil, fmt.Errorf("could not find booking for bookingID %v", bookingID)
	}

	if !booking.CanTransition(domain.StatusCancelled) {
		return nil, domain.ErrInvalidTransition
	}

	event := domain.BookingUpdatedEvent{
		BookingID: bookingID.String(),
		DriverID:  driverID.String(),
		Status:    string(domain.StatusCancelled),
	}
	envelope := domain.NewEventEnvelope(ctx, event)

	cancelledBooking, err := s.repository.Cancel(ctx, bookingID, driverID, &envelope)
	if err != nil {
		return nil, err
	}

	return cancelledBooking, nil
}

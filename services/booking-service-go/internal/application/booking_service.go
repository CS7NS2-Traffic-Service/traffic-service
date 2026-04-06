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
	repository     BookingRepository
	eventPublisher EventPublisher
}

func NewBookingService(br BookingRepository, ep EventPublisher) *BookingService {
	return &BookingService{
		repository:     br,
		eventPublisher: ep,
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
	booking, err := s.repository.UpdateStatus(ctx, bookingID, status)

	if err != nil {
		return err
	}

	if booking == nil {
		return fmt.Errorf("booking %v not found", bookingID)
	}

	log.Printf("updated status of booking %v to %v", bookingID, status)

	updatedEvent := domain.BookingUpdatedEvent{
		BookingID: bookingID.String(),
		DriverID:  booking.DriverID.String(),
		Status:    string(status),
	}

	if err := s.eventPublisher.Publish(ctx, updatedEvent); err != nil {
		return err
	}

	return nil
}

func (s *BookingService) StartExpiryLoop(ctx context.Context) {
	log.Println("booking expiry loop started (every 30s)")
	for {
		if err := s.ExpireBookings(ctx); err != nil {
			log.Printf("expiry loop error: %v", err)
		}
		time.Sleep(30 * time.Second)
	}
}

func (s *BookingService) ExpireBookings(ctx context.Context) error {
	expired, err := s.repository.FindExpired(ctx)
	if err != nil {
		return err
	}

	for _, booking := range expired {
		updated, err := s.repository.UpdateStatus(ctx, booking.BookingID, domain.StatusExpired)
		if err != nil {
			log.Printf("failed to expire booking %v: %v", booking.BookingID, err)
			continue
		}
		if updated == nil {
			continue
		}

		event := domain.BookingUpdatedEvent{
			BookingID: updated.BookingID.String(),
			DriverID:  updated.DriverID.String(),
			Status:    string(domain.StatusExpired),
		}
		if err := s.eventPublisher.Publish(ctx, event); err != nil {
			log.Printf("failed to publish expiry event for booking %v: %v", booking.BookingID, err)
		}
		log.Printf("expired booking %v", booking.BookingID)
	}

	return nil
}

func (s *BookingService) CreateBooking(ctx context.Context, booking *domain.Booking) (*domain.Booking, error) {
	createdBooking, err := s.repository.Create(ctx, booking)
	if err != nil {
		return nil, err
	}

	event := domain.BookingCreatedEvent{
		BookingID:     createdBooking.BookingID.String(),
		DriverID:      createdBooking.DriverID.String(),
		RouteID:       createdBooking.RouteID.String(),
		DepartureTime: createdBooking.DepartureTime.UTC().Format(time.RFC3339),
	}

	if err := s.eventPublisher.Publish(ctx, event); err != nil {
		return nil, err
	}

	return booking, nil
}

func (s *BookingService) GetAll(ctx context.Context, driverID uuid.UUID) ([]*domain.Booking, error) {
	return s.repository.GetAll(ctx, driverID)
}

func (s *BookingService) GetByID(ctx context.Context, driverID uuid.UUID) (*domain.Booking, error) {
	return s.repository.GetByID(ctx, driverID)
}

func (s *BookingService) CancelBooking(ctx context.Context, bookingID uuid.UUID, driverID uuid.UUID) (*domain.Booking, error) {
	booking, err := s.repository.GetByID(ctx, bookingID)

	if err != nil {
		return nil, err
	}
	if booking == nil {
		return nil, fmt.Errorf("could not find booking for bookingID %v", bookingID)
	}

	canTransition := booking.CanTransition(domain.StatusCancelled)

	if !canTransition {
		return nil, domain.ErrInvalidTransition
	}

	cancledBooking, err := s.repository.Cancel(ctx, bookingID, driverID)

	if err != nil {
		return nil, err
	}

	event := domain.BookingUpdatedEvent{
		BookingID: cancledBooking.BookingID.String(),
		DriverID:  cancledBooking.DriverID.String(),
		Status:    string(cancledBooking.Status),
	}

	if err := s.eventPublisher.Publish(ctx, event); err != nil {
		return nil, err
	}

	return cancledBooking, nil
}

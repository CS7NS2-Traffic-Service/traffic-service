package handler

import (
	"encoding/json"
	"errors"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
	"github.com/lukaslinss98/booking-service/internal/application"
	"github.com/lukaslinss98/booking-service/internal/domain"
)

type BookingHandler struct {
	service *application.BookingService
}

func NewBookingHandler(service *application.BookingService) *BookingHandler {
	return &BookingHandler{
		service: service,
	}
}

func (h *BookingHandler) CancelBooking(w http.ResponseWriter, r *http.Request) {
	ctx := domain.ContextWithCorrelationID(r.Context(), r.Header.Get("X-Correlation-ID"))

	bookingID, err := uuid.Parse(chi.URLParam(r, "booking_id"))
	if err != nil {
		http.Error(w, "bookingID is not a valid UUID", http.StatusBadRequest)
		return
	}

	driverID, err := uuid.Parse(r.Header.Get("X-Driver-ID"))
	if err != nil {
		http.Error(w, "driverID is not a valid UUID", http.StatusBadRequest)
		return
	}

	booking, err := h.service.CancelBooking(ctx, bookingID, driverID)

	if err != nil {
		if errors.Is(err, domain.ErrInvalidTransition) {
			http.Error(w, err.Error(), http.StatusConflict)
			return
		}
		http.Error(w, "encountered error while canceling booking", http.StatusInternalServerError)
		return
	}

	if booking == nil {
		http.Error(w, "booking not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	response := h.toResponse(booking)
	json.NewEncoder(w).Encode(response)

}

func (h *BookingHandler) GetBooking(w http.ResponseWriter, r *http.Request) {
	ctx := domain.ContextWithCorrelationID(r.Context(), r.Header.Get("X-Correlation-ID"))

	bookingID, err := uuid.Parse(chi.URLParam(r, "booking_id"))

	if err != nil {
		http.Error(w, "bookingID is not a valid UUID", http.StatusBadRequest)
		return
	}

	driverID, err := uuid.Parse(r.Header.Get("X-Driver-ID"))
	if err != nil {
		http.Error(w, "driverID is not a valid UUID", http.StatusBadRequest)
		return
	}

	booking, err := h.service.GetByID(ctx, bookingID, driverID)

	if err != nil {
		http.Error(w, "encountered error while fetching booking", http.StatusInternalServerError)
		return
	}

	if booking == nil {
		http.Error(w, "booking not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	response := h.toResponse(booking)
	json.NewEncoder(w).Encode(response)

}

func (h *BookingHandler) CreateBooking(w http.ResponseWriter, r *http.Request) {
	ctx := domain.ContextWithCorrelationID(r.Context(), r.Header.Get("X-Correlation-ID"))

	driverID, err := uuid.Parse(r.Header.Get("X-Driver-ID"))
	if err != nil {
		http.Error(w, "driverID is not a valid UUID", http.StatusBadRequest)
		return
	}

	var req CreateBookingRequestDto
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if req.DepartureTime.Before(time.Now().UTC()) {
		http.Error(w, "departure_time must be in the future", http.StatusBadRequest)
		return
	}

	expiresAt := req.DepartureTime
	if req.EstimatedArrival != nil {
		expiresAt = *req.EstimatedArrival
	}
	expiresAtUTC := expiresAt.UTC()

	booking := &domain.Booking{
		DriverID:         driverID,
		RouteID:          req.RouteID,
		DepartureTime:    req.DepartureTime.UTC(),
		EstimatedArrival: req.EstimatedArrival,
		Status:           domain.StatusPending,
		ExpiresAt:        &expiresAtUTC,
	}
	if booking.EstimatedArrival != nil {
		estimatedArrivalUTC := booking.EstimatedArrival.UTC()
		booking.EstimatedArrival = &estimatedArrivalUTC
	}

	created, err := h.service.CreateBooking(ctx, booking)
	if err != nil {
		http.Error(w, "encountered error while creating booking", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(h.toResponse(created))
}

func (h *BookingHandler) ListBookings(w http.ResponseWriter, r *http.Request) {
	ctx := domain.ContextWithCorrelationID(r.Context(), r.Header.Get("X-Correlation-ID"))

	driverIDHeader := r.Header.Get("X-Driver-ID")
	driverID, err := uuid.Parse(driverIDHeader)

	if err != nil {
		http.Error(w, "driverId is not a valid UUID", http.StatusBadRequest)
		return
	}

	bookings, err := h.service.GetAll(ctx, driverID)

	if err != nil {
		http.Error(w, "no bookings found for given driverID", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	response := h.toResponses(bookings)
	if response == nil {
		response = []BookingResponseDto{}
	}
	json.NewEncoder(w).Encode(response)

}

func (h BookingHandler) toResponses(bookings []*domain.Booking) []BookingResponseDto {
	var responses []BookingResponseDto
	for _, booking := range bookings {
		response := h.toResponse(booking)
		responses = append(responses, response)

	}
	return responses

}

func (h BookingHandler) toResponse(booking *domain.Booking) BookingResponseDto {
	return BookingResponseDto{
		BookingID:        booking.BookingID,
		DriverID:         booking.DriverID,
		RouteID:          booking.RouteID,
		DepartureTime:    booking.DepartureTime,
		EstimatedArrival: booking.EstimatedArrival,
		Status:           string(booking.Status),
		CreatedAt:        booking.CreatedAt,
		ExpiresAt:        booking.ExpiresAt,
	}

}

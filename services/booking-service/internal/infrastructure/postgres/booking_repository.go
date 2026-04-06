package postgres

import (
	"context"
	"errors"
	"log"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/lukaslinss98/booking-service/internal/domain"
)

type BookingRepository struct {
	pool *pgxpool.Pool
}

func NewBookingRepository(pool *pgxpool.Pool) *BookingRepository {
	return &BookingRepository{
		pool: pool,
	}
}

func (r *BookingRepository) Create(ctx context.Context, booking *domain.Booking) (*domain.Booking, error) {
	sql := `
		INSERT INTO bookings (driver_id, route_id, departure_time, estimated_arrival, status, expires_at)
	  VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING booking_id, created_at
	`
	row := r.pool.QueryRow(
		ctx,
		sql,
		booking.DriverID,
		booking.RouteID,
		booking.DepartureTime,
		booking.EstimatedArrival,
		booking.Status,
		booking.ExpiresAt,
	)

	err := row.Scan(&booking.BookingID, &booking.CreatedAt)

	if err != nil {
		log.Printf("failed to create booking: %v", err)
		return nil, err
	}
	return booking, nil
}

func (r *BookingRepository) GetAll(ctx context.Context, driverID uuid.UUID) ([]*domain.Booking, error) {
	sql := `
      SELECT booking_id, driver_id, route_id, departure_time,
   estimated_arrival, status, created_at, expires_at
      FROM bookings
			WHERE driver_id = $1
  `
	rows, err := r.pool.Query(ctx, sql, driverID)

	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var bookings []*domain.Booking
	for rows.Next() {
		var booking domain.Booking
		err := rows.Scan(
			&booking.BookingID,
			&booking.DriverID,
			&booking.RouteID,
			&booking.DepartureTime,
			&booking.EstimatedArrival,
			&booking.Status,
			&booking.CreatedAt,
			&booking.ExpiresAt,
		)

		if err != nil {
			return nil, err
		}
		bookings = append(bookings, &booking)
	}

	return bookings, rows.Err()
}

func (r *BookingRepository) GetByID(ctx context.Context, bookingID uuid.UUID) (*domain.Booking, error) {
	sql := `
      SELECT booking_id, driver_id, route_id, departure_time,
   estimated_arrival, status, created_at, expires_at
      FROM bookings
      WHERE booking_id = $1
  `
	row := r.pool.QueryRow(ctx, sql, bookingID)

	var booking domain.Booking

	err := row.Scan(
		&booking.BookingID,
		&booking.DriverID,
		&booking.RouteID,
		&booking.DepartureTime,
		&booking.EstimatedArrival,
		&booking.Status,
		&booking.CreatedAt,
		&booking.ExpiresAt,
	)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}
		return nil, err
	}

	return &booking, nil
}

func (r *BookingRepository) UpdateStatus(ctx context.Context, bookingID uuid.UUID, status domain.BookingStatus) (*domain.Booking, error) {
	sql := `
		UPDATE bookings
		SET status = $1
		WHERE booking_id = $2
		RETURNING booking_id, driver_id, route_id, departure_time, estimated_arrival, status, created_at, expires_at
	`
	row := r.pool.QueryRow(ctx, sql, status, bookingID)

	var booking domain.Booking
	err := row.Scan(
		&booking.BookingID,
		&booking.DriverID,
		&booking.RouteID,
		&booking.DepartureTime,
		&booking.EstimatedArrival,
		&booking.Status,
		&booking.CreatedAt,
		&booking.ExpiresAt,
	)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}
		return nil, err
	}

	return &booking, nil
}

func (r *BookingRepository) Cancel(ctx context.Context, bookingID uuid.UUID, driverID uuid.UUID) (*domain.Booking, error) {
	sql := `
		UPDATE bookings
		SET status = $1
		WHERE booking_id = $2 AND driver_id = $3
		RETURNING booking_id, driver_id, route_id, departure_time, estimated_arrival, status, created_at, expires_at
	`
	row := r.pool.QueryRow(ctx, sql, domain.StatusCancelled, bookingID, driverID)

	var booking domain.Booking
	err := row.Scan(
		&booking.BookingID,
		&booking.DriverID,
		&booking.RouteID,
		&booking.DepartureTime,
		&booking.EstimatedArrival,
		&booking.Status,
		&booking.CreatedAt,
		&booking.ExpiresAt,
	)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}
		return nil, err
	}

	return &booking, nil
}

func (r *BookingRepository) FindExpired(ctx context.Context) ([]*domain.Booking, error) {
	sql := `
		SELECT booking_id, driver_id, route_id, departure_time,
		estimated_arrival, status, created_at, expires_at
		FROM bookings
		WHERE departure_time < NOW()
		AND status IN ($1, $2)
	`
	rows, err := r.pool.Query(ctx, sql, domain.StatusPending, domain.StatusApproved)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var bookings []*domain.Booking
	for rows.Next() {
		var booking domain.Booking
		err := rows.Scan(
			&booking.BookingID,
			&booking.DriverID,
			&booking.RouteID,
			&booking.DepartureTime,
			&booking.EstimatedArrival,
			&booking.Status,
			&booking.CreatedAt,
			&booking.ExpiresAt,
		)
		if err != nil {
			return nil, err
		}
		bookings = append(bookings, &booking)
	}

	return bookings, rows.Err()
}

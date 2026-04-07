package postgres

import (
	"context"
	"encoding/json"
	"errors"
	"log"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/lukaslinss98/booking-service/internal/application"
	"github.com/lukaslinss98/booking-service/internal/domain"
)

type BookingRepository struct {
	pool   *pgxpool.Pool
	outbox *OutboxRepository
}

func NewBookingRepository(pool *pgxpool.Pool, outbox *OutboxRepository) *BookingRepository {
	return &BookingRepository{
		pool:   pool,
		outbox: outbox,
	}
}

func (r *BookingRepository) withTx(ctx context.Context, fn func(tx pgx.Tx) error) error {
	tx, err := r.pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	if err := fn(tx); err != nil {
		return err
	}
	return tx.Commit(ctx)
}

func (r *BookingRepository) insertOutbox(ctx context.Context, db DBTX, envelope *domain.EventEnvelope) error {
	payload, err := json.Marshal(envelope)
	if err != nil {
		return err
	}
	return r.outbox.Insert(ctx, db, envelope.EventType, payload)
}

func (r *BookingRepository) Create(ctx context.Context, booking *domain.Booking, envelope *domain.EventEnvelope) (*domain.Booking, error) {
	err := r.withTx(ctx, func(tx pgx.Tx) error {
		sql := `
			INSERT INTO bookings (booking_id, driver_id, route_id, departure_time, estimated_arrival, status, expires_at)
			VALUES ($1, $2, $3, $4, $5, $6, $7)
			RETURNING created_at
		`
		row := tx.QueryRow(ctx, sql,
			booking.BookingID,
			booking.DriverID,
			booking.RouteID,
			booking.DepartureTime,
			booking.EstimatedArrival,
			booking.Status,
			booking.ExpiresAt,
		)
		if err := row.Scan(&booking.CreatedAt); err != nil {
			log.Printf("failed to create booking: %v", err)
			return err
		}
		if envelope != nil {
			return r.insertOutbox(ctx, tx, envelope)
		}
		return nil
	})
	if err != nil {
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

func (r *BookingRepository) GetByID(ctx context.Context, bookingID uuid.UUID, driverID uuid.UUID) (*domain.Booking, error) {
	sql := `
		SELECT booking_id, driver_id, route_id, departure_time,
			estimated_arrival, status, created_at, expires_at
		FROM bookings
		WHERE booking_id = $1 AND driver_id = $2
	`
	row := r.pool.QueryRow(ctx, sql, bookingID, driverID)

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

func (r *BookingRepository) UpdateStatus(ctx context.Context, bookingID uuid.UUID, status domain.BookingStatus, buildEnvelope application.EnvelopeBuilder) (*domain.Booking, error) {
	var booking domain.Booking

	err := r.withTx(ctx, func(tx pgx.Tx) error {
		sql := `
			UPDATE bookings
			SET status = $1
			WHERE booking_id = $2
			RETURNING booking_id, driver_id, route_id, departure_time, estimated_arrival, status, created_at, expires_at
		`
		row := tx.QueryRow(ctx, sql, status, bookingID)
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
			return err
		}
		if buildEnvelope != nil {
			envelope := buildEnvelope(&booking)
			if envelope != nil {
				return r.insertOutbox(ctx, tx, envelope)
			}
		}
		return nil
	})
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}
		return nil, err
	}
	return &booking, nil
}

func (r *BookingRepository) Cancel(ctx context.Context, bookingID uuid.UUID, driverID uuid.UUID, envelope *domain.EventEnvelope) (*domain.Booking, error) {
	var booking domain.Booking

	err := r.withTx(ctx, func(tx pgx.Tx) error {
		sql := `
			UPDATE bookings
			SET status = $1
			WHERE booking_id = $2 AND driver_id = $3
			RETURNING booking_id, driver_id, route_id, departure_time, estimated_arrival, status, created_at, expires_at
		`
		row := tx.QueryRow(ctx, sql, domain.StatusCancelled, bookingID, driverID)
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
			return err
		}
		if envelope != nil {
			return r.insertOutbox(ctx, tx, envelope)
		}
		return nil
	})
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

func (r *BookingRepository) IsEventProcessed(ctx context.Context, eventID string, consumer string) (bool, error) {
	sql := `
		SELECT 1
		FROM processed_events
		WHERE event_id = $1 AND consumer_name = $2
		LIMIT 1
	`
	var marker int
	err := r.pool.QueryRow(ctx, sql, eventID, consumer).Scan(&marker)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return false, nil
		}
		return false, err
	}
	return true, nil
}

func (r *BookingRepository) MarkEventProcessed(ctx context.Context, eventID string, consumer string, stream string) (bool, error) {
	sql := `
		INSERT INTO processed_events (event_id, consumer_name, stream_name)
		VALUES ($1, $2, $3)
		ON CONFLICT (event_id, consumer_name) DO NOTHING
	`
	result, err := r.pool.Exec(ctx, sql, eventID, consumer, stream)
	if err != nil {
		return false, err
	}
	return result.RowsAffected() == 1, nil
}

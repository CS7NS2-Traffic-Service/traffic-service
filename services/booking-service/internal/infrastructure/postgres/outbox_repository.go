package postgres

import (
	"context"

)

type OutboxEvent struct {
	ID      int64
	Stream  string
	Payload []byte
}

type OutboxRepository struct{}

func NewOutboxRepository() *OutboxRepository {
	return &OutboxRepository{}
}

func (r *OutboxRepository) Insert(ctx context.Context, db DBTX, stream string, payload []byte) error {
	_, err := db.Exec(ctx,
		`INSERT INTO outbox_events (stream, payload) VALUES ($1, $2)`,
		stream, payload,
	)
	return err
}

func (r *OutboxRepository) FetchUnpublished(ctx context.Context, db DBTX, limit int) ([]OutboxEvent, error) {
	rows, err := db.Query(ctx,
		`SELECT id, stream, payload
		FROM outbox_events
		WHERE published = false
		ORDER BY id
		LIMIT $1
		FOR UPDATE SKIP LOCKED`,
		limit,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var events []OutboxEvent
	for rows.Next() {
		var e OutboxEvent
		if err := rows.Scan(&e.ID, &e.Stream, &e.Payload); err != nil {
			return nil, err
		}
		events = append(events, e)
	}
	return events, rows.Err()
}

func (r *OutboxRepository) MarkPublished(ctx context.Context, db DBTX, ids []int64) error {
	_, err := db.Exec(ctx,
		`UPDATE outbox_events SET published = true WHERE id = ANY($1)`,
		ids,
	)
	return err
}

func (r *OutboxRepository) DeleteOldPublished(ctx context.Context, db DBTX, olderThan any) (int64, error) {
	tag, err := db.Exec(ctx,
		`DELETE FROM outbox_events WHERE published = true AND created_at < $1`,
		olderThan,
	)
	if err != nil {
		return 0, err
	}
	return tag.RowsAffected(), nil
}

